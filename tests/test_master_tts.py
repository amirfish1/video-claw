"""One ElevenLabs request, stable slices/captions and no paid network traffic."""
import base64
import io
import json
import math
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from video_claw import captions, tts
from video_claw.cache import Cache


def response_for(text, audio=b"mock audio"):
    return {
        "audio_base64": base64.b64encode(audio).decode(),
        "alignment": {
            "characters": list(text),
            "character_start_times_seconds": [0.2 + i * 0.1 for i in range(len(text))],
            "character_end_times_seconds": [0.3 + i * 0.1 for i in range(len(text))],
        },
    }


@pytest.fixture
def network(monkeypatch):
    requests = []
    monkeypatch.setattr(tts.keys, "get", lambda name: "test-key")

    def urlopen(req, timeout):
        body = json.loads(req.data)
        requests.append((req, body))
        return io.BytesIO(json.dumps(response_for(body["text"])).encode())

    monkeypatch.setattr(tts.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(tts, "_ffprobe_duration", lambda *args: pytest.fail("must not probe cuts"))
    return requests


@pytest.fixture
def encodes(monkeypatch):
    commands = []

    def run(cmd, **kwargs):
        assert cmd[0] == "ffmpeg"
        commands.append(cmd)
        Path(cmd[-1]).write_bytes(b"encoded " + " ".join(cmd).encode())

    monkeypatch.setattr(tts.subprocess, "run", run)
    return commands


def synth(tmp_path, texts=None, rates=None, **cfg):
    return tts.make_audio_elevenlabs_master(
        texts or ["Hello.", "World!"], rates=rates or [1.0, 2.0],
        workdir=tmp_path, cache=Cache(tmp_path), tts_cfg=cfg)


def test_one_request_slices_original_timeline_and_offsets_captions(tmp_path, network, encodes):
    segments = synth(tmp_path)
    assert len(network) == 1
    req, body = network[0]
    assert req.full_url.endswith("/cgSgspJ2msm6clMCkdW9/with-timestamps")
    assert body["text"] == "Hello.\n\nWorld!"
    assert body["model_id"] == "eleven_turbo_v2_5"
    # First word ends at .8, second starts at 1.0; split the pause at .9.
    assert [d for _, d in segments] == pytest.approx([0.9, 0.35])
    for cmd in encodes:
        assert "silenceremove" not in " ".join(cmd)
    first_filter = encodes[0][encodes[0].index("-filter:a") + 1]
    second_filter = encodes[1][encodes[1].index("-filter:a") + 1]
    assert first_filter.startswith("atrim=start=0.0:end=")
    assert "asetpts=PTS-STARTPTS,atempo=2.0" in second_filter
    local = json.loads((tmp_path / "narr_01.alignment.json").read_text())
    assert "".join(local["characters"]) == "World!"
    assert local["character_start_times_seconds"][0] == pytest.approx(0.1)
    entries = captions.build_srt_for_slide(1, offset_s=1.05, rate=2.0, workdir=tmp_path)
    assert entries[0][0] == pytest.approx(1.1)
    assert entries[-1][1] == pytest.approx(1.4)
    assert entries[0][2] == "World!"
    assert segments[-1][0].exists()


def test_cache_reuses_master_and_rebuilds_only_changed_rate(tmp_path, network, encodes):
    synth(tmp_path)
    (tmp_path / "narr_01.alignment.json").unlink()
    synth(tmp_path)
    assert len(network) == 1
    assert len(encodes) == 2
    assert (tmp_path / "narr_01.alignment.json").exists()
    synth(tmp_path, rates=[1.0, 0.75])
    assert len(network) == 1
    assert len(encodes) == 3
    synth(tmp_path, texts=["Hello.", "Changed."])
    synth(tmp_path, voice_id="another-voice")
    synth(tmp_path, model="another-model")
    assert len(network) == 4


@pytest.mark.parametrize("damage", ["missing", "normalized", "short", "nan", "reversed", "empty"])
def test_invalid_alignment_fails_without_more_paid_requests(tmp_path, network, encodes, monkeypatch, damage):
    response = response_for("Hello.\n\nWorld!")
    a = response["alignment"]
    if damage == "missing":
        response["normalized_alignment"] = response.pop("alignment")
    elif damage == "normalized":
        a["characters"][0] = "X"
    elif damage == "short":
        a["character_start_times_seconds"].pop()
    elif damage == "nan":
        a["character_end_times_seconds"][-1] = float("nan")
    elif damage == "reversed":
        a["character_start_times_seconds"][2] = -1
    else:
        a["character_start_times_seconds"] = [0] * len(a["characters"])
        a["character_end_times_seconds"] = [0] * len(a["characters"])
    calls = []

    def request(*args):
        calls.append(args)
        return response

    monkeypatch.setattr(tts, "_request_elevenlabs", request)
    for _ in range(2):
        with pytest.raises(ValueError, match="alignment"):
            synth(tmp_path)
    assert len(calls) == 1
    assert not encodes


@pytest.mark.parametrize("rate", [0, -1, float("nan"), float("inf")])
def test_invalid_rates_fail_before_spend(tmp_path, network, encodes, rate):
    with pytest.raises(ValueError, match="speaking rate"):
        synth(tmp_path, rates=[1, rate])
    assert not network
    assert not encodes


def test_single_slide_entrypoint_preserves_requested_index(tmp_path, network, encodes):
    path, duration = tts.make_audio_elevenlabs(
        "  Hi!  ", 7, workdir=tmp_path, cache=Cache(tmp_path), tts_cfg={"speaking_rate": 2})
    assert path.name == "narr_07.m4a"
    assert duration == pytest.approx(0.25)
    assert (tmp_path / "narr_07.alignment.json").exists()
    assert network[0][1]["text"] == "Hi!"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_real_ffmpeg_last_slice_and_speed_with_mock_response(tmp_path, monkeypatch):
    # 1.6 seconds of PCM tone stand in for paid audio; ffmpeg detects the format.
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"".join(int(8000 * math.sin(2 * math.pi * 440 * i / 16000))
                                .to_bytes(2, "little", signed=True) for i in range(25600)))
    calls = []

    def request(text, cfg):
        calls.append(text)
        return response_for(text, buffer.getvalue())

    monkeypatch.setattr(tts, "_request_elevenlabs", request)
    monkeypatch.setattr(tts, "_ffprobe_duration", lambda *args: pytest.fail("must not probe cuts"))
    segments = synth(tmp_path)
    assert len(calls) == 1
    for path, duration in segments:
        pcm = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1",
             "-ar", "16000", "pipe:1"], check=True, capture_output=True).stdout
        assert len(pcm) / 32000 == pytest.approx(duration, abs=0.08)
        assert any(pcm), "the final slice must contain audio, not fall past EOF"
