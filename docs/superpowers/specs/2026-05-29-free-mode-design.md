# Design: `$0 mode` (free mode) for video-claw

Date: 2026-05-29

## Goal

Add a single `mode: "free"` switch to a project's `CONFIG` that guarantees
**zero paid API calls** while still producing a presenter-fronted, captioned
video:

- Narration via the local macOS `say` TTS (free, offline).
- No fal.ai OmniHuman lip-sync (the only per-slide paid step today).
- Becky shown as a **static circular badge on every slide** (the bundled
  `video_claw/assets/avatar.png`).
- **Free estimated-timing captions** burned in via the existing local libass
  path.

`mode: "free"` is an ironclad $0 guarantee: it *forces* the local/free path
rather than merely defaulting to it, so a stray `provider: "elevenlabs"` or a
slide-level `lipsync: True` left in the file cannot silently incur cost.

## Background (current behavior)

- `tts/macos.py` + `tts.make_audio` already support `provider: "macos"`
  (macOS `say` → wav → m4a). Free and offline, no word-level alignment.
- Captions (`captions.py`) and burn-in (`ffmpeg_video.burn_captions`, libass)
  are **100% local and free**. The only paid ingredient anywhere in captions
  is word-level *timing*, which rides inside the ElevenLabs TTS call — it is
  not a separate charge. There is no caption API.
- `core.py` builds captions **only** when the provider starts with `eleven`,
  so macOS/Deepgram slides currently get no captions at all.
- The avatar is shown **only** through fal.ai lip-sync (paid). There is no
  static-image avatar path today.
- `assets/avatar.png` (827×767, transparent background) is Becky — a portrait
  suitable for a circular badge.

## Components

### 1. Activation preset — `config.py`

After the existing `_deep_merge(DEFAULT_CONFIG, user_cfg)`, a new
`_apply_free_mode(config)` runs when `config.get("mode") == "free"`:

Forces (overrides user values — the $0 guarantee):
- `config["tts"]["provider"] = "macos"`
- removes/ignores `lipsync: True` on every slide (free mode never calls fal);
  implemented by clearing the slide-level `lipsync` flag during normalization.
- enables the new `avatar` block (see §3): `{"static": True, "scope": "all",
  "image": "<lipsync.avatar or bundled>", "diameter": 280}`
- enables caption estimation (see §4): `config["captions"]["estimate"] = True`

Respects:
- `config["tts"]["macos_voice"]` if the user set one; otherwise defaults to
  `"Zoe (Premium)"`.

`mode` is added to `DEFAULT_CONFIG` as `None`. The new top-level `avatar` and
`captions` blocks are added to `DEFAULT_CONFIG` so non-free projects have
explicit, documented defaults (`avatar.static = False`,
`captions.estimate = False`).

### 2. macOS voice resolution + fallback — `tts/macos.py`

`say` cannot speak a voice that is not downloaded. Add `_resolve_voice(requested)`:

- Query installed voices via `say -v ?`.
- Match `requested` case-insensitively as a substring of the voice name, so
  `"Zoe"` resolves `"Zoe (Premium)"` and an exact `"Zoe (Premium)"` also matches.
- If no match, print a one-line hint
  (`download "<voice>" in System Settings → Accessibility → Spoken Content;
  falling back to Samantha`) and return `Samantha`.

`synthesize(...)` calls `_resolve_voice(voice)` before invoking `say`, so free
mode never hard-fails on a missing premium voice.

### 3. Static avatar overlay — new `avatar.py` + `ffmpeg_video.py`

New module `video_claw/avatar.py` (single purpose: turn a still image into a
ready-to-overlay circular badge):

- `resolve_avatar_image(avatar_cfg, project_dir) -> Path`
  - Use the configured `image` path (relative to `project_dir`) if it exists.
  - Otherwise fall back to the **bundled** `video_claw/assets/avatar.png`
    (resolved relative to this module's location, so it works after pipx
    install).
- `crop_image_to_circle(png, *, cache, diameter=280) -> Path`
  - ffmpeg `geq` alpha mask mirroring `lipsync.crop_to_circle_video`, but on a
    single still image, producing a circular **PNG** with alpha.
  - Cached via `cache.run("avatar_circle", [png, "diameter", diameter, ...],
    "png", _generate)`. Same wall-clock-timeout + size-ceiling safety as the
    video circle crop.

`core.py`:
- Resolve and circle-crop the avatar once per render (cached) when
  `avatar.static` is on.
- Per slide: when `avatar.scope == "all"` (free mode default), pass the
  circular PNG as a new `avatar_circle` argument to `make_slide_video`.
  (Scopes `"intro"` and `"flagged"` are supported by the config schema for
  future use, but free mode uses `"all"`.)

`ffmpeg_video.py`:
- `make_slide_video(...)` gains `avatar_circle: Optional[Path] = None`.
- New `_static_avatar_overlay_cmd(png, badge_png, m4a, out, ox, oy, pad_dur)`:
  identical to `_lipsync_overlay_cmd` but the badge input uses `-loop 1`
  (still PNG) instead of `-stream_loop -1` (looped MOV). Same bottom-right
  slot math (`diameter=280`, `margin=40`, `oy` lifted 30px) as the lip-sync
  variant.
- Precedence: if `lipsync_circle` is set it wins (animated beats static);
  otherwise if `avatar_circle` is set, use the static overlay; otherwise the
  plain still-slide path. In free mode `lipsync_circle` is always `None`.

### 4. Free estimated-timing captions — `captions.py` + `core.py`

New `build_estimated_srt_for_slide(text, idx, offset_s, duration, rate, workdir)
-> List[Entry]`:

- Reuse the same ~7-word chunking rules as `build_srt_for_slide` (break on
  punctuation at ≥6 words, hard break at ≥9).
- Distribute timing across `[0, duration]` proportionally to per-word
  character length (a word with more characters takes proportionally longer),
  then offset every entry by `offset_s`.
- `duration` is the **measured** post-`atempo` audio length already returned by
  `make_audio`, so no `rate` division is needed (kept in the signature for
  symmetry / future use).

`core.py` caption gate changes from "provider startswith eleven" to:

```
align_path = workdir / f"narr_{idx:02d}.alignment.json"
if align_path.exists():
    all_captions.extend(caps_mod.build_srt_for_slide(idx, cumulative, rate, workdir))
elif captions_cfg.get("estimate"):
    all_captions.extend(caps_mod.build_estimated_srt_for_slide(
        narration, idx, cumulative, dur, rate, workdir))
```

This keeps real ElevenLabs alignment word-perfect while giving macOS/free mode
readable, free captions. `_clamp_overlaps` (already applied at write time)
guarantees monotonic, non-overlapping output.

### 5. Wiring — `core.py` signature + `cli.py`

- `core.make_video(...)` gains `avatar_cfg` and `captions_cfg` parameters
  (both default `None` → empty/disabled), alongside the existing `tts_cfg` /
  `lipsync_cfg`.
- `cli.py` `cmd_render` passes `avatar_cfg=project.config.get("avatar")` and
  `captions_cfg=project.config.get("captions")`.

### 6. Surfacing

- `SAMPLE_SLIDES_PY` scaffold and `SKILL.md` document `CONFIG = {"mode":
  "free", ...}` and what it implies ($0, macOS voice, static Becky, estimated
  captions), so a prompt like "make me a *free* video about X" routes Claude to
  set `mode: "free"`.
- README: short "Free / $0 mode" subsection under the TTS notes.
- Preview gate messaging reflects `$0 — local TTS, no paid APIs` when
  `mode == "free"` (informational; the gate still runs for visual review).

## Data flow

```
CONFIG.mode == "free"
  → config._apply_free_mode  (provider=macos, strip lipsync, avatar.static, captions.estimate)
  → core.make_video(tts_cfg, lipsync_cfg, avatar_cfg, captions_cfg)
      render PNGs → preview gate ($0 message)
      per slide:
        tts.make_audio (macos say → m4a, measured duration)   [free]
        captions: alignment.json? real : estimate(duration)   [free]
        avatar.scope==all → avatar_circle (cached circle PNG)  [free]
        ffmpeg_video.make_slide_video(png, m4a, avatar_circle=…)
      concat → burn_captions (libass)                          [free]
```

## Error handling

- Missing/undownloaded macOS voice → resolved to `Samantha` with a printed
  hint; never a hard failure.
- Avatar image missing at the project path → falls back to bundled asset.
- Circle crop reuses the existing timeout + size-ceiling safety; on failure the
  slide renders without the badge (matches today's lip-sync soft-fail).
- Caption burn failure → existing fallback (raw MP4 + SRT sidecar) unchanged.

## Testing

- `config`: `mode:"free"` forces `provider=macos`, strips slide `lipsync`,
  enables `avatar.static`/`scope=all`, enables `captions.estimate`; respects a
  user-set `macos_voice`; leaves non-free projects untouched.
- `captions`: `build_estimated_srt_for_slide` yields monotonic,
  non-overlapping entries whose span ≈ `duration`, chunking matches the real
  splitter's word grouping.
- `avatar`: `resolve_avatar_image` returns the project path when present and
  the bundled asset when absent.
- macOS-`say`-dependent tests (`_resolve_voice`, `synthesize`) stay gated to
  Darwin, following the existing `platform.system()` pattern.

## Out of scope (YAGNI)

- Linux free TTS (espeak/piper) — macOS-only for now; Linux users keep
  Deepgram/ElevenLabs.
- Non-circular or multi-position avatar layouts.
- Animating the static avatar locally.
```
