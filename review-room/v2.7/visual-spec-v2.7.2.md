# Visual Build Spec v2.7.2 (Antigravity deliverable + Director adjustments)

Source: Antigravity (Gemini 3.5 Flash), group chat 2026-06-02. Good skeleton;
**Director adjustments flagged inline** where the lighter model's execution detail
needs engineering judgment. This drives the v2.7 asset generation + assembler.

## Assets to generate (5)
1. `empty_debate_room.png` — clean plate of the empty table matching the camera
   angle/lighting of `raw/sample5_real_debate.mp4` (inpaint the people out).
2. `diagram_corporate_v2.7.2.png` (or `.mp4`) — 3-node corporate orchestration.
3. `group_chat_overlay.png` — high-contrast translucent chat panel, right margin.
4. `deck_agent_overlay.png` — Deck-Agent status card, Codex copy verbatim.
5. `founder_labels_overlay.png` — bounding-box labels for the final shot.

## (a) t30 Diagram — clean corporate-flow  [ACCEPTED as specced]
- Vibe: polished SaaS architecture, NOT a dev IDE. BG deep dark gray `#0c0f14`.
- 3 nodes, vertical hierarchy:
  1. `FOUNDER INPUT` — rounded rect, soft amber `#D97706` border (the brief).
  2. `COORDINATOR AGENT` — hexagon/gear, electric indigo `#3B82F6` (orchestrator).
  3. `AGENT BENCH` — card with 3 sub-labels `Copywriter` · `Audience Planner` ·
     `Designer`, soft teal `#0D9488`.
- Connectors: Founder→Coordinator→Bench, plus a return loop Bench→Coordinator
  (iterative refinement).
- Animation: slow Ken-Burns push-in + amber pulse dots traveling the connectors.

## (b) t45 Founder reprise — UI-label fade  [DIRECTOR ADJUSTMENT]
- Antigravity proposed bounding boxes over the 3 people + fading the two coworkers
  to 10% opacity while the founder stays 100%.
- **Problem:** fading specific *moving people* (not rectangular regions) needs a
  per-subject alpha mask that tracks motion — FFMPEG can't roto arbitrary moving
  subjects cleanly. On `founder_motion.mp4` the people move, so a fixed positional
  mask will smear.
- **Director call (decide at build):**
  - Option 1 (robust): freeze on a STATIC isolation frame for t45 so a fixed
    positional mask reliably dims the two flanking people while the founder stays
    lit. Labels overlay on the frozen frame.
  - Option 2 (simplest): don't dissolve the people at all — let the LABELS carry
    the meaning. Teal `[ AGENT: Audience Planner ]` / `[ AGENT: Copywriter ]` boxes
    over the coworkers, gold `[ HUMAN: Founder ]` box over the founder; founder box
    pulses + label brightens. Reads "two are agents, one is human" without fragile
    masking.
  - Lean: Option 2 first (lowest risk, one render); escalate to Option 1 only if
    the labels alone don't sell the isolation.
- Labels (either option): Left woman teal `[ AGENT: Audience Planner ]`; right
  woman teal `[ AGENT: Copywriter ]`; center founder gold `[ HUMAN: Founder ]`.

## (c) t27 Turn — pixel-dissolve  [ACCEPTED]
- t25.5 start on wide debate (`sample5_real_debate.mp4`), actors visible.
- t26.5 begin clean cross-fade; t27.5 actors fully gone.
- t27.5–t30.3 hold on the empty room/chairs to let it settle.
- Needs `empty_debate_room.png` (matched plate); FFMPEG handles the cross-fade.

## Per-beat shot list (v2.7.2)
| Beat | t | dur | Scene | Visual | Source |
|---|---|---|---|---|---|
| 01 | 0–5 | 5.0 | Bustling Hub | Wide office, fade in | `sample3_bustling_hub.mp4` (exists) |
| 02 | 5–9 | 4.0 | Debate Wide | Team at table | `sample5_real_debate.mp4` (exists) |
| 03a | 9–12.5 | 3.5 | Close-up A | A: the promise | `debate_personA.mp4` (exists) |
| 03b | 12.5–16 | 3.5 | Close-up B | B: the pain | `debate_personB.mp4` (exists) |
| 04 | 16–21 | 5.0 | Kneaded Slide | Campaign slide projected | `slide_kneaded.png` on ROOM (exists) |
| 05 | 21–25.5 | 4.5 | Founder Review | Founder + notes | `founder_motion.mp4` (exists) |
| 06 | 25.5–30.3 | 4.8 | The Turn | Pixel-dissolve to empty table | **GEN** `empty_debate_room.png` + `sample5_real_debate.mp4` |
| 07 | 30.3–36.3 | 6.0 | Diagram | Push-in 3-node corporate diagram | **GEN** `diagram_corporate_v2.7.2` |
| 08 | 36.3–40.3 | 4.0 | Debate Replay | Debate + chat overlay (right) | `sample5_real_debate.mp4` + **GEN** `group_chat_overlay.png` |
| 09 | 40.3–44.3 | 4.0 | Presenter Replay | Hallway + Deck-Agent card | `shot_04.mp4` + **GEN** `deck_agent_overlay.png` |
| 10 | 44.3–48.3 | 4.0 | Founder Reprise | Founder + UI labels (see (b)) | `founder_motion.mp4` + **GEN** `founder_labels_overlay.png` |
| 11 | 48.3–52.3 | 4.0 | End Slate | Clean end card, higher contrast | programmatic (exists) |

NOTE: beat timing differs slightly from v2.6 (shot 05 now 4.5s, shot 06 turn at
25.5). Reconcile against Codex's VO anchors at build — VO turn line is t27.0
("the room was never the company") which sits inside the dissolve hold. Good.
