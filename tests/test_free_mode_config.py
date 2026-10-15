"""Tests for the `mode: "free"` config preset (the $0 guarantee)."""
from __future__ import annotations
from pathlib import Path


def _write_project(dir_: Path, config_src: str, slides_src: str) -> Path:
    (dir_ / "slides.py").write_text(f"CONFIG = {config_src}\nSLIDES = {slides_src}\n")
    return dir_


def test_free_mode_forces_macos_and_strips_lipsync(tmp_path):
    from video_claw import config as cfg_mod
    _write_project(
        tmp_path,
        '{"mode": "free", "tts": {"provider": "elevenlabs"}}',
        '[{"type": "html", "html": "a.html", "narration": "hi", "lipsync": True}]',
    )
    project = cfg_mod.load(tmp_path)
    assert project.config["tts"]["provider"] == "macos"
    assert project.config["tts"]["macos_voice"] == "auto"
    assert project.config["avatar"]["static"] is True
    assert project.config["avatar"]["scope"] == "all"
    assert project.config["captions"]["estimate"] is True
    assert "lipsync" not in project.slides[0]


def test_free_mode_respects_custom_voice(tmp_path):
    from video_claw import config as cfg_mod
    _write_project(
        tmp_path,
        '{"mode": "free", "tts": {"macos_voice": "Samantha"}}',
        '[{"type": "html", "html": "a.html", "narration": "hi"}]',
    )
    project = cfg_mod.load(tmp_path)
    assert project.config["tts"]["macos_voice"] == "Samantha"


def test_non_free_mode_untouched(tmp_path):
    from video_claw import config as cfg_mod
    _write_project(
        tmp_path,
        '{"tts": {"provider": "elevenlabs"}}',
        '[{"type": "html", "html": "a.html", "narration": "hi", "lipsync": True}]',
    )
    project = cfg_mod.load(tmp_path)
    assert project.config["tts"]["provider"] == "elevenlabs"
    assert project.config["avatar"]["static"] is False
    assert project.slides[0]["lipsync"] is True


def test_default_provider_and_captions(tmp_path):
    from video_claw import config as cfg_mod
    _write_project(
        tmp_path, '{}',
        '[{"type": "html", "html": "a.html", "narration": "hi"}]',
    )
    project = cfg_mod.load(tmp_path)
    assert project.config["tts"]["provider"] == "auto"
    assert project.config["tts"]["macos_voice"] == "auto"
    assert project.config["captions"]["estimate"] is True


def test_scaffold_uses_natural_speaking_rate():
    from video_claw.config import SAMPLE_SLIDES_PY
    namespace = {}
    exec(SAMPLE_SLIDES_PY % {"title": "Test", "orientation": "horizontal", "slug": "test"}, namespace)
    assert namespace["CONFIG"]["tts"]["speaking_rate"] == 1.0
    assert len(namespace["SLIDES"]) == 4
    assert all(slide["speed"] == 1.0 for slide in namespace["SLIDES"])


def test_free_mode_clears_paid_global_lipsync_default(tmp_path):
    from video_claw import config as cfg_mod
    _write_project(tmp_path, '{"mode": "free", "tts": {"lipsync": "fal"}}',
                   '[{"narration": "hi"}]')
    project = cfg_mod.load(tmp_path)
    assert project.config["tts"]["lipsync"] is False
    assert project.config["avatar"]["static"] is True
