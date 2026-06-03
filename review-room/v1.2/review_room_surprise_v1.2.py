#!/usr/bin/env python3
"""Assemble "An Afternoon at Kneaded.ai" — the SURPRISE cut (v2).

Act 1 plays as a normal company (hub, debate, group chat, presentation, VP
review), then turns digital (agentic flows + an ANIMATED orchestration diagram),
then replays the beats revealed as AI via OVERLAYS (debate+group-chat,
review+AI-deck, VP+reveal). Narrated by ElevenLabs, burned mute-first captions.
Output: review-room/surprise-v1.mp4 (+ .srt). Run from repo root:
    python3 scripts/review_room_surprise.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root (archived at review-room/v1.2/)
RR = ROOT / "review-room"
STILLS = RR / "v1" / "owned" / "stills"
SAMPLES = RR / "raw"
MOTION = RR / "v1" / "owned" / "motion"
WORK = RR / "work_surprise"
CLIPS = WORK / "clips"
OUT = RR / "output"
for d in (WORK, CLIPS, OUT):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
GROUPCHAT = Path("/Users/amirfish/Downloads/anim_group_chat.mp4")
DIAGRAM = Path("/Users/amirfish/.claude/command-center/pasted-images/paste-1780336777122.png")
DECK = ROOT / "docs/free-mode-demo.mp4"
VOICE_ID = "cgSgspJ2msm6clMCkdW9"  # ElevenLabs Jessica (warm narrator)

SLATE_TITLE = "This is how Kneaded.ai works."
SLATE_CTA = "Kneaded.ai  -  a company run by agents."

SHOTS = [
    {"id": "01", "kind": "clip",    "src": SAMPLES / "sample3_bustling_hub.mp4", "dur": 5, "fin": True,  "fout": False},
    {"id": "02", "kind": "clip",    "src": SAMPLES / "sample5_real_debate.mp4",  "dur": 4, "fin": False, "fout": False},
    {"id": "03", "kind": "screen",  "src": GROUPCHAT, "bg": STILLS / "shot_05.png", "dur": 6, "ss": 0, "speed": 0.5, "fin": False, "fout": False},
    {"id": "04", "kind": "screen",  "src": DECK,      "bg": STILLS / "shot_05.png", "dur": 4, "ss": 2, "speed": 1.0, "fin": False, "fout": False},
    {"id": "05", "kind": "clip",    "src": MOTION / "shot_04.mp4", "dur": 4, "fin": False, "fout": True},   # VP review
    {"id": "06", "kind": "clip",    "src": SAMPLES / "sample4_agentic_flows.mp4", "dur": 5, "fin": True, "fout": False},  # turn
    {"id": "07", "kind": "diagramanim", "src": MOTION / "diagram_anim.mp4", "dur": 6, "fin": False, "fout": True},  # animated reveal
    {"id": "08", "kind": "overlay", "src": SAMPLES / "sample5_real_debate.mp4", "ov": GROUPCHAT, "speed": 0.5, "ovss": 0, "dur": 4, "fin": False, "fout": False},
    {"id": "09", "kind": "overlay", "src": MOTION / "shot_04.mp4", "ov": DECK, "speed": 1.0, "ovss": 2, "dur": 4, "fin": False, "fout": False},
    {"id": "10", "kind": "clip",    "src": MOTION / "shot_06.mp4", "dur": 3, "fin": False, "fout": True},   # VP -> AI
    {"id": "11", "kind": "slate",   "dur": 4, "fin": True, "fout": True},
]

VO_LINES = [
    (1.0,  "An ordinary afternoon at Kneaded A.I."),
    (5.3,  "The team can't agree on the opening line."),
    (9.3,  "Stop wasting opens on the pain, not the promise. First impressions should inspire, not scold."),
    (15.3, "Someone presents the fix."),
    (19.3, "They take it to the boss. Who has notes. A lot of notes."),
    (23.3, "Except, there is no team."),
    (28.3, "Every session is an agent. One connector runs them all."),
    (34.3, "The debate was a group chat."),
    (38.3, "The presenter was A.I."),
    (42.3, "And so was the boss."),
    (45.3, "This is how Kneaded A.I. works."),
]


def _ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


FFMPEG = _ffmpeg_bin()


def run(cmd):
    if cmd and cmd[0] == "ffmpeg":
        cmd = [FFMPEG, *cmd[1:]]
    print("+", " ".join(str(c) for c in cmd[:6]), "...")
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


def clip_shot(src, dur, fin, fout, out, ss=0):
    fl = _fades(dur, fin, fout)
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,fps={FPS},"
          f"tpad=stop_mode=clone:stop_duration=12,format=yuv420p")
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-ss", str(ss), "-i", str(src), "-an", "-vf", vf,
         "-t", str(dur), "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def screen_shot(src, bg, dur, fin, fout, out, ss=0, speed=1.0):
    fl = ["format=yuv420p"] + _fades(dur, fin, fout)
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,"
        f"eq=brightness=-0.16:saturation=0.92,setsar=1,fps={FPS}[bg];"
        f"[1:v]setpts={speed}*PTS,scale={int(W*0.6)}:-2,eq=contrast=1.05,"
        f"setsar=1,fps={FPS}[demo];"
        f"[bg][demo]overlay=(W-w)/2:(H-h)/2-40,vignette=PI/5,"
        + ",".join(fl) + "[v]"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(bg),
         "-ss", str(ss), "-i", str(src), "-filter_complex", fc, "-map", "[v]",
         "-t", str(dur), "-r", str(FPS), "-an", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(out)])


def diagram_shot(src, dur, fin, fout, out):
    frames = int(dur * FPS)
    fl = _fades(dur, fin, fout)
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0c0f14,setsar=1,"
        f"zoompan=z='min(zoom+0.0004,1.10)':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p"
    )
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur),
         "-r", str(FPS), "-vf", vf, "-an", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(out)])


def overlay_shot(base, ov, dur, speed, fin, fout, out, ovss=0):
    fl = _fades(dur, fin, fout)
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,fps={FPS}[bg];"
        f"[1:v]setpts={speed}*PTS,scale=760:-2,setsar=1,fps={FPS},"
        f"format=yuva420p,colorchannelmixer=aa=0.93[pip];"
        f"[bg][pip]overlay=W-w-70:(H-h)/2,"
        + ",".join(["format=yuv420p"] + fl) + "[v]"
    )
    run(["ffmpeg", "-y", "-i", str(base), "-ss", str(ovss), "-i", str(ov),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), "-r", str(FPS),
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def make_slate(dur, fin, fout, out):
    t = WORK / "slate_title.txt"; t.write_text(SLATE_TITLE)
    c = WORK / "slate_cta.txt"; c.write_text(SLATE_CTA)
    vf = (f"format=yuv420p,"
          f"drawtext=fontfile={FONT}:textfile={t}:fontcolor=white:fontsize=66:x=(w-tw)/2:y=h/2-70,"
          f"drawtext=fontfile={FONT}:textfile={c}:fontcolor=0xC9C9C9:fontsize=34:x=(w-tw)/2:y=h/2+30")
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0c0f14:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def build_audio(total, placed, out):
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo"]
    for _, _, af, _ in placed:
        inputs += ["-i", str(af)]
    fc, labels = [], ["[0:a]"]
    for i, (start, _d, _a, _t) in enumerate(placed, start=1):
        ms = int(start * 1000)
        fc.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(placed)+1}:normalize=0:dropout_transition=0[mix]")
    fc.append("[mix]loudnorm=I=-16:TP=-1.5:LRA=11[ao]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[ao]", "-t", f"{total}", "-c:a", "aac", "-b:a", "192k", str(out)])


def burn_captions(in_v, placed, out):
    chain = ["format=yuv420p"]
    for i, (start, d, _a, text) in enumerate(placed):
        cf = WORK / f"cap_{i:02d}.txt"; cf.write_text(text)
        end = start + d
        chain.append(
            f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=white:fontsize=46:"
            f"box=1:boxcolor=0x000000AA:boxborderw=18:"
            f"x=(w-tw)/2:y=h-170:enable='between(t,{start:.2f},{end:.2f})'")
    run(["ffmpeg", "-y", "-i", str(in_v), "-vf", ",".join(chain), "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def _srt_ts(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60); ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def main():
    listfile = WORK / "concat.txt"
    total = 0.0
    with listfile.open("w") as f:
        for s in SHOTS:
            out = CLIPS / f"beat_{s['id']}.mp4"
            k = s["kind"]
            if k == "clip":
                clip_shot(s["src"], s["dur"], s["fin"], s["fout"], out, ss=s.get("ss", 0))
            elif k == "screen":
                screen_shot(s["src"], s["bg"], s["dur"], s["fin"], s["fout"], out,
                            ss=s.get("ss", 0), speed=s.get("speed", 1.0))
            elif k == "diagramanim":
                if Path(s["src"]).exists():
                    clip_shot(s["src"], s["dur"], s["fin"], s["fout"], out)
                else:
                    print("  [diagram] animated clip not found; using static fallback")
                    diagram_shot(DIAGRAM, s["dur"], s["fin"], s["fout"], out)
            elif k == "overlay":
                overlay_shot(s["src"], s["ov"], s["dur"], s.get("speed", 1.0),
                             s["fin"], s["fout"], out, ovss=s.get("ovss", 0))
            elif k == "slate":
                make_slate(s["dur"], s["fin"], s["fout"], out)
            f.write(f"file '{out.as_posix()}'\n")
            total += s["dur"]

    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])

    # Narration via ElevenLabs (through video-claw), cached so re-renders are free.
    sys.path.insert(0, str(ROOT))
    from video_claw import keys as vkeys
    for kk, vv in vkeys.load_keys().items():
        os.environ.setdefault(kk, vv)
    from video_claw import tts as vtts
    from video_claw.cache import Cache as VCache
    vcache = VCache(WORK)
    placed, prev_end = [], 0.0
    for i, (anchor, text) in enumerate(VO_LINES):
        m4a, d = vtts.make_audio(text, i, workdir=WORK, cache=vcache, tts_cfg={
            "provider": "elevenlabs", "voice_id": VOICE_ID,
            "model": "eleven_turbo_v2_5", "speaking_rate": 1.05})
        start = max(anchor, prev_end + 0.4)
        placed.append((start, d, m4a, text))
        prev_end = start + d

    audio = WORK / "audio.m4a"
    build_audio(total, placed, audio)
    captioned = WORK / "captioned.mp4"
    burn_captions(silent, placed, captioned)

    final = OUT / "v1.2.mp4"
    run(["ffmpeg", "-y", "-i", str(captioned), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest", str(final)])

    srt = OUT / "v1.2.srt"
    with srt.open("w") as f:
        for i, (start, d, _a, text) in enumerate(placed, start=1):
            f.write(f"{i}\n{_srt_ts(start)} --> {_srt_ts(start+d)}\n{text}\n\n")
    print("\nWROTE", final, f"(~{total:.0f}s)")


if __name__ == "__main__":
    main()
