"""Estimated-timing captions for providers with no word-level alignment."""
from __future__ import annotations


def test_estimated_captions_monotonic_and_span():
    from video_claw.captions import build_estimated_srt_for_slide
    text = "one two three four five six, seven eight nine ten."
    entries = build_estimated_srt_for_slide(text, offset_s=5.0, duration=10.0)
    assert entries, "should produce at least one chunk"

    starts = [e[0] for e in entries]
    assert starts == sorted(starts), "starts must be non-decreasing"
    for s, e, t in entries:
        assert e > s, "each caption end must be after its start"
        assert t.strip(), "caption text must be non-empty"

    assert abs(entries[0][0] - 5.0) < 0.5, "first caption starts ~offset"
    assert abs(entries[-1][1] - 15.0) < 0.5, "last caption ends ~offset+duration"


def test_estimated_captions_empty_or_zero_duration():
    from video_claw.captions import build_estimated_srt_for_slide
    assert build_estimated_srt_for_slide("", 0.0, 10.0) == []
    assert build_estimated_srt_for_slide("hi there", 0.0, 0.0) == []
