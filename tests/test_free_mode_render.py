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
