# v2.10 reveal-callback assets

Standalone creative assets supporting the v2.10 reveal: the three bustling rooms
shown EMPTY, one after another, as the film reveals the team was AI agents.
These are RAW picture/audio for a CapCut pipeline — fades, speed, and timing are
applied downstream, not here.

All video/audio encoded with the bundled imageio-ffmpeg binary
(`ffmpeg-macos-aarch64-v7.1`), not Homebrew ffmpeg.

Build scripts (reproducible) live one level up in `review-room/v2.10/`:
`build_kenburns.py`, `build_roomtones.py`, `build_vo.py`.

## A — Ken Burns clips (fade-free, no audio, no baked text)

Each: 1920x1080, 30 fps, 4.50 s (135 frames), libx264 High, yuv420p (full-range
yuvj420p from the source PNG), `+faststart`. No audio stream (`-an`). No fades.
Source plates are 1365x768; upscaled to a 7680x4320 lanczos working canvas, then
ffmpeg `zoompan` renders the move to 1920x1080. Total zoom range stays within
~1.00–1.12 and uses `d=135` for a smooth, non-jittery move.

| File | Source plate | Move | Duration |
|------|--------------|------|----------|
| `kenburns_hub.mp4` | v2.8/assets/empty_hub.png | slow push-IN (zoom 1.00→1.12, centered) | 4.50 s |
| `kenburns_debate.mp4` | v2.7/assets/empty_debate_room.png | slow PAN left→right (constant zoom 1.06) | 4.50 s |
| `kenburns_meeting.mp4` | v2.8/assets/empty_meeting.png | slow pull-OUT (zoom 1.12→1.00, centered) | 4.50 s |

The three moves are deliberately distinct (in / pan / out) so the reveal beats
don't feel identical.

## B — Room-tone ambient beds

Each: ~6.00 s, WAV PCM s16le, 48 kHz, stereo, with a 0.3 s fade in/out on the
tone itself (these are ambience, so the gentle edge fade is intentional and only
affects the audio, not any picture).

**Method: ElevenLabs text-to-sound-effects** (`/v1/sound-generation`,
`duration_seconds=6`) for all three — the endpoint returned audio successfully,
so no ffmpeg-synth fallback was needed. Each room was prompted for its own space:

| File | Prompt intent | Measured mean / max level | Duration |
|------|---------------|---------------------------|----------|
| `roomtone_hub.wav` | large open office: faint broadband HVAC hum, subtle spacious reverb, slightly brighter | mean -42.6 dB / max -30.5 dB | 6.00 s |
| `roomtone_debate.wav` | small room: tighter, low-mid, drier, quieter | mean -45.7 dB / max -33.5 dB | 6.00 s |
| `roomtone_meeting.wav` | quiet conference room: most still/dead, low rumble floor | mean -41.2 dB / max -30.7 dB | 6.00 s |

The three are audibly distinct (different spectral character from the per-room
prompts; debate is the quietest at the mean). An ffmpeg-lavfi fallback
(`anoisesrc` shaped per room) is implemented in `build_roomtones.py` but was not
triggered this run.

## C — Narrator VO lines (reveal callback)

TTS'd via the project's `video_claw.tts.make_audio` helper in the NARRATOR voice
(`provider=elevenlabs`, `voice_id=cgSgspJ2msm6clMCkdW9`,
`model=eleven_turbo_v2_5`, `speaking_rate=1.05`). Output is AAC/m4a, 44.1 kHz
mono. Copied from the helper's workdir output to the asset names below.

| File | Line | Measured duration |
|------|------|-------------------|
| `vo_callback_hub.m4a` | "But the room was never the company." | 1.606 s |
| `vo_callback_debate.m4a` | "There was no team." | 0.886 s |
| `vo_callback_meeting.m4a` | "And no one was ever in the meeting." | 1.439 s |

## Notes / issues

- The three source plates are **1365x768**, not 1920x1080 as the brief assumed.
  Handled by upscaling to a large lanczos canvas before `zoompan`, so the final
  clips are a true 1920x1080 without visible softening.
- Ken Burns pixel format reports as `yuvj420p` (full-range) because it derives
  from a full-range PNG via `format=yuv420p`. This is standard and players treat
  it as yuv420p; no action needed.
- The brief's `cache={}` for `make_audio` is illustrative — the helper requires a
  real `video_claw.cache.Cache` instance (it calls `cache.run(...)`). Used a
  `Cache` pointed at `review-room/v2.10/work`.
- Nothing here modifies the assembler, renders the final film, or touches git.
