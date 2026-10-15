"""Offline planning estimates using the approximate rates documented in README.

These are not provider quotes or billing limits. Assume five characters per
word and 150 words/minute before atempo. Cache reuse can reduce actual spend;
model, plan, speech pauses, and provider pricing can change it in either direction.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List

from .avatar import resolve_lipsync_mode
from .tts import resolve_provider


@dataclass(frozen=True)
class SpendEstimate:
    elevenlabs: float
    deepgram: float
    fal: float
    char_count: int
    slide_count: int
    lipsync_seconds: float
    lipsync_slides: int

    @property
    def total(self) -> float:
        return self.elevenlabs + self.deepgram + self.fal


def estimate_spend(slides: List[Dict[str, Any]], tts_cfg: Dict[str, Any]) -> SpendEstimate:
    """Estimate a full render before cache savings; never synthesize or probe audio.

    TTS is charged on the original narration. Speed only affects the duration
    sent to fal.ai, since atempo runs locally after synthesis.
    """
    provider = resolve_provider(tts_cfg)
    if provider not in ("elevenlabs", "deepgram", "macos"):
        raise ValueError(f"Unknown TTS provider: {provider!r}")
    chars = 0
    lipsync_seconds = 0.0
    lipsync_slides = 0
    for idx, slide in enumerate(slides):
        text = slide.get("narration") or ""
        if not text.strip():
            raise ValueError(f"slide {idx}: missing narration text")
        rate = float(slide.get("speed", tts_cfg.get("speaking_rate", 1.0)))
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError(f"slide {idx}: speaking rate must be positive and finite")
        chars += len(text)
        if resolve_lipsync_mode(slide, tts_cfg) == "fal":
            lipsync_slides += 1
            lipsync_seconds += len(text) / 5 / 150 * 60 / rate
    if provider == "elevenlabs":
        chars = len("\n\n".join(slide["narration"].strip() for slide in slides))
    return SpendEstimate(
        elevenlabs=chars / 5 / 150 * 0.30 if provider == "elevenlabs" else 0.0,
        deepgram=chars / 1000 * 0.015 if provider == "deepgram" else 0.0,
        fal=lipsync_seconds * 0.16,
        char_count=chars,
        slide_count=len(slides),
        lipsync_seconds=lipsync_seconds,
        lipsync_slides=lipsync_slides,
    )


def print_estimate(estimate: SpendEstimate) -> None:
    if not estimate.total:
        return

    def dollars(amount: float) -> str:
        if 0 < amount < 0.0001:
            return f"${amount:.6f}".rstrip("0")
        return f"${amount:.4f}" if 0 < amount < 0.01 else f"${amount:.2f}"

    print(f"[spend] estimated cost: ~{dollars(estimate.total)} (before cache savings)")
    for name, amount in (("ElevenLabs", estimate.elevenlabs), ("Deepgram", estimate.deepgram)):
        if amount:
            print(f"        {name}: ~{dollars(amount)} "
                  f"({estimate.char_count} chars across {estimate.slide_count} slides)")
    if estimate.fal:
        print(f"        fal.ai: ~{dollars(estimate.fal)} "
              f"({estimate.lipsync_seconds:.1f} seconds of lipsync on "
              f"{estimate.lipsync_slides} slides)")
    print("        Rough README rates; 5 chars/word, 150 wpm. "
          "Actual charges vary by model/plan/duration; cached or skipped steps cost less.",
          flush=True)
