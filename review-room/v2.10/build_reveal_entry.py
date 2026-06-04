#!/usr/bin/env python3
"""Reveal-entry clips: a LIVE room (callback to the shot we saw) dissolves into the
EMPTY room — restoring the v2.9.1/0603 "part 1 -> part 2" move the user liked. Built per
room (hub, debate). Output: review-room/v2.10/assets/reveal_<room>_from_live.mp4
(fade-free, no audio), used as the reveal segments in place of the kenburns_<room>.mp4.
Meeting has no matching live source in raw/, so it stays Ken Burns (or a populated still).
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
A = RR / "v2.10" / "assets"
W, H, FPS = 1920, 1080, 30
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
LIVE_LEN, XF = 2.2, 0.9
KB_LEN = 4.5

# (room, live source clip, empty-room Ken Burns clip)
ROOMS = [
    ("hub",     RR / "raw" / "sample3_bustling_hub.mp4", A / "kenburns_hub.mp4"),
    ("debate",  RR / "raw" / "sample5_real_debate.mp4",  A / "kenburns_debate.mp4"),
    ("meeting", RR / "raw" / "founder_motion.mp4",       A / "kenburns_meeting.mp4"),  # founder review -> empty table
]


def build(room, live, kb):
    out = A / f"reveal_{room}_from_live.mp4"
    total = LIVE_LEN + KB_LEN - XF
    # NB: fps AFTER setpts (CFR fix) — xfade errors with -22 otherwise.
    def norm(idx, length):
        return (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,trim=0:{length},"
                f"setpts=PTS-STARTPTS,fps={FPS},format=yuv420p")
    fc = (norm(0, LIVE_LEN) + "[a];" + norm(1, KB_LEN) + "[b];"
          + f"[a][b]xfade=transition=fade:duration={XF}:offset={LIVE_LEN-XF:.3f},format=yuv420p[v]")
    subprocess.run([FF, "-y", "-i", str(live), "-i", str(kb),
                    "-filter_complex", fc, "-map", "[v]", "-t", f"{total:.3f}", "-r", str(FPS),
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                   check=True)
    print("wrote", out, f"({total:.1f}s)")


def build_hub_from_founder():
    """Hub entry with a lead-in: founder reviewing -> dissolve -> bustling -> dissolve ->
    empty hub. Smooths the sudden cut into the reveal (user: "another half a second of
    the founder and then it would dissolve"). 3-input xfade chain. ~6.1s; used trimmed."""
    out = A / "reveal_hub_from_live.mp4"
    N = ("scale=1920:1080:force_original_aspect_ratio=increase,"
         "crop=1920:1080:(in_w-1920)/2:(in_h-1080)/2,setsar=1")
    def n(i, L):
        return f"[{i}:v]{N},trim=0:{L},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p"
    fc = (n(0, 1.6) + "[a];" + n(1, 2.2) + "[b];" + n(2, 4.5) + "[c];"
          "[a][b]xfade=transition=fade:duration=0.6:offset=1.0[ab];"
          "[ab][c]xfade=transition=fade:duration=0.8:offset=2.4,format=yuv420p[v]")
    subprocess.run([FF, "-y", "-i", str(RR / "raw" / "founder_motion.mp4"),
                    "-i", str(RR / "raw" / "sample3_bustling_hub.mp4"),
                    "-i", str(A / "kenburns_hub.mp4"),
                    "-filter_complex", fc, "-map", "[v]", "-t", "6.1", "-r", str(FPS),
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                   check=True)
    print("wrote", out, "(6.1s, founder->bustling->empty)")


def main():
    build_hub_from_founder()                 # hub: founder -> bustling -> empty
    for room, live, kb in ROOMS:
        if room == "hub":
            continue                          # hub built above (with founder lead-in)
        build(room, live, kb)


if __name__ == "__main__":
    main()
