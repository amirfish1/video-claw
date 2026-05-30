"""Text-to-speech providers: ElevenLabs (primary), Deepgram, macOS `say`.

Each `make_audio_<provider>` takes `(text, idx, *, workdir, cache, tts_cfg)`
and returns `(m4a_path, duration_seconds)`. ElevenLabs additionally writes
an alignment JSON sidecar (`narr_NN.alignment.json` in workdir) for
caption timing. Deepgram and macOS produce no word-level alignment;
caption flow degrades to estimated timing.

Caching is wired through `cache.run`:
  - kind="tts" caches raw provider output (mp3 / wav / optional alignment sidecar)
  - kind="m4a" caches the silenceremove+atempo m4a encode

Voice defaults (DO NOT change without reading CLAUDE.md):
  ElevenLabs: cgSgspJ2msm6clMCkdW9  (Jessica)
  Deepgram:   aura-2-thalia-en
  macOS say:  Samantha               (system voice, always installed)
"""
from __future__ import annotations
import base64
import json
import platform
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

from .. import keys
from . import macos as _macos


DEFAULT_TTS = {
    "provider": "auto",
    "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.0,
    "deepgram_voice": "aura-2-thalia-en",
    "macos_voice": "auto",
}


def _ffprobe_duration(path: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(res.stdout.strip())


def _encode_to_m4a(src: Path, dst: Path, rate: float) -> Path:
    """AAC m4a with silenceremove (trim leading + collapse internal >0.25s
    pauses) and optional atempo speedup. Mirrors growth-machine make_video.py.
    """
    filters = [
        "silenceremove=start_periods=1:start_duration=0:start_threshold=-40dB"
        ":stop_periods=-1:stop_duration=0.25:stop_threshold=-38dB",
    ]
    if abs(rate - 1.0) > 1e-3:
        filters.append(f"atempo={rate}")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-filter:a", ",".join(filters),
        "-c:a", "aac", "-b:a", "192k", str(dst),
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return dst


def make_audio_elevenlabs(text: str, idx: int, *, workdir: Path,
                          cache, tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """ElevenLabs /text-to-speech/{voice}/with-timestamps → m4a + alignment JSON.
    Cached by (text, voice, model). m4a encode separately cached by (mp3, rate)."""
    api_key = keys.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ElevenLabs requested but no ELEVENLABS_API_KEY found.\n"
            "Run: video-claw keys set EL=<your-key>"
        )

    voice_id = tts_cfg.get("voice_id", DEFAULT_TTS["voice_id"])
    model = tts_cfg.get("model", DEFAULT_TTS["model"])
    rate = float(tts_cfg.get("speaking_rate", DEFAULT_TTS["speaking_rate"]))

    def _generate(out_path: Path) -> None:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
        body = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5, "similarity_boost": 0.75,
                "style": 0.0, "use_speaker_boost": True,
            },
        }
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.load(r)
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="ignore")[:300]
            raise RuntimeError(f"ElevenLabs error {e.code}: {err}")
        out_path.write_bytes(base64.b64decode(res["audio_base64"]))
        align_path = out_path.with_suffix(".alignment.json")
        align_path.write_text(json.dumps(res.get("alignment") or {}))

    tts_key = [text, "voice", voice_id, "model", model]
    cached_mp3 = cache.run("tts", tts_key, "mp3", _generate)

    # Copy cached output to canonical per-slide paths used downstream.
    target_mp3 = workdir / f"narr_{idx:02d}.mp3"
    target_align = workdir / f"narr_{idx:02d}.alignment.json"
    target_mp3.write_bytes(cached_mp3.read_bytes())
    align_src = cached_mp3.with_suffix(".alignment.json")
    if align_src.exists():
        target_align.write_text(align_src.read_text())

    m4a_key = [cached_mp3, "rate", round(rate, 4), "silenceremove", "0.25", "0.0"]

    def _m4a_gen(out_path: Path) -> None:
        _encode_to_m4a(target_mp3, out_path, rate=rate)

    cached_m4a = cache.run("m4a", m4a_key, "m4a", _m4a_gen)
    target_m4a = workdir / f"narr_{idx:02d}.m4a"
    target_m4a.write_bytes(cached_m4a.read_bytes())
    return target_m4a, _ffprobe_duration(target_m4a)


def make_audio_deepgram(text: str, idx: int, *, workdir: Path,
                        cache, tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """Deepgram Aura-2 TTS → m4a. No timestamp alignment available; captions
    that depend on word-level timings will be skipped for Deepgram slides.
    """
    api_key = keys.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Deepgram requested but no DEEPGRAM_API_KEY found.\n"
            "Run: video-claw keys set DG=<your-key>"
        )
    voice = tts_cfg.get("deepgram_voice", DEFAULT_TTS["deepgram_voice"])
    rate = float(tts_cfg.get("speaking_rate", DEFAULT_TTS["speaking_rate"]))
    url = f"https://api.deepgram.com/v1/speak?model={voice}&encoding=mp3"

    def _generate(out_path: Path) -> None:
        req = urllib.request.Request(
            url,
            data=json.dumps({"text": text}).encode(),
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                audio = r.read()
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="ignore")[:300]
            raise RuntimeError(f"Deepgram error {e.code}: {err}")
        out_path.write_bytes(audio)

    tts_key = [text, "deepgram", "voice", voice]
    cached_mp3 = cache.run("tts", tts_key, "mp3", _generate)
    target_mp3 = workdir / f"narr_{idx:02d}.mp3"
    target_mp3.write_bytes(cached_mp3.read_bytes())

    m4a_key = [cached_mp3, "rate", round(rate, 4), "silenceremove", "0.25", "0.0", "dg"]

    def _m4a_gen(out_path: Path) -> None:
        _encode_to_m4a(target_mp3, out_path, rate=rate)

    cached_m4a = cache.run("m4a", m4a_key, "m4a", _m4a_gen)
    target_m4a = workdir / f"narr_{idx:02d}.m4a"
    target_m4a.write_bytes(cached_m4a.read_bytes())
    return target_m4a, _ffprobe_duration(target_m4a)


def make_audio_macos(text: str, idx: int, *, workdir: Path,
                     cache, tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """macOS `say` -> wav -> m4a. Free, offline, macOS-only. No alignment.

    The heavy lifting lives in `video_claw.tts.macos.synthesize` so it can be
    imported directly from tests / external code.
    """
    voice = tts_cfg.get("macos_voice", DEFAULT_TTS["macos_voice"])
    rate = float(tts_cfg.get("speaking_rate", DEFAULT_TTS["speaking_rate"]))

    def _generate(out_path: Path) -> None:
        # synthesize writes a wav directly to out_path.
        _macos.synthesize(text, out_path, voice=voice)

    tts_key = [text, "macos", "voice", voice]
    cached_wav = cache.run("tts", tts_key, "wav", _generate)
    target_wav = workdir / f"narr_{idx:02d}.wav"
    target_wav.write_bytes(cached_wav.read_bytes())

    m4a_key = [cached_wav, "rate", round(rate, 4), "silenceremove", "0.25", "0.0", "macos"]

    def _m4a_gen(out_path: Path) -> None:
        _encode_to_m4a(target_wav, out_path, rate=rate)

    cached_m4a = cache.run("m4a", m4a_key, "m4a", _m4a_gen)
    target_m4a = workdir / f"narr_{idx:02d}.m4a"
    target_m4a.write_bytes(cached_m4a.read_bytes())
    return target_m4a, _ffprobe_duration(target_m4a)


def resolve_provider(tts_cfg: Dict[str, Any]) -> str:
    """Resolve a (possibly "auto") provider to a concrete one from keys + platform.

    Explicit providers pass through unchanged (the per-provider function still
    raises its own clear error if that provider's key is missing). "auto" (the
    default) picks the best available: ElevenLabs -> Deepgram -> macOS local;
    if none is possible (Linux, no keys) it raises a single clear error.
    Pure: no network, no synthesis. Safe to call repeatedly (idempotent).
    """
    provider = (tts_cfg or {}).get("provider") or "auto"
    provider = provider.lower()
    if provider in ("elevenlabs", "el", "eleven"):
        return "elevenlabs"
    if provider == "deepgram":
        return "deepgram"
    if provider in ("macos", "say", "macos-say"):
        return "macos"
    if provider != "auto":
        return provider  # unknown explicit value; dispatch will raise a clear error

    if keys.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    if keys.get("DEEPGRAM_API_KEY"):
        return "deepgram"
    if platform.system() == "Darwin":
        return "macos"
    raise RuntimeError(
        "No TTS available: set ELEVENLABS_API_KEY or DEEPGRAM_API_KEY, or run "
        "on macOS for free local TTS (provider=auto found no usable option)."
    )


def make_audio(text: str, idx: int, *, workdir: Path, cache,
               tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """Dispatch to the resolved provider. `provider:"auto"` (the default) picks
    the best available from the keys present (see `resolve_provider`)."""
    provider = resolve_provider(tts_cfg)
    tts_cfg = {**tts_cfg, "provider": provider}
    if provider == "deepgram":
        return make_audio_deepgram(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    if provider == "macos":
        return make_audio_macos(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    if provider == "elevenlabs":
        return make_audio_elevenlabs(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    raise ValueError(
        f"Unknown TTS provider: {provider!r}. "
        "Use 'auto', 'elevenlabs', 'deepgram', or 'macos'."
    )
