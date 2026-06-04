#!/usr/bin/env python3
"""Reveal entry clip: the LIVE bustling hub (callback to the opening shot) dissolves
into the EMPTY hub with a slow Ken Burns push — restoring the v2.9.1/0603 "part 1 ->
part 2" move the user liked. Output: review-room/v2.10/assets/reveal_hub_from_live.mp4
(fade-free, no audio), used as the first reveal segment in place of kenburns_hub.mp4.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
LIVE = RR / "raw" / "sample3_bustling_hub.mp4"
KB_HUB = RR / "v2.10" / "assets" / "kenburns_hub.mp4"   # pre-rendered empty-hub Ken Burns
OUT = RR / "v2.10" / "assets" / "reveal_hub_from_live.mp4"
W, H, FPS = 1920, 1080, 30
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()

LIVE_LEN, XF = 2.2, 0.9          # live frames, then dissolve into the empty-hub KB clip
KB_LEN = 4.5                      # kenburns_hub.mp4 length
TOTAL = LIVE_LEN + KB_LEN - XF    # ~5.8s


def main():
    # NB: fps AFTER setpts (CFR fix) — xfade errors with -22 otherwise.
    def norm(idx, length):
        return (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,trim=0:{length},"
                f"setpts=PTS-STARTPTS,fps={FPS},format=yuv420p")
    live = norm(0, LIVE_LEN) + "[a]"
    empty = norm(1, KB_LEN) + "[b]"
    fc = (live + ";" + empty + ";"
          + f"[a][b]xfade=transition=fade:duration={XF}:offset={LIVE_LEN-XF:.3f},format=yuv420p[v]")
    subprocess.run([FF, "-y", "-i", str(LIVE), "-i", str(KB_HUB),
                    "-filter_complex", fc, "-map", "[v]", "-t", f"{TOTAL:.3f}", "-r", str(FPS),
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)],
                   check=True)
    print("wrote", OUT, f"({TOTAL:.1f}s)")


if __name__ == "__main__":
    main()
