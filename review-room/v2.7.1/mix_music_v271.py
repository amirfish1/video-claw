#!/usr/bin/env python3
"""Mix the v2 score + held-breath under the v2.7.1 VO. -> output/v2.7.1-music.mp4
Carries the same music_eleven_v2.mp3 + subbass_breath.wav from v2.7/assets.
Run: python3 review-room/v2.7.1/mix_music_v271.py
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "review-room" / "v2.7.1" / "work"
A7 = ROOT / "review-room" / "v2.7" / "assets"
OUT = ROOT / "review-room" / "output" / "v2.7.1-music.mp4"
VID = WORK / "captioned.mp4"
VO = WORK / "audio.m4a"
MUS = A7 / "music_eleven_v2.mp3"
SUB = A7 / "subbass_breath.wav"
BASE = 0.82
DUR = 52.27


def ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


fc = (
    "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start=0:end=25.2,"
    "asetpts=N/SR/TB,afade=t=in:st=0:d=2[m1];"
    "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start=25.2:end=27.0,"
    "asetpts=N/SR/TB,afade=t=out:st=0.2:d=0.6[m2];"
    "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start=27.0:end=52.27,"
    "asetpts=N/SR/TB,afade=t=in:st=0:d=1.0,afade=t=out:st=23.8:d=1.6[m3];"
    "[m1][m2][m3]concat=n=3:v=0:a=1[musseq];"
    f"[musseq]volume={BASE}[musg];"
    "[3:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.7,adelay=25400|25400[sub];"
    "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[vo][vokey];"
    "[musg][vokey]sidechaincompress=threshold=0.06:ratio=4:attack=20:release=260[musd];"
    "[vo][musd][sub]amix=inputs=3:normalize=0:dropout_transition=0,"
    "loudnorm=I=-14:TP=-1.5:LRA=11[ao]"
)
cmd = [ffmpeg_bin(), "-y", "-i", str(VID), "-i", str(VO), "-i", str(MUS), "-i", str(SUB),
       "-filter_complex", fc, "-map", "0:v", "-map", "[ao]", "-t", str(DUR),
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(OUT)]
print("+ mixing ->", OUT)
subprocess.run(cmd, check=True)
print("WROTE", OUT)
