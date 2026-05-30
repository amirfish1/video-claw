# "The Review Room" Film — Phase 1 Production Plan (Rev 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. NOTE: media-production plan — "verify" means *render and inspect* (ffprobe + frame grab + visual review), not unit tests.

**Goal:** Assemble a ~59s, 16:9 cinematic LinkedIn film ("The Review Room") from Nano Banana stills, ffmpeg motion/compositing, and a video-claw $0 narration with burned mute-first captions — with the real `free-mode-demo.mp4` screen-composited into the review beat.

**Architecture:** Generate 9 cinematic shot stills (reusing 2 already made), Ken-Burns each, screen-composite the real demo for the review beat, render an end slate, narrate the 6-line script with video-claw's macOS $0 TTS (duration-aware placement), burn the lines on-screen, anchor + loudnorm the audio, and assemble — all via one Python script. Heavy media stays in gitignored `review-room/`; the script is committed.

**Tech Stack:** Nano Banana (`mcp__nanobanana-pro__generate_image`), ffmpeg/ffprobe, `video_claw.tts.macos.synthesize` (the $0 TTS engine), Python 3.

Reference: `docs/superpowers/specs/2026-05-30-review-room-video-design.md` (Rev 2). Rev 2 incorporates the Codex + Antigravity/Gemini peer review.

---

## File Structure

- `review-room/` — **gitignored.** `stills/`, `work/`, output MP4, SRT, poster.
- `review-room/stills/shot_01.png … shot_10.png` — 10 shot frames (shot 11 is a generated slate).
- `scripts/review_room_assemble.py` — **committed.** Full assembler.
- `.gitignore` — add `review-room/`.
- `docs/free-mode-demo.mp4` — existing real clip for the review beat (committed).
- Reused frames in `nanobanana-output/`: two-group establishing → shot 1; tribe huddle → shot 2.

Timing budget (≈59s): S1 6 · S2 5 · S3 4 · S4 4 · S5 10 · S6 3 · S7 6 · S8 4 · S9 6 · S10 7 · slate 4.

---

## Task 1: Scaffold + reuse frames

**Files:** Create `review-room/stills/` (gitignored); modify `.gitignore`.

- [ ] **Step 1: Working dir + ignore**

```bash
mkdir -p review-room/stills review-room/work
printf '\n# Review Room film working media (not source)\nreview-room/\n' >> .gitignore
```

- [ ] **Step 2: Reuse the two existing frames**

```bash
cp nanobanana-output/widescreen_169_cinematic_establi.png review-room/stills/shot_01.png
cp nanobanana-output/widescreen_169_cinematic_still_p_1.png review-room/stills/shot_02.png
ls -la review-room/stills/
```
Expected: `shot_01.png`, `shot_02.png` present.

- [ ] **Step 3: Commit the gitignore**

```bash
git add .gitignore
git commit --only .gitignore -m "chore: ignore review-room/ film working media

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Generate the 8 remaining shot stills

**Files:** Create `review-room/stills/shot_03.png … shot_10.png`.

Each step calls `mcp__nanobanana-pro__generate_image` with `styles: ["photorealistic"]`, then rename the produced `nanobanana-output/*.png` to the exact `review-room/stills/shot_NN.png`. Constant look: **cinematic prestige-TV, teal-amber grade, film grain, shallow DoF, fully human young (~25–30) diverse cast, three tribes by shirt color (blue/charcoal/rust) with ORIGINAL fictional insignia (NOT real company logos) + per-tribe motif (blue=cool haze, charcoal=tablet/terminal glow, rust=warm soft light), no readable text.**

- [ ] **Step 1: Shot 3 — the tablet insert**

Prompt: "Widescreen 16:9 cinematic extreme close-up, prestige-TV office drama, teal-and-amber grade, shallow DoF, film grain. A young rust-orange-shirted hand (Claude tribe, original soft sunrise-arc insignia — not a real logo) holds a glowing tablet showing a clean narrated-slide deck. Faint floating holographic annotation marks/redlines hover near the tablet, suggesting peer review. Soft bokeh of other agents behind. No readable text."
`mv` → `review-room/stills/shot_03.png`.

- [ ] **Step 2: Shot 4 — entering the room**

Prompt: "Widescreen 16:9 cinematic shot, prestige-TV office drama, teal-and-amber grade, film grain, shallow DoF. A young rust-orange-shirted human agent (Claude tribe, original sunrise-arc insignia, warm soft key light) steps through a glass door into a brightly lit executive review room; at the table head an executive sits in backlit silhouette. Fully human, not a robot. No readable text."
`mv` → `review-room/stills/shot_04.png`.

- [ ] **Step 3: Shot 5 — the room with the screen (composite background)**

Prompt: "Widescreen 16:9 cinematic interior, prestige-TV office drama, teal-and-amber grade, film grain. Inside a glass executive review room: a large blank glowing wall presentation screen on the back wall; a young agent stands presenting beside it; an executive silhouette sits foreground watching. Moody, the screen bright and empty. No readable text."
`mv` → `review-room/stills/shot_05.png`. (Used as the BG; the real demo is composited inset by the assembler.)

- [ ] **Step 4: Shot 6 — VP reaction**

Prompt: "Widescreen 16:9 cinematic over-the-shoulder close-up, prestige-TV office drama, teal-and-amber grade, film grain, shallow DoF. Foreground: the silhouetted back of an executive's head/shoulder. Beyond: a young hopeful agent watching for the verdict. A weighing, considered moment. No readable text."
`mv` → `review-room/stills/shot_06.png`.

- [ ] **Step 5: Shot 7 — customer-project placeholder**

Prompt: "Widescreen 16:9 cinematic interior, prestige-TV office drama, teal-and-amber grade, film grain. A young blue-shirted agent (Gemini tribe, original ring/orbit insignia, faint cool-blue haze) presents in the glass room; the wall screen shows an abstract generic small-business app dashboard (charts, a calendar, a booking widget), clearly a customer project with no real branding. Executive silhouette watches. No readable text."
`mv` → `review-room/stills/shot_07.png`. (Placeholder; swap real Ineed AI clip in Phase 2.)

- [ ] **Step 6: Shot 8 — approval beat**

Prompt: "Widescreen 16:9 cinematic extreme close-up, prestige-TV office drama, film grain, shallow DoF. A young agent's chest insignia and face catch a sudden soft GREEN glow of approval; relief breaking across the face. Warm green light momentarily replacing the cold corridor tones. No readable text."
`mv` → `review-room/stills/shot_08.png`.

- [ ] **Step 7: Shot 9 — the threshold (sent back vs relieved)**

Prompt: "Widescreen 16:9 cinematic shot, prestige-TV office drama, teal-and-amber grade, film grain. At the glass doorway, a group of young agents EXITING — most relieved/smiling, but ONE holding a glowing red 'rejected/sent-back' marker, dejected — passes a nervous group ENTERING. Mixed tribe shirt colors (blue, charcoal, rust) with original insignia in both groups. Fully human, diverse, young. No readable text."
`mv` → `review-room/stills/shot_09.png`.

- [ ] **Step 8: Shot 10 — the reveal / pull-back**

Prompt: "Widescreen 16:9 cinematic wide pull-back, prestige-TV office drama, teal-and-amber grade, film grain, deep perspective. A long corridor packed with a queue of young tribe-colored agents (blue, charcoal, rust) toward a glowing glass review room. Inside, the executive silhouette is revealed as a lone founder at the table; the glass reflects faint scrolling terminal/code text, blurring human and machine. Epic, intimate, aspirational. No readable lettering on people."
`mv` → `review-room/stills/shot_10.png`.

- [ ] **Step 9: Verify all 10 stills**

```bash
ls review-room/stills/shot_0{1,2,3,4,5,6,7,8,9}.png review-room/stills/shot_10.png && echo OK
```
Expected: all 10, `OK`. (No commit — gitignored.)

---

## Task 3: Write the assembler script

**Files:** Create `scripts/review_room_assemble.py`.

- [ ] **Step 1: Write the full assembler**

Create `scripts/review_room_assemble.py` with exactly this content:

```python
#!/usr/bin/env python3
"""Assemble "The Review Room" Phase-1 cut.

Stills (centered Ken Burns) + graded screen-composite of the real $0 demo +
end slate + duration-aware video-claw $0 narration + burned mute-first captions
+ silent-anchored, loudnorm'd audio (no -shortest truncation).
Output: review-room/review-room-v1.mp4 (+ .srt). Run from repo root:
    python3 scripts/review_room_assemble.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RR = ROOT / "review-room"
STILLS = RR / "stills"
WORK = RR / "work"
CLIPS = WORK / "clips"
for d in (WORK, CLIPS):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
# A common macOS TrueType font; change if missing on this machine.
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"

SLATE_TITLE = "This is how Ineed AI ships."
SLATE_CTA = "Ineed AI  -  your small business, run by agents."

# id, source, kind, duration_s, motion, fade_in, fade_out
SHOTS = [
    ("01", STILLS / "shot_01.png", "still", 6, "in",  True,  False),
    ("02", STILLS / "shot_02.png", "still", 5, "pan", False, False),
    ("03", STILLS / "shot_03.png", "still", 4, "in",  False, True),   # act break
    ("04", STILLS / "shot_04.png", "still", 4, "in",  True,  False),
    ("05", ROOT / "docs/free-mode-demo.mp4", "screen", 10, None, True, True),
    ("06", STILLS / "shot_06.png", "still", 3, "in",  False, False),
    ("07", STILLS / "shot_07.png", "still", 6, "pan", False, True),   # act break
    ("08", STILLS / "shot_08.png", "still", 4, "in",  True,  False),
    ("09", STILLS / "shot_09.png", "still", 6, "pan", False, False),
    ("10", STILLS / "shot_10.png", "still", 7, "out", False, True),
    ("11", None,                   "slate", 4, None,  True,  True),
]

# (desired_start, text). Actual offsets recomputed from measured WAV durations.
VO_LINES = [
    (2.0,  "I don't have a team. I have a bench of agents."),
    (8.0,  "Some build for our customers. Some rebuild our own backend."),
    (15.0, "Every task gets reviewed before it reaches my desk."),
    (22.0, "Then, one by one, they come in and present."),
    (40.0, "I approve. Or I send it back."),
    (49.0, "This is how Ineed AI ships."),
]


def run(cmd):
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)


def probe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def _fades(dur, fin, fout):
    f = []
    if fin:
        f.append("fade=t=in:st=0:d=0.6")
    if fout:
        f.append(f"fade=t=out:st={dur-0.6:.3f}:d=0.6")
    return f


def ken_burns(src, dur, motion, fin, fout, out):
    frames = int(dur * FPS)
    uw, uh = int(W * 1.5), int(H * 1.5)   # modest upscale -> no zoompan OOM
    if motion == "out":
        z = "if(eq(on,0),1.12,max(zoom-0.0006,1.0))"
    elif motion == "pan":
        z = "1.08"
    else:
        z = "min(zoom+0.0006,1.12)"
    if motion == "pan":
        x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    else:
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = (
        f"scale={uw}:{uh}:force_original_aspect_ratio=increase,"
        f"crop={uw}:{uh}:(in_w-{uw})/2:(in_h-{uh})/2,"          # CENTERED crop
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
        f"setsar=1,fps={FPS},format=yuv420p"
    )
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur),
         "-r", str(FPS), "-vf", vf, "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def screen_shot(src, dur, fin, fout, out):
    """Graded 'on the room screen' composite so the demo lives in the world."""
    bg = STILLS / "shot_05.png"
    fl = ["format=yuv420p"] + _fades(dur, fin, fout)
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,"
        f"eq=brightness=-0.18:saturation=0.9,setsar=1,fps={FPS}[bg];"
        f"[1:v]scale={int(W*0.6)}:-2,eq=contrast=1.05,"
        f"colorbalance=rm=0.04:bm=-0.04,setsar=1,fps={FPS}[demo];"
        f"[bg][demo]overlay=(W-w)/2:(H-h)/2-40,vignette=PI/5,"
        + ",".join(fl) + "[v]"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(bg),
         "-i", str(src), "-filter_complex", fc, "-map", "[v]", "-t", str(dur),
         "-r", str(FPS), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def make_slate(dur, fin, fout, out):
    t = WORK / "slate_title.txt"
    t.write_text(SLATE_TITLE)
    c = WORK / "slate_cta.txt"
    c.write_text(SLATE_CTA)
    vf = (
        f"format=yuv420p,"
        f"drawtext=fontfile={FONT}:textfile={t}:fontcolor=white:fontsize=66:"
        f"x=(w-tw)/2:y=h/2-70,"
        f"drawtext=fontfile={FONT}:textfile={c}:fontcolor=0xC9C9C9:fontsize=34:"
        f"x=(w-tw)/2:y=h/2+30"
    )
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c=0x0c0f14:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def build_audio(total, placed, out):
    """Silent base anchors the whole timeline; VO mixed in; final loudnorm."""
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo"]
    for _, _, wav, _ in placed:
        inputs += ["-i", str(wav)]
    fc, labels = [], ["[0:a]"]
    for i, (start, _d, _w, _t) in enumerate(placed, start=1):
        ms = int(start * 1000)
        fc.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    fc.append("".join(labels)
              + f"amix=inputs={len(placed)+1}:normalize=0:dropout_transition=0[mix]")
    fc.append("[mix]loudnorm=I=-16:TP=-1.5:LRA=11[ao]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[ao]", "-t", f"{total}", "-c:a", "aac", "-b:a", "192k", str(out)])


def burn_captions(in_v, placed, out):
    chain = ["format=yuv420p"]
    for i, (start, d, _w, text) in enumerate(placed):
        cf = WORK / f"cap_{i:02d}.txt"
        cf.write_text(text)
        end = start + d
        chain.append(
            f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=white:fontsize=46:"
            f"box=1:boxcolor=0x000000AA:boxborderw=18:"
            f"x=(w-tw)/2:y=h-170:enable='between(t,{start:.2f},{end:.2f})'"
        )
    run(["ffmpeg", "-y", "-i", str(in_v), "-vf", ",".join(chain), "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def _srt_ts(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def main():
    listfile = WORK / "concat.txt"
    total = 0.0
    with listfile.open("w") as f:
        for sid, src, kind, dur, motion, fin, fout in SHOTS:
            out = CLIPS / f"shot_{sid}.mp4"
            if kind == "still":
                ken_burns(src, dur, motion, fin, fout, out)
            elif kind == "screen":
                screen_shot(src, dur, fin, fout, out)
            elif kind == "slate":
                make_slate(dur, fin, fout, out)
            f.write(f"file '{out.as_posix()}'\n")
            total += dur

    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])

    # Narration via video-claw's $0 TTS (best installed macOS voice),
    # placed duration-aware so lines never overlap.
    sys.path.insert(0, str(ROOT))
    from video_claw.tts.macos import synthesize
    placed, prev_end = [], 0.0
    for i, (anchor, text) in enumerate(VO_LINES):
        wav = WORK / f"vo_{i:02d}.wav"
        synthesize(text, wav, voice="auto")
        d = probe_dur(wav)
        start = max(anchor, prev_end + 0.6)
        placed.append((start, d, wav, text))
        prev_end = start + d

    audio = WORK / "audio.m4a"
    build_audio(total, placed, audio)
    captioned = WORK / "captioned.mp4"
    burn_captions(silent, placed, captioned)

    final = RR / "review-room-v1.mp4"
    run(["ffmpeg", "-y", "-i", str(captioned), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
         "-shortest", str(final)])  # safe: video and audio are both == total

    srt = RR / "review-room-v1.srt"
    with srt.open("w") as f:
        for i, (start, d, _w, text) in enumerate(placed, start=1):
            f.write(f"{i}\n{_srt_ts(start)} --> {_srt_ts(start+d)}\n{text}\n\n")
    print("\nWROTE", final, "and", srt, f"(~{total:.0f}s)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit the script**

```bash
git add scripts/review_room_assemble.py
git commit --only scripts/review_room_assemble.py -m "feat(film): Review Room assembler rev2 (composite, captions, anchored audio)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Render and verify

**Files:** produces `review-room/review-room-v1.mp4` + `.srt` (gitignored).

- [ ] **Step 1: Confirm the font path exists** (drawtext needs it)

Run: `ls "/System/Library/Fonts/Supplemental/Arial.ttf" || ls /System/Library/Fonts/*.ttf | head`
If Arial is absent, set `FONT` in the script to a present `.ttf`/`.ttc` and re-save.

- [ ] **Step 2: Run the assembler**

Run: `python3 scripts/review_room_assemble.py`
Expected: ends with `WROTE .../review-room-v1.mp4 and .../review-room-v1.srt (~59s)`. If one ffmpeg sub-call errors, fix that function and re-run.

- [ ] **Step 3: Verify duration, resolution, audio, and no truncation**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 review-room/review-room-v1.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 review-room/review-room-v1.mp4
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 review-room/review-room-v1.mp4
```
Expected: duration ~58–60s (the full slate present → no `-shortest` truncation); `1920,1080`; `aac`.

- [ ] **Step 4: Eyeball key frames**

```bash
for t in 3 12 30 44 52 58; do ffmpeg -y -ss $t -i review-room/review-room-v1.mp4 -frames:v 1 review-room/work/check_$t.png; done
```
Read `check_3` (huddle + a burned caption), `check_12` (insert/enter), `check_30` (demo inset on screen, graded), `check_44` (threshold/sent-back), `check_52` (reveal), `check_58` (end slate). Confirm: captions legible, demo reads as on-screen, tribe colors/insignia present, slate shows.

- [ ] **Step 5: Fix-and-rerun loop (as needed)**

If a shot is off: regenerate the still (Task 2 prompt) or adjust its `SHOTS` row / a filter in the script; re-run Step 2. Re-commit the script if changed.

---

## Task 5: Deliver

**Files:** `review-room/poster.png` (gitignored), plus the MP4 + SRT.

- [ ] **Step 1: Grab a poster/thumbnail frame**

Pick a strong hero beat (the pull-back reveal):
```bash
ffmpeg -y -ss 52 -i review-room/review-room-v1.mp4 -frames:v 1 review-room/poster.png
```

- [ ] **Step 2: Send the deliverables to the user**

`SendUserFile` (status `normal`) with `review-room/review-room-v1.mp4`,
`review-room/review-room-v1.srt`, and `review-room/poster.png`. Caption: Phase-1
stylized cut — real $0 demo screen-composited at the review beat, narrated by
video-claw's $0 TTS, burned mute-first captions, shot-7 is the swap-in
placeholder.

- [ ] **Step 3: Hand over the Phase-2 blueprint + caption**

In the message: list the marquee shots to regenerate externally (1, 4, 9, 10)
with their Task-2 prompts; note where to drop the real Ineed AI clip (the `SHOTS`
row 07 → swap to a `"screen"` row) and exact brand/CCC logos; remind that a
royalty-free or user-supplied music bed goes under the VO in Phase 2; offer a
9:16 teaser crop; and paste the draft LinkedIn caption from the spec.

---

## Self-Review notes

- **Spec (Rev 2) coverage:** look bible + original insignia + per-tribe motif →
  Task 2 prompts; visible orchestration (annotations) → shots 3/2; "sent back"
  beat → shot 9; screen composite + grade → `screen_shot()`; founder/VP reveal →
  shot 10; end slate + CTA → `make_slate()` + SHOTS row 11; mute-first burned
  captions + SRT → `burn_captions()` + SRT writer; duration-aware VO →
  `main()` placement loop; anchored audio + loudnorm + no truncation →
  `build_audio()` (anullsrc base) and the final mux note; dip-to-black act breaks
  → `fade_out`/`fade_in` on SHOTS rows 03/04/07/08 and start/slate; delivery
  package (poster, SRT, caption, 9:16 note) → Task 5; narration sharper line →
  VO_LINES[2].
- **Peer-review fixes confirmed in code:** centered crop `(in_w-uw)/2`; modest
  1.5× upscale (no zoompan OOM); `setsar=1,fps` normalization on every clip incl.
  the real demo; silent `anullsrc` base anchoring `amix`; `-shortest` only at the
  final mux where video and audio are both exactly `total`; `loudnorm` pass.
- **No copyrighted assets:** original fictional tribe insignia (no real logos);
  no music track embedded (Phase 2); original VO script + caption; the real demo
  clip is the user's own.
- **Consistency:** `ken_burns / screen_shot / make_slate / build_audio /
  burn_captions` signatures match their call sites; `placed` is a uniform
  `(start, dur, wav, text)` 4-tuple everywhere; shot files are
  `review-room/stills/shot_01.png … shot_10.png`.
```
