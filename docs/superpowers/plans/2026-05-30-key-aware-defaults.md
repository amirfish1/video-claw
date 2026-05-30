# Key-Aware Auto Defaults Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make video-claw work with zero keys and improve as keys appear — `provider:"auto"` resolves ElevenLabs → Deepgram → macOS local from the keys present; macOS local auto-picks the best installed voice; captions are always produced (word-aligned for ElevenLabs, estimated otherwise).

**Architecture:** A pure `resolve_provider()` in `tts/__init__.py` decides the provider at render time; `core.py` resolves once, announces the choice, and threads the concrete provider into TTS + the caption gate. macOS voice selection gains `_best_installed_voice()` ranked Premium > Enhanced > basic. Config defaults flip to `auto`/`auto`/`estimate=True`.

**Tech Stack:** Python 3.10+, macOS `say`, ffmpeg, pytest. No new dependencies.

---

## File Structure

- `video_claw/tts/__init__.py` — **modify**: `DEFAULT_TTS["provider"]` → `"auto"`, `DEFAULT_TTS["macos_voice"]` → `"auto"`; add `resolve_provider()`; `make_audio` resolves first.
- `video_claw/tts/macos.py` — **modify**: add `_installed_voice_records()`, `_voice_quality()`, `_best_installed_voice()`, `_warned_basic_only` flag; `synthesize` handles `voice="auto"`; default `voice="auto"`.
- `video_claw/config.py` — **modify**: `DEFAULT_CONFIG["tts"]` provider→`auto` + `macos_voice="auto"`; `captions.estimate`→`True`; `_apply_free_mode` stops hardcoding the voice.
- `video_claw/core.py` — **modify**: `DEFAULT_TTS["provider"]`→`auto`; resolve provider once + print; thread resolved provider into `slide_tts`; add `_captions_for_slide()` helper and use it.
- `README.md` + `video_claw/skill_data/video-claw/SKILL.md` — **modify**: document auto provider + always-on captions.
- `pyproject.toml` + `video_claw/__init__.py` — **modify**: version 0.6.0 → 0.7.0.

Tests:
- `tests/test_provider_resolution.py` — **create** (Task 1)
- `tests/test_say_tts.py` — **modify** (Task 2)
- `tests/test_free_mode_config.py` — **modify** (Task 3)
- `tests/test_core_captions.py` — **create** (Task 4)

---

## Task 1: Provider auto-resolution

**Files:**
- Modify: `video_claw/tts/__init__.py`
- Test: `tests/test_provider_resolution.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_provider_resolution.py`:

```python
"""provider:auto resolves from the keys present + platform."""
from __future__ import annotations
import platform
import pytest


def _patch_keys(monkeypatch, mapping):
    from video_claw import keys
    monkeypatch.setattr(keys, "get", lambda name: mapping.get(name))


def test_explicit_provider_passes_through(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {})
    assert tts.resolve_provider({"provider": "deepgram"}) == "deepgram"
    assert tts.resolve_provider({"provider": "elevenlabs"}) == "elevenlabs"
    assert tts.resolve_provider({"provider": "macos"}) == "macos"


def test_auto_prefers_elevenlabs(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {"ELEVENLABS_API_KEY": "x", "DEEPGRAM_API_KEY": "y"})
    assert tts.resolve_provider({"provider": "auto"}) == "elevenlabs"


def test_auto_falls_to_deepgram(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {"DEEPGRAM_API_KEY": "y"})
    assert tts.resolve_provider({"provider": "auto"}) == "deepgram"


def test_auto_falls_to_macos_on_darwin(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {})
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert tts.resolve_provider({"provider": "auto"}) == "macos"


def test_auto_errors_on_linux_without_keys(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {})
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="No TTS"):
        tts.resolve_provider({"provider": "auto"})


def test_unset_provider_defaults_to_auto(monkeypatch):
    from video_claw import tts
    _patch_keys(monkeypatch, {"ELEVENLABS_API_KEY": "x"})
    assert tts.resolve_provider({}) == "elevenlabs"


def test_make_audio_auto_no_keys_non_darwin_errors(monkeypatch, tmp_path):
    from video_claw import tts
    from video_claw.cache import Cache
    _patch_keys(monkeypatch, {})
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="No TTS"):
        tts.make_audio("hi", 0, workdir=tmp_path, cache=Cache(tmp_path),
                       tts_cfg={"provider": "auto"})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_provider_resolution.py -v`
Expected: FAIL — `AttributeError: module 'video_claw.tts' has no attribute 'resolve_provider'`.

- [ ] **Step 3: Add the `platform` import**

In `video_claw/tts/__init__.py`, the import block currently is:

```python
from __future__ import annotations
import base64
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple
```

Add `import platform` after `import json`:

```python
from __future__ import annotations
import base64
import json
import platform
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple
```

- [ ] **Step 4: Flip the TTS defaults to auto**

In `video_claw/tts/__init__.py`, change `DEFAULT_TTS`:

```python
DEFAULT_TTS = {
    "provider": "elevenlabs",
    "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.0,
    "deepgram_voice": "aura-2-thalia-en",
    "macos_voice": "Samantha",
}
```

to:

```python
DEFAULT_TTS = {
    "provider": "auto",
    "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.0,
    "deepgram_voice": "aura-2-thalia-en",
    "macos_voice": "auto",
}
```

- [ ] **Step 5: Add `resolve_provider`**

In `video_claw/tts/__init__.py`, add this function just above `make_audio` (the dispatcher at the bottom):

```python
def resolve_provider(tts_cfg: Dict[str, Any]) -> str:
    """Resolve a (possibly "auto") provider to a concrete one from keys + platform.

    Explicit providers pass through unchanged (the per-provider function still
    raises its own clear error if that provider's key is missing). "auto" (the
    default) picks the best available: ElevenLabs -> Deepgram -> macOS local;
    if none is possible (Linux, no keys) it raises a single clear error.
    Pure: no network, no synthesis. Safe to call repeatedly (idempotent).
    """
    provider = (tts_cfg or {}).get("provider") or "auto"
    provider = provider.lower()
    if provider in ("elevenlabs", "el", "eleven"):
        return "elevenlabs"
    if provider == "deepgram":
        return "deepgram"
    if provider in ("macos", "say", "macos-say"):
        return "macos"
    if provider != "auto":
        return provider  # unknown explicit value; dispatch will raise a clear error

    if keys.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    if keys.get("DEEPGRAM_API_KEY"):
        return "deepgram"
    if platform.system() == "Darwin":
        return "macos"
    raise RuntimeError(
        "No TTS available: set ELEVENLABS_API_KEY or DEEPGRAM_API_KEY, or run "
        "on macOS for free local TTS (provider=auto found no usable option)."
    )
```

- [ ] **Step 6: Resolve at the top of `make_audio`**

In `video_claw/tts/__init__.py`, the dispatcher currently is:

```python
def make_audio(text: str, idx: int, *, workdir: Path, cache,
               tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """Dispatch to the configured provider. Falls back to ElevenLabs when unset."""
    provider = (tts_cfg.get("provider") or DEFAULT_TTS["provider"]).lower()
    if provider == "deepgram":
        return make_audio_deepgram(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    if provider in ("macos", "say", "macos-say"):
        return make_audio_macos(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    if provider in ("elevenlabs", "el", "eleven"):
        return make_audio_elevenlabs(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    raise ValueError(
        f"Unknown TTS provider: {provider!r}. "
        "Use 'elevenlabs', 'deepgram', or 'macos'."
    )
```

Replace it with:

```python
def make_audio(text: str, idx: int, *, workdir: Path, cache,
               tts_cfg: Dict[str, Any]) -> Tuple[Path, float]:
    """Dispatch to the resolved provider. `provider:"auto"` (the default) picks
    the best available from the keys present (see `resolve_provider`)."""
    provider = resolve_provider(tts_cfg)
    tts_cfg = {**tts_cfg, "provider": provider}
    if provider == "deepgram":
        return make_audio_deepgram(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    if provider == "macos":
        return make_audio_macos(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    if provider == "elevenlabs":
        return make_audio_elevenlabs(text, idx, workdir=workdir, cache=cache, tts_cfg=tts_cfg)
    raise ValueError(
        f"Unknown TTS provider: {provider!r}. "
        "Use 'auto', 'elevenlabs', 'deepgram', or 'macos'."
    )
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_provider_resolution.py -v`
Expected: PASS (7 passed).

- [ ] **Step 8: Commit**

```bash
git add video_claw/tts/__init__.py tests/test_provider_resolution.py
git commit --only video_claw/tts/__init__.py tests/test_provider_resolution.py -m "feat(tts): provider=auto resolves EL -> Deepgram -> macOS from keys

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Best macOS voice

**Files:**
- Modify: `video_claw/tts/macos.py`
- Test: `tests/test_say_tts.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_say_tts.py`:

```python
# ---------------------------------------------------------------------------
# Best-voice auto-detection (Premium > Enhanced > basic, English only).
# ---------------------------------------------------------------------------

def test_voice_records_capture_locale_and_name(monkeypatch):
    from video_claw.tts import macos
    import subprocess as sp
    sample = (
        "Samantha            en_US    # Hi\n"
        "Zoe (Premium)       en_US    # Hi\n"
        "Daniel (Enhanced)   en_GB    # Hi\n"
        "Amelie              fr_CA    # Bonjour\n"
    )

    class _R:
        stdout = sample

    monkeypatch.setattr(sp, "run", lambda *a, **k: _R())
    recs = macos._installed_voice_records("say")
    assert ("Zoe (Premium)", "en_US") in recs
    assert ("Daniel (Enhanced)", "en_GB") in recs
    assert ("Amelie", "fr_CA") in recs


def test_best_voice_prefers_premium_english(monkeypatch):
    from video_claw.tts import macos
    monkeypatch.setattr(macos, "_installed_voice_records", lambda b: [
        ("Samantha", "en_US"),
        ("Daniel (Enhanced)", "en_GB"),
        ("Zoe (Premium)", "en_US"),
        ("Amelie (Premium)", "fr_CA"),  # non-English, must be ignored
    ])
    assert macos._best_installed_voice("say") == "Zoe (Premium)"


def test_best_voice_basic_only_falls_back_to_samantha(monkeypatch, capsys):
    from video_claw.tts import macos
    macos._warned_basic_only = False
    monkeypatch.setattr(macos, "_installed_voice_records", lambda b: [
        ("Alex", "en_US"), ("Samantha", "en_US")])
    assert macos._best_installed_voice("say") == "Samantha"
    assert "Premium voice" in capsys.readouterr().out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_say_tts.py -v -k "voice_records or best_voice"`
Expected: FAIL — `AttributeError: ... has no attribute '_installed_voice_records'`.

- [ ] **Step 3: Add the imports and module flag**

In `video_claw/tts/macos.py`, the import block currently is:

```python
from __future__ import annotations
import platform
import shutil
import subprocess
import sys
from pathlib import Path
```

It already imports what we need. Directly below the `DEFAULT_VOICE = "Samantha"` line, add:

```python
# Set once we've warned that only basic-quality voices are installed, so the
# download hint prints at most once per process instead of per slide.
_warned_basic_only = False
```

- [ ] **Step 4: Add the voice-record + ranking helpers**

In `video_claw/tts/macos.py`, add these functions just above `_resolve_voice`:

```python
def _installed_voice_records(say_bin: str) -> list[tuple[str, str]]:
    """Return [(name, locale), ...] from `say -v ?`.

    Each line is `Zoe (Premium)      en_US    # sample`. The locale is the first
    short token containing `_`; everything before it is the (space-containing)
    voice name. Same parsing rule as `_list_installed_voices`, but also keeps
    the locale so we can filter to English.
    """
    res = subprocess.run([say_bin, "-v", "?"], capture_output=True, text=True)
    records: list[tuple[str, str]] = []
    for line in res.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        name_tokens: list[str] = []
        locale = ""
        for tok in parts:
            if "_" in tok and len(tok) <= 6:
                locale = tok
                break
            name_tokens.append(tok)
        if name_tokens:
            records.append((" ".join(name_tokens), locale))
    return records


def _voice_quality(name: str) -> int:
    """3 = Premium, 2 = Enhanced, 1 = basic (from the name suffix)."""
    low = name.lower()
    if "(premium)" in low:
        return 3
    if "(enhanced)" in low:
        return 2
    return 1


def _best_installed_voice(say_bin: str | None = None) -> str:
    """Highest-quality installed English voice (Premium > Enhanced > basic).

    Falls back to Samantha (or the first English basic voice) and prints a
    one-time download hint when only basic voices are installed.
    """
    global _warned_basic_only
    say_bin = say_bin or shutil.which("say") or "say"
    english = [(n, loc) for (n, loc) in _installed_voice_records(say_bin)
               if loc.lower().startswith("en")]
    if not english:
        return DEFAULT_VOICE

    best_name, best_q = english[0][0], _voice_quality(english[0][0])
    for name, _loc in english[1:]:
        q = _voice_quality(name)
        if q > best_q:
            best_name, best_q = name, q

    if best_q <= 1:  # only basic voices available
        if not _warned_basic_only:
            _warned_basic_only = True
            print("  [macos-tts] for better narration, download a Premium voice "
                  "in System Settings > Accessibility > Spoken Content.")
        for name, _loc in english:
            if name.lower().startswith("samantha"):
                return name
        return best_name
    return best_name
```

- [ ] **Step 5: Use auto-detection in `synthesize`**

In `video_claw/tts/macos.py`, change the `synthesize` signature default from:

```python
def synthesize(text: str, out_path: Path, *, voice: str = DEFAULT_VOICE) -> Path:
```

to:

```python
def synthesize(text: str, out_path: Path, *, voice: str = "auto") -> Path:
```

Then find this block (added by the prior feature):

```python
    _require_macos()
    say = _require_binary("say")
    voice = _resolve_voice(voice, say)
    out_path = Path(out_path).resolve()
```

Replace it with:

```python
    _require_macos()
    say = _require_binary("say")
    if not voice or voice == "auto":
        voice = _best_installed_voice(say)
    else:
        voice = _resolve_voice(voice, say)
    out_path = Path(out_path).resolve()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_say_tts.py -v`
Expected: PASS (existing macOS-gated tests still pass/skip; the 3 new ranking tests pass everywhere via monkeypatch).

- [ ] **Step 7: Commit**

```bash
git add video_claw/tts/macos.py tests/test_say_tts.py
git commit --only video_claw/tts/macos.py tests/test_say_tts.py -m "feat(tts): auto-detect best installed macOS voice (Premium > Enhanced > basic)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Config defaults + free-mode preset

**Files:**
- Modify: `video_claw/config.py`
- Test: `tests/test_free_mode_config.py`

- [ ] **Step 1: Update the tests (defaults changed)**

In `tests/test_free_mode_config.py`, change the assertion in
`test_free_mode_forces_macos_and_strips_lipsync` from:

```python
    assert project.config["tts"]["macos_voice"] == "Zoe (Premium)"
```

to:

```python
    assert project.config["tts"]["macos_voice"] == "auto"
```

Then append a new test for the changed defaults:

```python
def test_default_provider_and_captions(tmp_path):
    from video_claw import config as cfg_mod
    _write_project(
        tmp_path, '{}',
        '[{"type": "html", "html": "a.html", "narration": "hi"}]',
    )
    project = cfg_mod.load(tmp_path)
    assert project.config["tts"]["provider"] == "auto"
    assert project.config["tts"]["macos_voice"] == "auto"
    assert project.config["captions"]["estimate"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_free_mode_config.py -v`
Expected: FAIL — the Zoe assertion now expects `"auto"`, and `test_default_provider_and_captions` sees `provider == "elevenlabs"` / `estimate is False`.

- [ ] **Step 3: Flip the config defaults**

In `video_claw/config.py`, change the `DEFAULT_CONFIG["tts"]` block from:

```python
    "tts": {
        "provider": "elevenlabs",
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica (matches CCC-outreach default)
        "model": "eleven_turbo_v2_5",
        "speaking_rate": 1.0,
        # Deepgram fallback voice if provider=deepgram
        "deepgram_voice": "aura-2-thalia-en",
    },
```

to:

```python
    "tts": {
        "provider": "auto",  # auto-select EL -> Deepgram -> macOS from the keys present
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica (matches CCC-outreach default)
        "model": "eleven_turbo_v2_5",
        "speaking_rate": 1.0,
        # Deepgram fallback voice if provider=deepgram
        "deepgram_voice": "aura-2-thalia-en",
        # macOS local voice; "auto" picks the best installed English voice
        "macos_voice": "auto",
    },
```

- [ ] **Step 4: Default captions to always-on**

In `video_claw/config.py`, change the `DEFAULT_CONFIG["captions"]` block from:

```python
    "captions": {
        "estimate": False,     # estimate caption timing when TTS gives no alignment
    },
```

to:

```python
    "captions": {
        "estimate": True,      # always caption: estimate timing when TTS gives no alignment
    },
```

- [ ] **Step 5: Stop hardcoding the free-mode voice**

In `video_claw/config.py`, in `_apply_free_mode`, change:

```python
    tts = config.setdefault("tts", {})
    tts["provider"] = "macos"
    tts.setdefault("macos_voice", "Zoe (Premium)")
```

to:

```python
    tts = config.setdefault("tts", {})
    tts["provider"] = "macos"
    tts.setdefault("macos_voice", "auto")  # best installed voice; respects an explicit override
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_free_mode_config.py -v`
Expected: PASS.

- [ ] **Step 7: Run the full suite for regressions**

Run: `python3 -m pytest tests/ -q`
Expected: PASS (no regressions from the default flip).

- [ ] **Step 8: Commit**

```bash
git add video_claw/config.py tests/test_free_mode_config.py
git commit --only video_claw/config.py tests/test_free_mode_config.py -m "feat(config): default provider=auto, macos_voice=auto, captions always on

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Core wiring (resolve once, caption gate)

**Files:**
- Modify: `video_claw/core.py`
- Test: `tests/test_core_captions.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_core_captions.py`:

```python
"""The per-slide caption gate: real for ElevenLabs+alignment, else estimated."""
from __future__ import annotations
import json


def test_captions_estimated_for_macos(tmp_path):
    from video_claw.core import _captions_for_slide
    entries = _captions_for_slide("macos", tmp_path, 0, "one two three four",
                                  offset_s=0.0, dur=4.0, rate=1.0, estimate=True)
    assert entries, "macOS should get estimated captions"


def test_captions_none_when_estimate_off_and_not_eleven(tmp_path):
    from video_claw.core import _captions_for_slide
    assert _captions_for_slide("macos", tmp_path, 0, "hi there",
                               offset_s=0.0, dur=4.0, rate=1.0, estimate=False) == []


def test_captions_real_for_eleven_with_alignment(tmp_path):
    from video_claw.core import _captions_for_slide
    (tmp_path / "narr_00.alignment.json").write_text(json.dumps({
        "characters": list("hi there"),
        "character_start_times_seconds": [i * 0.1 for i in range(8)],
        "character_end_times_seconds": [i * 0.1 + 0.1 for i in range(8)],
    }))
    entries = _captions_for_slide("elevenlabs", tmp_path, 0, "hi there",
                                  offset_s=0.0, dur=4.0, rate=1.0, estimate=True)
    assert entries, "ElevenLabs with alignment should produce real captions"


def test_captions_eleven_without_alignment_estimates(tmp_path):
    from video_claw.core import _captions_for_slide
    entries = _captions_for_slide("elevenlabs", tmp_path, 0, "one two three",
                                  offset_s=0.0, dur=3.0, rate=1.0, estimate=True)
    assert entries, "ElevenLabs without an alignment file should fall back to estimate"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_core_captions.py -v`
Expected: FAIL — `ImportError: cannot import name '_captions_for_slide'`.

- [ ] **Step 3: Update core's `DEFAULT_TTS` provider**

In `video_claw/core.py`, change the local `DEFAULT_TTS`:

```python
DEFAULT_TTS = {
    "provider": "elevenlabs",
    "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.0,
    "deepgram_voice": "aura-2-thalia-en",
}
```

to:

```python
DEFAULT_TTS = {
    "provider": "auto",
    "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
    "model": "eleven_turbo_v2_5",
    "speaking_rate": 1.0,
    "deepgram_voice": "aura-2-thalia-en",
    "macos_voice": "auto",
}
```

- [ ] **Step 4: Add the `_captions_for_slide` helper**

In `video_claw/core.py`, add this function above `make_video` (it uses
`caps_mod`, already imported):

```python
def _captions_for_slide(provider: str, workdir: Path, idx: int, narration: str,
                        *, offset_s: float, dur: float, rate: float,
                        estimate: bool) -> List[Tuple[float, float, str]]:
    """Word-aligned captions for ElevenLabs (when its alignment sidecar exists),
    otherwise estimated captions when `estimate` is on, else none.

    The `provider.startswith("eleven") and alignment-exists` guard keeps a stale
    alignment file from a prior ElevenLabs run from hijacking a later macOS/auto
    render in the same workdir.
    """
    align_path = workdir / f"narr_{idx:02d}.alignment.json"
    if provider.startswith("eleven") and align_path.exists():
        return caps_mod.build_srt_for_slide(idx, offset_s, rate, workdir)
    if estimate:
        return caps_mod.build_estimated_srt_for_slide(narration, offset_s, dur)
    return []
```

- [ ] **Step 5: Resolve the provider once + announce it**

In `video_claw/core.py`, find the start of Phase 3 (added by the prior feature):

```python
    # Phase 3: TTS (cached), optional lipsync/avatar (cached), per-slide MP4 stitching.
    if free:
        print("[boot] $0 mode: local macOS TTS, no paid APIs")
```

Replace those two lines with:

```python
    # Phase 3: TTS (cached), optional lipsync/avatar (cached), per-slide MP4 stitching.
    if free:
        print("[boot] $0 mode: local macOS TTS, no paid APIs")

    resolved_provider = tts_mod.resolve_provider(tts_cfg)
    if (tts_cfg.get("provider") or "auto").lower() == "auto":
        print(f"[tts] auto → {resolved_provider} (selected from available keys)")
```

- [ ] **Step 6: Thread the resolved provider + use the helper**

In `video_claw/core.py`, find (inside the per-slide loop):

```python
        rate = float(slide.get("speed") or tts_cfg.get("speaking_rate", 1.0))
        slide_tts = {**tts_cfg, "speaking_rate": rate}
```

Replace with:

```python
        rate = float(slide.get("speed") or tts_cfg.get("speaking_rate", 1.0))
        slide_tts = {**tts_cfg, "provider": resolved_provider, "speaking_rate": rate}
```

Then find the caption gate (added by the prior feature):

```python
        # ElevenLabs gives word-perfect alignment; otherwise estimate from the
        # measured audio duration when caption estimation is enabled.
        align_path = workdir / f"narr_{idx:02d}.alignment.json"
        if slide_tts["provider"].lower().startswith("eleven") and align_path.exists():
            all_captions.extend(caps_mod.build_srt_for_slide(idx, cumulative, rate, workdir))
        elif captions_cfg.get("estimate"):
            all_captions.extend(
                caps_mod.build_estimated_srt_for_slide(narration, cumulative, dur))
```

Replace it with:

```python
        # Always caption: word-aligned for ElevenLabs, estimated otherwise.
        all_captions.extend(_captions_for_slide(
            resolved_provider, workdir, idx, narration,
            offset_s=cumulative, dur=dur, rate=rate,
            estimate=captions_cfg.get("estimate", True)))
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_core_captions.py -v`
Expected: PASS (4 passed).

- [ ] **Step 8: Run the full suite**

Run: `python3 -m pytest tests/ -q`
Expected: PASS (no regressions).

- [ ] **Step 9: Commit**

```bash
git add video_claw/core.py tests/test_core_captions.py
git commit --only video_claw/core.py tests/test_core_captions.py -m "feat(core): resolve provider once, announce auto choice, always caption

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Docs + version bump

**Files:**
- Modify: `README.md`
- Modify: `video_claw/skill_data/video-claw/SKILL.md`
- Modify: `pyproject.toml`, `video_claw/__init__.py`

- [ ] **Step 1: Update the README "What you get" TTS bullet**

In `README.md`, change:

```markdown
- **Two TTS providers.** ElevenLabs (default, with timestamps for captions)
  or Deepgram (cheaper, no captions).
```

to:

```markdown
- **Works with zero keys.** `provider` defaults to `"auto"`: it uses ElevenLabs
  if you have a key, else Deepgram, else free macOS local TTS — no config, no
  hard failure. Add keys to upgrade quality.
- **Captions always.** Word-aligned from ElevenLabs; estimated from Deepgram /
  macOS. Never silently dropped.
```

- [ ] **Step 2: Update the README "API keys" section**

In `README.md`, change:

```markdown
The minimum is one TTS key. Lipsync is opt-in per slide.
```

to:

```markdown
**No keys are required** — on a Mac, `provider:"auto"` renders with free local
TTS out of the box. Add a TTS key to upgrade quality; lipsync is opt-in per
slide. Keys only become mandatory when you pin a paid provider explicitly or
run on Linux with no key.
```

- [ ] **Step 3: Update the SKILL.md TTS guidance**

First locate the TTS section:

Run: `grep -n "provider\|TTS\|## \|### " video_claw/skill_data/video-claw/SKILL.md | head -40`

Then add this subsection immediately after the free-mode section (the
`### Free / $0 mode` block ends before the next `##`/`###` heading):

```markdown
### Provider selection (auto by default)

`tts.provider` defaults to `"auto"`: ElevenLabs if `ELEVENLABS_API_KEY` is set,
else Deepgram if `DEEPGRAM_API_KEY` is set, else macOS local TTS (Mac only).
Pin a provider explicitly to force it. Captions are always produced —
word-aligned for ElevenLabs, estimated otherwise. So a brand-new user with no
keys still gets a complete captioned video on a Mac; keys only raise quality.
```

- [ ] **Step 4: Bump the version to 0.7.0**

In `pyproject.toml`, change `version = "0.6.0"` to `version = "0.7.0"`.
In `video_claw/__init__.py`, change `__version__ = "0.6.0"` to `__version__ = "0.7.0"`.

- [ ] **Step 5: Verify docs + version**

Run: `grep -rn "auto\|Captions always\|0.7.0" README.md video_claw/skill_data/video-claw/SKILL.md pyproject.toml video_claw/__init__.py | grep -iE "auto|captions always|0.7.0" | head`
Expected: matches for the auto-provider text in README + SKILL.md and `0.7.0` in both version files.

- [ ] **Step 6: Commit**

```bash
git add README.md video_claw/skill_data/video-claw/SKILL.md pyproject.toml video_claw/__init__.py
git commit --only README.md video_claw/skill_data/video-claw/SKILL.md pyproject.toml video_claw/__init__.py -m "docs: document auto provider + always-on captions; bump to 0.7.0

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: End-to-end manual verification (macOS)

**Files:** none (manual smoke on a real Mac with Chrome + ffmpeg, no API keys).

- [ ] **Step 1: Scaffold a throwaway project (no free mode this time)**

Run (from the repo root so the editable CLI loads local code):
```bash
rm -rf /tmp/vc-auto && python3 -c "import sys; sys.argv=['video-claw','init','/tmp/vc-auto']; from video_claw.cli import main; main()"
```
Do NOT enable `mode: "free"` — leave the default `provider:"auto"`.

- [ ] **Step 2: Render with no API keys**

Run:
```bash
env -u ELEVENLABS_API_KEY -u FAL_API_KEY -u DEEPGRAM_API_KEY python3 -c "import sys; sys.argv=['video-claw','render','/tmp/vc-auto','--yes','--no-preview']; from video_claw.cli import main; sys.exit(main())"
```
Expected console: `[tts] auto → macos (selected from available keys)`, TTS runs via macOS, `[captions] N chunks via libass`, and an MP4 in `/tmp/vc-auto/out/`.

- [ ] **Step 3: Confirm the voice + captions**

Open the MP4. Confirm narration plays in a high-quality installed voice
(Premium/Enhanced if present, else Samantha with the printed hint) and captions
are burned in. Then clean up: `rm -rf /tmp/vc-auto`.
Expected: captioned video, no API spend, no avatar (auto mode doesn't force it).

---

## Self-Review notes

- **Spec coverage:** §1 provider resolution → Task 1; §2 best macOS voice → Task 2; §3 captions always (config default + gate) → Tasks 3 & 4; §4 core wiring (resolve once, announce, thread, gate) → Task 4; §5 config defaults + free-mode preset → Task 3; docs + version → Task 5; backward-compat exercised by the unchanged-explicit-provider tests (Task 1) and the full-suite runs (Tasks 3, 4).
- **Type consistency:** `resolve_provider(tts_cfg) -> str`, `_installed_voice_records(say_bin) -> list[tuple[str,str]]`, `_voice_quality(name) -> int`, `_best_installed_voice(say_bin=None) -> str`, and `_captions_for_slide(provider, workdir, idx, narration, *, offset_s, dur, rate, estimate)` are defined and called with identical signatures across tasks. The caption gate uses the same `provider.startswith("eleven") and align-exists` guard as the prior feature.
- **Deliberate default change:** flipping `provider` to `auto` and `captions.estimate` to `True` changes behavior for keyless and Deepgram users by design (per the approved spec); Tasks 3 and 4 each run the full suite to catch regressions for explicit-provider users.
