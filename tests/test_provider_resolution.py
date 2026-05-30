"""provider:auto resolves from the keys present + platform."""
from __future__ import annotations
import platform
import pytest


def _patch_keys(monkeypatch, mapping):
    from video_claw import keys
    monkeypatch.setattr(keys, "get", lambda name: mapping.get(name))


def test_explicit_provider_passes_through(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {})
    assert tts.resolve_provider({"provider": "deepgram"}) == "deepgram"
    assert tts.resolve_provider({"provider": "elevenlabs"}) == "elevenlabs"
    assert tts.resolve_provider({"provider": "macos"}) == "macos"


def test_auto_prefers_elevenlabs(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {"ELEVENLABS_API_KEY": "x", "DEEPGRAM_API_KEY": "y"})
    assert tts.resolve_provider({"provider": "auto"}) == "elevenlabs"


def test_auto_falls_to_deepgram(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {"DEEPGRAM_API_KEY": "y"})
    assert tts.resolve_provider({"provider": "auto"}) == "deepgram"


def test_auto_falls_to_macos_on_darwin(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {})
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert tts.resolve_provider({"provider": "auto"}) == "macos"


def test_auto_errors_on_linux_without_keys(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {})
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="No TTS"):
        tts.resolve_provider({"provider": "auto"})


def test_unset_provider_defaults_to_auto(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {"ELEVENLABS_API_KEY": "x"})
    assert tts.resolve_provider({}) == "elevenlabs"


def test_make_audio_auto_no_keys_non_darwin_errors(monkeypatch, tmp_path):
    from video_claw import tts
    from video_claw.cache import Cache
    _patch_keys(monkeypatch, {})
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="No TTS"):
        tts.make_audio("hi", 0, workdir=tmp_path, cache=Cache(tmp_path),
                       tts_cfg={"provider": "auto"})
