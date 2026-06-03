#!/usr/bin/env python3
"""Build three fade-free, audio-free, text-free Ken Burns clips for v2.10.

Each clip: 1920x1080, 30fps, 4.5s (135 frames), libx264 yuv420p, +faststart.
Distinct moves so the three reveal beats don't feel identical:
  - hub     -> slow push-IN  (zoom 1.00 -> 1.12, centered)
  - debate  -> slow PAN left -> right (slight constant zoom 1.06, x sweeps)
  - meeting -> slow pull-OUT (zoom 1.12 -> 1.00, centered)

Source plates are 1365x768. We upscale to a large working canvas first so
zoompan has clean pixels to sample, then zoompan outputs 1920x1080.
"""
import subprocess
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()

FPS = 30
DUR = 4.5
FRAMES = int(round(FPS * DUR))  # 135
OUT_W, OUT_H = 1920, 1080
# Upscale working canvas (keeps zoompan smooth; large so subpixel pan is fine)
WORK = "scale=7680:4320:flags=lanczos"

ASSETS = "review-room/v2.10/assets"

# zoompan d = FRAMES so the move spans the whole clip; s=output size.
# z expression drives the move; x/y center or pan.
JOBS = [
    # HUB: push-IN. zoom from 1.00 to 1.12 linearly over the clip, centered.
    dict(
        src="review-room/v2.8/assets/empty_hub.png",
        out=f"{ASSETS}/kenburns_hub.mp4",
        zoompan=(
            f"zoompan="
            f"z='1.00+0.12*on/{FRAMES-1}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={FRAMES}:s={OUT_W}x{OUT_H}:fps={FPS}"
        ),
    ),
    # DEBATE: PAN left -> right at a gentle constant zoom (1.06).
    # At zoom 1.06 there is headroom to slide x from 0 (left) to max (right).
    dict(
        src="review-room/v2.7/assets/empty_debate_room.png",
        out=f"{ASSETS}/kenburns_debate.mp4",
        zoompan=(
            f"zoompan="
            f"z='1.06':"
            f"x='(iw-iw/zoom)*on/{FRAMES-1}':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={FRAMES}:s={OUT_W}x{OUT_H}:fps={FPS}"
        ),
    ),
    # MEETING: pull-OUT. zoom from 1.12 down to 1.00, centered.
    dict(
        src="review-room/v2.8/assets/empty_meeting.png",
        out=f"{ASSETS}/kenburns_meeting.mp4",
        zoompan=(
            f"zoompan="
            f"z='1.12-0.12*on/{FRAMES-1}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={FRAMES}:s={OUT_W}x{OUT_H}:fps={FPS}"
        ),
    ),
]


def build(job):
    vf = f"{WORK},{job['zoompan']},format=yuv420p"
    cmd = [
        FF, "-y",
        "-loop", "1", "-i", job["src"],
        "-t", str(DUR),
        "-vf", vf,
        "-r", str(FPS),
        "-an",  # NO audio
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-crf", "18",
        "-movflags", "+faststart",
        job["out"],
    ]
    print("==>", job["out"])
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    for j in JOBS:
        build(j)
    print("kenburns: done")
