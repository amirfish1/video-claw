#!/usr/bin/env python3
"""Assemble "The Review Room" Phase-1 cut.

Stills (centered Ken Burns) + graded screen-composite of the real $0 demo +
end slate + duration-aware video-claw $0 narration + burned mute-first captions
+ silent-anchored, loudnorm'd audio (no -shortest truncation).
Output: review-room/output/v1.mp4 (+ v1.srt). Run from repo root:
    python3 scripts/review_room_assemble.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RR = ROOT / "review-room"
STILLS = RR / "v1" / "owned" / "stills"
WORK = RR / "work"
CLIPS = WORK / "clips"
# Phase-2 motion clips (image-to-video). A "still" shot auto-upgrades to its
# motion clip when present here; otherwise it falls back to the Ken-Burns still.
MOTION_DIR = RR / "v1" / "owned" / "motion"
OUT = RR / "output"
for d in (WORK, CLIPS, OUT):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
# A common macOS TrueType font; change if missing on this machine.
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"

SLATE_TITLE = "This is how Kneaded.ai ships."
SLATE_CTA = "Kneaded.ai  -  your small business, run by agents."

# Real customer-project clip presented at the shot-7 review beat.
TELEMETRY_CLIP = Path(
    "/Users/amirfish/Apps/ccc-outreach/growth-machine/"
    "ccc-telemetry-pitch/out/ccc-telemetry-pitch.mp4")

# id, source, kind, duration_s, motion, fade_in, fade_out, seek_s
# (seek_s = in-point for "screen" clips; ignored for stills/slate)
SHOTS = [
    ("01", STILLS / "shot_01.png", "still", 6, "in",  True,  False, 0),
    ("02", STILLS / "shot_02.png", "still", 5, "pan", False, False, 0),
    ("03", STILLS / "shot_03.png", "still", 4, "in",  False, True,  0),   # act break
    ("04", STILLS / "shot_04.png", "still", 4, "in",  True,  False, 0),
    ("05", ROOT / "docs/free-mode-demo.mp4", "screen", 10, None, True, True, 0),
    ("06", STILLS / "shot_06.png", "still", 3, "in",  False, False, 0),
    ("07", TELEMETRY_CLIP,         "screen", 6, None, False, True, 33),   # act break
    ("08", STILLS / "shot_08.png", "still", 4, "in",  True,  False, 0),
    ("09", STILLS / "shot_09.png", "still", 6, "pan", False, False, 0),
    ("10", STILLS / "shot_10.png", "still", 7, "out", False, True,  0),
    ("11", None,                   "slate", 4, None,  True,  True,  0),
]

# (desired_start, text). Actual offsets recomputed from measured WAV durations.
VO_LINES = [
    (2.0,  "I don't have a team. I have a bench of agents."),
    (8.0,  "Some build for our customers. Some rebuild our own backend."),
    (15.0, "Every task gets reviewed before it reaches my desk."),
    (22.0, "Then, one by one, they come in and present."),
    (40.0, "I approve. Or I send it back."),
    (49.0, "This is how Kneaded ships."),
]


def _ffmpeg_bin():
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


FFMPEG = _ffmpeg_bin()


def run(cmd):
    if cmd and cmd[0] == "ffmpeg":
        cmd = [FFMPEG, *cmd[1:]]
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)


def probe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def _fades(dur, fin, fout):
    f = []
    if fin:
        f.append("fade=t=in:st=0:d=0.6")
    if fout:
        f.append(f"fade=t=out:st={dur-0.6:.3f}:d=0.6")
    return f


def ken_burns(src, dur, motion, fin, fout, out):
    frames = int(dur * FPS)
    uw, uh = int(W * 1.5), int(H * 1.5)   # modest upscale -> no zoompan OOM
    if motion == "out":
        z = "if(eq(on,0),1.12,max(zoom-0.0006,1.0))"
    elif motion == "pan":
        z = "1.08"
    else:
        z = "min(zoom+0.0006,1.12)"
    if motion == "pan":
        x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    else:
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = (
        f"scale={uw}:{uh}:force_original_aspect_ratio=increase,"
        f"crop={uw}:{uh}:(in_w-{uw})/2:(in_h-{uh})/2,"          # CENTERED crop
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
        f"setsar=1,fps={FPS},format=yuv420p"
    )
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur),
         "-r", str(FPS), "-vf", vf, "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def screen_shot(src, bg, dur, fin, fout, out, ss=0):
    """Graded 'on the room screen' composite so a real clip lives in the world.

    `bg` is the per-shot room still; `ss` is the clip in-point (seconds).
    """
    fl = ["format=yuv420p"] + _fades(dur, fin, fout)
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,"
        f"eq=brightness=-0.18:saturation=0.9,setsar=1,fps={FPS}[bg];"
        f"[1:v]scale={int(W*0.6)}:-2,eq=contrast=1.05,"
        f"colorbalance=rm=0.04:bm=-0.04,setsar=1,fps={FPS}[demo];"
        f"[bg][demo]overlay=(W-w)/2:(H-h)/2-40,vignette=PI/5,"
        + ",".join(fl) + "[v]"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(bg),
         "-ss", str(ss), "-i", str(src), "-filter_complex", fc, "-map", "[v]",
         "-t", str(dur), "-r", str(FPS), "-an", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(out)])


def prep_motion_clip(src, dur, fin, fout, out):
    """Normalize a Phase-2 image-to-video clip into the shot slot: scale/pad to
    1920x1080, setsar/fps, hold the last frame if the clip is short, trim to dur,
    same fades. No Ken Burns, no audio.
    """
    fl = _fades(dur, fin, fout)
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,fps={FPS},"
        f"tpad=stop_mode=clone:stop_duration=12,format=yuv420p"
    )
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-i", str(src), "-an", "-vf", vf, "-t", str(dur),
         "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def make_slate(dur, fin, fout, out):
    t = WORK / "slate_title.txt"
    t.write_text(SLATE_TITLE)
    c = WORK / "slate_cta.txt"
    c.write_text(SLATE_CTA)
    vf = (
        f"format=yuv420p,"
        f"drawtext=fontfile={FONT}:textfile={t}:fontcolor=white:fontsize=66:"
        f"x=(w-tw)/2:y=h/2-70,"
        f"drawtext=fontfile={FONT}:textfile={c}:fontcolor=0xC9C9C9:fontsize=34:"
        f"x=(w-tw)/2:y=h/2+30"
    )
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c=0x0c0f14:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def build_audio(total, placed, out):
    """Silent base anchors the whole timeline; VO mixed in; final loudnorm."""
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo"]
    for _, _, wav, _ in placed:
        inputs += ["-i", str(wav)]
    fc, labels = [], ["[0:a]"]
    for i, (start, _d, _w, _t) in enumerate(placed, start=1):
        ms = int(start * 1000)
        fc.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    fc.append("".join(labels)
              + f"amix=inputs={len(placed)+1}:normalize=0:dropout_transition=0[mix]")
    fc.append("[mix]loudnorm=I=-16:TP=-1.5:LRA=11[ao]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[ao]", "-t", f"{total}", "-c:a", "aac", "-b:a", "192k", str(out)])


def burn_captions(in_v, placed, out):
    chain = ["format=yuv420p"]
    for i, (start, d, _w, text) in enumerate(placed):
        cf = WORK / f"cap_{i:02d}.txt"
        cf.write_text(text)
        end = start + d
        chain.append(
            f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=white:fontsize=46:"
            f"box=1:boxcolor=0x000000AA:boxborderw=18:"
            f"x=(w-tw)/2:y=h-170:enable='between(t,{start:.2f},{end:.2f})'"
        )
    run(["ffmpeg", "-y", "-i", str(in_v), "-vf", ",".join(chain), "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def _srt_ts(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def main():
    listfile = WORK / "concat.txt"
    total = 0.0
    with listfile.open("w") as f:
        for sid, src, kind, dur, motion, fin, fout, ss in SHOTS:
            out = CLIPS / f"shot_{sid}.mp4"
            if kind == "still":
                mclip = MOTION_DIR / f"shot_{sid}.mp4"
                if mclip.exists():
                    prep_motion_clip(mclip, dur, fin, fout, out)
                else:
                    ken_burns(src, dur, motion, fin, fout, out)
            elif kind == "screen":
                bg = STILLS / f"shot_{sid}.png"
                screen_shot(src, bg, dur, fin, fout, out, ss)
            elif kind == "slate":
                make_slate(dur, fin, fout, out)
            f.write(f"file '{out.as_posix()}'\n")
            total += dur

    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])

    # Narration via video-claw's $0 TTS (best installed macOS voice),
    # placed duration-aware so lines never overlap.
    sys.path.insert(0, str(ROOT))
    from video_claw.tts.macos import synthesize
    placed, prev_end = [], 0.0
    for i, (anchor, text) in enumerate(VO_LINES):
        wav = WORK / f"vo_{i:02d}.wav"
        synthesize(text, wav, voice="auto")
        d = probe_dur(wav)
        start = max(anchor, prev_end + 0.6)
        placed.append((start, d, wav, text))
        prev_end = start + d

    audio = WORK / "audio.m4a"
    build_audio(total, placed, audio)
    captioned = WORK / "captioned.mp4"
    burn_captions(silent, placed, captioned)

    final = OUT / "v1.mp4"
    run(["ffmpeg", "-y", "-i", str(captioned), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
         "-shortest", str(final)])  # safe: video and audio are both == total

    srt = OUT / "v1.srt"
    with srt.open("w") as f:
        for i, (start, d, _w, text) in enumerate(placed, start=1):
            f.write(f"{i}\n{_srt_ts(start)} --> {_srt_ts(start+d)}\n{text}\n\n")
    print("\nWROTE", final, "and", srt, f"(~{total:.0f}s)")


if __name__ == "__main__":
    main()
