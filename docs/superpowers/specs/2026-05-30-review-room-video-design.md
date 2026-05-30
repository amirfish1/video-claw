# Design: "The Review Room" — Ineed AI LinkedIn film (Phase 1)

Date: 2026-05-30

## Goal

A ~50–60s cinematic LinkedIn film that brags about how **Ineed AI** (an AI-for-
small-business startup) operates: a one-person company that ships like a team,
because the team is **AI agents**. The agents peer-review each other
(orchestration layer) before presenting their work to the founder in a VP-style
**review room**. The brand-new video-claw **$0 / auto-defaults** feature appears
as a standout presentation inside the room — and the film itself is narrated by
that very feature. The medium is the message.

Two-phase production:
- **Phase 1 (this session):** a complete, watchable *stylized cut* assembled
  entirely from tools available here (Nano Banana stills + ffmpeg motion +
  video-claw narration), plus a shot list where every shot carries its
  generation prompt.
- **Phase 2 (external, later):** regenerate the marquee "hero" shots in an
  external motion-video generator (Sora / Veo / Kling) using the Phase 1
  prompts, swap in the real customer clip, and optionally composite exact brand
  logos. Decided per-shot after viewing Phase 1.

## Audience & platform

LinkedIn feed. Founder flex aimed at the AI / startup / build-in-public crowd.
**16:9, ~50–60s.** Video carries the *feeling*; the caption carries the
*substance*.

## Hero message

Mostly the **operating model** ("this is how Ineed AI ships — a bench of agents
I review like a VP"), with the **$0 video-claw feature** as a standout mid-roll
beat, not the sole payoff. End on the operating-model note.

## Visual bible (locked)

- **Look:** cinematic prestige-TV office drama (Severance-adjacent). Moody
  volumetric corridor lighting, teal-and-amber grade, shallow depth of field,
  film grain. Emotionally semi-serious; the comedy is in the recognition.
- **Cast:** fully **human**, **diverse** (mixed genders/ethnicities), all
  **young (~25–30)**, modern and attractive. No elderly. Not robots.
- **Agent tribes (by underlying model):** signalled by **uniform shirt color +
  a bold chest emblem**:
  - **Blue** — Antigravity / Gemini (four-pointed spark motif)
  - **Charcoal/black** — Codex / OpenAI (geometric knot motif)
  - **Rust-orange** — Claude / Anthropic (sunburst motif)
  - Groups skew **Claude-heavy** (e.g. a group of 4 = 1 blue, 1 charcoal, 2
    rust), reflecting the real agent mix.
- **Brand marks:** rendered as bold **homage** emblems for Phase 1 (recognizable
  by color + signature shape). For exact official logos, composite real brand
  assets in Phase 2. Same for the **CCC** mark — **skipped for now** (no asset
  yet); can be added as a sleeve patch later.
- **VP / reviewer (proposed):** an abstract executive silhouette at the head of
  the glass-room table — could read as the founder. Confirm on review.

## Shot list (10 shots, 3 acts)

**Act 1 — The Huddle (~15s)**
1. Establishing — corridor, glass review room glowing, tribes queued. *(frame
   already generated)*
2. Peer-review huddle — a mixed-tribe group critiquing a deck on a glowing
   tablet (the orchestration layer made physical); anxious faces.
3. Insert — the tablet showing a real video-claw slide; nervous hallway chatter.

**Act 2 — The Review (~25s)**
4. A rust/Claude agent enters the glass room; the VP waits at the table.
5. **[REAL CLIP #1]** the presentation plays on the room's wall screen — the
   **$0 free-mode demo** (`docs/free-mode-demo.mp4`, already in repo). VP watches.
6. VP reaction — a considered beat (nod / raised eyebrow).
7. **[REAL CLIP #2 — placeholder]** a different tribe presents a customer-facing
   Ineed AI project. Phase 1 uses a tasteful stand-in frame; real clip swapped
   in when available.

**Act 3 — The Verdict (~15s)**
8. Approval beat — the agent's badge/emblem pulses **green**; the VP nod.
9. The agent exits, relieved; the **exiting group** passes the **entering
   group** at the threshold (mixed verdicts on the exiting faces). "Next." *(two-
   group frame already generated)*
10. Pull back — corridor full of tribes, queue stretching out → end logline:
    **"This is how Ineed AI ships."**

## Narration (proposed)

A single calm VO, **narrated by video-claw's $0 macOS voice** (the feature being
announced narrates its own announcement). Draft script (~6 lines, adjustable):

1. "I don't have a team. I have a bench of agents."
2. "Some build for our customers. Some rebuild our own backend."
3. "Before anything reaches me, they review each other."
4. "Then, one by one, they come in and present."
5. "I approve, or I send it back."
6. "This is how Ineed AI ships."

Plus light cinematic ambient/music. **Music must be royalty-free or user-
supplied** — no copyrighted tracks embedded. Confirm VO vs. music-only on review.

## Caption (proposed LinkedIn copy)

Draft (adjustable):

> I run Ineed AI mostly alone — but it doesn't ship like a one-person company.
>
> I run a bench of AI agents across Claude, Codex and Gemini. Some build for our
> small-business customers; some rebuild our own backend. Before anything
> reaches me, they peer-review each other through an orchestration layer I built
> (CCC). Then they "present" to me — and I approve or send it back, like a review
> room.
>
> The deck in this film? One of those internal tools — video-claw — just shipped
> a $0 mode: narrated presenter videos with no API keys. This whole video was
> narrated by it.
>
> This is how a startup of one ships like a team.
>
> [CTA / link]

## Production pipeline

**Phase 1 (here), per shot:**
1. Generate the still(s) with Nano Banana (prompts captured in the plan).
2. Animate to a clip with ffmpeg — slow push-in / pan (Ken Burns), subtle
   parallax where possible, crossfade transitions, the teal-amber grade + grain
   baked consistent.
3. For shot 5 (and 7), composite the real video-claw clip onto the room's wall
   screen (ffmpeg overlay into a screen rectangle), or hard-cut to it full-frame.
4. Generate the VO via video-claw `mode:"free"` from the narration script.
5. Assemble: concat shots, lay VO + music bed, output a 16:9 MP4 (~50–60s).

**Phase 1 deliverables:** the assembled MP4 **and** the per-shot prompt list
(which is the Phase 2 blueprint).

**Phase 2 (external, later):** regenerate hero motion shots (1, 4, 9, 10) in
Sora/Veo/Kling from the prompts; swap real clip #7; optionally composite exact
brand logos + CCC.

## Assets

- Have: `docs/free-mode-demo.mp4` (real clip #5); locked concept frames in
  `nanobanana-output/`.
- Needed later (Phase 2 / user-supplied): real customer Ineed AI clip (#7), CCC
  logo, exact brand logos, music bed.

## Open items (confirm on spec review)

- Narration: VO-by-video-claw (proposed) vs. music + on-screen text only.
- VP identity: abstract silhouette (proposed) vs. clearly the founder.
- Caption copy tone + final CTA/link.
- How literal on brand logos in Phase 1 (homage, proposed) vs. wait for Phase 2.

## Out of scope (Phase 1)

- Photoreal motion video of people walking/talking (Phase 2, external).
- Exact official brand logos and CCC mark (need assets).
- The real customer clip (#7) — placeholder until supplied.
