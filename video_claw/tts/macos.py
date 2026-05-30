"""macOS `say` TTS provider.

Free, offline, and bundled with every Mac. Uses the system `say` command to
write a `.aiff`, then `afconvert` (also bundled with macOS) to transcode to
16-bit PCM `.wav`. We stay on Apple tools by default because they're
guaranteed available on macOS and don't depend on the ffmpeg build the user
happens to have. If `afconvert` is missing for some reason, we fall back to
ffmpeg.

Caveats:
  * macOS-only. On Linux we raise immediately with a clear error.
  * No word-level timing. Callers that need alignment (caption burn) will
    fall back to estimated timing based on character count + speaking rate.
  * Voice quality is "decent" — fine for long technical walkthroughs, not
    flashy for "Hi, I'm Becky" intros (use ElevenLabs for those).

Public API:
    synthesize(text, out_path, *, voice="Samantha") -> Path
"""
from __future__ import annotations
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# Default voice. Samantha ships with every macOS install since 10.x; using
# this avoids forcing users to download an enhanced voice the first time.
DEFAULT_VOICE = "Samantha"

# Set once we've warned that only basic-quality voices are installed, so the
# download hint prints at most once per process instead of per slide.
_warned_basic_only = False


def _require_macos() -> None:
    """Raise if we're not on macOS. Linux users picking `macos` get a clear hint."""
    if platform.system() != "Darwin":
        raise RuntimeError(
            "the macos TTS provider only works on macOS — "
            "use elevenlabs or deepgram on Linux."
        )


def _require_binary(name: str) -> str:
    """Resolve `name` on PATH or raise with a hint."""
    p = shutil.which(name)
    if not p:
        raise RuntimeError(
            f"`{name}` not found on PATH; macOS TTS needs Apple's built-in {name}."
        )
    return p


def _list_installed_voices(say_bin: str) -> list[str]:
    """Installed voice names from `say -v ?`.

    Each line looks like `Zoe (Premium)      en_US    # sample text`. The voice
    name can contain spaces and parentheses; the locale token (e.g. `en_US`) is
    the first short token containing `_`. Everything before it is the name.
    """
    res = subprocess.run([say_bin, "-v", "?"], capture_output=True, text=True)
    voices: list[str] = []
    for line in res.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        name_tokens: list[str] = []
        for tok in parts:
            if "_" in tok and len(tok) <= 6:
                break
            name_tokens.append(tok)
        if name_tokens:
            voices.append(" ".join(name_tokens))
    return voices


def _installed_voice_records(say_bin: str) -> list[tuple[str, str]]:
    """Return [(name, locale), ...] from `say -v ?`.

    Each line is `Zoe (Premium)      en_US    # sample`. The locale is the first
    short token containing `_`; everything before it is the (space-containing)
    voice name. Same parsing rule as `_list_installed_voices`, but also keeps
    the locale so we can filter to English.
    """
    res = subprocess.run([say_bin, "-v", "?"], capture_output=True, text=True)
    records: list[tuple[str, str]] = []
    for line in res.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        name_tokens: list[str] = []
        locale = ""
        for tok in parts:
            if "_" in tok and len(tok) <= 6:
                locale = tok
                break
            name_tokens.append(tok)
        if name_tokens:
            records.append((" ".join(name_tokens), locale))
    return records


def _voice_quality(name: str) -> int:
    """3 = Premium, 2 = Enhanced, 1 = basic (from the name suffix)."""
    low = name.lower()
    if "(premium)" in low:
        return 3
    if "(enhanced)" in low:
        return 2
    return 1


def _best_installed_voice(say_bin: str | None = None) -> str:
    """Highest-quality installed English voice (Premium > Enhanced > basic).

    Falls back to Samantha (or the first English basic voice) and prints a
    one-time download hint when only basic voices are installed.
    """
    global _warned_basic_only
    say_bin = say_bin or shutil.which("say") or "say"
    english = [(n, loc) for (n, loc) in _installed_voice_records(say_bin)
               if loc.lower().startswith("en")]
    if not english:
        return DEFAULT_VOICE

    best_name, best_q = english[0][0], _voice_quality(english[0][0])
    for name, _loc in english[1:]:
        q = _voice_quality(name)
        if q > best_q:
            best_name, best_q = name, q

    if best_q <= 1:  # only basic voices available
        if not _warned_basic_only:
            _warned_basic_only = True
            print("  [macos-tts] for better narration, download a Premium voice "
                  "in System Settings > Accessibility > Spoken Content.")
        for name, _loc in english:
            if name.lower().startswith("samantha"):
                return name
        return best_name
    return best_name


def _resolve_voice(requested: str, say_bin: str) -> str:
    """Resolve `requested` to an installed voice (case-insensitive, substring).

    Premium voices like "Zoe (Premium)" must be downloaded by the user. If the
    requested voice isn't installed, fall back to the always-present default
    with a printed hint rather than letting `say` fail.
    """
    installed = _list_installed_voices(say_bin)
    req = requested.lower()
    for v in installed:           # exact (case-insensitive) wins
        if v.lower() == req:
            return v
    for v in installed:           # then forward substring: "Zoe" -> "Zoe (Premium)"
        if req in v.lower():
            return v
    print(
        f'  [macos-tts] voice "{requested}" not installed; download it in '
        f'System Settings > Accessibility > Spoken Content. '
        f'Falling back to {DEFAULT_VOICE}.'
    )
    return DEFAULT_VOICE


def synthesize(text: str, out_path: Path, *, voice: str = "auto") -> Path:
    """Speak `text` with the macOS `say` command and write 16-bit PCM wav to `out_path`.

    macOS `say` can emit WAVE directly when given `--file-format=WAVE` plus a
    PCM data-format spec, so we skip the historical aiff -> afconvert step.
    We use LEI16@22050 mono: little-endian signed 16-bit PCM, 22050 Hz —
    the same format `afconvert` would have produced anyway, and the shape
    that ffmpeg's silenceremove + atempo filters handle cleanly downstream.

    Voice tip: run `say -v ?` to list installed voices. Anything in that
    output works as the `voice` arg.
    """
    _require_macos()
    say = _require_binary("say")
    if not voice or voice == "auto":
        voice = _best_installed_voice(say)
    else:
        voice = _resolve_voice(voice, say)
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        say, "-v", voice,
        "-o", str(out_path),
        "--file-format=WAVE",
        "--data-format=LEI16@22050",
        text,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode(errors="ignore")[-300:]
        raise RuntimeError(f"macOS `say` failed (exit {e.returncode}): {err}") from e

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"macOS say synthesis produced no output at {out_path}")
    return out_path


def is_available() -> bool:
    """True iff we're on macOS and `say` is callable. Used by the setup wizard."""
    if platform.system() != "Darwin":
        return False
    return shutil.which("say") is not None


if __name__ == "__main__":  # pragma: no cover - quick manual sanity check
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out.wav")
    synthesize("This is a one second narration test.", out)
    print(f"wrote {out}")
