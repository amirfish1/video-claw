"""Cache diagnostics preserve synthesis identity and never call paid providers."""
import base64
import json
from pathlib import Path

import pytest

from video_claw import tts, tts_cache
from video_claw.cache import Cache


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.delenv("MNV_FORCE_REGEN", raising=False)
    monkeypatch.setattr(tts.urllib.request, "urlopen",
                        lambda *a, **kw: pytest.fail("paid network call"))
    return Cache(tmp_path)


def seed(cache, slides, cfg):
    texts = [slide["narration"] for slide in slides]
    master = tts.cache_settings(cfg)["provider"] == "elevenlabs"
    if master:
        texts = ["\n\n".join(text.strip() for text in texts)]
    for text in texts:
        key, ext = tts.audio_cache_entry(text, cfg)
        if master:
            cache.path("tts", key, ext).write_text(json.dumps({
                "audio_base64": base64.b64encode(b"audio").decode(),
                "alignment": {"characters": list(text),
                              "character_start_times_seconds": [0.0] * len(text),
                              "character_end_times_seconds": [1.0] * len(text)},
            }))
        else:
            cache.path("tts", key, ext).write_bytes(b"cached audio")


@pytest.mark.parametrize("cfg, key, ext", [
    ({"provider": "el", "voice_id": "Jessica", "model": "turbo"},
     ["elevenlabs-master-v1", "hello", "Jessica", "turbo"], "json"),
    ({"provider": "deepgram", "deepgram_voice": "aura-2-thalia-en"},
     ["hello", "deepgram", "voice", "aura-2-thalia-en"], "mp3"),
    ({"provider": "say", "macos_voice": "Samantha"},
     ["hello", "macos", "voice", "Samantha"], "wav"),
])
def test_cache_keys_match_effective_provider(cfg, key, ext):
    assert tts.audio_cache_entry("hello", cfg) == (key, ext)
    assert tts.audio_cache_entry("hello", {**cfg, "speaking_rate": 2}) == (key, ext)


def test_first_render_and_repeat_hit(cache, capsys):
    slides = [{"narration": "private narration"}]
    cfg = {"provider": "macos", "macos_voice": "Samantha"}
    snapshot = tts_cache.report(slides, cfg, cache)
    assert "0 hits / 1 misses before synthesis (no cache yet)" in capsys.readouterr().out
    seed(cache, slides, cfg)
    tts_cache.remember(cache, snapshot)
    assert "private narration" not in (cache.root / "tts-last-render.json").read_text()
    tts_cache.report(slides, cfg, cache)
    assert "1 hits / 0 misses" in capsys.readouterr().out


def test_voice_change_explains_miss_and_switching_back_reuses_audio(cache, capsys):
    slides = [{"narration": "hello"}]
    before = {"provider": "macos", "macos_voice": "Samantha"}
    after = {**before, "macos_voice": "Zoe (Premium)"}
    seed(cache, slides, before)
    tts_cache.remember(cache, tts_cache.report(slides, before, cache))
    capsys.readouterr()
    tts_cache.remember(cache, tts_cache.report(slides, after, cache))
    output = capsys.readouterr().out
    assert "0 hits / 1 misses" in output
    assert "TTS config changed: macos_voice" in output
    tts_cache.report(slides, before, cache)
    assert "1 hits / 0 misses" in capsys.readouterr().out


def test_narration_change_reports_count_without_logging_text(cache, capsys):
    cfg = {"provider": "macos"}
    slides = [{"narration": "first"}, {"narration": "second"}]
    seed(cache, slides, cfg)
    tts_cache.remember(cache, tts_cache.report(slides, cfg, cache))
    capsys.readouterr()
    tts_cache.report([slides[0], {"narration": "new private words"}], cfg, cache)
    output = capsys.readouterr().out
    assert "1 hits / 1 misses" in output
    assert "narration changed on 1 slide positions" in output
    assert "new private words" not in output


def test_force_regen_explains_misses(cache, monkeypatch, capsys):
    slides = [{"narration": "hello"}]
    cfg = {"provider": "macos"}
    seed(cache, slides, cfg)
    monkeypatch.setenv("MNV_FORCE_REGEN", "1")
    tts_cache.report(slides, cfg, cache)
    output = capsys.readouterr().out
    assert "0 hits / 1 misses" in output
    assert "MNV_FORCE_REGEN requests re-synthesis" in output


@pytest.mark.parametrize("contents", ["broken json", "null", '{"version":1}',
    '{"version":1,"settings":{},"narrations":[null]}'])
def test_missing_or_corrupt_metadata_does_not_block_render(cache, contents, capsys):
    cfg = {"provider": "macos"}
    seed(cache, [{"narration": "old"}], cfg)
    (cache.root / "tts-last-render.json").write_text(contents)
    tts_cache.report([{"narration": "new"}], cfg, cache)
    assert "matching audio missing; no recorded config/text change" in capsys.readouterr().out


@pytest.mark.parametrize("provider", ["macos", "elevenlabs", "deepgram"])
def test_provider_uses_the_same_cache_as_diagnostics(cache, monkeypatch, provider):
    cfg = {"provider": provider}
    seed(cache, [{"narration": "hello"}], cfg)
    monkeypatch.setattr(tts.keys, "get", lambda name: "test-key")
    monkeypatch.setattr(tts, "_encode_to_m4a", lambda src, dst, rate: dst.write_bytes(b"encoded"))
    monkeypatch.setattr(tts, "_ffprobe_duration", lambda path: 1.0)
    monkeypatch.setattr(tts.subprocess, "run", lambda cmd, **kw: Path(cmd[-1]).write_bytes(b"encoded"))
    monkeypatch.setattr(tts._macos, "synthesize", lambda *a, **kw: pytest.fail("synthesis"))
    path, duration = tts.make_audio("hello", 0, workdir=cache.workdir, cache=cache, tts_cfg=cfg)
    assert path.read_bytes() == b"encoded"
    assert duration == 1.0
    assert cache.stats["tts"] == {"hit": 1, "miss": 0}


def test_irrelevant_voice_settings_do_not_invalidate_active_provider(cache, capsys):
    cfg = {"provider": "deepgram", "macos_voice": "Samantha"}
    slides = [{"narration": "hello"}]
    seed(cache, slides, cfg)
    tts_cache.remember(cache, tts_cache.report(slides, cfg, cache))
    capsys.readouterr()
    tts_cache.report(slides, {**cfg, "macos_voice": "Zoe", "speaking_rate": 2}, cache)
    output = capsys.readouterr().out
    assert "1 hits / 0 misses" in output
    assert "changed" not in output


def test_completed_render_records_snapshot_and_next_render_explains_voice_change(
    cache, monkeypatch, capsys,
):
    from video_claw import core

    monkeypatch.setattr(core, "render_pngs", lambda *a, **kw: None)
    monkeypatch.setattr(core, "_captions_for_slide", lambda *a, **kw: [])
    monkeypatch.setattr(core.ff, "make_slide_video", lambda *a, **kw: cache.workdir / "part.mp4")
    monkeypatch.setattr(core.ff, "ffprobe_duration", lambda path: 1.0)
    raw = cache.workdir / "raw.mp4"
    raw.write_bytes(b"video")
    monkeypatch.setattr(core.ff, "concat_slides", lambda *a, **kw: raw)

    def audio(text, idx, *, workdir, cache, tts_cfg):
        key, ext = tts.audio_cache_entry(text, tts_cfg)
        result = cache.run("tts", key, ext, lambda path: path.write_bytes(b"audio"))
        return result, 1.0

    monkeypatch.setattr(tts, "make_audio", audio)
    slides = [{"narration": "hello"}]
    first = {"provider": "macos", "macos_voice": "Samantha"}
    assert core.make_video(slides, workdir=cache.workdir, tts_cfg=first,
                           skip_preview=True).read_bytes() == b"video"
    stored = json.loads((cache.root / "tts-last-render.json").read_text())
    assert stored["settings"]["macos_voice"] == "Samantha"
    capsys.readouterr()
    second = {**first, "macos_voice": "Zoe"}
    core.make_video(slides, workdir=cache.workdir, tts_cfg=second, skip_preview=True)
    assert "TTS config changed: macos_voice" in capsys.readouterr().out
    stored = json.loads((cache.root / "tts-last-render.json").read_text())
    assert stored["settings"]["macos_voice"] == "Zoe"


def test_elevenlabs_diagnostics_match_whole_script_cache(cache, capsys):
    cfg = {"provider": "elevenlabs"}
    slides = [{"narration": "  First.  "}, {"narration": "Second."}]
    snapshot = tts_cache.report(slides, cfg, cache)
    output = capsys.readouterr().out
    assert "0 hits / 1 misses" in output
    assert "one master take across 2 slides" in output
    seed(cache, slides, cfg)
    tts_cache.remember(cache, snapshot)
    tts_cache.report(slides, {**cfg, "speaking_rate": 2}, cache)
    assert "1 hits / 0 misses" in capsys.readouterr().out
    tts_cache.report([slides[0], {"narration": "Changed."}], cfg, cache)
    output = capsys.readouterr().out
    assert "0 hits / 1 misses" in output
    assert "narration changed on 1 slide positions" in output
    tts_cache.report(slides, {**cfg, "voice_id": "new-voice"}, cache)
    assert "TTS config changed: voice_id" in capsys.readouterr().out
