#!/usr/bin/env python3
"""Mix the ElevenLabs score under the v2.7 VO with milestone automation.

Sculpts the dynamics the raw track didn't nail:
  - near-silent GAP carved at t25.7-27.0 (the turn), swell back in at 27.0
  - whole bed sidechain-ducked under the VO (so narration + founder beat breathe)
  - fade in at head, fade out tail

Keeps v2.7.mp4 intact; writes a sibling output/v2.7-music.mp4.
Run: python3 review-room/v2.7/mix_music.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "review-room" / "v2.7" / "work"
ASSETS = ROOT / "review-room" / "v2.7" / "assets"
OUT = ROOT / "review-room" / "output" / "v2.7-music2.mp4"

VID = WORK / "captioned.mp4"
VO = WORK / "audio.m4a"
MUS = ASSETS / "music_eleven_v2.mp3"        # v2: punchier track (user note)
SUB = ASSETS / "subbass_breath.wav"         # held-breath under the turn gap
BASE = 0.82         # louder bed (user: too quiet)
DUR = 52.27


def ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


# music dynamics via segment trims + per-segment fades (comma-free expressions):
#   m1 0-25.0   : head fade-in, full
#   m2 25.0-27.0: fade to silence (the turn gap)
#   m3 27.0-end : swell back in, tail fade-out
fc = (
    # music dynamics: shorter gap (25.9-27.0) so the held-breath, not silence, fills it
    "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start=0:end=25.2,"
    "asetpts=N/SR/TB,afade=t=in:st=0:d=2[m1];"
    "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start=25.2:end=27.0,"
    "asetpts=N/SR/TB,afade=t=out:st=0.2:d=0.6[m2];"
    "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=start=27.0:end=52.27,"
    "asetpts=N/SR/TB,afade=t=in:st=0:d=1.0,afade=t=out:st=23.8:d=1.6[m3];"
    "[m1][m2][m3]concat=n=3:v=0:a=1[musseq];"
    f"[musseq]volume={BASE}[musg];"
    # sub-bass held-breath, dropped in under the turn (~t25.4)
    "[3:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.7,"
    "adelay=25400|25400[sub];"
    "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[vo][vokey];"
    # lighter duck so music stays present (user: too quiet)
    "[musg][vokey]sidechaincompress=threshold=0.06:ratio=4:attack=20:release=260[musd];"
    "[vo][musd][sub]amix=inputs=3:normalize=0:dropout_transition=0,"
    "loudnorm=I=-14:TP=-1.5:LRA=11[ao]"
)

cmd = [
    ffmpeg_bin(), "-y",
    "-i", str(VID),     # 0: video (+burned captions)
    "-i", str(VO),      # 1: VO
    "-i", str(MUS),     # 2: music
    "-i", str(SUB),     # 3: sub-bass held-breath
    "-filter_complex", fc,
    "-map", "0:v", "-map", "[ao]",
    "-t", str(DUR), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(OUT),
]
print("+ mixing music ->", OUT)
subprocess.run(cmd, check=True)
print("WROTE", OUT)
