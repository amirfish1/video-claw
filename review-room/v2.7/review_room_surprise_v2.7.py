#!/usr/bin/env python3
"""Assemble the SURPRISE cut — v2.7 (writers'-room pass on v2.6).

Locked decisions (group chat 2026-06-02, Director + Codex + Antigravity):
  - t27 turn  : clean PIXEL-DISSOLVE ghost-table (debate clip -> empty room plate).
  - t30 diagram: clean 3-node corporate-flow (Founder input -> Coordinator ->
                 Agent bench), NO dev/git leak. (PIL asset.)
  - t42 reveal: Deck-Agent UI card (Codex copy verbatim), replaces video-claw deck.
  - t45 ending: founder isolated by AGENT/HUMAN label boxes (label-led, not a
                fragile moving-people alpha-fade).
  - narration : Codex v2.7.2 script — VOICED A/B debate + light prove-then-explain.

New tuple contract (Codex):
  VO_LINES : (anchor_s, voice_tag, vo_text, caption_text)
  DIALOGUE : (anchor_s, dur_s, voice_tag, vo_text, caption_text)
  voice_tag: N narrator (Jessica) / A debater-promise / B debater-pain

Output: review-room/output/v2.7.mp4 (+ v2.7.srt). Run from repo root:
    python3 review-room/v2.7/build_assets.py        # once, builds PIL overlays
    python3 review-room/v2.7/review_room_surprise_v2.7.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
STILLS = RR / "v1" / "owned" / "stills"
SAMPLES = RR / "raw"
ALT = RR / "v1.5" / "owned" / "altframes-codex"
MOTION = RR / "v1" / "owned" / "motion"
A7 = RR / "v2.7" / "assets"            # v2.7 PIL/inpaint overlays
WORK = RR / "v2.7" / "work"
CLIPS = WORK / "clips"
OUT = RR / "output"
for d in (WORK, CLIPS, OUT):
    d.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
ROOM = STILLS / "shot_05.png"

# Voices (ElevenLabs). Narrator = Jessica; debaters = distinct stock voices.
VOICES = {
    "N": "cgSgspJ2msm6clMCkdW9",   # Jessica (narrator)
    "A": "pNInz6obpgDQGcFmaJgB",   # Adam (debater — promise/upside)
    "B": "21m00Tcm4TlvDq8ikWAM",   # Rachel (debater — pain/counter)
}

SLATE_TITLE = "This is how Kneaded.ai works."
SLATE_CTA = "Kneaded.ai  -  a founder and a bench of agents."

SHOTS = [
    {"id": "01",  "kind": "clip",      "src": SAMPLES / "sample3_bustling_hub.mp4", "dur": 5,   "fin": True,  "fout": False},
    {"id": "02",  "kind": "clip",      "src": SAMPLES / "sample5_real_debate.mp4",  "dur": 4,   "fin": False, "fout": False},
    {"id": "03a", "kind": "clip",      "src": SAMPLES / "debate_personA.mp4",  "dur": 3.5, "ss": 0.4, "zoom": 1.18, "cx": 0.5, "fin": False, "fout": False},
    {"id": "03b", "kind": "clip",      "src": SAMPLES / "debate_personB.mp4",  "dur": 3.5, "ss": 0.4, "zoom": 1.18, "cx": 0.5, "fin": False, "fout": False},
    {"id": "04",  "kind": "screenimg", "src": ALT / "slide_kneaded.png", "bg": ROOM, "dur": 5,  "fin": False, "fout": False},
    {"id": "05",  "kind": "clip",      "src": SAMPLES / "founder_motion.mp4", "dur": 4.5, "ss": 0, "zoom": 1.12, "cx": 0.5, "fin": False, "fout": False},
    {"id": "06",  "kind": "dissolve",  "src": SAMPLES / "sample5_real_debate.mp4", "plate": A7 / "empty_debate_room.png", "dur": 4.8, "fin": False, "fout": False},
    {"id": "07",  "kind": "diagramimg", "src": A7 / "diagram_corporate.png", "dur": 6, "fin": True, "fout": True},
    {"id": "08",  "kind": "overlayimg", "src": SAMPLES / "sample5_real_debate.mp4", "ov": A7 / "group_chat_overlay.png", "dur": 4, "ss": 1.0, "fin": False, "fout": False},
    {"id": "09",  "kind": "overlayimg", "src": MOTION / "shot_04.mp4", "ov": A7 / "deck_agent_overlay.png", "dur": 4, "ss": 2.0, "fin": False, "fout": False},
    {"id": "10",  "kind": "stillimg",  "src": A7 / "founder_labeled.png", "dur": 4, "motion": "in", "fin": False, "fout": False},
    {"id": "11",  "kind": "slate",     "dur": 4, "fin": True, "fout": True},
]

# Codex v2.7.2 narration. (anchor, voice, vo_text, caption_text)
VO_LINES = [
    (1.0,  "N", "An ordinary afternoon at Kneaded A.I. A small studio making local marketing work.", "An ordinary afternoon at Kneaded.ai."),
    (5.3,  "N", "Today, the team is stuck on one thing: the opening line.", "The team is stuck on the opening line."),
    (16.3, "N", "Someone turns the argument into a pitch: one clean slide, one recommendation.", "Someone turns the argument into a pitch."),
    (21.3, "N", "They take it to the founder. He has notes. A lot of notes.", "They take it to the founder. He has notes. A lot of notes."),
    (27.0, "N", "But the room was never the company.", "But the room was never the company."),
    (30.3, "N", "There was no team.", "There was no team."),
    (33.0, "N", "Every role was an agent. One coordinator kept them in sync.", "Every role was an agent. One coordinator kept them in sync."),
    (36.3, "N", "The debate you watched was a group chat between agents.", "The debate was a group chat."),
    (40.3, "N", "The presenter was the deck agent, rebuilding the slide from founder notes.", "The presenter was the deck agent."),
    (44.3, "N", "Everyone here is an agent. Except the founder.", "Everyone here is an agent. Except the founder."),
    (48.3, "N", "One human. A whole agency. This is how Kneaded A.I. works.", None),  # caption suppressed; slate carries it
]

# Voiced debate (real audio, not captions-only). (anchor, dur, voice, vo, caption)
DIALOGUE = [
    (9.4,  3.2, "A", "Lead with the promise. Save five hours a week on local marketing.", "Lead with the promise: save five hours a week on local marketing."),
    (12.9, 3.4, "B", "No. Open on the pain. You're drowning in posts you don't have time to write.", "Open on the pain: you're drowning in posts you don't have time to write."),
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


def _fades(dur, fin, fout):
    f = []
    if fin:
        f.append("fade=t=in:st=0:d=0.6")
    if fout:
        f.append(f"fade=t=out:st={dur-0.6:.3f}:d=0.6")
    return f


def clip_shot(src, dur, fin, fout, out, ss=0, zoom=1.0, cx=0.5):
    sw, sh = int(W * zoom), int(H * zoom)
    fl = _fades(dur, fin, fout)
    vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H}:(in_w-{W})*{cx}:(in_h-{H})/2,setsar=1,fps={FPS},"
          f"tpad=stop_mode=clone:stop_duration=12,format=yuv420p")
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-ss", str(ss), "-i", str(src), "-an", "-vf", vf,
         "-t", str(dur), "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def still_shot(src, dur, motion, fin, fout, out):
    frames = int(dur * FPS)
    uw, uh = int(W * 1.5), int(H * 1.5)
    if motion == "out":
        z = "if(eq(on,0),1.10,max(zoom-0.0005,1.0))"
    else:
        z = "min(zoom+0.0005,1.10)"
    x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = (f"scale={uw}:{uh}:force_original_aspect_ratio=increase,"
          f"crop={uw}:{uh}:(in_w-{uw})/2:(in_h-{uh})/2,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
          f"setsar=1,fps={FPS},format=yuv420p")
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur),
         "-r", str(FPS), "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def screen_img(content, bg, dur, fin, fout, out):
    fl = ["format=yuv420p"] + _fades(dur, fin, fout)
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,"
        f"eq=brightness=-0.16:saturation=0.92,setsar=1,fps={FPS}[bg];"
        f"[1:v]scale={int(W*0.62)}:-2,setsar=1,fps={FPS}[c];"
        f"[bg][c]overlay=(W-w)/2:(H-h)/2-30,vignette=PI/5,"
        + ",".join(fl) + "[v]"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(bg),
         "-loop", "1", "-t", str(dur), "-i", str(content), "-filter_complex", fc,
         "-map", "[v]", "-t", str(dur), "-r", str(FPS), "-an", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(out)])


def diagram_img(src, dur, fin, fout, out):
    """Slow push-in on a full-frame diagram PNG (its bg already matches 0x0c0f14)."""
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
         "-r", str(FPS), "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def dissolve_shot(src, plate, dur, fin, fout, out, hold=1.4, xf=1.0):
    """Pixel-dissolve from a live clip to a matched empty-room plate (ghost table)."""
    t1 = hold + xf            # live portion length
    t2 = dur - hold           # plate portion length (output = t1 + t2 - xf = dur)
    fl = _fades(dur, fin, fout)
    post = ",".join(["format=yuv420p"] + fl) if fl else "format=yuv420p"
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,"
        f"trim=0:{t1:.3f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[a];"
        f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,"
        f"trim=0:{t2:.3f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[b];"
        f"[a][b]xfade=transition=pixelize:duration={xf:.3f}:offset={hold:.3f},"
        f"{post}[v]"
    )
    run(["ffmpeg", "-y", "-ss", "0.5", "-i", str(src), "-loop", "1", "-t", str(t2 + 1), "-i", str(plate),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), "-r", str(FPS),
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def overlayimg_shot(base, png, dur, fin, fout, out, ss=0, zoom=1.0, cx=0.5):
    """Live clip with a full-frame RGBA PNG overlay (chat panel / deck card)."""
    sw, sh = int(W * zoom), int(H * zoom)
    fl = _fades(dur, fin, fout)
    post = ",".join(["format=yuv420p"] + fl) if fl else "format=yuv420p"
    fc = (
        f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(in_w-{W})*{cx}:(in_h-{H})/2,setsar=1,fps={FPS},"
        f"tpad=stop_mode=clone:stop_duration=12[bg];"
        f"[1:v]scale={W}:{H},setsar=1[ov];"
        f"[bg][ov]overlay=0:0,{post}[v]"
    )
    run(["ffmpeg", "-y", "-ss", str(ss), "-i", str(base), "-loop", "1", "-t", str(dur), "-i", str(png),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), "-r", str(FPS),
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def make_slate(dur, fin, fout, out):
    t = WORK / "slate_title.txt"; t.write_text(SLATE_TITLE)
    c = WORK / "slate_cta.txt"; c.write_text(SLATE_CTA)
    # brighter text + gentler end-fade (t48 readability fix)
    vf = (f"format=yuv420p,"
          f"drawtext=fontfile={FONT}:textfile={t}:fontcolor=white:fontsize=70:x=(w-tw)/2:y=h/2-74,"
          f"drawtext=fontfile={FONT}:textfile={c}:fontcolor=0xE6E6E6:fontsize=36:x=(w-tw)/2:y=h/2+34")
    fl = []
    if fin:
        fl.append("fade=t=in:st=0:d=0.6")
    if fout:
        fl.append(f"fade=t=out:st={dur-0.5:.3f}:d=0.5")
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0c0f14:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def build_audio(total, placed, out):
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo"]
    for ev in placed:
        inputs += ["-i", str(ev["af"])]
    fc, labels = [], ["[0:a]"]
    for i, ev in enumerate(placed, start=1):
        ms = int(ev["start"] * 1000)
        fc.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(placed)+1}:normalize=0:dropout_transition=0[mix]")
    fc.append("[mix]loudnorm=I=-16:TP=-1.5:LRA=11[ao]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[ao]", "-t", f"{total}", "-c:a", "aac", "-b:a", "192k", str(out)])


def burn_captions(in_v, placed, out):
    chain = ["format=yuv420p"]
    for ev in placed:
        cap = ev["caption"]
        if not cap:
            continue
        cf = WORK / f"cap_{ev['idx']:02d}.txt"; cf.write_text(cap)
        start, end = ev["start"], ev["start"] + ev["dur"]
        if ev["voice"] == "N":   # narrator — bottom, white
            chain.append(
                f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=white:fontsize=46:"
                f"box=1:boxcolor=0x000000AA:boxborderw=18:"
                f"x=(w-tw)/2:y=h-170:enable='between(t,{start:.2f},{end:.2f})'")
        else:                    # voiced debate — higher, warm tint
            chain.append(
                f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=0xFFF1D6:fontsize=50:"
                f"box=1:boxcolor=0x000000B0:boxborderw=20:"
                f"x=(w-tw)/2:y=h-250:enable='between(t,{start:.2f},{end:.2f})'")
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
                clip_shot(s["src"], s["dur"], s["fin"], s["fout"], out,
                          ss=s.get("ss", 0), zoom=s.get("zoom", 1.0), cx=s.get("cx", 0.5))
            elif k == "screenimg":
                screen_img(s["src"], s["bg"], s["dur"], s["fin"], s["fout"], out)
            elif k == "stillimg":
                still_shot(s["src"], s["dur"], s.get("motion", "in"), s["fin"], s["fout"], out)
            elif k == "diagramimg":
                diagram_img(s["src"], s["dur"], s["fin"], s["fout"], out)
            elif k == "dissolve":
                dissolve_shot(s["src"], s["plate"], s["dur"], s["fin"], s["fout"], out)
            elif k == "overlayimg":
                overlayimg_shot(s["src"], s["ov"], s["dur"], s["fin"], s["fout"], out,
                                ss=s.get("ss", 0), zoom=s.get("zoom", 1.0), cx=s.get("cx", 0.5))
            elif k == "slate":
                make_slate(s["dur"], s["fin"], s["fout"], out)
            f.write(f"file '{out.as_posix()}'\n")
            total += s["dur"]

    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])

    # ---- audio: narrator + voiced debate, each with its own voice id ----
    sys.path.insert(0, str(ROOT))
    from video_claw import keys as vkeys
    for kk, vv in vkeys.load_keys().items():
        os.environ.setdefault(kk, vv)
    from video_claw import tts as vtts
    from video_claw.cache import Cache as VCache
    vcache = VCache(WORK)

    # unified event list, sorted by anchor
    events = []
    for (anchor, voice, vo, cap) in VO_LINES:
        events.append({"anchor": anchor, "voice": voice, "vo": vo, "caption": cap})
    for (anchor, _d, voice, vo, cap) in DIALOGUE:
        events.append({"anchor": anchor, "voice": voice, "vo": vo, "caption": cap})
    events.sort(key=lambda e: e["anchor"])

    placed, prev_end = [], 0.0
    for idx, e in enumerate(events):
        m4a, d = vtts.make_audio(e["vo"], idx, workdir=WORK, cache=vcache, tts_cfg={
            "provider": "elevenlabs", "voice_id": VOICES[e["voice"]],
            "model": "eleven_turbo_v2_5", "speaking_rate": 1.05})
        start = max(e["anchor"], prev_end + 0.15)
        placed.append({"idx": idx, "start": start, "dur": d, "af": m4a,
                       "voice": e["voice"], "caption": e["caption"]})
        prev_end = start + d

    audio = WORK / "audio.m4a"
    build_audio(total, placed, audio)
    captioned = WORK / "captioned.mp4"
    burn_captions(silent, placed, captioned)

    final = OUT / "v2.7.mp4"
    run(["ffmpeg", "-y", "-i", str(captioned), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest", str(final)])

    cues = sorted((p["start"], p["start"] + p["dur"], p["caption"])
                  for p in placed if p["caption"])
    srt = OUT / "v2.7.srt"
    with srt.open("w") as f:
        for i, (start, end, text) in enumerate(cues, start=1):
            f.write(f"{i}\n{_srt_ts(start)} --> {_srt_ts(end)}\n{text}\n\n")
    print("\nWROTE", final, f"(~{total:.0f}s)")

    # auto-stamp STATE.md
    subprocess.run([sys.executable, str(ROOT / "scripts" / "stamp_state.py"),
                    str(final), "review-room/v2.7/review_room_surprise_v2.7.py"], check=False)


if __name__ == "__main__":
    main()
