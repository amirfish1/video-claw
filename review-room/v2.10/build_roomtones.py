#!/usr/bin/env python3
"""Build three distinct ~6s room-tone WAV beds (48kHz stereo) for v2.10.

PRIMARY: ElevenLabs text-to-sound-effects.
FALLBACK: ffmpeg lavfi (anoisesrc shaped per room).

Output WAVs get a 0.3s fade in/out on the tone (these are ambience, OK).
"""
import json
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

import os
sys.path.insert(0, os.getcwd())  # repo root holds the video_claw package

import imageio_ffmpeg
import video_claw.keys as keys

FF = imageio_ffmpeg.get_ffmpeg_exe()
ASSETS = Path("review-room/v2.10/assets")
DUR = 6.0
SR = 48000

ROOMS = {
    "hub": dict(
        prompt=(
            "Large open-plan office room tone, quiet but alive: faint broadband "
            "HVAC air conditioning hum, very subtle spacious room reverb, slightly "
            "bright air, no voices, no music, steady continuous ambience"
        ),
        # ffmpeg fallback: brighter, wider, a touch of reverb/echo, audible-ish
        lavfi=(
            "anoisesrc=color=white:amplitude=0.06:duration=6.5:sample_rate=48000,"
            "highpass=f=90,lowpass=f=4000,"
            "aecho=0.8:0.85:60:0.25,"
            "volume=0.7"
        ),
    ),
    "debate": dict(
        prompt=(
            "Small meeting room tone, tight enclosed space, quiet: gentle low-mid "
            "air, slight room hum, drier and quieter than an open office, no voices, "
            "no music, steady continuous ambience"
        ),
        lavfi=(
            "anoisesrc=color=brown:amplitude=0.05:duration=6.5:sample_rate=48000,"
            "highpass=f=70,lowpass=f=1800,"
            "volume=0.55"
        ),
    ),
    "meeting": dict(
        prompt=(
            "Very quiet conference room tone, still and dead, almost silent: only a "
            "low rumble floor, deep building HVAC subsonic hum, no voices, no music, "
            "no high frequencies, steady continuous ambience"
        ),
        lavfi=(
            "anoisesrc=color=brown:amplitude=0.045:duration=6.5:sample_rate=48000,"
            "lowpass=f=320,"
            "volume=0.5"
        ),
    ),
}


def elevenlabs_sfx(prompt, raw_out):
    api_key = keys.load_keys()["ELEVENLABS_API_KEY"]
    body = json.dumps({"text": prompt, "duration_seconds": DUR}).encode()
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/sound-generation",
        data=body,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    # ElevenLabs returns audio (mp3) bytes. Reject if it's JSON error.
    if data[:1] == b"{":
        raise RuntimeError("ElevenLabs returned JSON, not audio: " + data[:200].decode("utf-8", "ignore"))
    raw_out.write_bytes(data)
    return data


def to_wav_from_bytes(src_path, out_wav):
    """Normalize an arbitrary audio file to 6s 48k stereo wav + 0.3s fades."""
    af = (
        f"aformat=sample_rates={SR}:channel_layouts=stereo,"
        f"atrim=0:{DUR},apad=whole_dur={DUR},"
        f"afade=t=in:st=0:d=0.3,afade=t=out:st={DUR-0.3}:d=0.3"
    )
    cmd = [
        FF, "-y", "-i", str(src_path),
        "-af", af, "-ar", str(SR), "-ac", "2",
        "-c:a", "pcm_s16le", str(out_wav),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def synth_wav(lavfi, out_wav):
    af = (
        f"aformat=sample_rates={SR}:channel_layouts=stereo,"
        f"atrim=0:{DUR},apad=whole_dur={DUR},"
        f"afade=t=in:st=0:d=0.3,afade=t=out:st={DUR-0.3}:d=0.3"
    )
    cmd = [
        FF, "-y", "-f", "lavfi", "-i", lavfi,
        "-af", af, "-t", str(DUR), "-ar", str(SR), "-ac", "2",
        "-c:a", "pcm_s16le", str(out_wav),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    methods = {}
    tmp = Path(tempfile.mkdtemp(prefix="roomtone_", dir="review-room/v2.10/work"))
    for name, cfg in ROOMS.items():
        out_wav = ASSETS / f"roomtone_{name}.wav"
        try:
            raw = tmp / f"{name}.el.mp3"
            elevenlabs_sfx(cfg["prompt"], raw)
            to_wav_from_bytes(raw, out_wav)
            methods[name] = "elevenlabs"
            print(f"[{name}] ElevenLabs OK")
        except Exception as e:
            print(f"[{name}] ElevenLabs failed -> ffmpeg-synth ({e})", file=sys.stderr)
            synth_wav(cfg["lavfi"], out_wav)
            methods[name] = "ffmpeg-synth"
    print("METHODS:", json.dumps(methods))
    return methods


if __name__ == "__main__":
    main()
