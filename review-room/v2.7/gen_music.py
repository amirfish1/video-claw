#!/usr/bin/env python3
"""Generate the v2.7 score via the ElevenLabs Music API, structured to the cue map.

Sections sum to 52.3s and place the dramatic turn at ~t25.5-30.3 so the drop lands
on the ghost-table dissolve. Output: review-room/v2.7/assets/music_eleven_v1.mp3
Run: python3 review-room/v2.7/gen_music.py
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "review-room" / "v2.7" / "assets"
OUT = ASSETS / "music_eleven_v2.mp3"   # v2: punchier / less mellow (user note)

sys.path.insert(0, str(ROOT))
from video_claw import keys as vkeys
KEY = vkeys.load_keys()["ELEVENLABS_API_KEY"]

plan = {
    "positive_global_styles": [
        "cinematic instrumental brand film score", "modern", "driving", "confident",
        "energetic momentum", "pulsing rhythm", "electronic with warmth", "punchy",
        "high production value", "tasteful tension",
    ],
    "negative_global_styles": [
        "vocals", "lyrics", "singing", "harsh distortion", "horror",
        "sleepy", "mellow", "ambient wash", "cheesy",
    ],
    "sections": [
        {
            "section_name": "ordinary",
            "positive_local_styles": [
                "warm but driving", "bright optimistic pulse", "light rhythmic momentum",
                "modern workday energy", "subtle propulsive groove",
            ],
            "negative_local_styles": ["sleepy", "mellow", "ambient", "dark"],
            "duration_ms": 25500,
            "lines": [],
        },
        {
            "section_name": "the_turn",
            "positive_local_styles": [
                "impactful sub-bass drop", "suspended tension hit",
                "low held drone", "cold resonant swell", "anticipation",
            ],
            "negative_local_styles": ["melody", "busy drums", "warm"],
            "duration_ms": 4800,
            "lines": [],
        },
        {
            "section_name": "reveal",
            "positive_local_styles": [
                "driving electronic pulse", "propulsive arpeggio", "rising intensity",
                "technological momentum", "energetic build", "punchy synth bass",
            ],
            "negative_local_styles": ["mellow", "acoustic", "slow", "ambient"],
            "duration_ms": 14000,
            "lines": [],
        },
        {
            "section_name": "resolve",
            "positive_local_styles": [
                "triumphant warm resolution", "confident uplifting swell",
                "bright hopeful final chord", "strong landing",
            ],
            "negative_local_styles": ["tense", "cold", "fading away", "weak"],
            "duration_ms": 8000,
            "lines": [],
        },
    ],
}

body = json.dumps({"composition_plan": plan, "model_id": "music_v1"}).encode()
req = urllib.request.Request(
    "https://api.elevenlabs.io/v1/music",
    data=body,
    headers={"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=240) as r:
        data = r.read()
    OUT.write_bytes(data)
    print("OK wrote", OUT, f"({len(data)} bytes)")
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, e.reason)
    print(e.read().decode(errors="replace")[:1500])
    sys.exit(1)
except Exception as e:
    print("ERROR", type(e).__name__, e)
    sys.exit(1)
