# v1.5 render was overwritten

v1.5 ("surprise cut, alt-stills") and v2 are two successive writes of
`scripts/review_room_surprise.py`, and both rendered to the **same** output path
`review-room/surprise-v1.mp4`. When v2 was written and re-run, it overwrote both
the script and that render. So **no v1.5 `.mp4` survives** — but everything needed
to rebuild it does:

- **Script:** `review_room_surprise_v1.5.py` here (recovered verbatim from the
  session transcript, 2026-06-01 21:22 write).
- **Inputs:** all resolve today — `owned/altframes-codex/*`, plus `../raw/*`
  (samples, deck, group chat) and `../v1/owned/*` (shot_04, room bg).
- **Surviving frames:** `lost-render-frames/v3_{12,22,45}.png` — check-frame grabs
  from v1.5's actual render (mtime 2:24 PM, matching the 14:22 script write). These
  are the only visual record of what v1.5 looked like before v2 overwrote it.

## To rebuild v1.5

The recovered script reads its altframes from its own `owned/altframes-codex/`, its
samples/deck/group-chat from `../raw/`, and the borrowed `shot_04` + room-bg
`shot_05` from `../v1/owned/`. From the repo root:

```bash
python3 review-room/v1.5/review_room_surprise_v1.5.py
```

It writes to `review-room/output/v1.5.mp4` — its **own** version-named output, so it
**no longer collides with v2** (`output/v2.mp4`). Just run it.

## Known gap

Beat 7 referenced `review-room/motion/diagram_anim.mp4` (an animated diagram that
was never generated) with a fallback to the static `altframes-codex/diagram_kneaded.png`.
A rebuild today will use that static fallback.
