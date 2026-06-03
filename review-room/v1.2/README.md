# v1.2 — Surprise cut, iteration #2

The **second** surprise-cut attempt (script written 1:13 PM). Builds on v1.1 by
adding **animated-diagram handling** (`diagram_anim` with a static fallback) and
motion wiring. ElevenLabs narration.

- **Script:** `review_room_surprise_v1.2.py` — recovered verbatim from the session
  transcript (1:13 write), modernized to the new layout (reads `../raw`,
  `../v1/owned`; `diagram_anim` → `../raw/diagram_anim.mp4` which was never produced,
  so the static fallback triggers; writes `../output/v1.2.mp4`).
- **Render:** ⚠️ **lost** — overwritten by later surprise iterations. Rebuildable:
  `python3 review-room/v1.2/review_room_surprise_v1.2.py`.
- **Surviving frames:** `lost-render-frames/v2_*.png` (mtime 1:16 PM) — the only
  visual record of this iteration.

Inputs: `../raw/` (samples, deck, group chat) · `../v1/owned/` (room bg, motion) ·
external static diagram. *(The `v2_` filename prefix is just the grab label from
that session — it is **not** version v2.)*
