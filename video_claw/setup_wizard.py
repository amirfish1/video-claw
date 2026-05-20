"""Interactive setup wizard for video-claw.

Walks the user through configuring API keys for the providers we support:
  - ElevenLabs   (paid TTS + word-level captions)
  - fal.ai       (optional, lip-synced presenter)
  - Deepgram     (optional, cheaper paid TTS, no word-level captions)

There's also a free macOS-only `say` provider that needs no key — we
mention it up front so users know they can opt into free TTS instead of
ElevenLabs if they're on a Mac.

Designed to also work in a `curl ... | bash` install context where stdin is
the script itself. In that case we read user input from /dev/tty directly,
not from sys.stdin. The caller hand-off is handled by install.sh which uses
`exec </dev/tty` before invoking us — but as a belt-and-braces measure we
also re-open /dev/tty inside the wizard whenever stdin isn't a TTY.
"""
from __future__ import annotations
import os
import platform
import sys
from pathlib import Path
from typing import Optional, TextIO, Tuple

from . import keys as keys_mod


# TTS-provider intro. Printed before any key prompt so the user understands
# they have a free option (macOS say) and aren't forced to paste an EL key.
def _tts_intro() -> str:
    macos_line = "  1. macOS say (free, built-in)  — voice quality: decent, no captions, macOS-only"
    if platform.system() != "Darwin":
        macos_line += "  [unavailable on this OS]"
    return (
        "TTS provider — three options:\n"
        f"{macos_line}\n"
        "  2. ElevenLabs Turbo v2.5 (~$0.30/min audio, paid) — voice quality: high, with word-level captions\n"
        "  3. Deepgram Aura-2 (cheaper than ElevenLabs, no word captions)\n"
        "\n"
        'For "Hi I\'m Becky" intros: ElevenLabs is the typical pick.\n'
        "For long technical walkthroughs: macOS say is great, free, and offline."
    )


# Provider copy. Edit these strings if pricing changes upstream.
ELEVENLABS_BLURB = (
    "Paid TTS, also drives word-level captions. ~$0.30/min generated audio. "
    "Free tier exists but rate-limited. Required ONLY if you want option 2 above."
)
FAL_BLURB = (
    "Only needed if any slide has `lipsync: True`. fal.ai OmniHuman 1.5 costs "
    "~$0.16/sec of generated lipsync video. Skip if you don't plan to use a "
    "presenter avatar."
)
DEEPGRAM_BLURB = (
    "Alternative paid TTS provider. Cheaper than ElevenLabs but no word-level "
    "captions (only SRT-style timing). Required ONLY if you want option 3 above "
    "(i.e. you plan to set `tts.provider='deepgram'`)."
)


# ---------------------------------------------------------------------------
# TTY handling for `curl | bash` contexts
# ---------------------------------------------------------------------------

def _open_tty() -> Tuple[Optional[TextIO], Optional[TextIO]]:
    """Return (input_stream, output_stream) suitable for interactive prompts.

    When stdin is not a TTY (e.g. we were piped via `curl ... | bash` and
    then handed off to python), try to open /dev/tty directly so the user
    can still type. Returns (None, None) if no TTY is available; the caller
    should bail out non-interactively.
    """
    if sys.stdin.isatty() and sys.stdout.isatty():
        return sys.stdin, sys.stdout
    try:
        tty_in = open("/dev/tty", "r")
        tty_out = open("/dev/tty", "w")
        return tty_in, tty_out
    except OSError:
        return None, None


def _readline(stream: TextIO) -> str:
    line = stream.readline()
    if not line:
        return ""
    return line.rstrip("\r\n")


def _print(stream: TextIO, msg: str = "") -> None:
    stream.write(msg + "\n")
    stream.flush()


def _prompt(in_s: TextIO, out_s: TextIO, label: str) -> str:
    """Write `label` to out_s without a newline, read one line from in_s."""
    out_s.write(label)
    out_s.flush()
    return _readline(in_s)


def _hint(existing: Optional[str]) -> str:
    """One-line hint for the prompt suffix: `[keep current sk_...XYZW]` or `[skip]`."""
    if existing:
        return f" [keep current {keys_mod.mask(existing)}]"
    return " [Enter to skip]"


def _provenance_lines(name: str, out_s: TextIO) -> None:
    """Print the SOURCE of an existing key (file path + mtime, or env var name).

    This was the user's biggest trust concern post-0.3.0 — "is this MY key
    or some dev artifact?". Always surface where the value came from before
    asking for a replacement.
    """
    prov = keys_mod.key_provenance(name)
    if not prov:
        return
    masked = keys_mod.mask(prov["value"])
    _print(out_s, f"  found existing key ({masked})")
    _print(out_s, f"  source: {prov['where']}")
    if prov.get("mtime"):
        _print(out_s, f"  last set: {prov['mtime']}")


def _looks_like_key(value: str) -> bool:
    """Lenient sanity check. Reject obviously-empty / too-short values."""
    v = value.strip()
    if len(v) < 12:
        return False
    # Allow most printable ascii; just bar whitespace inside.
    for ch in v:
        if ch.isspace():
            return False
    return True


# ---------------------------------------------------------------------------
# Wizard
# ---------------------------------------------------------------------------

def _collect(name: str, blurb: str, existing: Optional[str],
             in_s: TextIO, out_s: TextIO, *, required: bool) -> Optional[str]:
    """Run one provider's prompt cycle. Returns the new value, or None to skip.

    When `existing` is set, prints source/mtime provenance before the prompt
    so the user knows whether the value is theirs or a leftover.
    """
    _print(out_s)
    tag = "REQUIRED" if required else "OPTIONAL"
    _print(out_s, f"--- {name} ({tag}) ---")
    _print(out_s, blurb)
    if existing:
        _provenance_lines(name, out_s)
    while True:
        if existing:
            label = f"Paste a new key, or press Enter to keep: "
        else:
            label = f"Paste your {name} key{_hint(existing)}: "
        raw = _prompt(in_s, out_s, label)
        raw = raw.strip()
        if not raw:
            if existing:
                return existing  # keep existing
            if required:
                _print(out_s,
                       f"  (no value entered; {name} is required for the chosen "
                       f"provider. You can rerun `video-claw setup` later.)")
            return None
        if not _looks_like_key(raw):
            _print(out_s, "  That doesn't look like a key (too short or has whitespace).")
            _print(out_s, "  Try again, or press Enter to skip.")
            continue
        return raw


def run_wizard() -> int:
    """Interactive wizard. Returns shell-style exit code."""
    in_s, out_s = _open_tty()
    if in_s is None or out_s is None:
        sys.stderr.write(
            "video-claw setup: no TTY available; can't prompt for keys.\n"
            "Run `video-claw setup` directly in your terminal, or set\n"
            "ELEVENLABS_API_KEY / FAL_API_KEY / DEEPGRAM_API_KEY env vars.\n"
        )
        return 2

    existing = keys_mod.load_keys()

    _print(out_s, "")
    _print(out_s, "video-claw setup")
    _print(out_s, "================")
    _print(out_s,
           f"Keys will be stored in {keys_mod.KEYS_FILE} "
           "(readable only by you — Unix permission 0600).")
    _print(out_s, "(re-run this wizard any time with: video-claw setup)")
    _print(out_s, "Existing values are kept on Enter.")

    _print(out_s, "")
    _print(out_s, _tts_intro())

    # ElevenLabs is no longer REQUIRED at the wizard level — macOS users can
    # pick `tts.provider="macos"` and skip it entirely. Mark it optional and
    # let `video-claw render` re-check at render time based on the project's
    # actual `tts.provider` setting.
    el = _collect(
        "ELEVENLABS_API_KEY", ELEVENLABS_BLURB,
        existing.get("ELEVENLABS_API_KEY"),
        in_s, out_s, required=False,
    )
    fal = _collect(
        "FAL_API_KEY", FAL_BLURB,
        existing.get("FAL_API_KEY"),
        in_s, out_s, required=False,
    )
    dg = _collect(
        "DEEPGRAM_API_KEY", DEEPGRAM_BLURB,
        existing.get("DEEPGRAM_API_KEY"),
        in_s, out_s, required=False,
    )

    updates = {}
    if el:
        updates["ELEVENLABS_API_KEY"] = el
    if fal:
        updates["FAL_API_KEY"] = fal
    if dg:
        updates["DEEPGRAM_API_KEY"] = dg

    if updates:
        path = keys_mod.save_keys(updates)
        _print(out_s, "")
        _print(out_s, f"Saved keys to {path}.")
    else:
        _print(out_s, "")
        _print(out_s, "No keys saved.")

    _print(out_s, "")
    _print(out_s, "Verifying keys with each provider...")
    rc = print_status(stream=out_s)

    _print(out_s, "")
    _print(out_s, "Next: `video-claw init <project>` to start your first video.")
    _print(out_s, "Or open Claude Code and say: \"make me a 30-second video about X\".")
    return 0 if rc == 0 else 0  # don't fail wizard on optional-key network errors


# ---------------------------------------------------------------------------
# --check (non-interactive status)
# ---------------------------------------------------------------------------

def print_status(stream: Optional[TextIO] = None) -> int:
    """Run `keys test` and print per-key status. Returns 0 unless a REQUIRED key fails."""
    if stream is None:
        stream = sys.stdout
    results = keys_mod.test_all()

    label_map = {
        "ELEVENLABS_API_KEY": "ElevenLabs",
        "FAL_API_KEY": "FAL (fal.ai lipsync)",
        "DEEPGRAM_API_KEY": "Deepgram",
    }
    # All three are technically optional now that macOS `say` is a real free
    # TTS option — render-time validation still complains if you pick a
    # provider whose key is missing. The wizard's job is just to show status.
    optional = {"ELEVENLABS_API_KEY", "FAL_API_KEY", "DEEPGRAM_API_KEY"}
    required_failed = False
    for name in ("ELEVENLABS_API_KEY", "FAL_API_KEY", "DEEPGRAM_API_KEY"):
        ok, msg = results[name]
        label = label_map[name]
        if ok:
            mark = "[ok ]"
        elif msg == "not set" and name in optional:
            mark = "[opt]"
            msg = "skipped"
        else:
            mark = "[FAIL]"
            if name not in optional:
                required_failed = True
        _print(stream, f"  {mark} {label}: {msg}")

    return 1 if required_failed else 0


def run_check() -> int:
    """Non-interactive: just print status. Used by CI and install scripts."""
    return print_status()
