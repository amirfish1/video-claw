# "The Review Room" Film — Phase 1 Production Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. NOTE: this is a media-production plan — "verify" steps mean *render and inspect* (ffprobe + frame grab + visual review), not unit tests.

**Goal:** Assemble a ~55s, 16:9 cinematic LinkedIn film ("The Review Room") entirely from tools available in this session — Nano Banana stills, ffmpeg motion/assembly, and a video-claw $0 narration — with the real `free-mode-demo.mp4` as the in-room presentation.

**Architecture:** Generate 10 cinematic shot stills (reusing 2 already made), Ken-Burns each into a clip with ffmpeg, hard-cut to the real video-claw clip for the review beat, narrate the 6-line script with video-claw's macOS $0 TTS, and assemble everything with one Python script. Heavy media stays in a gitignored `review-room/`; the assembler script is committed.

**Tech Stack:** Nano Banana (`mcp__nanobanana-pro__generate_image`), ffmpeg/ffprobe, `video_claw.tts.macos.synthesize` (the $0 TTS engine), Python 3.

Reference: `docs/superpowers/specs/2026-05-30-review-room-video-design.md`.

---

## File Structure

- `review-room/` — **gitignored working dir.** Holds `stills/`, `work/`, and the output MP4.
- `review-room/stills/shot_01.png … shot_10.png` — the 10 shot source frames.
- `scripts/review_room_assemble.py` — **committed.** The full assembler (Ken Burns → concat with act fades → VO synth → mix).
- `.gitignore` — add `review-room/`.
- `docs/free-mode-demo.mp4` — existing real clip for shot 5 (already committed).
- Reused frames (already in `nanobanana-output/`): the two-group establishing frame → shot 1; the tribe huddle frame → shot 2.

Shot timing budget (≈55s): S1 6 · S2 5 · S3 4 · S4 4 · S5 10 · S6 3 · S7 6 · S8 4 · S9 6 · S10 7.

---

## Task 1: Scaffold working dir + reuse existing frames

**Files:**
- Create: `review-room/stills/` (gitignored)
- Modify: `.gitignore`

- [ ] **Step 1: Create the working dir and ignore it**

Run:
```bash
mkdir -p review-room/stills review-room/work
printf '\n# Review Room film working media (not source)\nreview-room/\n' >> .gitignore
```

- [ ] **Step 2: Copy the two reusable frames into the shot set**

The establishing two-group frame becomes shot 1; the tribe-huddle frame becomes shot 2.
Run:
```bash
cp nanobanana-output/widescreen_169_cinematic_establi.png review-room/stills/shot_01.png
cp nanobanana-output/widescreen_169_cinematic_still_p_1.png review-room/stills/shot_02.png
ls -la review-room/stills/
```
Expected: `shot_01.png` and `shot_02.png` present.

- [ ] **Step 3: Commit the gitignore change**

```bash
git add .gitignore
git commit --only .gitignore -m "chore: ignore review-room/ film working media

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Generate the 8 remaining shot stills

**Files:**
- Create: `review-room/stills/shot_03.png … shot_10.png`

Each step calls `mcp__nanobanana-pro__generate_image` with `styles: ["photorealistic"]`. After generating, move/rename the produced file from `nanobanana-output/` to the exact `review-room/stills/shot_NN.png` path (the tool names files by prompt; rename explicitly). Keep the look constant: **cinematic prestige-TV, teal-amber grade, film grain, shallow DoF, fully human young (~25–30) diverse cast, three tribes by shirt color + bold homage emblem (blue=Gemini spark, charcoal=Codex knot, rust=Claude sunburst), no readable text.**

- [ ] **Step 1: Shot 3 — the tablet insert**

Prompt: "Widescreen 16:9 cinematic extreme close-up, prestige-TV office drama, teal-and-amber grade, shallow depth of field, film grain. A young rust-orange-shirted hand holds a glowing tablet in a dim office corridor; on the tablet, a clean narrated-slide presentation glows. Soft bokeh of other agents behind. Tense, intimate. No readable text."
Then: `mv nanobanana-output/<generated>.png review-room/stills/shot_03.png`
Verify: `ffprobe -v error -show_entries stream=width,height -of csv=p=0 review-room/stills/shot_03.png` → roughly 16:9.

- [ ] **Step 2: Shot 4 — the agent enters the room**

Prompt: "Widescreen 16:9 cinematic shot, prestige-TV office drama, teal-and-amber grade, film grain, shallow depth of field. A young rust-orange-shirted human agent (Claude tribe, sunburst chest emblem) steps through a glass door into a brightly lit executive review room. At the head of the table, an executive in silhouette waits, backlit. Anticipation, tension. The agent is fully human, not a robot. No readable text."
Then `mv` → `review-room/stills/shot_04.png`.

- [ ] **Step 3: Shot 5 — the room with the presentation screen**

Prompt: "Widescreen 16:9 cinematic interior, prestige-TV office drama, teal-and-amber grade, film grain. Inside a glass executive review room: a large blank glowing wall presentation screen dominates the back wall; a young agent stands presenting beside it; an executive silhouette sits foreground watching. Cinematic, tense, the screen is bright and empty ready for content. No readable text."
Then `mv` → `review-room/stills/shot_05.png`. (Backdrop; the real clip hard-cuts over this beat.)

- [ ] **Step 4: Shot 6 — the VP reaction**

Prompt: "Widescreen 16:9 cinematic over-the-shoulder close-up, prestige-TV office drama, teal-and-amber grade, film grain, shallow depth of field. The back of an executive's head/shoulder in foreground silhouette; beyond, a young hopeful agent watches for the verdict. A considered, weighing moment. No readable text."
Then `mv` → `review-room/stills/shot_06.png`.

- [ ] **Step 5: Shot 7 — customer-project placeholder**

Prompt: "Widescreen 16:9 cinematic interior, prestige-TV office drama, teal-and-amber grade, film grain. A young blue-shirted agent (Gemini tribe, spark emblem) presents in the glass review room; the wall screen shows an abstract, generic small-business app dashboard mockup (charts, a calendar, a booking widget) — clearly a customer project, no real branding. Executive silhouette watches. No readable text."
Then `mv` → `review-room/stills/shot_07.png`. (Placeholder — user swaps the real Ineed AI clip in Phase 2.)

- [ ] **Step 6: Shot 8 — the approval beat**

Prompt: "Widescreen 16:9 cinematic extreme close-up, prestige-TV office drama, film grain, shallow depth of field. A young agent's chest emblem and face catch a sudden soft GREEN glow of approval; relief breaking across their face. Warm green light replacing the cold corridor tones for this beat. No readable text."
Then `mv` → `review-room/stills/shot_08.png`.

- [ ] **Step 7: Shot 9 — the threshold (exiting passes entering)**

Prompt: "Widescreen 16:9 cinematic shot, prestige-TV office drama, teal-and-amber grade, film grain. At the glass doorway of the review room, a group of young agents EXITING (relieved, a couple smiling, one dejected) passes a group ENTERING (nervous, prepping). Mixed tribe shirt colors (blue, charcoal, rust) in both groups. A 'next one in' moment. Fully human, diverse, young. No readable text."
Then `mv` → `review-room/stills/shot_09.png`.

- [ ] **Step 8: Shot 10 — the pull-back hero**

Prompt: "Widescreen 16:9 cinematic wide pull-back establishing shot, prestige-TV office drama, teal-and-amber grade, film grain, deep perspective. A long modern office corridor packed with a queue of young human agents in tribe-colored shirts (blue, charcoal, rust), stretching toward a glowing glass review room at the far end. Epic, aspirational, the engine of a company. No readable text."
Then `mv` → `review-room/stills/shot_10.png`.

- [ ] **Step 9: Verify all 10 stills exist**

Run: `ls review-room/stills/shot_0{1,2,3,4,5,6,7,8,9}.png review-room/stills/shot_10.png && echo OK`
Expected: all 10 listed, `OK`.
(No commit — `review-room/` is gitignored.)

---

## Task 3: Write the assembler script

**Files:**
- Create: `scripts/review_room_assemble.py`

- [ ] **Step 1: Write the full assembler**

Create `scripts/review_room_assemble.py` with exactly this content:

```python
#!/usr/bin/env python3
"""Assemble "The Review Room" Phase-1 cut: Ken-Burns stills + real clip +
video-claw $0 narration -> review-room/review-room-v1.mp4.

Run from the repo root:  python3 scripts/review_room_assemble.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # repo root
RR = ROOT / "review-room"
STILLS = RR / "stills"
WORK = RR / "work"
CLIPS = WORK / "clips"
for d in (WORK, CLIPS):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30

# id, source, kind, duration_s, motion, fade_in, fade_out
SHOTS = [
    ("01", STILLS / "shot_01.png", "still", 6, "in",  True,  False),
    ("02", STILLS / "shot_02.png", "still", 5, "pan", False, False),
    ("03", STILLS / "shot_03.png", "still", 4, "in",  False, True),
    ("04", STILLS / "shot_04.png", "still", 4, "in",  True,  False),
    ("05", ROOT / "docs/free-mode-demo.mp4", "clip", 10, None, True, True),
    ("06", STILLS / "shot_06.png", "still", 3, "in",  False, False),
    ("07", STILLS / "shot_07.png", "still", 6, "pan", False, True),
    ("08", STILLS / "shot_08.png", "still", 4, "in",  True,  False),
    ("09", STILLS / "shot_09.png", "still", 6, "pan", False, False),
    ("10", STILLS / "shot_10.png", "still", 7, "out", False, True),
]

VO_LINES = [
    (2.0,  "I don't have a team. I have a bench of agents."),
    (8.0,  "Some build for our customers. Some rebuild our own backend."),
    (15.0, "Before anything reaches me, they review each other."),
    (21.0, "Then, one by one, they come in and present."),
    (40.0, "I approve. Or I send it back."),
    (49.0, "This is how Ineed AI ships."),
]


def run(cmd):
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)


def ken_burns(src, dur, motion, fin, fout, out):
    frames = int(dur * FPS)
    if motion == "out":
        z = f"if(eq(on,0),1.12,max(zoom-0.0006,1.0))"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan":
        z = "1.08"
        x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    else:  # "in"
        z = "min(zoom+0.0006,1.12)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W*2}:{H*2},"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p"
    )
    fades = []
    if fin:
        fades.append("fade=t=in:st=0:d=0.6")
    if fout:
        fades.append(f"fade=t=out:st={dur-0.6}:d=0.6")
    if fades:
        vf += "," + ",".join(fades)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur),
         "-r", str(FPS), "-vf", vf, "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def prep_clip(src, dur, fin, fout, out):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p")
    fades = []
    if fin:
        fades.append("fade=t=in:st=0:d=0.4")
    if fout:
        fades.append(f"fade=t=out:st={dur-0.4}:d=0.4")
    if fades:
        vf += "," + ",".join(fades)
    run(["ffmpeg", "-y", "-i", str(src), "-t", str(dur), "-r", str(FPS),
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def main():
    listfile = WORK / "concat.txt"
    with listfile.open("w") as f:
        for sid, src, kind, dur, motion, fin, fout in SHOTS:
            out = CLIPS / f"shot_{sid}.mp4"
            if kind == "still":
                ken_burns(src, dur, motion, fin, fout, out)
            else:
                prep_clip(src, dur, fin, fout, out)
            f.write(f"file '{out.as_posix()}'\n")

    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])

    # Narration via video-claw's $0 TTS (best installed macOS voice).
    sys.path.insert(0, str(ROOT))
    from video_claw.tts.macos import synthesize
    vo = []
    for i, (off, text) in enumerate(VO_LINES):
        wav = WORK / f"vo_{i:02d}.wav"
        synthesize(text, wav, voice="auto")
        vo.append((off, wav))

    inputs = ["-i", str(silent)]
    for _, wav in vo:
        inputs += ["-i", str(wav)]
    fc, labels = [], []
    for i, (off, _) in enumerate(vo, start=1):
        ms = int(off * 1000)
        fc.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(vo)}:normalize=0[vomix]")

    final = RR / "review-room-v1.mp4"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "0:v", "-map", "[vomix]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print("\nWROTE", final)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit the script**

```bash
git add scripts/review_room_assemble.py
git commit --only scripts/review_room_assemble.py -m "feat(film): Review Room Phase-1 assembler (ken-burns + real clip + \$0 VO)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Render and verify the cut

**Files:** produces `review-room/review-room-v1.mp4` (gitignored).

- [ ] **Step 1: Run the assembler**

Run: `python3 scripts/review_room_assemble.py`
Expected: ends with `WROTE .../review-room/review-room-v1.mp4`. If a single `ffmpeg`/`zoompan` invocation errors, fix that shot's filter and re-run (only that shot + assembly rerun).

- [ ] **Step 2: Verify duration, resolution, audio**

Run:
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 review-room/review-room-v1.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 review-room/review-room-v1.mp4
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 review-room/review-room-v1.mp4
```
Expected: duration ~50–60s; `1920,1080`; `aac`.

- [ ] **Step 3: Eyeball key frames**

Run:
```bash
for t in 3 18 30 44 53; do ffmpeg -y -ss $t -i review-room/review-room-v1.mp4 -frames:v 1 review-room/work/check_$t.png; done
```
Read `review-room/work/check_3.png` (huddle), `check_18.png` (enter), `check_30.png` (real clip review), `check_44.png` (approval/exit), `check_53.png` (pull-back logline). Confirm look consistency, tribe colors, and that the real clip shows at ~30s.

- [ ] **Step 4: Fix-and-rerun loop (as needed)**

If a shot looks off: regenerate that still (Task 2 prompt, tweak), or adjust its `SHOTS` row (duration/motion) in `scripts/review_room_assemble.py`, then re-run Step 1. Repeat until the cut reads well. (Re-commit the script if you changed it.)

---

## Task 5: Deliver

**Files:** none new.

- [ ] **Step 1: Send the cut to the user**

Use `SendUserFile` with `review-room/review-room-v1.mp4` (status `normal`), caption noting: Phase-1 stylized cut, real $0 demo at the review beat, narrated by video-claw's $0 TTS, shot-7 is the swap-in placeholder.

- [ ] **Step 2: Hand over the Phase-2 blueprint**

In the message, list the marquee shots to regenerate externally (1, 4, 9, 10) with their Task-2 prompts, note where to drop the real Ineed AI clip (shot 5 list row → swap source) and exact brand/CCC logos, and remind that a royalty-free or user-supplied music bed can be laid under the VO. Offer the draft caption from the spec for the post.

---

## Self-Review notes

- **Spec coverage:** look bible → Tasks 1–2 (stills carry the grade/cast/tribes); 10-shot list → Tasks 1–2 + the `SHOTS` table; real clip #5 → `SHOTS` row 05 (`docs/free-mode-demo.mp4`); placeholder #7 → Task 2 Step 5 + swap note in Task 5; narration by video-claw $0 → assembler `synthesize(..., voice="auto")`; 16:9 ~55s → `SHOTS` budget + verify in Task 4; Phase-2 blueprint → Task 5 Step 2; caption → spec (handed over, not embedded in video).
- **No copyrighted assets embedded:** brand marks are homage stills (exact logos deferred to Phase 2, user-supplied); no music track is embedded (Phase 1 is VO-only; user adds royalty-free/own music later); VO script + caption are original.
- **Consistency:** `ken_burns(src, dur, motion, fin, fout, out)` and `prep_clip(src, dur, fin, fout, out)` signatures match their call sites; the `SHOTS` 7-tuple shape is unpacked identically in the build loop; shot files are `review-room/stills/shot_01.png … shot_10.png` everywhere.
- **Note on shot 5:** Phase 1 hard-cuts to the real clip full-frame (letterboxed/padded). Compositing it *into* the on-screen rectangle of shot_05.png is a Phase-2 polish, not required for the cut to read.
```
