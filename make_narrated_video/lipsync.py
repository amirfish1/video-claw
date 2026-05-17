"""fal.ai OmniHuman 1.5 lipsync + circular badge pre-processor.

Public entry points:
  - fal_upload_file(path, *, cache) -> public URL (cached by content hash)
  - fal_omnihuman_lipsync(audio_path, image_path, *, cache, version, resolution) -> MP4
  - crop_to_circle_video(mp4, *, cache, diameter) -> MOV with circular alpha mask

Safety:
  - The ffmpeg circle crop runs with a hard 180s wall-clock timeout and a
    100MB output ceiling. A runaway encode (the old looped-PNG-input bug
    that produced a 131GB file) can't happen silently again.
  - fal queue poll has a 10-minute budget per generation.
"""
from __future__ import annotations
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from . import keys


def _fal_key() -> str:
    api_key = keys.get("FAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "fal.ai lipsync requested but no FAL_API_KEY found.\n"
            "Run: make-narrated-video keys set FAL=<your-key>"
        )
    return api_key


def fal_upload_file(path: Path, *, cache) -> str:
    """Upload to fal.ai's storage and return the public URL. Cached in a
    tiny JSON table keyed by content hash so re-uploads are free.
    """
    api_key = _fal_key()
    digest = cache.hash([path])
    table_path = cache.root / "fal_uploads.json"
    table = json.loads(table_path.read_text()) if table_path.exists() else {}
    if digest in table:
        return table[digest]

    suffix = path.suffix.lower()
    if suffix == ".mp3":
        content_type = "audio/mpeg"
    elif suffix == ".m4a":
        content_type = "audio/mp4"
    elif suffix == ".png":
        content_type = "image/png"
    elif suffix in (".jpg", ".jpeg"):
        content_type = "image/jpeg"
    elif suffix == ".mp4":
        content_type = "video/mp4"
    else:
        content_type = "application/octet-stream"

    init_req = urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        data=json.dumps({"file_name": path.name, "content_type": content_type}).encode(),
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(init_req, timeout=60) as r:
            init = json.load(r)
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="ignore")[:300]
        raise RuntimeError(f"fal upload initiate failed {e.code}: {err}")
    upload_url = init["upload_url"]
    file_url = init["file_url"]

    put_req = urllib.request.Request(
        upload_url,
        data=path.read_bytes(),
        headers={"Content-Type": init.get("content_type", content_type)},
        method="PUT",
    )
    with urllib.request.urlopen(put_req, timeout=300) as r:
        if r.status not in (200, 201, 204):
            raise RuntimeError(f"fal upload PUT failed: HTTP {r.status}")

    table[digest] = file_url
    table_path.write_text(json.dumps(table, indent=2))
    return file_url


def fal_omnihuman_lipsync(audio_path: Path, image_path: Path, *, cache,
                          version: str = "v1.5",
                          resolution: str = "720p",
                          budget_seconds: int = 600) -> Path:
    """Generate a lipsync MP4 from (audio, headshot). Cached by all inputs."""

    def _generate(out_path: Path) -> None:
        api_key = _fal_key()
        print("  [fal] uploading audio + image to fal storage...")
        image_url = fal_upload_file(image_path, cache=cache)
        audio_url = fal_upload_file(audio_path, cache=cache)
        body = {
            "image_url": image_url,
            "audio_url": audio_url,
            "resolution": resolution,
        }
        submit_req = urllib.request.Request(
            f"https://queue.fal.run/fal-ai/bytedance/omnihuman/{version}",
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(submit_req, timeout=60) as r:
            sub = json.load(r)
        request_id = sub["request_id"]
        status_url = sub["status_url"]
        response_url = sub["response_url"]
        print(f"  [fal] queued {request_id}; polling...")

        deadline = time.time() + budget_seconds
        while time.time() < deadline:
            time.sleep(4)
            sreq = urllib.request.Request(
                status_url, headers={"Authorization": f"Key {api_key}"}
            )
            with urllib.request.urlopen(sreq, timeout=30) as r:
                st = json.load(r)
            status = st.get("status")
            print(f"  [fal] status={status}")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"fal omnihuman {status}: {st}")
        else:
            raise RuntimeError("fal omnihuman timed out (10 min budget)")

        rreq = urllib.request.Request(
            response_url, headers={"Authorization": f"Key {api_key}"}
        )
        with urllib.request.urlopen(rreq, timeout=60) as r:
            result = json.load(r)
        vid = result.get("video")
        video_url = vid.get("url") if isinstance(vid, dict) else vid
        if not video_url:
            raise RuntimeError(f"fal omnihuman returned no video url: {result}")
        with urllib.request.urlopen(video_url, timeout=180) as r:
            out_path.write_bytes(r.read())
        print(f"  [fal] saved {out_path.name} ({out_path.stat().st_size} bytes)")

    return cache.run(
        "lipsync",
        [audio_path, image_path, "omnihuman", version, resolution],
        "mp4",
        _generate,
    )


def crop_to_circle_video(lipsync_mp4: Path, *, cache,
                         diameter: int = 280,
                         size_ceiling_bytes: int = 100 * 1024 * 1024,
                         ffmpeg_timeout: int = 180) -> Path:
    """Pre-process the lipsync MP4 into a circular badge MOV with proper alpha.

    Pipeline (ffmpeg -vf):
      format=yuv420p       strip any source alpha
      crop+scale           square -> diameter x diameter
      format=yuva420p      re-add an alpha channel
      geq                  paint alpha = 255 inside circle, 0 outside

    Safety: hard wall-clock timeout + output size ceiling. If either trips,
    the partial output is removed and we raise.
    """
    def _generate(out_path: Path) -> None:
        r = diameter / 2
        vf = (
            f"format=yuv420p,"
            f"crop='min(iw\\,ih)':'min(iw\\,ih)',"
            f"scale={diameter}:{diameter},"
            f"format=yuva420p,"
            f"geq="
            f"lum='lum(X\\,Y)':"
            f"cb='cb(X\\,Y)':"
            f"cr='cr(X\\,Y)':"
            f"a='if(lt(sqrt(pow(X-{r}\\,2)+pow(Y-{r}\\,2))\\,{r-2}),255,0)'"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(lipsync_mp4),
            "-vf", vf,
            "-c:v", "qtrle",
            "-an",
            "-t", "60",  # belt-and-suspenders cap
            str(out_path),
        ]
        subprocess.run(
            cmd, check=True, timeout=ffmpeg_timeout,
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        )
        size = out_path.stat().st_size
        if size > size_ceiling_bytes:
            out_path.unlink()
            raise RuntimeError(
                f"circle output suspiciously large ({size}B > {size_ceiling_bytes}B); aborting"
            )

    return cache.run(
        "circle",
        [lipsync_mp4, "diameter", diameter, "v4-geq-full-planes"],
        "mov",
        _generate,
    )
