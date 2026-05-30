"""Command-builder + selector tests for free-mode rendering (no ffmpeg run)."""
from __future__ import annotations
from pathlib import Path


def test_static_avatar_overlay_cmd_loops_still_image():
    from video_claw.ffmpeg_video import _static_avatar_overlay_cmd
    cmd = _static_avatar_overlay_cmd(
        Path("slide.png"), Path("badge.png"), Path("a.m4a"),
        Path("out.mp4"), ox=100, oy=200, pad_dur=3.0,
    )
    joined = " ".join(cmd)
    # both the slide PNG and the still badge are looped (-loop 1 appears twice)
    assert cmd.count("-loop") == 2
    assert "overlay=x=100:y=200" in joined
    assert str(Path("badge.png")) in cmd


def test_select_avatar_scope_all():
    from video_claw.core import _select_avatar_badge
    assert _select_avatar_badge("BADGE", "all", 3, {}) == "BADGE"


def test_select_avatar_scope_intro_only_first():
    from video_claw.core import _select_avatar_badge
    assert _select_avatar_badge("BADGE", "intro", 0, {}) == "BADGE"
    assert _select_avatar_badge("BADGE", "intro", 1, {}) is None


def test_select_avatar_scope_flagged():
    from video_claw.core import _select_avatar_badge
    assert _select_avatar_badge("BADGE", "flagged", 2, {"avatar": True}) == "BADGE"
    assert _select_avatar_badge("BADGE", "flagged", 2, {}) is None


def test_select_avatar_no_badge():
    from video_claw.core import _select_avatar_badge
    assert _select_avatar_badge(None, "all", 0, {}) is None


def test_prompt_user_prints_cost_note(tmp_path, capsys):
    from video_claw.preview import prompt_user
    out = tmp_path / "out"; out.mkdir()
    slides = [{"type": "html", "html": "a.html", "narration": "hi"}]
    ok = prompt_user(out, slides, "horizontal", auto_yes=True,
                     preview_ttl=0, cost_note="$0 — local TTS, no paid APIs")
    assert ok is True
    assert "$0 — local TTS, no paid APIs" in capsys.readouterr().out
