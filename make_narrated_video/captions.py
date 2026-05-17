"""SRT + ASS caption generation from ElevenLabs `with-timestamps` alignment.

Public entry points:
  - build_srt_for_slide(idx, offset_s, rate, workdir) -> [(start, end, text), ...]
  - write_master_srt(entries, out_path)
  - write_master_ass(entries, out_path, *, width, height)

Each ElevenLabs alignment JSON has parallel arrays:
  characters, character_start_times_seconds, character_end_times_seconds

We reassemble word boundaries on whitespace/punctuation, then group ~7 words
per chunk, breaking on punctuation when possible. If audio was sped up via
atempo (rate != 1.0), original-speed timings are divided by rate to match
the sped-up timeline.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple


Entry = Tuple[float, float, str]


def fmt_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_srt_for_slide(idx: int, offset_s: float, rate: float,
                        workdir: Path) -> List[Entry]:
    """Read `narr_NN.alignment.json` from workdir; return caption chunks already
    offset by `offset_s` (cumulative start time of this slide in the final
    concatenated video).
    """
    align_path = workdir / f"narr_{idx:02d}.alignment.json"
    if not align_path.exists():
        return []
    align = json.loads(align_path.read_text())
    chars = align.get("characters") or []
    starts = align.get("character_start_times_seconds") or []
    ends = align.get("character_end_times_seconds") or []
    if not chars or not starts or not ends:
        return []

    r = max(rate, 1e-3)

    # Reassemble word boundaries: split on whitespace + retain trailing punctuation.
    words: List[Tuple[float, float, str]] = []
    cur_word = ""
    cur_start: float | None = None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace() or ch in ".,!?;:":
            if cur_word:
                tail = ch if ch in ".,!?;:" else ""
                words.append((cur_start / r, e / r, cur_word + tail))
                cur_word = ""
                cur_start = None
            continue
        if not cur_word:
            cur_start = s
        cur_word += ch
    if cur_word and cur_start is not None:
        words.append((cur_start / r, ends[-1] / r, cur_word))

    # Group into chunks of ~7 words, breaking on punctuation if possible.
    chunks: List[List[Tuple[float, float, str]]] = []
    chunk: List[Tuple[float, float, str]] = []
    for w in words:
        chunk.append(w)
        last_text = w[2]
        if len(chunk) >= 6 and (last_text.endswith(",") or last_text.endswith(".")):
            chunks.append(chunk)
            chunk = []
        elif len(chunk) >= 9:
            chunks.append(chunk)
            chunk = []
    if chunk:
        chunks.append(chunk)

    entries: List[Entry] = []
    for c in chunks:
        start = c[0][0] + offset_s
        end = c[-1][1] + offset_s
        text = " ".join(w[2] for w in c).strip()
        entries.append((start, end, text))
    return entries


def write_master_srt(entries: List[Entry], out_path: Path) -> None:
    with out_path.open("w") as f:
        for i, (start, end, text) in enumerate(entries, start=1):
            f.write(f"{i}\n{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n{text}\n\n")


def write_master_ass(entries: List[Entry], out_path: Path, *,
                     width: int = 1920, height: int = 1080) -> None:
    """ASS subtitle file with styling baked in (avoids ffmpeg force_style quoting
    headaches). MarginV biases captions to the lower-third; MarginR=560 keeps
    text out of the bottom-right corner where the optional lipsync badge sits.
    """
    margin_r = 560 if width >= 1600 else 80
    margin_l = 120 if width >= 1600 else 60
    margin_v = 80 if width >= height else 220
    fontsize = 44 if width >= 1600 else 56
    header = f"""[Script Info]
Title: make-narrated-video captions
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{fontsize},&H00F5F5F2,&H000000FF,&H001A1A1A,&HA0000000,1,0,0,0,100,100,0,0,1,3,1,2,{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    parts = [header]
    for (start, end, text) in entries:
        t = text.replace("{", "\\{").replace("}", "\\}")
        parts.append(
            f"Dialogue: 0,{fmt_ass_time(start)},{fmt_ass_time(end)},Default,,0,0,0,,{t}\n"
        )
    out_path.write_text("".join(parts))
