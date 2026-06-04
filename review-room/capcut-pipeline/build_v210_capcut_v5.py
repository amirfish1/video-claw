#!/usr/bin/env python3
"""v2.10-capcut-v5 — round-3 feedback, all codified.

Over v4:
  1) FOUNDER -> BUSTLING dissolve entry into the reveal (reveal_hub_from_live.mp4 now
     leads with ~0.5s more founder, then dissolves to the bustling callback, then to the
     empty hub). Reveal block kept at 12s (hub 4.5 + debate 3.75 + meeting 3.75) so the
     VO/music/room-tone timing doesn't drift.
  2) ENERGETIC MUSIC: cropped to source 6.133 (user's crop) via trim, NO fade keyframe and
     NOT baked — the user adds the fade natively in CapCut (keeps flexibility). The earlier
     capcut-cli volume keyframe didn't ramp in CapCut, which muted B; dropping it avoids that.
  3) CAPTION STYLE from the user's hand-styled cue applied to ALL captions: scale 0.48,
     lower-third (y -0.694), font size 13 (CapCut font), warm off-white + thin black
     stroke, UPPERCASE. (read back via read_project / draft_info.json.)

Build IMPORTANT: close CapCut before running (it auto-saves and races capcut-cli writes).
"""
import json, os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
A210 = RR / "v2.10" / "assets"
RAW = RR / "v2.10" / "raw-export"
BEATS = RAW / "beats"
STEMS = RR / "output" / "stems-v2.9.1"
TPL = RR / "capcut-pipeline" / "template"
DRAFTS = Path(os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft"))
DEST = "v2.10-capcut-v5"
CC = shutil.which("capcut-cli") or "capcut-cli"

VIDEO = [
    (BEATS / "beat_01.mp4", 5.0, None),
    (BEATS / "beat_02.mp4", 4.5, None),
    (BEATS / "beat_03a.mp4", 3.5, None),
    (BEATS / "beat_03b.mp4", 3.5, None),
    (BEATS / "beat_04.mp4", 5.0, None),
    (BEATS / "beat_05.mp4", 4.5, None),
    (A210 / "reveal_hub_from_live.mp4", 4.5, None),       # founder->bustling->empty
    (A210 / "reveal_debate_from_live.mp4", 3.75, None),   # live debate -> empty
    (A210 / "reveal_meeting_from_live.mp4", 3.75, None),  # founder review -> empty
    (BEATS / "beat_07.mp4", 6.0, None),
    (BEATS / "beat_08.mp4", 5.4, None),
    (BEATS / "beat_09.mp4", 5.0, None),
    (BEATS / "beat_10.mp4", 4.0, None),
    (BEATS / "beat_11.mp4", 6.0, None),
]
MB_START, MB_SRC, MB_DUR = 35.5, 6.133, 18.3   # energetic music: timeline start, source crop, length
BASS_START, BASS_DUR, BASS_VOL = 25.3, 13.0, 0.55
ROOM_TONE_VOL = 1.0

# caption style read back from the user's hand-styled cue (v4 "Open on the pain")
CAP = dict(
    scale=0.4803929485184054, pos_y=-0.6940298507462686,
    font_size=13.0, text_size=30, line_spacing=0.02,
    color=[0.8666666746139526, 0.87058824300766, 0.8078431487083435],
    stroke_w=0.0599999986588955,
    font_path="/Users/amirfish/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/"
              "User Data/Cache/effect/7580216980498615553/76ee229e13aa7dc239426216a9008a8d/font.ttf",
    font_id="7580216980498615553", uppercase=True,
)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


def cc(*args):
    r = subprocess.run([CC, *map(str, args)], capture_output=True, text=True)
    if r.returncode == 2:
        print(f"!! {args[0]} exit2: {(r.stderr or r.stdout).strip()[:200]}"); raise SystemExit(1)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def style_captions(proj):
    """Apply the user's caption style to every cue in the captions track."""
    jf = proj / "draft_info.json"
    d = json.load(open(jf))
    texts = {m["id"]: m for m in d["materials"].get("texts", [])}
    n = 0
    for tr in d["tracks"]:
        if tr.get("type") != "text":
            continue
        for s in tr["segments"]:
            clip = s.setdefault("clip", {})
            clip["scale"] = {"x": CAP["scale"], "y": CAP["scale"]}
            clip.setdefault("transform", {})["x"] = 0.0
            clip["transform"]["y"] = CAP["pos_y"]
            mat = texts.get(s["material_id"])
            if not mat:
                continue
            mat["font_size"] = CAP["font_size"]
            mat["text_size"] = CAP["text_size"]
            mat["line_spacing"] = CAP["line_spacing"]
            mat["font_path"] = CAP["font_path"]
            try:
                c = json.loads(mat.get("content", "{}"))
            except Exception:
                c = {}
            txt = c.get("text", "")
            if CAP["uppercase"]:
                txt = txt.upper()
            c["text"] = txt
            c["styles"] = [{
                "fill": {"content": {"solid": {"color": CAP["color"]}, "render_type": "solid"}},
                "range": [0, len(txt)],
                "strokes": [{"width": CAP["stroke_w"], "mode": 0,
                             "content": {"solid": {"color": [0, 0, 0]}, "render_type": "solid"}}],
                "useLetterColor": True, "size": int(CAP["font_size"]),
                "font": {"path": CAP["font_path"], "id": CAP["font_id"]},
            }]
            mat["content"] = json.dumps(c, ensure_ascii=False)
            n += 1
    json.dump(d, open(jf, "w"), ensure_ascii=False)
    print(f"styled {n} captions")


def main():
    proj = DRAFTS / DEST
    if proj.exists():
        shutil.rmtree(proj)
    cc("init", DEST, "--template", str(TPL))

    t = 0.0
    for path, d, _ in VIDEO:
        cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        t += d
    total = t
    print(f"video: {len(VIDEO)} beats (founder->bustling entry), total {total:.1f}s")

    cc("add-audio", str(proj), str(RAW / "v2.10_vo_track.m4a"), 0, round(dur(RAW / "v2.10_vo_track.m4a"), 3), "--track-name", "VO", "--volume", "1.0")
    cc("add-audio", str(proj), str(STEMS / "music_A_suspense.mp3"), 0, 26.0, "--track-name", "music", "--volume", "0.8")
    # energetic music: cropped to source 6.133 (user's crop), NO fade/keyframe — user adds the
    # fade natively in CapCut (keeps flexibility; capcut-cli volume keyframes don't ramp -> muted).
    bseg = cc("add-audio", str(proj), str(STEMS / "music_B_triumph.mp3"), MB_START, MB_DUR, "--track-name", "music", "--volume", "0.85")
    if bseg.get("segment_id"):
        cc("trim", str(proj), bseg["segment_id"], MB_SRC, MB_DUR)
    cc("add-audio", str(proj), str(A210 / "reveal_bass.wav"), BASS_START, BASS_DUR, "--track-name", "bass", "--volume", str(BASS_VOL))
    for name, start in (("hub", 26.0), ("debate", 30.0), ("meeting", 34.0)):
        cc("add-audio", str(proj), str(A210 / f"roomtone_{name}.wav"), start, 4.0, "--track-name", "room tone", "--volume", str(ROOM_TONE_VOL))

    cc("import-srt", str(proj), str(RAW / "v2.10_captions.srt"), "--track-name", "captions")
    style_captions(proj)
    _finalize(proj)
    r = subprocess.run([CC, "lint", str(proj), "-H"], capture_output=True, text=True)
    print("lint:", (r.stdout or r.stderr).strip()[:400])
    subprocess.run([CC, "tracks", str(proj), "-H"])
    print("DONE ->", proj)


def _finalize(proj):
    import uuid, copy, re
    ph = None
    for jf in proj.rglob("draft_info.json"):
        d = json.load(open(jf))
        if ph is None:
            for cat in d.get("materials", {}).values():
                for m in (cat or []):
                    mm = re.search(r"placeholder_([0-9A-Fa-f-]+)_", str(m.get("path", "")))
                    if mm:
                        ph = mm.group(1); break
                if ph:
                    break
        if ph and d.get("id") != ph:
            d["id"] = ph
            json.dump(d, open(jf, "w"), ensure_ascii=False)
    new_id = str(uuid.uuid4()).upper()
    mp = proj / "draft_meta_info.json"
    m = json.load(open(mp)); m.update({"draft_id": new_id, "draft_name": proj.name, "draft_fold_path": str(proj)})
    json.dump(m, open(mp, "w"), ensure_ascii=False)
    rp = DRAFTS / "root_meta_info.json"
    if not rp.exists():
        return
    shutil.copy2(rp, str(rp) + ".bak")
    r = json.load(open(rp)); store = r.setdefault("all_draft_store", [])
    store[:] = [e for e in store if e.get("draft_name") != proj.name]
    ne = copy.deepcopy(store[0]) if store else {}
    ne.update({"draft_name": proj.name, "draft_id": new_id, "draft_fold_path": str(proj),
               "draft_json_file": str(proj / "draft_info.json"), "draft_cover": str(proj / "draft_cover.jpg")})
    store.append(ne)
    json.dump(r, open(rp, "w"), ensure_ascii=False)
    print("registered", proj.name, new_id)


if __name__ == "__main__":
    main()
