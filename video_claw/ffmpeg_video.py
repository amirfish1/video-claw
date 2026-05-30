"""ffmpeg-based slide-MP4 stitching + final concat + caption burn.

Public entry points:
  - make_slide_video(png, m4a, duration, idx, *, slide, workdir, cache,
                     dimensions, lipsync_circle=None) -> mp4 path
  - concat_slides(mp4_paths, *, workdir) -> raw concat mp4
  - burn_captions(raw_mp4, ass_path, out_path) -> final mp4
                  (uses imageio-ffmpeg because homebrew ffmpeg lacks libass)

A "slide MP4" is one of three shapes:
  1. type=video: PNG background + an embedded clip in a viewport rect + audio
  2. lipsync_circle present: PNG + circular lipsync overlay in bottom-right + audio
  3. default: still PNG + audio (cached so identical re-renders are free)
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _video_slide_cmd(png: Path, clip: Path, m4a: Path, out: Path,
                     vp: Tuple[int, int, int, int], pad_dur: float) -> List[str]:
    vp_x, vp_y, vp_w, vp_h = vp
    return [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(png),
        "-stream_loop", "-1", "-i", str(clip),
        "-i", str(m4a),
        "-filter_complex",
        f"[1:v]scale={vp_w}:{vp_h}:force_original_aspect_ratio=decrease,"
        f"pad={vp_w}:{vp_h}:(ow-iw)/2:(oh-ih)/2:color=0x000000[clip];"
        f"[0:v][clip]overlay=x={vp_x}:y={vp_y}[v];"
        f"[2:a]apad=pad_dur=0.15[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-t", f"{pad_dur:.3f}",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30", "-shortest",
        str(out),
    ]


def _lipsync_overlay_cmd(png: Path, circle: Path, m4a: Path, out: Path,
                        ox: int, oy: int, pad_dur: float) -> List[str]:
    return [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(png),
        "-stream_loop", "-1", "-i", str(circle),
        "-i", str(m4a),
        "-filter_complex",
        f"[0:v][1:v]overlay=x={ox}:y={oy}:shortest=0[v];"
        f"[2:a]apad=pad_dur=0.15[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-t", f"{pad_dur:.3f}",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30", "-shortest",
        str(out),
    ]


def _static_avatar_overlay_cmd(png: Path, badge: Path, m4a: Path, out: Path,
                               ox: int, oy: int, pad_dur: float) -> List[str]:
    """Overlay a STILL circular avatar PNG (looped) in the bottom-right slot.

    Identical to `_lipsync_overlay_cmd` except the badge is a still image
    (`-loop 1`) rather than a looped MOV.
    """
    return [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(png),
        "-loop", "1", "-i", str(badge),
        "-i", str(m4a),
        "-filter_complex",
        f"[0:v][1:v]overlay=x={ox}:y={oy}:shortest=0[v];"
        f"[2:a]apad=pad_dur=0.15[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-t", f"{pad_dur:.3f}",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30", "-shortest",
        str(out),
    ]


def _still_slide_cmd(png: Path, m4a: Path, out: Path, pad_dur: float) -> List[str]:
    return [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(png),
        "-i", str(m4a),
        "-filter_complex", "[1:a]apad=pad_dur=0.15[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-t", f"{pad_dur:.3f}",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30", "-shortest",
        str(out),
    ]


def make_slide_video(png: Path, m4a: Path, duration: float, idx: int, *,
                     slide: Dict[str, Any], workdir: Path, cache,
                     dimensions: Tuple[int, int],
                     lipsync_circle: Optional[Path] = None,
                     avatar_circle: Optional[Path] = None) -> Path:
    """Build one slide MP4. Returns the per-slide MP4 path under workdir.

    `lipsync_circle` is the pre-cropped circular MOV (caller decides whether
    to make one; this module doesn't talk to fal directly).
    """
    width, height = dimensions
    out = workdir / f"slide_{idx:02d}.mp4"
    pad_dur = duration + 0.15

    # Variant 1: type=video. Overlay an embedded clip inside the slide PNG.
    if slide.get("type") == "video" and slide.get("video"):
        clip = Path(slide["video"])
        if not clip.is_absolute():
            clip = (workdir / clip).resolve()
            if not clip.exists():
                # also accept paths relative to the project dir
                clip = Path(slide["video"]).resolve()
        # Viewport defaults to ~80% of frame centered. Override via slide["_vp"].
        vp = slide.get("_vp")
        if not vp:
            margin = int(width * 0.08)
            top = int(height * 0.13)
            vp = (margin, top, width - 2 * margin, height - top - int(height * 0.06))
        cmd = _video_slide_cmd(png, clip, m4a, out, vp, pad_dur)
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return out

    # Variant 2: lipsync overlay in the bottom-right corner.
    if lipsync_circle is not None:
        diameter = 280
        margin = 40
        ox = width - diameter - margin
        oy = height - diameter - margin - 30
        cmd = _lipsync_overlay_cmd(png, lipsync_circle, m4a, out, ox, oy, pad_dur)
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return out

    # Variant 2b: static avatar badge (free mode). Same bottom-right slot as
    # lip-sync, but a still PNG. Lip-sync (above) takes precedence if both set.
    if avatar_circle is not None:
        diameter = 280
        margin = 40
        ox = width - diameter - margin
        oy = height - diameter - margin - 30
        cmd = _static_avatar_overlay_cmd(png, avatar_circle, m4a, out, ox, oy, pad_dur)
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return out

    # Variant 3: still PNG + audio, cached so identical re-renders are free.
    slide_key = [png, m4a, "pad", round(pad_dur, 3), "still", width, height]

    def _build(out_path: Path) -> None:
        cmd = _still_slide_cmd(png, m4a, out_path, pad_dur)
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    cached = cache.run("slide_mp4", slide_key, "mp4", _build)
    out.write_bytes(cached.read_bytes())
    return out


def concat_slides(mp4_paths: List[Path], *, workdir: Path) -> Path:
    """`ffmpeg -f concat` the per-slide mp4s into one raw mp4. Stream-copies,
    so all slide mp4s must share codec/timebase (libx264 / aac / 30fps).
    """
    list_file = workdir / "concat_list.txt"
    with list_file.open("w") as f:
        for p in mp4_paths:
            f.write(f"file '{p}'\n")
    raw = workdir / "concat_raw.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy",
        str(raw),
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return raw


def _imageio_ffmpeg() -> str:
    """Return a path to an ffmpeg binary that has libass. The pip
    `imageio-ffmpeg` wheel ships one; homebrew's bottle doesn't.
    """
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        # last resort: PATH ffmpeg may or may not have libass
        return shutil.which("ffmpeg") or "ffmpeg"


def burn_captions(raw_mp4: Path, ass_path: Path, out_path: Path) -> Path:
    """Burn ASS captions into a video using libass. Raises CalledProcessError on
    failure. The caller can catch and fall back to shipping the raw_mp4 + an
    SRT sidecar.
    """
    ffmpeg_bin = _imageio_ffmpeg()
    # ffmpeg 8.x rejects bare `ass=/path` (parses `/path` as an option name).
    # Use the explicit `filename=` keyword with single-quoted value so the
    # filter parser treats the path as a single value regardless of version.
    burn_cmd = [
        ffmpeg_bin, "-y", "-i", str(raw_mp4),
        "-vf", f"ass=filename='{ass_path}'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out_path),
    ]
    res = subprocess.run(burn_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise subprocess.CalledProcessError(
            res.returncode, burn_cmd,
            output=res.stdout, stderr=res.stderr,
        )
    return out_path


def ffprobe_duration(path: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(res.stdout.strip())
