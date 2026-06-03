# v2.5 — Surprise cut, v1.5 + reworked beat 3

**Based on v1.5** (not v2) — keeps everything that made v1.5 good (Act 1 fully
human, AI reveal only in Act 2, the Codex clean diagram + warm founder/boss) and
fixes only the third beat per your notes.

- **Script:** `review_room_surprise_v2.5.py`
- **Render:** `../output/v2.5.mp4` (+ `../output/v2.5.srt`), 52s, ElevenLabs.
- **Work/check:** `work/`, `check/`.

## What changed vs v1.5 (beat 3 only)

| | v1.5 beat 3 | v2.5 beat 3 |
|---|---|---|
| Visual | a **chat on a room screen** | the argument **in person** — two debate close-ups (`sample5`, framed on different people) |
| Problem fixed | jumped to a chat right after the in-person debate; leaked the Act-2 "it's online" reveal early | stays fully human → preserves the real-vs-virtual juxtaposition |
| Words | abstract narrator line ("opens on the pain, not the promise…") | the **people's own dialogue** (warm quoted captions, no narrator over this beat) |

## Beat 3 dialogue (two turns)
1. "I think the headline should lead with a promise."
2. "Like — save five hours a week on local marketing?"

## Inputs
`../raw/` (sample3/5/4, group chat, deck) · `../v1/owned/` (motion shot_04, room
bg) · `../v1.5/owned/altframes-codex/` (slide, founder, diagram fallback).

## Known follow-ups
- Beat 7 diagram is still the **static** Codex diagram (the animated `diagram_anim.mp4`
  was never produced; the script auto-swaps it in if it ever lands).
- The two beat-3 turns are crops of one real debate clip. True distinct single-person
  **close-ups** would need new generated footage — easy upgrade if you want it.
