# Design: key-aware "auto" defaults (progressive enhancement)

Date: 2026-05-30

## Goal

Make video-claw **work out of the box with zero keys** and get better as keys
appear, instead of hard-failing when a key is missing. Specifically:

1. **Auto provider selection.** With no explicit provider, pick the best
   pipeline for the keys present: ElevenLabs → Deepgram → macOS local. Only
   error when nothing is possible (Linux with no keys).
2. **Best macOS voice.** Whenever local TTS runs, auto-detect and use the
   highest-quality installed English voice (Premium > Enhanced > basic) instead
   of settling for the basic default.
3. **Captions always.** Every render gets captions — word-aligned from
   ElevenLabs, estimated from everything else (macOS, Deepgram, the no-key
   path). Never silently dropped.

This generalizes the existing `mode: "free"` ($0, macOS-only) into a default
behavior that scales with available keys. `mode: "free"` remains a hard $0
lock; this design changes what happens when no mode is set.

## Background (current behavior)

- `DEFAULT_CONFIG["tts"]["provider"] == "elevenlabs"`. If `ELEVENLABS_API_KEY`
  is missing, `make_audio_elevenlabs` raises a hard error — no fallback.
- `make_audio` dispatches on a concrete provider string; unknown → `ValueError`.
- macOS voice: free mode hardcodes `"Zoe (Premium)"`; `_resolve_voice`
  substring-matches an installed voice and falls back to `Samantha`.
- Captions: only produced for ElevenLabs (real alignment) or when
  `captions.estimate` is set (only free mode sets it). Deepgram/macOS otherwise
  get none.
- `mode: "free"` forces macOS local TTS + static Becky + estimated captions and
  strips paid lip-sync.

## Decisions (approved)

- Default `provider` becomes `"auto"`, resolved at render time from keys +
  platform. Approach chosen over a separate opt-in `mode:"auto"` (we want this
  to be the default) and over rewriting provider at config-load (couples config
  to env state, hides the choice).
- macOS voice auto-detects the best installed voice; explicit `macos_voice`
  still wins.
- Captions are always on; `captions.estimate` defaults to `True`.
- Auto-mode changes **only** TTS selection + captions. It does **not** force the
  Becky avatar (that stays free-mode-only or explicit). Lip-sync already
  degrades gracefully (skips with a notice when no `FAL_API_KEY`).

## Components

### 1. Provider resolution — `tts/__init__.py`

`DEFAULT_TTS["provider"]` and `config.DEFAULT_CONFIG["tts"]["provider"]` change
from `"elevenlabs"` to `"auto"`.

New pure function (no I/O, fully testable by monkeypatching `keys.get` and
`platform.system`):

```
resolve_provider(tts_cfg) -> str
```

- If `provider` is a concrete value (`elevenlabs`/`deepgram`/`macos` and
  aliases) → return it unchanged. Downstream still raises the existing clear
  error if that provider's key is missing (explicit choice is honored).
- If `provider` is `"auto"` (or unset):
  - `ELEVENLABS_API_KEY` present → `"elevenlabs"`
  - else `DEEPGRAM_API_KEY` present → `"deepgram"`
  - else on macOS (`platform.system() == "Darwin"`) → `"macos"`
  - else → `RuntimeError` with a clear message: no TTS key set and macOS `say`
    unavailable; set `ELEVENLABS_API_KEY` or `DEEPGRAM_API_KEY` (or run on a
    Mac for free local TTS).

`make_audio` calls `resolve_provider` first, so `"auto"` never reaches the
dispatch table and direct callers (tests) work too. Resolution is idempotent
for concrete providers.

**Selection table:**

| Keys present | Platform | resolves to |
| --- | --- | --- |
| ElevenLabs | any | elevenlabs (word-aligned captions) |
| Deepgram only | any | deepgram (estimated captions) |
| none | macOS | macos (best local voice, estimated captions) |
| none | Linux | error |

### 2. Best macOS voice — `tts/macos.py`

Extend the `say -v ?` parser to capture each voice's **locale** and **quality
suffix** (`(Premium)` / `(Enhanced)` / none), not just the name.

```
_best_installed_voice() -> str
```

- Rank English voices (`locale` starts with `en`) by quality: Premium = 3,
  Enhanced = 2, basic = 1; return the highest. Deterministic tie-break:
  first in `say -v ?` order.
- If only basic voices exist, return `Samantha` (or the first English basic
  voice if Samantha is somehow absent) and print a one-time hint:
  "for better narration, download a Premium voice in System Settings →
  Accessibility → Spoken Content." Guard the hint with a module-level
  `_warned_basic_only` flag so it prints at most once per process.

`macos_voice` default becomes `"auto"`. In `synthesize` / `make_audio_macos`:
if `macos_voice` is unset or `"auto"`, call `_best_installed_voice()`; otherwise
resolve the explicit name via the existing `_resolve_voice` (substring match +
Samantha fallback). Free mode stops hardcoding `"Zoe (Premium)"` — it leaves
`macos_voice` at `"auto"` so the best installed voice is chosen.

### 3. Captions always on — `config.py` + `core.py`

`DEFAULT_CONFIG["captions"]["estimate"]` defaults to `True`.

Caption gate in `core.py` (using the **resolved** provider — see §4):

```
align_path = workdir / f"narr_{idx:02d}.alignment.json"
if resolved_provider.startswith("eleven") and align_path.exists():
    all_captions.extend(caps_mod.build_srt_for_slide(idx, cumulative, rate, workdir))
elif captions_cfg.get("estimate", True):
    all_captions.extend(
        caps_mod.build_estimated_srt_for_slide(narration, cumulative, dur))
```

Result: ElevenLabs keeps word-perfect captions; everything else (macOS,
Deepgram, auto-local) gets estimated captions. Captions are only absent if the
user explicitly sets `captions: {"estimate": False}` and isn't on ElevenLabs.
The `provider.startswith("eleven") and align_path.exists()` guard preserves the
stale-alignment protection from the prior feature.

### 4. Core wiring — `core.py`

- Resolve the provider **once** before the per-slide loop (provider is constant
  across slides; only `speed` varies):

  ```
  resolved_provider = tts_mod.resolve_provider(tts_cfg)
  if (tts_cfg.get("provider") or "auto").lower() in ("auto", ""):
      print(f"[tts] auto → {resolved_provider} (selected from available keys)")
  ```

- Thread the resolved provider into each slide's `slide_tts` so `make_audio`
  receives a concrete provider and the caption gate sees the real value:
  `slide_tts = {**tts_cfg, "provider": resolved_provider, "speaking_rate": rate}`.
- The existing `[boot] $0 mode …` line stays gated on `free`.

### 5. Config defaults + free-mode preset — `config.py`

- `DEFAULT_CONFIG["tts"]["provider"]`: `"elevenlabs"` → `"auto"`.
- Add `DEFAULT_CONFIG["tts"]["macos_voice"] = "auto"`.
- `DEFAULT_CONFIG["captions"]["estimate"]`: `False` → `True`.
- `_apply_free_mode`: still forces `provider="macos"`, static Becky, strips
  lip-sync, sets `captions.estimate=True`; **stop** setting
  `macos_voice="Zoe (Premium)"` (leave it `"auto"` for best-voice detection).

## Data flow

```
render
  resolve_provider(tts_cfg)  [keys + platform]  -> concrete provider, printed once
  per slide:
    make_audio(provider=resolved)              -> m4a + measured duration
        macos: macos_voice=="auto" -> _best_installed_voice()
    captions: elevenlabs+alignment ? real : estimated(duration)   [always on]
    avatar/lipsync: unchanged (free-mode / explicit / graceful skip)
  concat -> burn captions (libass)
```

## Error handling

- `auto` on Linux with no keys → single clear `RuntimeError` naming the two
  env vars and the macOS option.
- Explicit provider with missing key → unchanged clear per-provider error.
- macOS with no Premium/Enhanced voices → Samantha + one-time download hint;
  never a failure.
- Lip-sync without `FAL_API_KEY` → existing per-slide soft-skip with notice.

## Backward compatibility

- Users with an `ELEVENLABS_API_KEY` and default config: `auto` resolves to
  ElevenLabs → identical output.
- Users who set `provider` explicitly: unchanged (including the missing-key
  error).
- Users with **no** keys (previously a hard error): now get macOS local TTS on
  a Mac, or a clearer error on Linux.
- Deepgram users: now also get estimated captions by default (previously none);
  opt out with `captions: {"estimate": False}`.

## Testing

- `resolve_provider`: monkeypatch `keys.get` + `platform.system` to assert each
  row of the selection table, including the Linux-no-keys error and that an
  explicit provider passes through untouched.
- `_best_installed_voice`: feed a fake `say -v ?` sample (Premium, Enhanced,
  basic, plus a non-English voice) and assert Premium wins, English-only,
  deterministic tie-break, and Samantha + one-time hint when only basic exists.
- Captions: `captions.estimate` defaults True; gate yields real for
  ElevenLabs+alignment and estimated otherwise (unit-test the selection with a
  present vs absent alignment file).
- Config: default provider is `auto`, `macos_voice` is `auto`, `captions.estimate`
  is True; `mode:"free"` forces `macos` and no longer hardcodes a voice.
- macOS-`say`-dependent tests stay gated to Darwin, following the existing
  `platform.system()` pattern.

## Out of scope (YAGNI)

- Auto-enabling the Becky avatar outside free mode.
- Linux local TTS (espeak/piper).
- Auto-downloading macOS Premium voices (can't be automated; we only hint).
- Quality ranking beyond the Premium/Enhanced/basic suffix (e.g. per-voice
  naturalness scoring).
