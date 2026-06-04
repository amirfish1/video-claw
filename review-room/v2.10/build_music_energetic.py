#!/usr/bin/env python3
"""Energetic (music B) clip, BAKED: cropped to the user's source window (6.133s in) with
a 2.8s fade-in rendered into the audio — so it plays reliably in CapCut without a volume
keyframe (capcut-cli volume keyframes don't reliably ramp in CapCut → music seemed muted).
Output: review-room/v2.10/assets/music_B_energetic.wav
"""
import subprocess
from pathlib import Path

RR = Path(__file__).resolve().parents[2] / "review-room"
SRC = RR / "output" / "stems-v2.9.1" / "music_B_triumph.mp3"
OUT = RR / "v2.10" / "assets" / "music_B_energetic.wav"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
SRC_START, DUR, FADE = 6.133, 18.3, 2.8


def main():
    subprocess.run([FF, "-y", "-ss", str(SRC_START), "-t", str(DUR), "-i", str(SRC),
                    "-af", f"afade=t=in:st=0:d={FADE}", "-ar", "48000", "-ac", "2", str(OUT)],
                   check=True)
    print("wrote", OUT, f"({DUR}s, source {SRC_START}s + {FADE}s fade)")


if __name__ == "__main__":
    main()
