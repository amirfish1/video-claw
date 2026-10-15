"""Offline estimates and ordering: no renderer, synthesis, network, or media tools."""
import pytest

from video_claw import core, spend, tts


def test_estimate_elevenlabs_and_lipsync_speed():
    slides = [{"narration": "x" * 750, "lipsync": True, "speed": 2},
              {"narration": "y" * 750}]
    estimate = spend.estimate_spend(slides, {"provider": "el", "speaking_rate": 0.5})
    assert estimate.elevenlabs == pytest.approx(0.6008)
    assert estimate.deepgram == 0
    assert estimate.char_count == 1502
    assert estimate.slide_count == 2
    assert estimate.lipsync_seconds == 30
    assert estimate.fal == pytest.approx(4.80)
    assert estimate.total == pytest.approx(5.4008)


@pytest.mark.parametrize("provider, el, dg", [
    ("elevenlabs", 0.4, 0), ("deepgram", 0, 0.015), ("say", 0, 0),
])
def test_tts_estimates_respect_provider(provider, el, dg):
    estimate = spend.estimate_spend([{"narration": "x" * 1000}], {"provider": provider})
    assert estimate.elevenlabs == pytest.approx(el)
    assert estimate.deepgram == pytest.approx(dg)
    assert estimate.fal == 0


def test_auto_provider_uses_local_keys_only(monkeypatch):
    monkeypatch.setattr(tts.keys, "get", lambda name: "fake" if name == "DEEPGRAM_API_KEY" else None)
    monkeypatch.setattr(tts.urllib.request, "urlopen", lambda *a, **kw: pytest.fail("network"))
    estimate = spend.estimate_spend([{"narration": "hello"}], {"provider": "auto"})
    assert estimate.deepgram > 0
    assert estimate.elevenlabs == 0


def test_local_tts_can_still_have_paid_lipsync():
    estimate = spend.estimate_spend([{"narration": "x" * 750, "lipsync": True}],
                                    {"provider": "macos", "speaking_rate": 2})
    assert estimate.elevenlabs == estimate.deepgram == 0
    assert estimate.fal == pytest.approx(4.80)


def test_free_project_has_no_spend(tmp_path, capsys):
    import json
    from video_claw.config import load
    (tmp_path / "project.json").write_text(json.dumps({
        "config": {"mode": "free", "tts": {"provider": "elevenlabs"}},
        "slides": [{"narration": "Hello", "lipsync": True}],
    }))
    project = load(tmp_path)
    estimate = spend.estimate_spend(project.slides, project.config["tts"])
    assert estimate.total == 0
    spend.print_estimate(estimate)
    assert capsys.readouterr().out == ""


def test_tiny_paid_estimates_do_not_round_to_zero(capsys):
    spend.print_estimate(spend.estimate_spend([{"narration": "Hi"}], {"provider": "deepgram"}))
    output = capsys.readouterr().out
    assert "Deepgram:" in output
    assert "$0.00 " not in output
    assert "before cache savings" in output


@pytest.mark.parametrize("rate", [-1, 0, float("nan"), float("inf")])
def test_invalid_rates_rejected_before_spend(rate):
    with pytest.raises(ValueError, match="speaking rate"):
        spend.estimate_spend([{"narration": "Hello"}],
                             {"provider": "macos", "speaking_rate": rate})


@pytest.mark.parametrize("skip_preview, auto_yes", [(False, False), (False, True), (True, False)])
def test_estimate_precedes_gate_and_tts(tmp_path, monkeypatch, capsys, skip_preview, auto_yes):
    monkeypatch.setattr(core, "render_pngs", lambda *a, **kw: None)
    monkeypatch.setattr(tts.urllib.request, "urlopen", lambda *a, **kw: pytest.fail("network"))
    events = []

    def gate(*args, **kwargs):
        assert kwargs["no_browser"] is True
        assert kwargs["auto_yes"] is auto_yes
        print("PREVIEW GATE")
        events.append("gate")
        return True

    def audio(*args, **kwargs):
        print("FIRST TTS CALL")
        events.append("tts")
        raise RuntimeError("stop before synthesis")

    monkeypatch.setattr(core.preview_mod, "prompt_user", gate)
    monkeypatch.setattr(tts, "make_audio_elevenlabs_master", audio)
    with pytest.raises(RuntimeError, match="stop before synthesis"):
        core.make_video([{"narration": "Hello", "lipsync": True}], workdir=tmp_path,
                        tts_cfg={"provider": "elevenlabs"}, skip_preview=skip_preview,
                        auto_yes=auto_yes, no_browser=True)
    output = capsys.readouterr().out
    assert output.index("[spend]") < output.index("FIRST TTS CALL")
    assert "fal.ai:" in output
    assert events == (["tts"] if skip_preview else ["gate", "tts"])
    if not skip_preview:
        assert output.index("[spend]") < output.index("PREVIEW GATE")
    assert not (tmp_path / "cache/tts-last-render.json").exists()


def test_aborted_preview_never_calls_tts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(core, "render_pngs", lambda *a, **kw: None)
    monkeypatch.setattr(core.preview_mod, "prompt_user", lambda *a, **kw: False)
    monkeypatch.setattr(tts, "make_audio_elevenlabs_master", lambda *a, **kw: pytest.fail("TTS on abort"))
    with pytest.raises(SystemExit, match="aborted"):
        core.make_video([{"narration": "Hello"}], workdir=tmp_path,
                        tts_cfg={"provider": "elevenlabs"}, no_browser=True)
    assert "[spend]" in capsys.readouterr().out
    assert not (tmp_path / "cache/tts-last-render.json").exists()


@pytest.mark.parametrize("default, slide, fal_slides", [
    ("static", {}, 0),
    (False, {"lipsync": "static"}, 0),
    ("fal", {"lipsync": False}, 0),
    ("fal", {}, 1),
    ("static", {"lipsync": True}, 1),
])
def test_spend_uses_same_lipsync_mode_as_renderer(default, slide, fal_slides):
    estimate = spend.estimate_spend(
        [{"narration": "x" * 750, **slide}],
        {"provider": "macos", "lipsync": default})
    assert estimate.lipsync_slides == fal_slides
    assert estimate.fal == pytest.approx(9.6 * fal_slides)


def test_zero_slide_rate_is_not_replaced_by_global_default():
    with pytest.raises(ValueError, match="speaking rate"):
        spend.estimate_spend([{"narration": "hello", "speed": 0}],
                             {"provider": "macos", "speaking_rate": 1})
