"""Static avatar badge: image resolution + circular crop."""
from __future__ import annotations
import shutil
import pytest


def test_resolve_avatar_falls_back_to_bundled(tmp_path):
    from video_claw import avatar
    p = avatar.resolve_avatar_image({"image": "missing.png"}, tmp_path)
    assert p == avatar.BUNDLED_AVATAR
    assert p.exists(), "bundled Becky portrait must ship in the package"


def test_resolve_avatar_uses_project_image(tmp_path):
    from video_claw import avatar
    img = tmp_path / "becky.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    p = avatar.resolve_avatar_image({"image": "becky.png"}, tmp_path)
    assert p == img.resolve()


def test_resolve_avatar_empty_cfg(tmp_path):
    from video_claw import avatar
    assert avatar.resolve_avatar_image({}, tmp_path) == avatar.BUNDLED_AVATAR


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_crop_image_to_circle_produces_png(tmp_path):
    from video_claw import avatar
    from video_claw.cache import Cache
    cache = Cache(tmp_path / "work")
    out = avatar.crop_image_to_circle(avatar.BUNDLED_AVATAR, cache=cache, diameter=120)
    assert out.exists()
    assert out.suffix == ".png"
    assert out.stat().st_size > 0
