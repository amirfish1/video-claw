# Kneaded.ai film — version archive

Every iteration of the LinkedIn film, each in its own folder. **Shared material
lives in `raw/`**; v1's own stills/motion package lives in `v1/owned/`. Later cuts
reference both directly. Each version folder holds its own script + any
version-specific assets; all renders go to **`output/<version>.mp4` (+ `.srt`)**.

All scripts (the canonical copies in `scripts/` and the archived copies in each
version folder) read assets directly from this layout. The old top-level shim
folders (`stills/`, `motion/`, `altframes/`, `samples/`) have been removed.
(`review-room/` is gitignored.)

## Two lineages

**v1** is the original **Review Room motion cut**. The **surprise cut** then
evolved through four writes of the same `review_room_surprise.py`:
**v1.1 → v1.2 → v1.5 → v2**. Each overwrote the previous at the shared output path,
so only **v2's render survives**; the earlier three are reconstructable from their
recovered scripts, and each kept a few check-frames (`lost-render-frames/`) as the
only visual record.

**v2.5** is a **new branch off v1.5** (not v2): it keeps v1.5's strengths (Act 1
fully human, Codex diagram + warm boss) and reworks only beat 3 — the in-person
argument carried by the people's own dialogue, replacing v1.5's chat-on-screen.
Render survives at `output/v2.5.mp4`. See `v2.5/README.md`.

| | v1 | v1.1 | v1.2 | v1.5 | v2 |
|---|---|---|---|---|---|
| **Cut** | Review Room (motion) | Surprise #1 | Surprise #2 | Surprise #3 | Surprise #4 (current) |
| **Script** | `v1/review_room_assemble.py` | `v1.1/…_v1.1.py` *(recovered)* | `v1.2/…_v1.2.py` *(recovered)* | `v1.5/…_v1.5.py` *(recovered)* | `v2/review_room_surprise.py` |
| **Render** | `output/v1.mp4` ✅ | ⚠️ lost (frames only) | ⚠️ lost (frames only) | ⚠️ lost (frames only) | `output/v2.mp4` ✅ |
| **Narration** | macOS `say` ($0) | ElevenLabs | ElevenLabs | ElevenLabs | ElevenLabs |
| **Write time** | — | 11:14 AM | 1:13 PM | 2:22 PM | 5:53 PM |

## Surprise-cut evolution (what changed each step)

- **v1.1** (11:14) — first surprise. 9 beats: hub · debate · group-chat-on-screen ·
  deck-on-screen · agentic-flows · **static diagram** · debate+groupchat overlay ·
  deck clip · slate. Samples + static diagram; no motion, no altframes.
  Frames: `v1.1/lost-render-frames/chk_*` (11:16).
- **v1.2** (1:13) — adds the **animated-diagram** handling (`diagram_anim` with
  static fallback) + motion wiring. Frames: `v1.2/lost-render-frames/v2_*` (1:16).
- **v1.5** (2:22) — swaps in the **hand-picked Codex alternate stills**
  (`v1.5/owned/altframes-codex/`: `chat_human`, `slide_kneaded`, `vp_founder`,
  `diagram_kneaded`). Rejected Claude set in `altframes-claude-rejected/`.
  Frames: `v1.5/lost-render-frames/v3_*` (2:24).
- **v2** (5:53) — drops altframes; uses the **real static diagram** (external
  `diagram_static-paste.png`), group-chat overlays, borrowed motion shots. The one
  render that survives.

## v1 — the Review Room motion cut (`v1/owned/`)

Owns the **entire shot package**: all **10 still seeds** (`stills/shot_01…10.png`)
and all **8 Kling motion clips** (`motion/shot_01,02,03,04,06,08,09,10.mp4`) — it is
the origin of this art. Plus the **$0 demo on a room screen** (shot 5), the
**telemetry pitch @33s** (shot 7), and the **founder/code-on-glass reveal** (shot
10). External: `telemetry-ccc-pitch.mp4`.

## Shared material (`raw/`) — not v1's own art

| File | used by |
|---|---|
| `sample3_bustling_hub.mp4`, `sample5_real_debate.mp4`, `sample4_agentic_flows.mp4` | all surprise cuts (v1.1, v1.2, v1.5, v2) |
| `anim_group_chat.mp4` *(copy of `~/Downloads/…`)* | all surprise cuts |
| `free-mode-demo.mp4` *(symlink → `docs/free-mode-demo.mp4`)* | v1 + all surprise cuts |

## Borrowed **from v1** (`v1/owned/`)

The surprise cuts reference v1's art rather than copying it:

| File (in `v1/owned/`) | borrowed by |
|---|---|
| `stills/shot_05.png` (room background) | all surprise cuts |
| `motion/shot_04.mp4` | v1.5, v2 |
| `motion/shot_06.mp4`, `motion/shot_08.mp4` | v2 |

## Not part of any finished cut

`exploration/` — the style/transition test reel (`sample1, 2, 2b, 6, 7, 8`,
`_compare.mp4`) reviewed during development. *(Note: this may have been moved under
`Not-used/`.)*

## Provenance note

The surprise cut's four iterations were successive writes of one
`review_room_surprise.py`, each rendering to the same `surprise-v1.mp4` path and
overwriting the last — so v1.1/v1.2/v1.5 renders are gone. The scripts were
recovered verbatim from the session transcript and modernized to the new layout
(own output names, so they no longer collide). The `lost-render-frames/` in each
folder are check-frame grabs that survived because they had unique names; their
mtimes (11:16 / 1:16 / 2:24 / 5:56) pin each set to its render session.
