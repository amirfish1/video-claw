# "The Review Room" — Phase 2 Motion Shot Package

Date: 2026-05-30 · For an external image-to-video generator (Veo 3 / Kling 2.x / Runway Gen-3 / Sora).

## How to use this

Each story shot already has a **seed still** in `review-room/stills/`. Use
**image-to-video** (not pure text-to-video) with that still as the **first
frame** — this keeps the cast, the three tribes (blue/charcoal/rust), the
**original invented insignia (NO real company logos)**, and the room geometry
consistent across shots. Generate 16:9, the listed duration, then drop the
results back into the assembler (see "Re-assembly" at the bottom).

**Global style (append to every prompt):** "cinematic prestige-TV office drama,
Severance-adjacent, teal-and-amber color grade, shallow depth of field, film
grain, moody volumetric lighting, photorealistic, fully human cast, ~25–30 years
old."

**Global negative (every shot):** "no on-screen text, no captions, no watermark,
no real company logos or brand marks, no morphing or distorting faces, no extra
limbs, no robots, no cartoon look."

Shots **5** and **7** stay as the local **screen composites** (real video-claw
$0 demo and the telemetry pitch) — they already have motion; skip them here.
Shot **11** is the static end slate.

---

## Shot 1 — Establishing (seed: `shot_01.png`) · 6s
**Camera/motion:** slow push-in down the corridor; the glass review room glows;
faint people-shift in the queued tribes.
**Prompt:** "Slowly push in down a modern office corridor toward a glowing
glass-walled executive review room at the end. Groups of young human agents in
blue, charcoal and rust uniform shirts wait along the hall, shifting and murmuring
nervously. Subtle volumetric light, slow drifting dust. Tense calm-before-the-room
atmosphere."

## Shot 2 — Peer-review huddle (seed: `shot_02.png`) · 5s
**Camera/motion:** slight handheld drift around the huddle; agents gesture and
whisper; faint holographic annotation/redline marks flicker near the tablet.
**Prompt:** "A tight huddle of young agents in mixed blue/charcoal/rust shirts
lean over a glowing tablet, whispering and pointing, critiquing a presentation.
Faint translucent annotation marks and red redline scribbles flicker in the air
between them. Anxious, collaborative energy. Subtle handheld camera drift."

## Shot 3 — Tablet insert (seed: `shot_03.png`) · 4s
**Camera/motion:** macro; a thumb swipes the slide; redline marks animate in then
settle.
**Prompt:** "Extreme close-up of a young rust-shirted hand holding a glowing
tablet; a thumb swipes to the next clean presentation slide; faint holographic
red annotation marks animate in and settle. Soft bokeh of agents behind. Shallow
focus."

## Shot 4 — Entering the room (seed: `shot_04.png`) · 4s
**Camera/motion:** the agent steps through the glass door; camera follows past the
threshold; the backlit executive turns slightly.
**Prompt:** "A young rust-shirted agent pushes through a glass door into a bright
executive review room; the camera follows them across the threshold. At the table,
a backlit executive in silhouette turns slightly toward them. Anticipation,
held breath."

## Shot 6 — VP reaction (seed: `shot_06.png`) · 3s
**Camera/motion:** static-ish; the executive gives a slow, weighing nod;
foreground silhouette breathes.
**Prompt:** "Over-the-shoulder on a silhouetted executive who gives a slow,
considered, weighing nod. Beyond, a young agent watches hopefully, anxious.
Minimal motion, maximum tension. Shallow depth of field."

## Shot 8 — Approval beat (seed: `shot_08.png`) · 4s
**Camera/motion:** a soft green glow blooms across the agent's chest insignia and
face; relief breaks; a held breath releases.
**Prompt:** "Extreme close-up: a soft green glow of approval blooms across a young
agent's chest insignia and face; relief and a small smile break through; their
held breath releases. Warm green light briefly washing the cold tones."

## Shot 9 — The threshold (seed: `shot_09.png`) · 6s
**Camera/motion:** two groups cross at the glass doorway; the rejected agent's red
'sent-back' marker pulses; relieved agents pass smiling.
**Prompt:** "At a glass doorway, a group of young agents exits — most relieved and
smiling — while one, holding a pulsing red 'sent-back' marker, walks out dejected,
passing a nervous group entering. Mixed blue/charcoal/rust shirts. Crossing
foot-traffic, natural motion, emotional contrast."

## Shot 10 — The reveal / pull-back (seed: `shot_10.png`) · 7s
**Camera/motion:** slow dolly back revealing the full corridor of tribes; inside,
the executive resolves into a lone founder; scrolling terminal/code text reflects
and drifts across the glass.
**Prompt:** "Slow dolly back along a long corridor packed with young tribe-colored
agents toward a glowing glass review room. Inside, the executive silhouette is
revealed as a single lone founder at the table; faint scrolling terminal/code text
reflects and drifts across the glass, blurring human and machine. Epic, intimate,
aspirational pull-back."

---

## Re-assembly (dropping motion clips back in)

1. Save each generated clip as `review-room/motion/shot_NN.mp4` (16:9).
2. In `scripts/review_room_assemble.py`, change those shots' rows from `"still"`
   to a new `"clip"` kind pointing at the motion file. A `"clip"` just needs
   scale/pad to 1920×1080 + `setsar=1,fps=30` + the same fade-in/out (no Ken
   Burns, no screen composite) — say the word and I'll add the ~10-line `clip`
   handler.
3. Keep shots 5, 7 (screen composites) and 11 (slate) as they are.
4. Re-run `python3 scripts/review_room_assemble.py` — the VO, burned captions,
   silent-anchored/loudnorm audio, dip-to-black act breaks, and slate all carry
   over unchanged; only the picture upgrades to motion.

**Continuity checklist when reviewing generated shots:** same cast ages (~25–30),
correct tribe shirt colors, original invented insignia (no real logos), consistent
room geometry/lighting, 16:9, no burned text.
