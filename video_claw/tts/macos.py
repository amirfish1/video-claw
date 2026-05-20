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


def synthesize(text: str, out_path: Path, *, voice: str = DEFAULT_VOICE) -> Path:
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
