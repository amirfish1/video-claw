# video-claw — project instructions

## Review Room film: STATE.md is the source of truth

Before doing ANY work on the Review Room film, **read `review-room/STATE.md`** —
it holds the current version, locked creative decisions, asset map, and next
steps. After a render or a structural decision, **update it** (the assembler
auto-stamps the technical block; you maintain the Decisions/Next block). A
`SessionStart` hook also injects it on start/resume/post-compaction. This file is
the defense against context loss — trust it over a stale Desktop/mobile view.

## Never overwrite a script or a render — always version as a sibling

When iterating on any **generated artifact** (an assembler/build script, a rendered
video, or any output), do **NOT** rewrite the existing file in place. Overwriting
destroys the prior version. (We permanently lost the v1.1, v1.2, and v1.5 *renders*
this way — each write of `review_room_surprise.py` clobbered the last at a shared
output path.)

Instead, for every new iteration:

1. **Create a new sibling version** — its own folder (e.g. `v2.5/` next to
   `v1.5/`, `v2/`) holding that version's script + version-specific assets.
2. **Write to a version-named output** — `output/<version>.mp4` (+ `.srt`), never a
   shared/overwritten filename like `surprise-v1.mp4`.
3. **Promote shared material to `raw/`** — anything used by ≥2 versions lives once in
   `raw/` (or in its originating version's `owned/`) and is *referenced*, not copied.
4. **Keep each version self-contained** — script, render, and its own assets in its
   folder; reference `../raw/` and `../<origin>/owned/` for the rest.

This applies to the film archive under `review-room/` (gitignored) and to any
similar versioned build. The goal: every prior version stays recoverable, and we
never "lose track of which material we used."
