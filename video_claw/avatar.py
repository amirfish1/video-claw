"""Static avatar badge: resolve an avatar image and crop it to a circular PNG.

Unlike `lipsync.py` (which animates a headshot via paid fal.ai), this module
overlays a *still* portrait as a circular badge — free, local, used by the
$0/free mode. The circle alpha mask mirrors `lipsync.crop_to_circle_video` but
operates on a single image and emits a PNG with alpha.

Public API:
    resolve_avatar_image(avatar_cfg, project_dir) -> Path
    crop_image_to_circle(png, *, cache, diameter=280) -> Path
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


# Bundled fallback portrait (Becky), shipped inside the package.
BUNDLED_AVATAR = Path(__file__).parent / "assets" / "avatar.png"


def resolve_avatar_image(avatar_cfg: Dict[str, Any],
                         project_dir: Optional[Path]) -> Path:
    """Configured `image` if it exists (resolved relative to `project_dir`),
    otherwise the bundled Becky portrait."""
    image = (avatar_cfg or {}).get("image")
    if image:
        p = Path(image)
        if not p.is_absolute() and project_dir is not None:
            p = (project_dir / p).resolve()
        if p.exists():
            return p
    return BUNDLED_AVATAR


def crop_image_to_circle(png: Path, *, cache, diameter: int = 280,
                         size_ceiling_bytes: int = 20 * 1024 * 1024,
                         ffmpeg_timeout: int = 60) -> Path:
    """Crop a still image to a `diameter`x`diameter` circular PNG with alpha.

    Cached by (image bytes, diameter). Safety: hard wall-clock timeout + output
    size ceiling, mirroring `lipsync.crop_to_circle_video`.
    """
    def _generate(out_path: Path) -> None:
        r = diameter / 2
        vf = (
            f"format=rgba,"
            f"crop='min(iw\\,ih)':'min(iw\\,ih)',"
            f"scale={diameter}:{diameter},"
            f"geq="
            f"r='r(X\\,Y)':g='g(X\\,Y)':b='b(X\\,Y)':"
            f"a='if(lt(sqrt(pow(X-{r}\\,2)+pow(Y-{r}\\,2))\\,{r - 2}),255,0)'"
        )
        cmd = [
            "ffmpeg", "-y", "-i", str(png),
            "-vf", vf, "-frames:v", "1",
            str(out_path),
        ]
        subprocess.run(cmd, check=True, timeout=ffmpeg_timeout,
                       stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        size = out_path.stat().st_size
        if size > size_ceiling_bytes:
            out_path.unlink()
            raise RuntimeError(
                f"avatar circle suspiciously large ({size}B > {size_ceiling_bytes}B); aborting"
            )

    return cache.run(
        "avatar_circle",
        [png, "diameter", diameter, "v1-rgba-geq"],
        "png",
        _generate,
    )
