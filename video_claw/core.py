"""Top-level orchestrator: turn a list of slide dicts into a narrated MP4.

Public entry point:
  make_video(slides, *, workdir, orientation, project_dir=None,
             out_path=None, tts_cfg=None, lipsync_cfg=None,
             auto_yes=False, skip_preview=False) -> Path

A slide dict carries:
  type:       "html" | "image" | "video"  (default "image")
  html:       path to an HTML file (for type=html), relative to project_dir
  image:      path to a still image (for type=image)
  video:      path to an MP4 to embed (for type=video)
  narration:  text the TTS engine speaks
  title:      optional, drawn as a strip for image/video slides
  lipsync:    optional bool. Requires FAL_API_KEY.
  speed:      optional float; overrides tts_cfg["speaking_rate"]

The orchestrator caches every expensive step so re-runs are cheap.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import cache as cache_mod
from . import captions as caps_mod
from . import ffmpeg_video as ff
from . import lipsync as lip_mod
from . import preview as preview_mod
from . import renderer_html
from . import tts as tts_mod


DEFAULT_TTS = {
    "provider": "elevenlabs",
    "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.0,
    "deepgram_voice": "aura-2-thalia-en",
}

DEFAULT_LIPSYNC = {
    "avatar": "assets/avatar.png",
    "fal_omnihuman_version": "v1.5",
    "resolution": "720p",
}


def _dims(orientation: str) -> Tuple[int, int]:
    if orientation == "short":
        return (1080, 1920)
    return (1920, 1080)


def _resolve(path_str: str, project_dir: Optional[Path]) -> Path:
    p = Path(path_str)
    if p.is_absolute() or project_dir is None:
        return p
    return (project_dir / p).resolve()


def render_pngs(slides: List[Dict[str, Any]], *, workdir: Path,
                project_dir: Optional[Path], dimensions: Tuple[int, int]) -> List[Optional[Path]]:
    """Render PNGs for HTML slides + copy image/video slide backgrounds.

    Returns one entry per slide, in order. Index N maps to `workdir/slide_NN.png`.
    For HTML slides we render directly; for image slides we copy/resize via
    Chrome by wrapping the image in a tiny HTML; for video slides we render
    an empty backdrop (PNG) into which the clip will be composited later.
    """
    width, height = dimensions
    out_pngs: List[Optional[Path]] = []
    for idx, slide in enumerate(slides):
        kind = slide.get("type", "image")
        png_path = workdir / f"slide_{idx:02d}.png"
        if kind == "html":
            html_rel = slide.get("html")
            if not html_rel:
                raise ValueError(f"slide {idx}: type=html requires `html` field")
            html_path = _resolve(html_rel, project_dir)
            if not html_path.exists():
                raise FileNotFoundError(f"slide {idx}: HTML not found: {html_path}")
            print(f"  [html->png] slide {idx:02d}: {html_rel}")
            renderer_html.render_html_to_png(html_path, png_path, width, height)
            out_pngs.append(png_path)
            continue

        if kind == "image":
            img_rel = slide.get("image")
            if not img_rel:
                raise ValueError(f"slide {idx}: type=image requires `image` field")
            img_path = _resolve(img_rel, project_dir)
            if not img_path.exists():
                raise FileNotFoundError(f"slide {idx}: image not found: {img_path}")
            # Wrap the image in a tiny HTML so Chrome can box it to the canvas.
            wrapper = workdir / f"_imgwrap_{idx:02d}.html"
            title = slide.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
            title_strip = (
                f'<div class="title">{title}</div>' if title else ""
            )
            wrapper.write_text(_image_wrapper_html(img_path, width, height, title_strip))
            print(f"  [img->png]  slide {idx:02d}: {img_rel}")
            renderer_html.render_html_to_png(wrapper, png_path, width, height)
            out_pngs.append(png_path)
            continue

        if kind == "video":
            # Render a backdrop (title strip + a framed viewport rectangle).
            vid_rel = slide.get("video")
            if not vid_rel:
                raise ValueError(f"slide {idx}: type=video requires `video` field")
            title = slide.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
            margin_x = int(width * 0.08)
            top = int(height * 0.13)
            vp_w = width - 2 * margin_x
            vp_h = height - top - int(height * 0.06)
            slide["_vp"] = (margin_x, top, vp_w, vp_h)
            wrapper = workdir / f"_vidwrap_{idx:02d}.html"
            wrapper.write_text(_video_backdrop_html(width, height, title, slide["_vp"]))
            renderer_html.render_html_to_png(wrapper, png_path, width, height)
            out_pngs.append(png_path)
            continue

        raise ValueError(f"slide {idx}: unknown type {kind!r}")
    return out_pngs


def _image_wrapper_html(img_path: Path, w: int, h: int, title_strip: str) -> str:
    """Tiny HTML so Chrome can letterbox the image cleanly onto the canvas."""
    return f"""<!doctype html>
<meta charset="utf-8">
<style>
 :root {{ --bg: #0f1216; --accent: #fac85a; --fg: #ebebe8; --dim: #404750; }}
 html, body {{ margin: 0; padding: 0; width: {w}px; height: {h}px;
   background: var(--bg); color: var(--fg);
   font: 600 28px/1.2 -apple-system, "SF Pro Text", system-ui, sans-serif; }}
 .title {{ position: absolute; top: 40px; left: 120px;
   border-left: 6px solid var(--accent); padding-left: 18px; font-size: 36px; }}
 .frame {{ position: absolute; inset: 0;
   display: grid; place-items: center; padding: 60px; box-sizing: border-box; }}
 .frame.with-title {{ padding-top: 130px; }}
 img {{ max-width: 100%; max-height: 100%; object-fit: contain;
   border: 1px solid var(--dim); border-radius: 6px; background: #000; }}
</style>
{title_strip}
<div class="frame {('with-title' if title_strip else '')}">
  <img src="file://{img_path}">
</div>
"""


def _video_backdrop_html(w: int, h: int, title: str, vp) -> str:
    vp_x, vp_y, vp_w, vp_h = vp
    title_strip = (
        f'<div class="title">{title}</div>' if title else ""
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<style>
 :root {{ --bg: #0f1216; --accent: #fac85a; --fg: #ebebe8; --dim: #404750; }}
 html, body {{ margin: 0; padding: 0; width: {w}px; height: {h}px;
   background: var(--bg); color: var(--fg);
   font: 600 28px/1.2 -apple-system, "SF Pro Text", system-ui, sans-serif; }}
 .title {{ position: absolute; top: 40px; left: 120px;
   border-left: 6px solid var(--accent); padding-left: 18px; font-size: 36px; }}
 .vp {{ position: absolute; left: {vp_x - 4}px; top: {vp_y - 4}px;
   width: {vp_w + 8}px; height: {vp_h + 8}px;
   border: 2px solid var(--dim); border-radius: 4px; }}
</style>
{title_strip}
<div class="vp"></div>
"""


def make_video(slides: List[Dict[str, Any]], *,
               workdir: Path,
               orientation: str = "horizontal",
               project_dir: Optional[Path] = None,
               out_path: Optional[Path] = None,
               tts_cfg: Optional[Dict[str, Any]] = None,
               lipsync_cfg: Optional[Dict[str, Any]] = None,
               auto_yes: bool = False,
               skip_preview: bool = False) -> Path:
    """End-to-end: PNGs → preview gate → TTS → optional lipsync → slide MP4s →
    concat → caption burn. Returns the final MP4 path.
    """
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    dimensions = _dims(orientation)
    tts_cfg = {**DEFAULT_TTS, **(tts_cfg or {})}
    lipsync_cfg = {**DEFAULT_LIPSYNC, **(lipsync_cfg or {})}
    if out_path is None:
        out_path = workdir / "video.mp4"
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cache = cache_mod.Cache(workdir)
    print(f"[boot] {len(slides)} slides, orientation={orientation}, dims={dimensions}")
    print(f"[boot] workdir={workdir}")

    # Phase 1: render slide PNGs (cheap + no third-party cost).
    render_pngs(slides, workdir=workdir, project_dir=project_dir, dimensions=dimensions)

    # Phase 2: preview gate. Give the user a chance to abort before TTS spend.
    if not skip_preview:
        ok = preview_mod.prompt_user(workdir, slides, orientation, auto_yes=auto_yes)
        if not ok:
            raise SystemExit("aborted at preview gate")

    # Phase 3: TTS (cached), optional lipsync (cached), per-slide MP4 stitching.
    parts: List[Path] = []
    all_captions: List[Tuple[float, float, str]] = []
    cumulative = 0.0
    for idx, slide in enumerate(slides):
        narration = slide.get("narration") or ""
        if not narration.strip():
            raise ValueError(f"slide {idx}: missing narration text")
        rate = float(slide.get("speed") or tts_cfg.get("speaking_rate", 1.0))
        slide_tts = {**tts_cfg, "speaking_rate": rate}
        rate_tag = f" speed={rate}x" if abs(rate - 1.0) > 1e-3 else ""
        print(f"  slide {idx + 1}/{len(slides)}: TTS ({slide_tts['provider']}){rate_tag}")
        m4a, dur = tts_mod.make_audio(narration, idx, workdir=workdir, cache=cache, tts_cfg=slide_tts)

        # Caption alignment is only produced by ElevenLabs.
        if slide_tts["provider"].lower().startswith("eleven"):
            all_captions.extend(caps_mod.build_srt_for_slide(idx, cumulative, rate, workdir))

        # Optional fal lipsync overlay.
        lipsync_circle = None
        if slide.get("lipsync"):
            avatar_rel = slide.get("lipsync_avatar") or lipsync_cfg["avatar"]
            avatar = _resolve(avatar_rel, project_dir)
            if not avatar.exists():
                print(f"  [lipsync] avatar not found at {avatar}; skipping")
            else:
                try:
                    # Generate an mp3 from the (silenceremoved + atempo'd) m4a for fal.
                    lip_mp3 = cache.path("m4a", [m4a, "lipsync-source"], "mp3")
                    if not lip_mp3.exists():
                        import subprocess
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", str(m4a), "-vn",
                             "-acodec", "libmp3lame", "-b:a", "192k", str(lip_mp3)],
                            check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        )
                    mp4 = lip_mod.fal_omnihuman_lipsync(
                        lip_mp3, avatar, cache=cache,
                        version=lipsync_cfg["fal_omnihuman_version"],
                        resolution=lipsync_cfg["resolution"],
                    )
                    lipsync_circle = lip_mod.crop_to_circle_video(mp4, cache=cache)
                except Exception as e:  # noqa: BLE001
                    print(f"  [lipsync] failed: {e}; continuing without overlay")

        png = workdir / f"slide_{idx:02d}.png"
        mp4 = ff.make_slide_video(
            png, m4a, dur, idx,
            slide=slide, workdir=workdir, cache=cache,
            dimensions=dimensions, lipsync_circle=lipsync_circle,
        )
        parts.append(mp4)
        cumulative += dur + 0.15
        print(f"    -> {dur:.1f}s audio")

    # Phase 4: concat + burn captions.
    raw = ff.concat_slides(parts, workdir=workdir)
    if all_captions:
        srt_path = workdir / "captions.srt"
        ass_path = workdir / "captions.ass"
        caps_mod.write_master_srt(all_captions, srt_path)
        caps_mod.write_master_ass(all_captions, ass_path,
                                  width=dimensions[0], height=dimensions[1])
        print(f"[captions] {len(all_captions)} chunks via libass")
        try:
            ff.burn_captions(raw, ass_path, out_path)
        except Exception as e:  # noqa: BLE001
            import shutil as _shutil
            _shutil.copyfile(raw, out_path)
            stderr = getattr(e, "stderr", None) or ""
            tail = stderr.strip().splitlines()[-2:] if isinstance(stderr, str) else []
            print(f"[captions] burn failed; shipping raw MP4 + SRT sidecar at:")
            print(f"             {srt_path}")
            if tail:
                print(f"           ffmpeg said: {' | '.join(tail)}")
            print(f"           fix: pip install imageio-ffmpeg (homebrew ffmpeg lacks libass)")
    else:
        import shutil as _shutil
        _shutil.copyfile(raw, out_path)

    duration = ff.ffprobe_duration(out_path)
    print(f"[done] {out_path}  duration: {duration:.1f}s")
    print(f"[cache] {cache.summary()}")
    return out_path
