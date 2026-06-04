#!/usr/bin/env python3
"""v2.10 — forked from v2.9.1. Adds a CapCut-pipeline RAW_EXPORT mode and is the home
for the v2.10 creative merge (Ken Burns turn, voice-swap debate, 3rd callback VO,
per-room tones — wired once review-room/v2.10/assets/ is populated).

Two modes (env MODE):
  MODE=final (default) — the normal captioned film with baked VO → output/v2.10.mp4.
  MODE=raw             — CapCut-owned-pipeline stems: a CLEAN picture master with
                         NO baked fades, NO baked captions, NO baked VO, PLUS a
                         separate VO-only track and an SRT. Reason (user architecture):
                         CapCut applies fades/speed itself, so baked fades stretch when
                         a clip's speed changes; and the video stem must be picture-only
                         so the supplied VO track doesn't double. Outputs →
                         review-room/v2.10/raw-export/ (clean master, per-beat raw clips,
                         vo_track.m4a, captions.srt).

Forked verbatim from v2.9.1 except: output names, RAW_EXPORT mode, and the v2.10
creative hooks marked `# v2.10:`.
"""
import os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
STILLS = RR / "v1" / "owned" / "stills"
SAMPLES = RR / "raw"
MOTION = RR / "v1" / "owned" / "motion"
A8 = RR / "v2.8" / "assets"
F271 = RR / "v2.7.1" / "assets"
A210 = RR / "v2.10" / "assets"            # v2.10: creative assets (subagent-produced)
WORK = RR / "v2.10" / "work"
CLIPS = WORK / "clips"
OUT = RR / "output"
RAWDIR = RR / "v2.10" / "raw-export"      # v2.10: CapCut-pipeline stems
for d in (WORK, CLIPS, OUT):
    d.mkdir(parents=True, exist_ok=True)

MODE = os.environ.get("MODE", "final").lower()
W, H, FPS = 1920, 1080, 30
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
ROOM = STILLS / "shot_05.png"
MINCAP = 2.2
VOICES = {"N": "cgSgspJ2msm6clMCkdW9", "A": "pNInz6obpgDQGcFmaJgB", "B": "21m00Tcm4TlvDq8ikWAM"}


def pick(a, b):
    return a if Path(a).exists() else b


SHOTS = [
    {"id": "01",  "kind": "clip",      "src": SAMPLES / "sample3_bustling_hub.mp4", "dur": 5,   "fin": False, "fout": False},
    {"id": "02",  "kind": "clip",      "src": SAMPLES / "sample5_real_debate.mp4",  "dur": 4.5, "fin": False, "fout": False},
    {"id": "03a", "kind": "clip",      "src": SAMPLES / "sample5_real_debate.mp4", "dur": 3.5, "ss": 0.3, "crop": (1067, 600, 300, 470), "fin": False, "fout": False},
    {"id": "03b", "kind": "clip",      "src": SAMPLES / "sample5_real_debate.mp4", "dur": 3.5, "ss": 0.7, "crop": (1067, 600, 760, 470), "fin": False, "fout": False},
    {"id": "04",  "kind": "screenimg", "src": A8 / "slide_tiein.png", "bg": ROOM, "dur": 5, "fin": False, "fout": False},
    {"id": "05",  "kind": "clip",      "src": SAMPLES / "founder_motion.mp4", "dur": 4.5, "ss": 0, "zoom": 1.12, "fin": False, "fout": False},
    # v2.10: turn = 3 empty rooms, slow Ken Burns + per-room tone, cross-dissolved (replaces
    # the turn3 dissolve + sub-bass stretch hack). per=4.5, xf=0.7 → 3*4.5-2*0.7 = 12.1s.
    {"id": "06",  "kind": "reveal3",   "clips": [A210 / "kenburns_hub.mp4", A210 / "kenburns_debate.mp4", A210 / "kenburns_meeting.mp4"], "per": 4.5, "xf": 0.7, "dur": 12.1, "fin": True, "fout": True},
    {"id": "07",  "kind": "clip",      "src": A8 / "diagram_anim.mp4", "dur": 6.0, "fin": True, "fout": True},
    {"id": "08",  "kind": "clip",      "src": A8 / "hero_chat.mp4", "dur": 5.4, "fin": True, "fout": True},
    {"id": "09",  "kind": "clip",      "src": A8 / "deck_montage.mp4", "dur": 5.0, "fin": True, "fout": True},
    {"id": "10",  "kind": "stillimg",  "src": F271 / "founder_labeled.png", "dur": 4, "motion": "in", "fin": False, "fout": False},
    {"id": "11",  "kind": "endcard",   "src": A8 / "endcard.png", "dur": 6, "fin": True, "fout": True},  # +2s so the final "Kneaded A.I." finishes (was cutting the "AY" tail)
]

VO_LINES = [
    (1.0,  "N", "An ordinary afternoon at Kneaded A.I.", "An ordinary afternoon at Kneaded.ai."),
    (5.3,  "N", "A local client needs their launch ad by tonight — and the team's stuck on the opening line.", "A client needs their launch ad — tonight."),
    (16.9, "N", "They merge the best of both into one line, and pitch it.", "They merge both into one line."),
    (21.9, "N", "They take it to the founder. He has notes. A lot of notes.", "They take it to the founder. He has notes. A lot of notes."),
    # v2.10: 3-room callback over the Ken Burns reveal (hub → debate → meeting); 3rd line is new.
    (26.8, "N", "But the room was never the company.", "But the room was never the company."),
    (30.6, "N", "There was no team.", "There was no team."),
    (34.6, "N", "And no one was ever in the meeting.", "And no one was ever in the meeting."),
    (38.5, "N", "Every job runs the same way: client request, agents, founder sign-off, delivered.", "Every job runs the same way."),
    (44.7, "N", "The debate? A run of agents — drafting, arguing, converging.", "The debate was a run of agents."),
    (49.9, "N", "The presenter? The deck agent — generating concepts at machine speed.", "The presenter was the deck agent."),
    (54.8, "N", "Everyone here is an agent. Except the founder.", "Everyone here is an agent. Except the founder."),
    (58.8, "N", "From brief to delivered — the same afternoon. That's Kneaded A.I.", None),
]
# v2.10: per-room ambience beds under the reveal (placed at each room's start, low gain).
ROOM_TONES = [
    (26.0, A210 / "roomtone_hub.wav",     0.40),
    (30.0, A210 / "roomtone_debate.wav",  0.40),
    (34.0, A210 / "roomtone_meeting.wav", 0.40),
]
# v2.10: voice-swap — line 1 now Rachel/female (over the visible woman), line 2 Adam/male
# (over the faceless hands cutaway). Was A,B in v2.9.1; swapped per user parking-lot note.
DIALOGUE = [
    (9.5,  3.5, "B", "Lead with the promise. Save five hours a week.", "Lead with the promise — save 5 hours a week.", None),
    (13.1, 2.9, "A", "No. Open on the pain. Hours lost to payments.", "Open on the pain — hours lost to payments.", None),
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


def clip_shot(src, dur, fin, fout, out, ss=0, zoom=1.0, cx=0.5, crop=None):
    fl = _fades(dur, fin, fout)
    if crop:
        cw, ch, cxp, cyp = crop
        vf = (f"crop={cw}:{ch}:{cxp}:{cyp},scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration=12,format=yuv420p")
    else:
        sw, sh = int(W * zoom), int(H * zoom)
        vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:(in_w-{W})*{cx}:(in_h-{H})/2,setsar=1,fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration=12,format=yuv420p")
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-ss", str(ss), "-i", str(src), "-an", "-vf", vf,
         "-t", str(dur), "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def still_shot(src, dur, motion, fin, fout, out):
    frames = int(dur * FPS); uw, uh = int(W * 1.5), int(H * 1.5)
    z = "min(zoom+0.0005,1.10)" if motion != "out" else "if(eq(on,0),1.10,max(zoom-0.0005,1.0))"
    vf = (f"scale={uw}:{uh}:force_original_aspect_ratio=increase,"
          f"crop={uw}:{uh}:(in_w-{uw})/2:(in_h-{uh})/2,"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"setsar=1,fps={FPS},format=yuv420p")
    fl = _fades(dur, fin, fout)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur), "-r", str(FPS),
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def endcard_shot(src, dur, fin, fout, out):
    fl = _fades(dur, fin, fout)
    vf = "scale=%d:%d,setsar=1,fps=%d,format=yuv420p" % (W, H, FPS)
    if fl:
        vf += "," + ",".join(fl)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", str(dur), "-r", str(FPS),
         "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def screen_img(content, bg, dur, fin, fout, out):
    fl = ["format=yuv420p"] + _fades(dur, fin, fout)
    fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,eq=brightness=-0.16:saturation=0.92,setsar=1,fps={FPS}[bg];"
          f"[1:v]scale={int(W*0.62)}:-2,setsar=1,fps={FPS}[c];"
          f"[bg][c]overlay=(W-w)/2:(H-h)/2-30,vignette=PI/5," + ",".join(fl) + "[v]")
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(bg), "-loop", "1", "-t", str(dur), "-i", str(content),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), "-r", str(FPS), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def turn3(src, plates, dur, fin, fout, out, xf=0.8):
    seg = (dur - xf) / 4.0
    fl = _fades(dur, fin, fout)
    post = ",".join(["format=yuv420p"] + fl) if fl else "format=yuv420p"
    def norm(idx, length):
        return (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,"
                f"trim=0:{length:.3f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p")
    L = seg + xf
    fc = (norm(0, L) + "[a0];" + norm(1, L) + "[a1];" + norm(2, L) + "[a2];" + norm(3, L) + "[a3];"
          + f"[a0][a1]xfade=transition=fade:duration={xf}:offset={seg:.3f}[x1];"
          + f"[x1][a2]xfade=transition=fade:duration={xf}:offset={2*seg:.3f}[x2];"
          + f"[x2][a3]xfade=transition=fade:duration={xf}:offset={3*seg:.3f}[xo];"
          + f"[xo]{post}[v]")
    run(["ffmpeg", "-y", "-ss", "0.5", "-i", str(src),
         "-loop", "1", "-t", str(L + 1), "-i", str(plates[0]),
         "-loop", "1", "-t", str(L + 1), "-i", str(plates[1]),
         "-loop", "1", "-t", str(L + 1), "-i", str(plates[2]),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), "-r", str(FPS),
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def reveal3(clips, per, xf, fin, fout, out):
    """v2.10 turn: cross-dissolve three Ken Burns room clips into one beat.
    Each clip plays `per` seconds; total = 3*per - 2*xf."""
    fl = _fades(3 * per - 2 * xf, fin, fout)
    post = ",".join(["format=yuv420p"] + fl) if fl else "format=yuv420p"
    def norm(i):
        return (f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,"
                f"trim=0:{per:.3f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p")
    o1 = per - xf; o2 = 2 * per - 2 * xf
    fc = (norm(0) + "[a0];" + norm(1) + "[a1];" + norm(2) + "[a2];"
          + f"[a0][a1]xfade=transition=fade:duration={xf}:offset={o1:.3f}[x1];"
          + f"[x1][a2]xfade=transition=fade:duration={xf}:offset={o2:.3f}[xo];"
          + f"[xo]{post}[v]")
    run(["ffmpeg", "-y", "-i", str(clips[0]), "-i", str(clips[1]), "-i", str(clips[2]),
         "-filter_complex", fc, "-map", "[v]", "-t", str(3 * per - 2 * xf), "-r", str(FPS),
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def build_audio(total, placed, out, loud=True):
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=stereo"]
    for ev in placed:
        inputs += ["-i", str(ev["af"])]
    fc, labels = [], ["[0:a]"]
    for i, ev in enumerate(placed, start=1):
        ms = int(ev["start"] * 1000)
        g = ev.get("gain")
        pre = f"volume={g}," if g is not None else ""
        fc.append(f"[{i}:a]{pre}adelay={ms}|{ms}[a{i}]"); labels.append(f"[a{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(placed)+1}:normalize=0:dropout_transition=0[mix]")
    if loud:
        fc.append("[mix]loudnorm=I=-16:TP=-1.5:LRA=11[ao]")
        omap = "[ao]"
    else:
        omap = "[mix]"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", omap, "-t", f"{total}",
         "-c:a", "aac", "-b:a", "192k", str(out)])


def caption_windows(placed):
    caps = sorted(((p["start"], p["dur"], p["caption"], p["voice"]) for p in placed if p["caption"]))
    out = []
    for i, (start, dur, text, voice) in enumerate(caps):
        nxt = caps[i + 1][0] if i + 1 < len(caps) else 1e9
        end = min(nxt - 0.10, start + max(dur, MINCAP)); end = max(end, start + min(dur, 1.0))
        out.append((start, end, text, voice))
    return out


def burn_captions(in_v, windows, out):
    chain = ["format=yuv420p"]
    for i, (start, end, text, voice) in enumerate(windows):
        cf = WORK / f"cap_{i:02d}.txt"; cf.write_text(text)
        if voice == "N":
            chain.append(f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=white:fontsize=46:box=1:boxcolor=0x000000AA:boxborderw=18:x=(w-tw)/2:y=h-170:enable='between(t,{start:.2f},{end:.2f})'")
        else:
            chain.append(f"drawtext=fontfile={FONT}:textfile={cf}:fontcolor=0xFFF1D6:fontsize=50:box=1:boxcolor=0x000000B0:boxborderw=20:x=(w-tw)/2:y=h-250:enable='between(t,{start:.2f},{end:.2f})'")
    run(["ffmpeg", "-y", "-i", str(in_v), "-vf", ",".join(chain), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


def _srt_ts(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60); ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def _write_srt(windows, path):
    with open(path, "w") as f:
        for i, (start, end, text, _v) in enumerate(windows, start=1):
            f.write(f"{i}\n{_srt_ts(start)} --> {_srt_ts(end)}\n{text}\n\n")


def build_beats(raw):
    """Render every beat clip. raw=True forces ALL fades off. Returns (listfile, total)."""
    listfile = WORK / ("concat_raw.txt" if raw else "concat.txt"); total = 0.0
    with listfile.open("w") as f:
        for s in SHOTS:
            fin = False if raw else s["fin"]
            fout = False if raw else s["fout"]
            out = CLIPS / f"beat_{s['id']}{'_raw' if raw else ''}.mp4"; k = s["kind"]
            if k == "clip":
                clip_shot(s["src"], s["dur"], fin, fout, out, ss=s.get("ss", 0), zoom=s.get("zoom", 1.0), cx=s.get("cx", 0.5), crop=s.get("crop"))
            elif k == "screenimg":
                screen_img(s["src"], s["bg"], s["dur"], fin, fout, out)
            elif k == "stillimg":
                still_shot(s["src"], s["dur"], s.get("motion", "in"), fin, fout, out)
            elif k == "endcard":
                endcard_shot(s["src"], s["dur"], fin, fout, out)
            elif k == "turn3":
                turn3(s["src"], s["plates"], s["dur"], fin, fout, out)
            elif k == "reveal3":
                reveal3(s["clips"], s["per"], s["xf"], fin, fout, out)
            f.write(f"file '{out.as_posix()}'\n"); total += s["dur"]
    return listfile, total


def place_vo():
    """TTS + place every VO/dialogue event. Returns (placed, total_shot_seconds)."""
    sys.path.insert(0, str(ROOT))
    from video_claw import keys as vkeys
    for kk, vv in vkeys.load_keys().items():
        os.environ.setdefault(kk, vv)
    from video_claw import tts as vtts
    from video_claw.cache import Cache as VCache
    vcache = VCache(WORK)
    events = [{"anchor": a, "voice": v, "vo": vo, "caption": c} for (a, v, vo, c) in VO_LINES]
    events += [{"anchor": a, "voice": v, "vo": vo, "caption": c, "afile": af} for (a, _d, v, vo, c, af) in DIALOGUE]
    events.sort(key=lambda e: e["anchor"])
    placed, prev_end = [], 0.0
    for idx, e in enumerate(events):
        if e.get("afile"):
            m4a = e["afile"]
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                      "-of", "csv=p=0", str(m4a)], capture_output=True, text=True).stdout.strip())
            start = e["anchor"]
        else:
            m4a, d = vtts.make_audio(e["vo"], idx, workdir=WORK, cache=vcache, tts_cfg={
                "provider": "elevenlabs", "voice_id": VOICES[e["voice"]], "model": "eleven_turbo_v2_5", "speaking_rate": 1.05})
            start = max(e["anchor"], prev_end + 0.15)
        placed.append({"idx": idx, "start": start, "dur": d, "af": m4a, "voice": e["voice"], "caption": e["caption"]})
        prev_end = start + d
    return placed


def export_raw():
    """CapCut-pipeline stems: clean fade-free picture-only master + per-beat raw clips
    + separate VO-only track + captions.srt. NOTHING baked (no fades/captions/VO)."""
    RAWDIR.mkdir(parents=True, exist_ok=True)
    beats_dir = RAWDIR / "beats"; beats_dir.mkdir(exist_ok=True)
    listfile, total = build_beats(raw=True)
    # clean picture-only master (no captions, no audio)
    master = RAWDIR / "v2.10_clean_master.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", str(master)])
    # copy per-beat raw clips out (for granular CapCut swapping)
    for s in SHOTS:
        src = CLIPS / f"beat_{s['id']}_raw.mp4"
        if src.exists():
            shutil.copy2(src, beats_dir / f"beat_{s['id']}.mp4")
    # separate VO-only track + SRT (picture stays VO-free)
    placed = place_vo()
    vo = RAWDIR / "v2.10_vo_track.m4a"; build_audio(total, placed, vo)
    windows = caption_windows(placed)
    _write_srt(windows, RAWDIR / "v2.10_captions.srt")
    # manifest
    (RAWDIR / "README_raw_export.md").write_text(
        "# v2.10 RAW EXPORT (CapCut-owned pipeline stems)\n\n"
        f"- `v2.10_clean_master.mp4` — picture only, {total:.1f}s, NO fades / NO captions / NO VO.\n"
        "- `beats/beat_XX.mp4` — per-beat raw clips (fade-free) for granular swapping.\n"
        "- `v2.10_vo_track.m4a` — VO-only audio track (place on its own CapCut track).\n"
        "- `v2.10_captions.srt` — import as a CapCut subtitle track.\n\n"
        "Apply fades + speed + music IN CapCut so they're speed-independent. Bundle any\n"
        "swapped clip inside the project's Resources/import/ (CapCut sandbox rule).\n")
    print(f"\nRAW EXPORT -> {RAWDIR} (master {total:.1f}s, {len(placed)} VO events)")


def export_final():
    listfile, total = build_beats(raw=False)
    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)])
    placed = place_vo()
    # v2.10: add per-room ambience beds (low gain) under the reveal
    for anchor, f, gain in ROOM_TONES:
        if Path(f).exists():
            placed.append({"start": anchor, "af": f, "gain": gain, "caption": None, "voice": "BED", "dur": 0})
    audio = WORK / "audio.m4a"; build_audio(total, placed, audio)
    windows = caption_windows(placed)
    captioned = WORK / "captioned.mp4"; burn_captions(silent, windows, captioned)
    final = OUT / "v2.10.mp4"
    run(["ffmpeg", "-y", "-i", str(captioned), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", str(final)])
    _write_srt(windows, OUT / "v2.10.srt")
    print("\nWROTE", final, f"(~{total:.0f}s)")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "stamp_state.py"), str(final),
                    "review-room/v2.10/review_room_surprise_v2.10.py"], check=False)


def main():
    if MODE == "raw":
        export_raw()
    else:
        export_final()


if __name__ == "__main__":
    main()
