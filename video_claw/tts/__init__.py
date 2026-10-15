"""Text-to-speech providers: ElevenLabs (primary), Deepgram, macOS `say`.

Each `make_audio_<provider>` takes `(text, idx, *, workdir, cache, tts_cfg)`
and returns `(m4a_path, duration_seconds)`. ElevenLabs additionally writes
an alignment JSON sidecar (`narr_NN.alignment.json` in workdir) for
caption timing. Deepgram and macOS produce no word-level alignment;
caption flow degrades to estimated timing.

Caching is wired through `cache.run`:
  - kind="tts" caches raw provider output (master JSON for ElevenLabs, mp3/wav otherwise)
  - kind="m4a" caches aligned ElevenLabs slices, or silenceremove+atempo for other providers

Voice defaults (DO NOT change without reading CLAUDE.md):
  ElevenLabs: cgSgspJ2msm6clMCkdW9  (Jessica)
  Deepgram:   aura-2-thalia-en
  macOS say:  Samantha               (system voice, always installed)
"""
from __future__ import annotations
import base64
import json
import math
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


def cache_settings(tts_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Only settings that affect raw synthesis, with aliases/defaults resolved."""
    cfg = {**DEFAULT_TTS, **tts_cfg}
    provider = resolve_provider(cfg)
    fields = {
        "elevenlabs": ("voice_id", "model"),
        "deepgram": ("deepgram_voice",),
        "macos": ("macos_voice",),
    }
    if provider not in fields:
        raise ValueError(f"Unknown TTS provider: {provider!r}")
    return {"provider": provider, **{key: cfg[key] for key in fields[provider]}}


def audio_cache_entry(text: str, tts_cfg: Dict[str, Any]) -> Tuple[list, str]:
    """Shared by synthesis and diagnostics; preserve the existing cache keys."""
    cfg = cache_settings(tts_cfg)
    if cfg["provider"] == "elevenlabs":
        return [text, "voice", cfg["voice_id"], "model", cfg["model"]], "mp3"
    if cfg["provider"] == "deepgram":
        return [text, "deepgram", "voice", cfg["deepgram_voice"]], "mp3"
    return [text, "macos", "voice", cfg["macos_voice"]], "wav"


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


def _request_elevenlabs(text: str, tts_cfg: Dict[str, Any]) -> dict:
    """One timestamped request. Called only on a master-cache miss."""
    api_key = keys.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ElevenLabs requested but no ELEVENLABS_API_KEY found.\n"
            "Run: video-claw keys set EL=<your-key>"
        )
    voice_id = tts_cfg.get("voice_id", DEFAULT_TTS["voice_id"])
    body = {
        "text": text,
        "model_id": tts_cfg.get("model", DEFAULT_TTS["model"]),
        "voice_settings": {
            "stability": 0.5, "similarity_boost": 0.75,
            "style": 0.0, "use_speaker_boost": True,
        },
    }
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
        data=json.dumps(body).encode(),
        headers={"xi-api-key": api_key, "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="ignore")[:300]
        raise RuntimeError(f"ElevenLabs error {e.code}: {err}") from e


def _validate_alignment(text: str, alignment: dict) -> tuple[list, list, list]:
    """Use original-text alignment, never normalized-text character offsets.

    Fail explicitly if the provider cannot map the requested text. Guessing
    offsets or retrying per slide could both corrupt speech and incur more cost.
    """
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    if (not chars or any(not isinstance(c, str) or len(c) != 1 for c in chars)
            or "".join(chars) != text or len(starts) != len(chars)
            or len(ends) != len(chars)):
        raise ValueError("ElevenLabs alignment does not match the master narration")
    try:
        starts = [float(t) for t in starts]
        ends = [float(t) for t in ends]
    except (TypeError, ValueError) as e:
        raise ValueError("ElevenLabs alignment has invalid timestamps") from e
    if (any(not math.isfinite(s) or not math.isfinite(e) or s < 0 or e < s
            for s, e in zip(starts, ends))
            or any(b < a for a, b in zip(starts, starts[1:]))
            or any(b < a for a, b in zip(ends, ends[1:]))):
        raise ValueError("ElevenLabs alignment has invalid timestamps")
    return chars, starts, ends


def _tempo_filters(rate: float) -> list[str]:
    # Chaining factors in [0.5, 2] also works with older ffmpeg versions.
    filters = []
    while rate < 0.5:
        filters.append("atempo=0.5")
        rate /= 0.5
    while rate > 2:
        filters.append("atempo=2")
        rate /= 2
    if rate != 1.0:
        filters.append(f"atempo={rate}")
    return filters


def make_audio_elevenlabs_master(narrations: list[str], *, workdir: Path,
                                 cache, tts_cfg: Dict[str, Any],
                                 rates: list[float],
                                 indices: list[int] | None = None) -> list[Tuple[Path, float]]:
    """Synthesize the whole script once, then cut it on its original timeline.

    Cache the response (audio AND alignment) atomically by text/voice/model.
    Slice before atempo so different slide rates need no global correction;
    segment duration is (end-start)/rate. Sidecars keep unsped, slide-local
    timestamps for captions.py, which divides by that slide's rate exactly once.
    No silenceremove and no ffprobe on the cut AAC files.
    """
    if not narrations or any(not isinstance(t, str) or not t.strip() for t in narrations):
        raise ValueError("Every slide needs narration text")
    rates = [float(rate) for rate in rates]
    if len(rates) != len(narrations) or any(not math.isfinite(r) or r <= 0 for r in rates):
        raise ValueError("Each slide needs a finite, positive speaking rate")
    indices = list(range(len(narrations))) if indices is None else indices
    if len(indices) != len(narrations):
        raise ValueError("indices must match narrations")
    texts = [t.strip() for t in narrations]
    master_text = "\n\n".join(texts)
    offsets = []
    offset = 0
    for text in texts:
        offsets.append((offset, offset + len(text)))
        offset += len(text) + 2

    def _generate(out_path: Path) -> None:
        response = _request_elevenlabs(master_text, tts_cfg)
        # A complete response remains cached even if alignment validation fails:
        # a rerun should not silently buy the same unusable audio again.
        tmp = out_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(response))
        tmp.replace(out_path)

    master_key = ["elevenlabs-master-v1", master_text,
                  tts_cfg.get("voice_id", DEFAULT_TTS["voice_id"]),
                  tts_cfg.get("model", DEFAULT_TTS["model"])]
    cached_response = cache.run("tts", master_key, "json", _generate)
    response = json.loads(cached_response.read_text())
    chars, starts, ends = _validate_alignment(master_text, response.get("alignment") or {})
    master_mp3 = workdir / "narr_master.mp3"
    master_mp3.write_bytes(base64.b64decode(response["audio_base64"], validate=True))
    (workdir / "narr_master.alignment.json").write_text(json.dumps(response["alignment"]))

    # Split separator pauses halfway. Adjacent segments are contiguous, and
    # neither slide loses a spoken character. Preserve the initial lead-in.
    boundaries = [0.0]
    for (_, prev_end), (next_start, _) in zip(offsets, offsets[1:]):
        if ends[prev_end - 1] > starts[next_start]:
            raise ValueError("ElevenLabs alignment overlaps a slide boundary")
        boundaries.append((ends[prev_end - 1] + starts[next_start]) / 2)
    boundaries.append(ends[-1])
    if any(b <= a for a, b in zip(boundaries, boundaries[1:])):
        raise ValueError("ElevenLabs alignment gives an empty slide segment")

    results = []
    for idx, (char_start, char_end), rate, start, end in zip(
            indices, offsets, rates, boundaries, boundaries[1:]):
        def _slice(out_path: Path) -> None:
            filters = [f"atrim=start={start}:end={end}", "asetpts=PTS-STARTPTS"]
            filters.extend(_tempo_filters(rate))
            tmp = out_path.with_suffix(".tmp.m4a")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(master_mp3), "-vn",
                 "-filter:a", ",".join(filters), "-c:a", "aac", "-b:a", "192k", str(tmp)],
                check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            )
            tmp.replace(out_path)

        segment_key = [cached_response, "aligned-slice-v1", start, end, rate]
        cached_m4a = cache.run("m4a", segment_key, "m4a", _slice)
        target = workdir / f"narr_{idx:02d}.m4a"
        target.write_bytes(cached_m4a.read_bytes())
        local_alignment = {
            "characters": chars[char_start:char_end],
            "character_start_times_seconds": [t - start for t in starts[char_start:char_end]],
            "character_end_times_seconds": [t - start for t in ends[char_start:char_end]],
        }
        (workdir / f"narr_{idx:02d}.alignment.json").write_text(json.dumps(local_alignment))
        results.append((target, (end - start) / rate))
    return results


def make_audio_elevenlabs(text: str, idx: int, *, workdir: Path,
                          cache, tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """Single-slide compatibility entrypoint with the same alignment guarantees."""
    return make_audio_elevenlabs_master(
        [text], workdir=workdir, cache=cache, tts_cfg=tts_cfg,
        rates=[float(tts_cfg.get("speaking_rate", DEFAULT_TTS["speaking_rate"]))],
        indices=[idx],
    )[0]


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

    tts_key, _ = audio_cache_entry(text, {**tts_cfg, "provider": "deepgram"})
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

    tts_key, _ = audio_cache_entry(text, {**tts_cfg, "provider": "macos"})
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
