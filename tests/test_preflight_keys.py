"""Preflight key check is auto-aware and degrades gracefully.

Surfaced by the no-key end-to-end render: the CLI preflight must let
`provider:"auto"` fall back to macOS local TTS instead of demanding a key, and
must treat a missing FAL key (lipsync) as a warning, not a hard block.
"""
from __future__ import annotations
import platform


def _project(tmp_path, tts_override, slides):
    from video_claw.config import Project, DEFAULT_CONFIG, _deep_merge
    cfg = _deep_merge(DEFAULT_CONFIG, {"tts": tts_override})
    return Project(project_dir=tmp_path, config=cfg, slides=slides)


def _no_keys(monkeypatch):
    from video_claw import keys as keys_mod
    monkeypatch.setattr(keys_mod, "load_keys", lambda: {})
    monkeypatch.setattr(keys_mod, "get", lambda name: None)
    for k in ("ELEVENLABS_API_KEY", "DEEPGRAM_API_KEY", "FAL_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def test_auto_no_keys_on_mac_ok(monkeypatch, tmp_path):
    from video_claw import cli
    _no_keys(monkeypatch)
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    proj = _project(tmp_path, {"provider": "auto"}, [{"narration": "hi"}])
    assert cli._ensure_keys_for(proj) is None


def test_auto_no_keys_on_linux_errors(monkeypatch, tmp_path):
    from video_claw import cli
    _no_keys(monkeypatch)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    proj = _project(tmp_path, {"provider": "auto"}, [{"narration": "hi"}])
    err = cli._ensure_keys_for(proj)
    assert err and "No TTS" in err


def test_explicit_elevenlabs_without_key_errors(monkeypatch, tmp_path):
    from video_claw import cli
    _no_keys(monkeypatch)
    proj = _project(tmp_path, {"provider": "elevenlabs"}, [{"narration": "hi"}])
    err = cli._ensure_keys_for(proj)
    assert err and "ELEVENLABS_API_KEY" in err


def test_lipsync_without_fal_warns_not_blocks(monkeypatch, tmp_path, capsys):
    from video_claw import cli, keys as keys_mod
    monkeypatch.setattr(keys_mod, "load_keys", lambda: {})
    monkeypatch.setattr(keys_mod, "get",
                        lambda name: "x" if name == "ELEVENLABS_API_KEY" else None)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "x")
    monkeypatch.delenv("FAL_API_KEY", raising=False)
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    proj = _project(tmp_path, {"provider": "auto"},
                    [{"narration": "hi", "lipsync": True}])
    assert cli._ensure_keys_for(proj) is None
    assert "lipsync" in capsys.readouterr().out.lower()
