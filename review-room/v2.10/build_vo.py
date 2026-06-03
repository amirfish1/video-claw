#!/usr/bin/env python3
"""TTS the three reveal-callback narrator lines for v2.10 and copy to asset names."""
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())  # repo root holds the video_claw package
import video_claw.tts as vtts
from video_claw.cache import Cache  # make_audio expects a Cache, not a plain dict

ASSETS = Path("review-room/v2.10/assets")
WORK = Path("review-room/v2.10/work")
WORK.mkdir(parents=True, exist_ok=True)

TTS_CFG = {
    "provider": "elevenlabs",
    "voice_id": "cgSgspJ2msm6clMCkdW9",
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.05,
}

LINES = [
    ("But the room was never the company.", "vo_callback_hub.m4a"),
    ("There was no team.", "vo_callback_debate.m4a"),
    ("And no one was ever in the meeting.", "vo_callback_meeting.m4a"),
]

cache = Cache(WORK)
results = []
for idx, (text, dest_name) in enumerate(LINES):
    m4a, dur = vtts.make_audio(text, idx, workdir=WORK, cache=cache, tts_cfg=TTS_CFG)
    dest = ASSETS / dest_name
    shutil.copy2(m4a, dest)
    results.append((dest_name, round(dur, 3), text))
    print(f"[{idx}] {dest_name}  {dur:.3f}s  <- {text!r}")

print("VO durations:", {n: d for n, d, _ in results})
