# Design: "The Review Room" — Ineed AI LinkedIn film (Phase 1)

Date: 2026-05-30 · Rev 2 (incorporates Codex + Antigravity/Gemini peer review)

## Goal

A ~55–60s cinematic LinkedIn film that brags about how **Ineed AI** (an AI-for-
small-business startup) operates: a one-person company that ships like a team,
because the team is **AI agents**. The agents peer-review each other (the
orchestration layer) before presenting their work to the founder in a VP-style
**review room**. The brand-new video-claw **$0 / auto-defaults** feature appears
as a standout presentation inside the room — and the film itself is narrated by
that very feature.

Two-phase production:
- **Phase 1 (this session):** a complete, watchable *stylized cut* from tools
  available here (Nano Banana stills + ffmpeg motion/compositing + video-claw $0
  narration + burned captions), plus a per-shot prompt list (the Phase 2
  blueprint).
- **Phase 2 (external, later):** regenerate marquee hero shots in an external
  motion generator (Sora/Veo/Kling), swap in the real customer clip, add a music
  bed, and (only if supplied) composite exact brand/CCC logos.

## Peer-review changes baked into this rev

From the cross-engine review: anchor audio with a full-length silent base + drop
`-shortest` (no truncation); centered Ken-Burns crop; `setsar=1`/fps
normalization; `loudnorm`; duration-aware VO placement; **burned mute-first
captions** (+SRT); a **rough screen composite** for the demo (not a raw cut);
**visible orchestration** artifacts + a **"sent back"** beat; an **end slate +
CTA**; a **founder/VP reveal** ending; **original fictional tribe insignia** (no
real logos in Phase 1); a sharper founder narration line; a fuller delivery
package.

## Audience & platform

LinkedIn feed (autoplays **muted** and **loops**). Founder flex for the AI /
startup / build-in-public crowd. **16:9, ~55–60s.** Video carries the *feeling*;
burned captions + the post caption carry the *substance*.

## Hero message (hierarchy)

The **operating model** stays dominant ("this is how Ineed AI ships — a bench of
agents I review like a VP"). The **$0 video-claw feature** is framed as *proof*,
a standout mid-roll beat, **not a detour**. End on the operating-model note.

## Visual bible (locked)

- **Look:** cinematic prestige-TV office drama (Severance-adjacent). Moody
  volumetric corridor lighting, teal-and-amber grade, shallow DoF, film grain.
  Semi-serious; comedy is in the recognition.
- **Cast:** fully **human**, **diverse**, all **young (~25–30)**, modern. No
  elderly. Not robots.
- **Agent tribes (by underlying model)** — read via **shirt color + an ORIGINAL
  fictional insignia + a per-tribe motif** (color alone won't read in 55s of
  moody footage):
  - **Blue** — Antigravity/Gemini. Insignia: a clean original ring/orbit mark.
    Motif: a faint cool-blue volumetric haze around them.
  - **Charcoal/black** — Codex. Insignia: an original angular chevron mark.
    Motif: always holding/working a tablet or terminal glow.
  - **Rust-orange** — Claude. Insignia: an original soft sunrise-arc mark. Motif:
    warmer, softer key light.
  - Groups skew **Claude-heavy** (e.g. a 4-group = 1 blue, 1 charcoal, 2 rust).
  - **No real company logos in Phase 1** — clean original insignia only. Exact
    brand logos and the **CCC** mark are Phase-2, and only if the founder
    supplies the assets.
- **Visible orchestration:** the peer-review huddle shows the layer physically —
  floating annotation cards / redlines / an approval stamp passing between
  agents. One exiting agent carries a **"SENT BACK"** stamp.
- **VP / reviewer:** an abstract executive silhouette — paid off in the final
  **reveal** (below).

## Shot list (11 segments, 3 acts + slate ≈ 59s)

**Act 1 — The Huddle (~15s)**
1. Establishing — corridor, glass room glowing, tribes queued *(frame made)*. 6s
2. Peer-review huddle — a mixed-tribe group around a glowing tablet **with
   floating annotation cards / redlines** between them (orchestration made
   visible). 5s
3. Insert — the tablet showing a video-claw slide; nervous chatter. 4s

**Act 2 — The Review (~21s)**
4. A rust/Claude agent enters; the VP silhouette waits. 4s
5. **[REAL CLIP #1 — screen composite]** the **$0 free-mode demo**
   (`docs/free-mode-demo.mp4`) plays **inset on the room screen**, color-graded +
   vignetted to live inside the cinematic world (not a raw full-frame cut). 10s
6. VP reaction — a considered beat. 3s
7. **[REAL CLIP #2 — placeholder]** a different tribe presents a customer-facing
   Ineed AI project (stand-in frame; swap real clip in Phase 2). 6s

**Act 3 — The Verdict + Reveal (~19s)**
8. Approval beat — the agent's insignia pulses **green**; the nod. 4s
9. The threshold — an **exiting** group (one stamped **"SENT BACK"**, others
   relieved) passes the **entering** group. "Next." *(frame made)*. 6s
10. **The reveal / pull-back** — the long corridor full of tribes; the VP
    silhouette resolves into the **founder, alone** at the table, the glass
    reflecting a **scrolling terminal** — blurring founder and orchestration
    engine. 7s
11. **End slate** — logline **"This is how Ineed AI ships."** + a CTA line, clean
    typography, ~4s (autoplay/loop-friendly). 4s

## Narration (video-claw $0 VO) + mute-first captions

A single calm VO **narrated by video-claw's $0 macOS voice**, and **every line
also burned on-screen** (LinkedIn plays muted) + shipped as an SRT. Lines are
placed **duration-aware** (measured per WAV) so they never overlap. Script:

1. "I don't have a team. I have a bench of agents."
2. "Some build for our customers. Some rebuild our own backend."
3. "Every task gets reviewed before it reaches my desk."   *(sharper founder line)*
4. "Then, one by one, they come in and present."
5. "I approve. Or I send it back."
6. "This is how Ineed AI ships."

**Audio polish:** a full-length silent base anchors the mix; final **`loudnorm`**
(I=-16, TP=-1.5). A music bed is **Phase 2** (royalty-free or user-supplied) — no
copyrighted track embedded.

## Transitions

Phase 1: **hard cuts within acts, dip-to-black at act breaks**, fade-in at start,
fade on the slate. (The earlier "crossfade" wording is corrected — true `xfade`
crossfades are a Phase-2 polish; dips are reliable now.)

## Caption (LinkedIn post copy — proposed)

> I run Ineed AI mostly alone — but it doesn't ship like a one-person company.
>
> I run a bench of AI agents across Claude, Codex and Gemini. Some build for our
> small-business customers; some rebuild our own backend. Before anything reaches
> me, they peer-review each other through an orchestration layer I built (CCC).
> Then they "present" to me — and I approve or send it back, like a review room.
>
> The deck in this film? One of those internal tools — video-claw — just shipped
> a $0 mode: narrated presenter videos with no API keys. This whole video was
> narrated by it.
>
> This is how a startup of one ships like a team.
>
> [CTA / link]

## Delivery package

- The 16:9 MP4 (`review-room/review-room-v1.mp4`).
- Burned captions in the video **+** an `.srt` sidecar.
- A **poster/thumbnail** frame (a strong hero still).
- The LinkedIn caption text (above).
- Optional **9:16 teaser crop** for Stories/Reels (Phase 2 nicety).
- The per-shot prompt blueprint (for Phase 2 regeneration).

## Assets

- Have: `docs/free-mode-demo.mp4` (real clip #5); concept frames in
  `nanobanana-output/`.
- Needed later (Phase 2 / user-supplied): real customer Ineed AI clip (#7), CCC
  logo, exact brand logos, music bed.

## Out of scope (Phase 1)

- Photoreal motion video of people walking/talking (Phase 2, external).
- Exact official brand/CCC logos (original insignia stand in).
- True `xfade` crossfades, music bed, the real customer clip.
