"""End-to-end smoke tests for the macOS `say` TTS provider.

These tests only run on macOS because `say` is Apple-only. On Linux / CI
without a Mac runner, the platform guard skips the heavy tests but still
verifies that picking the provider on a non-macOS host fails loudly with
a clear error (no silent fall-through to ElevenLabs).
"""
from __future__ import annotations
import platform
import struct
import sys
import wave
from pathlib import Path

import pytest


IS_MACOS = platform.system() == "Darwin"


# ---------------------------------------------------------------------------
# Platform smoke: import works everywhere, provider rejects non-macOS upfront.
# ---------------------------------------------------------------------------

def test_imports_everywhere():
    """The provider module must import even on Linux — we just refuse to run."""
    from video_claw.tts import macos  # noqa: F401
    from video_claw.tts.macos import synthesize, is_available  # noqa: F401


def test_is_available_matches_platform():
    from video_claw.tts.macos import is_available
    if IS_MACOS:
        # macOS always ships `say`; if this fails the build env is broken.
        assert is_available() is True
    else:
        assert is_available() is False


@pytest.mark.skipif(IS_MACOS, reason="non-macOS error path only meaningful off-Mac")
def test_synthesize_errors_on_linux(tmp_path):
    from video_claw.tts.macos import synthesize
    with pytest.raises(RuntimeError, match="only works on macOS"):
        synthesize("hello", tmp_path / "out.wav")


# ---------------------------------------------------------------------------
# Real end-to-end synthesis (macOS only).
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not IS_MACOS, reason="say(1) only exists on macOS")
def test_synthesize_writes_pcm_wav(tmp_path):
    """Speak a one-second narration and assert the file is parseable PCM."""
    from video_claw.tts.macos import synthesize

    out = tmp_path / "out.wav"
    synthesize("This is a one second narration test.", out)

    assert out.exists(), "synthesize should produce out.wav"
    assert out.stat().st_size > 1024, "wav is suspiciously small"

    # Parse as PCM wav via stdlib. If `say -> afconvert` produced something
    # non-PCM we'd get a wave.Error here.
    with wave.open(str(out), "rb") as w:
        assert w.getnchannels() in (1, 2), f"unexpected channel count {w.getnchannels()}"
        assert w.getsampwidth() == 2, f"expected 16-bit PCM, got {w.getsampwidth() * 8}-bit"
        # Defensive: there should be at least 0.3 seconds of audio.
        nframes = w.getnframes()
        rate = w.getframerate()
        assert nframes / rate > 0.3, f"clip too short: {nframes/rate:.2f}s"


@pytest.mark.skipif(not IS_MACOS, reason="say(1) only exists on macOS")
def test_dispatch_via_make_audio(tmp_path):
    """Round-trip via the public `make_audio` dispatcher with provider='macos'.

    Confirms that the cache + m4a encode wiring works for the new provider.
    """
    from video_claw import tts as tts_mod
    from video_claw.cache import Cache

    workdir = tmp_path / "work"
    workdir.mkdir()
    cache = Cache(workdir)

    cfg = {"provider": "macos", "macos_voice": "Samantha", "speaking_rate": 1.0}
    m4a, dur = tts_mod.make_audio(
        "Smoke test for the macOS provider.",
        idx=0, workdir=workdir, cache=cache, tts_cfg=cfg,
    )
    assert m4a.exists()
    assert m4a.suffix == ".m4a"
    assert dur > 0.3, f"narration too short: {dur:.2f}s"


# ---------------------------------------------------------------------------
# Voice resolution: premium voices may be missing; we match + fall back.
# ---------------------------------------------------------------------------

def test_list_voices_parses_premium_name(monkeypatch):
    from video_claw.tts import macos
    import subprocess as sp
    sample = "Samantha           en_US    # Hello\nZoe (Premium)      en_US    # Hi\n"

    class _R:
        stdout = sample

    monkeypatch.setattr(sp, "run", lambda *a, **k: _R())
    voices = macos._list_installed_voices("say")
    assert "Zoe (Premium)" in voices
    assert "Samantha" in voices


def test_resolve_voice_substring_match(monkeypatch):
    from video_claw.tts import macos
    monkeypatch.setattr(macos, "_list_installed_voices",
                        lambda b: ["Samantha", "Zoe (Premium)"])
    assert macos._resolve_voice("Zoe", "say") == "Zoe (Premium)"


def test_resolve_voice_falls_back_to_samantha(monkeypatch, capsys):
    from video_claw.tts import macos
    monkeypatch.setattr(macos, "_list_installed_voices", lambda b: ["Samantha"])
    assert macos._resolve_voice("Zoe (Premium)", "say") == "Samantha"
    assert "Falling back to Samantha" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Best-voice auto-detection (Premium > Enhanced > basic, English only).
# ---------------------------------------------------------------------------

def test_voice_records_capture_locale_and_name(monkeypatch):
    from video_claw.tts import macos
    import subprocess as sp
    sample = (
        "Samantha            en_US    # Hi\n"
        "Zoe (Premium)       en_US    # Hi\n"
        "Daniel (Enhanced)   en_GB    # Hi\n"
        "Amelie              fr_CA    # Bonjour\n"
    )

    class _R:
        stdout = sample

    monkeypatch.setattr(sp, "run", lambda *a, **k: _R())
    recs = macos._installed_voice_records("say")
    assert ("Zoe (Premium)", "en_US") in recs
    assert ("Daniel (Enhanced)", "en_GB") in recs
    assert ("Amelie", "fr_CA") in recs


def test_best_voice_prefers_premium_english(monkeypatch):
    from video_claw.tts import macos
    monkeypatch.setattr(macos, "_installed_voice_records", lambda b: [
        ("Samantha", "en_US"),
        ("Daniel (Enhanced)", "en_GB"),
        ("Zoe (Premium)", "en_US"),
        ("Amelie (Premium)", "fr_CA"),  # non-English, must be ignored
    ])
    assert macos._best_installed_voice("say") == "Zoe (Premium)"


def test_best_voice_basic_only_falls_back_to_samantha(monkeypatch, capsys):
    from video_claw.tts import macos
    macos._warned_basic_only = False
    monkeypatch.setattr(macos, "_installed_voice_records", lambda b: [
        ("Alex", "en_US"), ("Samantha", "en_US")])
    assert macos._best_installed_voice("say") == "Samantha"
    assert "Premium voice" in capsys.readouterr().out
