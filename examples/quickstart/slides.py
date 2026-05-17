"""Quickstart: a 3-slide narrated video to verify the install works.

Run from this directory:
    video-claw render

If ELEVENLABS_API_KEY is set (env or `keys set`), this will speak each
narration line in the Jessica voice, burn word-aligned captions, and write
out/quickstart.mp4. Total render time: ~30 sec on first run, ~2 sec on re-runs.
"""

CONFIG = {
    "title": "video-claw quickstart",
    "orientation": "horizontal",   # try "short" to render 1080x1920
    "out_path": "out/quickstart.mp4",
    "tts": {
        "provider": "elevenlabs",
        "voice_id": "cgSgspJ2msm6clMCkdW9",   # Jessica
        "model": "eleven_turbo_v2_5",
        "speaking_rate": 1.0,
    },
}

SLIDES = [
    {
        "type": "html",
        "html": "slides/intro.html",
        "narration": (
            "If you can write HTML, you can write a video. "
            "Three slides, three narration lines, one MP4."
        ),
    },
    {
        "type": "html",
        "html": "slides/point.html",
        "narration": (
            "Each slide carries one idea. The narration carries the meaning. "
            "Captions are aligned word by word and burned in."
        ),
    },
    {
        "type": "html",
        "html": "slides/outro.html",
        "narration": (
            "Edit slides dot py, run render, ship the file. "
            "Re-runs are cached. Iterate as much as you want."
        ),
    },
]
