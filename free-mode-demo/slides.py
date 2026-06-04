"""Project: free-mode-demo

This is the self-referential default scaffold: 4 slides about what video-claw
is. Run `video-claw render` to ship it as-is (~$2 in API calls), or hand this
file to Claude and ask for a video about something else. Claude knows the
schema and the design rules via the video-claw skill.

SLIDES is the source of truth: narration text, slide types, lipsync flags,
and speed overrides all live here. Each slide pairs an HTML/image/video
asset with a string of narration the TTS engine will speak.
"""

CONFIG = {
    "title": "free-mode-demo",
    "orientation": "horizontal",   # "horizontal" or "short"
    "out_path": "out/free-mode-demo.mp4",
    "mode": "free",
    "tts": {
        "provider": "elevenlabs",
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # ElevenLabs Jessica
        "model": "eleven_turbo_v2_5",
        "speaking_rate": 1.0,
    },
}

SLIDES = [
    {
        "type": "html",
        "html": "slides/intro.html",
        "narration": "Meet video-claw. A tiny tool that turns HTML slides into a narrated MP4.",
        "lipsync": True,    # uses assets/avatar.png; needs FAL_API_KEY
        "speed": 1.15,
    },
    {
        "type": "html",
        "html": "slides/tell_claude.html",
        "narration": "Step one. Tell Claude what you want. A topic, a length, an audience.",
        "speed": 1.15,
    },
    {
        "type": "html",
        "html": "slides/claude_writes.html",
        "narration": "Step two. Claude writes the slides and the narration, following the design rules in the skill.",
        "speed": 1.15,
    },
    {
        "type": "html",
        "html": "slides/outro.html",
        "narration": "Step three. Run video-claw render. You get an MP4 in the out folder. That is the whole thing.",
        "speed": 1.15,
    },
]
