# Music brief — Kneaded.ai film v2.7 (52.3s)

The film is a TWIST, so the score must perform the twist. One flat bed kills it.
Three movements: **Ordinary (warm) → THE TURN (drop) → Reveal (cool) → Resolve
(warm, singular)**. The pivot at t27 (room empties) is the whole point.

## Cue map (timestamps = the rendered cut)
| t | beat | music move |
|---|---|---|
| 0:00 | bustling hub (fade in) | **IN — warm & human.** Soft piano / acoustic + gentle pulse. An ordinary, optimistic workday. Stays UNDER the voices. |
| 0:05–0:16 | the debate | Light, curious, workshoppy. A little rhythmic life as they disagree — but NOTHING ominous (don't tip the twist). |
| 0:16–0:25 | slide → founder review | Subtle **anticipation lift** as the pitch goes to the founder. Small rise, still warm. |
| **0:25.5–0:27** | **THE TURN — pixel-dissolve to empty room** | **THE milestone.** Warm bed CUTS OUT ~0:25.5. ~1s of near-silence / room-tone. Then a low **sub-bass swell + one cold resonant tone** as the room empties at ~0:27.5 under "the room was never the company." Spine-tingle, not horror. |
| 0:30–0:36 | corporate diagram | **Act-2 cool.** Modern synth pad + subtle arpeggio/pulse that can sync to the diagram's pulse dots. "The machine." Building. |
| 0:36–0:44 | chat + deck-agent replays | Add a light rhythmic/UI pulse (ticks, soft clicks). Momentum building to the realization. |
| **0:44–0:48** | **founder isolation** ("Except the founder") | **Warm motif RETURNS — but solo / sparse.** One instrument (a single piano line). The human theme, now alone. Emotional payoff. |
| 0:48–0:52 | end slate | **RESOLVE.** Theme blooms into a confident final chord / button landing on "This is how Kneaded.ai works." |

## The 5 hits a track MUST honor
1. **0:00** warm in
2. **0:25.5** bed drops out (pre-turn silence)
3. **0:27.5** sub-bass swell / cold tone (room empty)
4. **0:44** warm motif returns, singular (founder)
5. **0:48** resolve/button (slate)

## Mix rules
- **Duck under the VO.** Music sits ~-18 to -22 LUFS under narration; sidechain/duck
  so dialogue stays crisp (the VO is already loudnorm'd to -16).
- **Respect the t27 silence** — do not let music paper over the dramatic gap.
- Total length ~52.3s; end clean on the slate (no hard cutoff).

## Sourcing options (pick one)
- **A — generate to-spec** (recommended): a ~52s custom track briefed on the 5 hits
  so the drop lands exactly at 0:27 (e.g. fal music model via CCC, or an ElevenLabs
  music call). Tightest sync.
- **B — library track + edit**: find a royalty-free cue with a natural build/drop;
  I time-stretch/cut it so the drop lands at 0:27 and add the sub-bass hit + duck.
- **C — two-layer build**: warm bed (Act 1 + resolve) + cool bed (Act 2) + a
  transition hit at t27, mixed + ducked in the assembler. Most control, needs 2 stems.
