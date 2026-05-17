"""Project config loader.

A project is a directory with `slides.py` (or `project.json`) that defines a SLIDES
list. We also accept a single-file `project.py` containing SLIDES + optional CONFIG.

slides.py format (preferred — Python so narration strings can be multi-line clean):

    CONFIG = {
        "title": "Skill demo",
        "orientation": "horizontal",      # or "short"
        "out_path": "out/skill_demo.mp4", # relative to project dir
        "tts": {
            "provider": "elevenlabs",     # or "deepgram"
            "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
            "model": "eleven_turbo_v2_5",
            "speaking_rate": 1.0,
        },
    }

    SLIDES = [
        {"type": "html", "html": "slides/intro.html", "narration": "Hi, I'm Becky AI..."},
        {"type": "image", "image": "assets/screenshot.png", "narration": "..."},
        {"type": "video", "video": "assets/demo.mp4", "narration": "...", "title": "Demo"},
    ]

Slide schema:
  type:       "html" | "image" | "video"
  html/image/video: path relative to project dir
  narration:  string the TTS engine will speak
  title:      optional, drawn as a strip for image/video slides
  lipsync:    optional bool, requires fal.ai key
  speed:      optional float override (default 1.0)
"""
from __future__ import annotations
import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG = {
    "title": "narrated-video",
    "orientation": "horizontal",  # "horizontal" (1920x1080) or "short" (1080x1920)
    "out_path": "out/video.mp4",
    "tts": {
        "provider": "elevenlabs",
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica (matches CCC-outreach default)
        "model": "eleven_turbo_v2_5",
        "speaking_rate": 1.0,
        # Deepgram fallback voice if provider=deepgram
        "deepgram_voice": "aura-2-thalia-en",
    },
    "lipsync": {
        "avatar": "assets/avatar.png",  # relative to project dir; only used on slides with lipsync=True
        "fal_omnihuman_version": "v1.5",
        "resolution": "720p",
    },
}


@dataclass
class Project:
    project_dir: Path
    config: Dict[str, Any]
    slides: List[Dict[str, Any]]
    out_dir: Path = field(init=False)

    def __post_init__(self):
        self.out_dir = (self.project_dir / "video_build").resolve()

    @property
    def orientation(self) -> str:
        return self.config.get("orientation", "horizontal")

    @property
    def dimensions(self) -> tuple[int, int]:
        return (1080, 1920) if self.orientation == "short" else (1920, 1080)

    @property
    def out_path(self) -> Path:
        p = Path(self.config.get("out_path") or DEFAULT_CONFIG["out_path"])
        if not p.is_absolute():
            p = (self.project_dir / p).resolve()
        return p


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load(project_dir: Path) -> Project:
    project_dir = project_dir.resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    py_path = project_dir / "slides.py"
    json_path = project_dir / "project.json"

    if py_path.exists():
        spec = importlib.util.spec_from_file_location("user_slides", py_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        slides = list(getattr(mod, "SLIDES", []))
        user_cfg = dict(getattr(mod, "CONFIG", {}))
    elif json_path.exists():
        data = json.loads(json_path.read_text())
        slides = list(data.get("slides", []))
        user_cfg = dict(data.get("config", {}))
    else:
        raise FileNotFoundError(
            f"No slides.py or project.json in {project_dir}.\n"
            "Run `video-claw init` to scaffold a project."
        )

    config = _deep_merge(DEFAULT_CONFIG, user_cfg)
    return Project(project_dir=project_dir, config=config, slides=slides)


SAMPLE_SLIDES_PY = '''"""Project: %(title)s

This is the self-referential default scaffold: 4 slides about what video-claw
is. Run `video-claw render` to ship it as-is (~$2 in API calls), or hand this
file to Claude and ask for a video about something else. Claude knows the
schema and the design rules via the video-claw skill.

SLIDES is the source of truth: narration text, slide types, lipsync flags,
and speed overrides all live here. Each slide pairs an HTML/image/video
asset with a string of narration the TTS engine will speak.
"""

CONFIG = {
    "title": "%(title)s",
    "orientation": "%(orientation)s",   # "horizontal" or "short"
    "out_path": "out/%(slug)s.mp4",
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
'''
