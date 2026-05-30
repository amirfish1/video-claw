"""The per-slide caption gate: real for ElevenLabs+alignment, else estimated."""
from __future__ import annotations
import json


def test_captions_estimated_for_macos(tmp_path):
    from video_claw.core import _captions_for_slide
    entries = _captions_for_slide("macos", tmp_path, 0, "one two three four",
                                  offset_s=0.0, dur=4.0, rate=1.0, estimate=True)
    assert entries, "macOS should get estimated captions"


def test_captions_none_when_estimate_off_and_not_eleven(tmp_path):
    from video_claw.core import _captions_for_slide
    assert _captions_for_slide("macos", tmp_path, 0, "hi there",
                               offset_s=0.0, dur=4.0, rate=1.0, estimate=False) == []


def test_captions_real_for_eleven_with_alignment(tmp_path):
    from video_claw.core import _captions_for_slide
    (tmp_path / "narr_00.alignment.json").write_text(json.dumps({
        "characters": list("hi there"),
        "character_start_times_seconds": [i * 0.1 for i in range(8)],
        "character_end_times_seconds": [i * 0.1 + 0.1 for i in range(8)],
    }))
    entries = _captions_for_slide("elevenlabs", tmp_path, 0, "hi there",
                                  offset_s=0.0, dur=4.0, rate=1.0, estimate=True)
    assert entries, "ElevenLabs with alignment should produce real captions"


def test_captions_eleven_without_alignment_estimates(tmp_path):
    from video_claw.core import _captions_for_slide
    entries = _captions_for_slide("elevenlabs", tmp_path, 0, "one two three",
                                  offset_s=0.0, dur=3.0, rate=1.0, estimate=True)
    assert entries, "ElevenLabs without an alignment file should fall back to estimate"
