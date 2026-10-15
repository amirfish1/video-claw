"""Static/fal routing is exercised with every external operation mocked."""
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from video_claw import avatar, cli, config, core, ffmpeg_video
from video_claw.cache import Cache


@pytest.mark.parametrize("value,expected", [(False, "off"), (None, "off"),
                                           (True, "fal"), ("fal", "fal"),
                                           ("static", "static")])
def test_mode_resolves_defaults_and_slide_overrides(value, expected):
    assert avatar.resolve_lipsync_mode({}, {"lipsync": value}) == expected
    assert avatar.resolve_lipsync_mode({"lipsync": value}, {"lipsync": "fal"}) == expected


@pytest.mark.parametrize("value", ["true", "false", "typo", 1, 0, [], {}])
def test_invalid_modes_cannot_accidentally_buy_fal(value):
    with pytest.raises(ValueError, match="lipsync must"):
        avatar.resolve_lipsync_mode({"lipsync": value}, {})


@pytest.fixture
def render_env(monkeypatch, tmp_path):
    seen = {"slides": [], "crops": [], "fal": []}
    monkeypatch.setattr(core, "render_pngs", lambda *args, **kwargs: [])
    monkeypatch.setattr(core.tts_mod, "resolve_provider", lambda cfg: cfg["provider"])

    def local_audio(text, idx, *, workdir, **kwargs):
        path = workdir / f"narr_{idx:02d}.m4a"
        path.write_bytes(b"local audio")
        return path, 1.0

    monkeypatch.setattr(core.tts_mod, "make_audio", local_audio)

    def crop(image, **kwargs):
        seen["crops"].append(image)
        badge = tmp_path / (image.stem + "-circle.png")
        Image.new("RGBA", (280, 280), "red").save(badge)
        return badge

    monkeypatch.setattr(core.avatar_mod, "crop_image_to_circle", crop)

    def fal(*args, **kwargs):
        seen["fal"].append(args)
        return tmp_path / "fal.mp4"

    monkeypatch.setattr(core.lip_mod, "fal_omnihuman_lipsync", fal)
    monkeypatch.setattr(core.lip_mod, "crop_to_circle_video", lambda *args, **kwargs: tmp_path / "circle.mov")

    def compose(png, m4a, dur, idx, **kwargs):
        seen["slides"].append((idx, dur, kwargs))
        return tmp_path / f"part-{idx}.mp4"

    monkeypatch.setattr(core.ff, "make_slide_video", compose)
    raw = tmp_path / "raw.mp4"
    raw.write_bytes(b"raw")
    monkeypatch.setattr(core.ff, "concat_slides", lambda *args, **kwargs: raw)
    monkeypatch.setattr(core.ff, "ffprobe_duration", lambda path: 3.0)
    monkeypatch.setattr(core.ff, "burn_captions", lambda src, ass, dst: dst.write_bytes(b"captioned"))
    return seen


def render(tmp_path, slides, **kwargs):
    return core.make_video(slides, project_dir=tmp_path, workdir=tmp_path / "work",
                           tts_cfg=kwargs.pop("tts_cfg", {"provider": "macos"}),
                           skip_preview=True, **kwargs)


def test_static_default_reuses_one_crop_and_false_disables_overlay(tmp_path, render_env):
    assets = tmp_path / "assets"
    assets.mkdir()
    image = assets / "avatar.png"
    image.write_bytes(b"project avatar")
    slides = [{"narration": "first"}, {"narration": "second"},
              {"narration": "third", "lipsync": False}]
    render(tmp_path, slides, tts_cfg={"provider": "macos", "lipsync": "static"})
    assert render_env["crops"] == [image.resolve()]
    badges = [item[2]["avatar_circle"] for item in render_env["slides"]]
    assert badges[0] == badges[1] and badges[0] is not None
    assert badges[2] is None
    assert not render_env["fal"]
    assert all(s[2]["lipsync_circle"] is None for s in render_env["slides"])


def test_static_slide_override_and_missing_image_fallback(tmp_path, render_env):
    render(tmp_path, [{"narration": "hi", "lipsync": "static"}, {"narration": "bye"}])
    assert render_env["crops"] == [avatar.BUNDLED_AVATAR]
    assert render_env["slides"][0][2]["avatar_circle"] is not None
    assert render_env["slides"][1][2]["avatar_circle"] is None
    assert not render_env["fal"]


@pytest.mark.parametrize("value", [True, "fal"])
def test_fal_modes_keep_existing_paid_path(tmp_path, render_env, monkeypatch, value):
    portrait = tmp_path / "portrait.png"
    portrait.write_bytes(b"avatar")
    monkeypatch.setattr(core.tts_mod.subprocess, "run", lambda cmd, **kwargs: Path(cmd[-1]).write_bytes(b"mp3"))
    render(tmp_path, [{"narration": "hi", "lipsync": value, "lipsync_avatar": str(portrait)}])
    assert len(render_env["fal"]) == 1
    assert render_env["slides"][0][2]["lipsync_circle"] == tmp_path / "circle.mov"
    assert not render_env["crops"]


def test_free_direct_call_disables_paid_project_default(tmp_path, render_env):
    render(tmp_path, [{"narration": "hi", "lipsync": True}], free=True,
           tts_cfg={"provider": "elevenlabs", "lipsync": "fal"})
    assert not render_env["fal"]


def test_core_uses_one_master_call_and_per_slide_rates(tmp_path, render_env, monkeypatch):
    calls = []

    def master(narrations, *, workdir, rates, **kwargs):
        calls.append((narrations, rates))
        results = []
        for idx, (text, rate) in enumerate(zip(narrations, rates)):
            path = workdir / f"narr_{idx:02d}.m4a"
            path.write_bytes(b"audio")
            (workdir / f"narr_{idx:02d}.alignment.json").write_text(json.dumps({
                "characters": list(text),
                "character_start_times_seconds": [0.2] * len(text),
                "character_end_times_seconds": [1.0] * len(text),
            }))
            results.append((path, 1.0 / rate))
        return results

    monkeypatch.setattr(core.tts_mod, "make_audio_elevenlabs_master", master)
    monkeypatch.setattr(core.tts_mod, "make_audio", lambda *a, **k: pytest.fail("per-slide TTS"))
    caption_entries = []
    write_srt = core.caps_mod.write_master_srt

    def capture_srt(entries, path):
        caption_entries.extend(entries)
        write_srt(entries, path)

    monkeypatch.setattr(core.caps_mod, "write_master_srt", capture_srt)
    render(tmp_path, [{"narration": "One."}, {"narration": "Two.", "speed": 2}],
           tts_cfg={"provider": "elevenlabs", "speaking_rate": 1})
    assert calls == [(["One.", "Two."], [1, 2])]
    assert [slide[1] for slide in render_env["slides"]] == [1.0, 0.5]
    assert caption_entries[0][:2] == pytest.approx((0.2, 1.0))
    assert caption_entries[1][:2] == pytest.approx((1.25, 1.65))
    assert "Two." in (tmp_path / "work/captions.srt").read_text()


@pytest.mark.parametrize("bad_slide", [{"narration": ""}, {"narration": "hi", "speed": 0},
                                      {"narration": "hi", "lipsync": "typo"}])
def test_bad_slide_fails_before_preview_or_spend(tmp_path, render_env, monkeypatch, bad_slide):
    monkeypatch.setattr(core, "render_pngs", lambda *a, **k: pytest.fail("must validate first"))
    with pytest.raises(ValueError):
        render(tmp_path, [bad_slide])
    assert not render_env["slides"]


@pytest.mark.parametrize("default,slide,warns", [("static", {}, False),
                                               ("fal", {"lipsync": False}, False),
                                               (False, {"lipsync": "static"}, False),
                                               ("fal", {}, True)])
def test_preflight_warns_only_for_effective_fal(monkeypatch, tmp_path, capsys, default, slide, warns):
    monkeypatch.setattr(cli.keys_mod, "load_keys", lambda: {})
    monkeypatch.setattr(cli.tts_mod, "resolve_provider", lambda cfg: "elevenlabs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.delenv("FAL_API_KEY", raising=False)
    project = config.Project(tmp_path, {"tts": {"lipsync": default}}, [slide])
    assert cli._ensure_keys_for(project) is None
    assert ("FAL_API_KEY" in capsys.readouterr().out) is warns


def test_video_slide_composes_static_badge_at_actual_diameter(tmp_path, monkeypatch):
    badge = tmp_path / "badge.png"
    Image.new("RGBA", (120, 120), "red").save(badge)
    commands = []
    monkeypatch.setattr(ffmpeg_video.subprocess, "run", lambda cmd, **kw: commands.append(cmd))
    ffmpeg_video.make_slide_video(
        tmp_path / "slide.png", tmp_path / "audio.m4a", 1.0, 0,
        slide={"type": "video", "video": str(tmp_path / "clip.mp4")},
        workdir=tmp_path, cache=Cache(tmp_path), dimensions=(640, 360), avatar_circle=badge)
    cmd = commands[0]
    assert cmd.count("-loop") == 2
    assert str(badge) in cmd
    assert "[base][3:v]overlay=x=480:y=170" in cmd[cmd.index("-filter_complex") + 1]


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
@pytest.mark.parametrize("kind", ["image", "video"])
def test_real_ffmpeg_static_overlay_has_transparent_corners(tmp_path, monkeypatch, kind):
    import subprocess
    import wave
    from PIL import ImageDraw

    # Ten small frames, one ffmpeg thread: cheap enough for the shared host.
    real_run = subprocess.run

    def one_thread(cmd, **kwargs):
        cmd = [*cmd[:-1], "-threads", "1", "-filter_complex_threads", "1", cmd[-1]]
        kwargs["stderr"] = subprocess.PIPE
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(ffmpeg_video.subprocess, "run", one_thread)
    background = tmp_path / "background.png"
    Image.new("RGB", (320, 240), "blue").save(background)
    badge = tmp_path / "badge.png"
    portrait = Image.new("RGBA", (64, 64))
    ImageDraw.Draw(portrait).ellipse((0, 0, 63, 63), fill="red")
    portrait.save(badge)
    audio = tmp_path / "audio.wav"
    with wave.open(str(audio), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\0\0" * 3200)
    slide = {"type": kind}
    if kind == "video":
        clip = tmp_path / "clip.mp4"
        real_run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                  "color=c=green:s=80x60:d=0.3", "-threads", "1", "-c:v", "libx264",
                  "-pix_fmt", "yuv420p", str(clip)], check=True)
        slide.update(video=str(clip), _vp=(0, 0, 80, 60))
    out = ffmpeg_video.make_slide_video(
        background, audio, 0.2, 0, slide=slide, workdir=tmp_path,
        cache=Cache(tmp_path), dimensions=(320, 240), avatar_circle=badge)
    frame = tmp_path / "frame.png"
    real_run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-frames:v", "1",
              "-threads", "1", str(frame)], check=True)
    with Image.open(frame) as rendered:
        # Badge origin (216,106): center red, transparent corner retains blue.
        red = rendered.getpixel((248, 138))
        blue = rendered.getpixel((217, 107))
        assert red[0] > 200 and red[2] < 40
        assert blue[2] > 200 and blue[0] < 40
        if kind == "video":
            green = rendered.getpixel((40, 30))
            assert green[1] > 90 and green[0] < 40 and green[2] < 40
