"""Explain synthesis cache misses without changing cache identity or doing TTS."""
from __future__ import annotations

import json
from itertools import zip_longest

from . import tts
from .cache import _force_regen


def report(slides, tts_cfg, cache) -> dict:
    """Print a pre-render cache plan and return metadata for a successful render.

    Persist only narration hashes and effective synthesis settings. Changes are
    compared with the last completed synthesis phase, never an aborted preview.
    """
    snapshot = {
        "version": 1,
        "settings": tts.cache_settings(tts_cfg),
        "narrations": [cache.hash([slide["narration"]]) for slide in slides],
    }
    hits = 0
    forced = _force_regen()
    master = snapshot["settings"]["provider"] == "elevenlabs"
    texts = [slide["narration"] for slide in slides]
    if master:
        texts = ["\n\n".join(text.strip() for text in texts)]
    for text in texts:
        key, ext = tts.audio_cache_entry(text, tts_cfg)
        hits += int(cache.path("tts", key, ext).is_file() and not forced)
    misses = len(texts) - hits
    reasons = []
    if misses:
        previous = _load_snapshot(cache)
        if forced:
            reasons.append("MNV_FORCE_REGEN requests re-synthesis")
        elif not any((cache.root / "tts").iterdir()):
            reasons.append("no cache yet")
        elif previous:
            before = previous["settings"]
            after = snapshot["settings"]
            changed = sorted(key for key in before.keys() | after.keys()
                             if before.get(key) != after.get(key))
            if changed:
                reasons.append("TTS config changed: " + ", ".join(changed))
            changed_texts = sum(a != b for a, b in zip_longest(
                previous["narrations"], snapshot["narrations"]))
            if changed_texts:
                reasons.append(f"narration changed on {changed_texts} slide positions")
        if not reasons:
            reasons.append("matching audio missing; no recorded config/text change")
    suffix = f" ({'; '.join(reasons)})" if reasons else ""
    if master:
        suffix += f"; one master take across {len(slides)} slides"
    print(f"[tts cache] {hits} hits / {misses} misses before synthesis{suffix}", flush=True)
    return snapshot


def _load_snapshot(cache):
    try:
        data = json.loads((cache.root / "tts-last-render.json").read_text())
    except (OSError, ValueError):
        return None
    if (isinstance(data, dict) and data.get("version") == 1
            and isinstance(data.get("settings"), dict)
            and isinstance(data.get("narrations"), list)
            and all(isinstance(value, str) for value in data["narrations"])):
        return data
    return None


def remember(cache, snapshot: dict) -> None:
    """Record only after all slides' synthesis succeeded; diagnostics are optional."""
    path = cache.root / "tts-last-render.json"
    try:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(snapshot, sort_keys=True))
        temporary.replace(path)
    except OSError as exc:
        print(f"[tts cache] could not save diagnostics: {exc}")
