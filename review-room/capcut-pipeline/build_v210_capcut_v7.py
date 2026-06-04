#!/usr/bin/env python3
"""v2.10-capcut-v7 — rooms as RAW live+empty clips with CapCut dissolve transitions
(user's idea), plus the user's v6 hand-edits codified.

Rooms (replaces the baked reveal_*_from_live clips): each room = a brief LIVE clip (raw
source, full length = big handles per [[capcut-clip-handles]]) -> CapCut dissolve ->
empty Ken Burns clip that LINGERS. The dissolve doesn't shift segments (verified), so the
reveal block stays 12s and VO/music/captions stay aligned. The user drags the live/empty
ratio + edits transitions in CapCut. beat_05 also gets a dissolve into the hub -> its last
founder frame freezes into the bustling (the founder-freeze, for free).

Codified from v6 (read back):
  - captions: the user's re-authored SRT (v2.10_captions_user.srt) + their style.
  - music A: extended to 26.67 with a 0.67s fade-out (added via JSON audio_fade).
  - music B: entrance 38.0, source crop 3.07, vol 0.26.
  - bass: vol 10 (set via JSON; add-audio caps at 1.0).
  - room tones: vol 1.0.
Run with CapCut CLOSED. Snapshots draft_info.json after build as the diff baseline.
"""
import json, os, shutil, subprocess, uuid, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
RAWSRC = RR / "raw"
A210 = RR / "v2.10" / "assets"
RAW = RR / "v2.10" / "raw-export"
BEATS = RAW / "beats"
STEMS = RR / "output" / "stems-v2.9.1"
TPL = RR / "capcut-pipeline" / "template"
DRAFTS = Path(os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft"))
DEST = os.environ.get("DEST", "v2.10-capcut-v7")
CC = shutil.which("capcut-cli") or "capcut-cli"

# pre-reveal + post-reveal beats (rendered, exact length)
PRE = [(BEATS / "beat_01.mp4", 5.0), (BEATS / "beat_02.mp4", 4.5),
       (BEATS / "beat_03a.mp4", 3.5), (BEATS / "beat_03b.mp4", 3.5),
       (BEATS / "beat_04.mp4", 5.0), (BEATS / "beat_05.mp4", 4.5)]
POST = [(BEATS / "beat_07.mp4", 6.0), (BEATS / "beat_08.mp4", 5.4),
        (BEATS / "beat_09.mp4", 5.0), (BEATS / "beat_10.mp4", 4.0), (BEATS / "beat_11.mp4", 6.0)]
# reveal: (file, dur, is_live) — live = raw source (handles); empty = kenburns (lingers)
REVEAL = [
    (RAWSRC / "sample3_bustling_hub.mp4", 1.0, True),   (A210 / "kenburns_hub.mp4", 3.0, False),
    (RAWSRC / "sample5_real_debate.mp4", 1.0, True),    (A210 / "kenburns_debate.mp4", 2.75, False),
    (RAWSRC / "founder_motion.mp4", 1.0, True),         (A210 / "kenburns_meeting.mp4", 3.25, False),
]
MB_START, MB_SRC, MB_DUR, MB_VOL = 38.0, 3.07, 21.37, 0.26
MA_DUR, MA_FADEOUT = 26.67, 0.667
BASS_VOL = 10.0
CAP = dict(scale=0.4803929485184054, pos_y=-0.6940298507462686, font_size=13.0, text_size=30,
           line_spacing=0.02, color=[0.8666666746139526, 0.87058824300766, 0.8078431487083435],
           stroke_w=0.0599999986588955, uppercase=True,
           font_path="/Users/amirfish/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/"
                     "User Data/Cache/effect/7580216980498615553/76ee229e13aa7dc239426216a9008a8d/font.ttf",
           font_id="7580216980498615553")


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


def main():
    proj = DRAFTS / DEST
    if proj.exists():
        shutil.rmtree(proj)
    cc("init", DEST, "--template", str(TPL))

    t = 0.0
    diss = []  # segments that dissolve into the next
    for path, d in PRE:
        res = cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        t += d
    diss.append(res["segment_id"])  # beat_05 -> hub (founder freeze into bustling)
    for path, d, _is_live in REVEAL:
        res = cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        diss.append(res["segment_id"])
        t += d
    diss.pop()  # last empty (meeting) cuts to the diagram, no dissolve
    for path, d in POST:
        cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        t += d
    total = t
    for sid in diss:
        cc("transition", str(proj), sid, "dissolve", "--duration", 0.6)
    print(f"video: reveal = live+empty raw clips, {len(diss)} dissolves, total {total:.1f}s")

    # audio
    cc("add-audio", str(proj), str(RAW / "v2.10_vo_track.m4a"), 0, round(dur(RAW / "v2.10_vo_track.m4a"), 3), "--track-name", "VO", "--volume", "1.0")
    cc("add-audio", str(proj), str(STEMS / "music_A_suspense.mp3"), 0, MA_DUR, "--track-name", "music", "--volume", "0.8")
    bseg = cc("add-audio", str(proj), str(STEMS / "music_B_triumph.mp3"), MB_START, MB_DUR, "--track-name", "music", "--volume", str(MB_VOL))
    if bseg.get("segment_id"):
        cc("trim", str(proj), bseg["segment_id"], MB_SRC, MB_DUR)
    cc("add-audio", str(proj), str(A210 / "reveal_bass.wav"), 25.3, 13.0, "--track-name", "bass", "--volume", "1.0")
    for name, start in (("hub", 26.0), ("debate", 30.0), ("meeting", 34.0)):
        cc("add-audio", str(proj), str(A210 / f"roomtone_{name}.wav"), start, 4.0, "--track-name", "room tone", "--volume", "1.0")

    cc("import-srt", str(proj), str(RAW / "v2.10_captions_user.srt"), "--track-name", "captions")
    _post_json(proj)
    _finalize(proj)
    r = subprocess.run([CC, "lint", str(proj), "-H"], capture_output=True, text=True)
    print("lint:", (r.stdout or r.stderr).strip()[:300])
    subprocess.run([CC, "tracks", str(proj), "-H"])
    # snapshot the clean build as the diff baseline
    snap = RR / "v2.10" / "snapshots"; snap.mkdir(exist_ok=True)
    shutil.copy2(proj / "draft_info.json", snap / f"{DEST}_baseline.json")
    print(f"DONE -> {proj}\nbaseline snapshot -> {snap / (DEST + '_baseline.json')}")


def _post_json(proj):
    """Apply caption style, music-A fade-out, and bass vol>1 directly in draft_info.json."""
    for jf in proj.rglob("draft_info.json"):
        d = json.load(open(jf))
        mats = d["materials"]
        # caption style
        texts = {m["id"]: m for m in mats.get("texts", [])}
        for tr in d["tracks"]:
            if tr.get("type") == "text":
                for s in tr["segments"]:
                    cl = s.setdefault("clip", {})
                    cl["scale"] = {"x": CAP["scale"], "y": CAP["scale"]}
                    cl.setdefault("transform", {})["x"] = 0.0
                    cl["transform"]["y"] = CAP["pos_y"]
                    m = texts.get(s["material_id"])
                    if not m:
                        continue
                    m["font_size"] = CAP["font_size"]; m["text_size"] = CAP["text_size"]
                    m["line_spacing"] = CAP["line_spacing"]; m["font_path"] = CAP["font_path"]
                    try:
                        c = json.loads(m.get("content", "{}"))
                    except Exception:
                        c = {}
                    txt = (c.get("text", "") or "").upper() if CAP["uppercase"] else c.get("text", "")
                    c["text"] = txt
                    c["styles"] = [{"fill": {"content": {"solid": {"color": CAP["color"]}, "render_type": "solid"}},
                                    "range": [0, len(txt)],
                                    "strokes": [{"width": CAP["stroke_w"], "mode": 0, "content": {"solid": {"color": [0, 0, 0]}, "render_type": "solid"}}],
                                    "useLetterColor": True, "size": int(CAP["font_size"]),
                                    "font": {"path": CAP["font_path"], "id": CAP["font_id"]}}]
                    m["content"] = json.dumps(c, ensure_ascii=False)
        # music A fade-out + bass vol>1 (add-audio caps at 1.0)
        auds = {m["id"]: m for m in mats.get("audios", [])}
        fades = mats.setdefault("audio_fades", [])
        for tr in d["tracks"]:
            for s in tr.get("segments", []):
                mat = auds.get(s.get("material_id"))
                if not mat:
                    continue
                nm = (mat.get("material_name") or mat.get("path", "")).split("/")[-1] if mat.get("path") else (mat.get("material_name") or "")
                if "music_A" in nm:
                    fid = str(uuid.uuid4())
                    fades.append({"id": fid, "type": "audio_fade",
                                  "fade_in_duration": 0, "fade_out_duration": int(MA_FADEOUT * 1e6),
                                  "fade_type": 0})
                    s.setdefault("extra_material_refs", []).append(fid)
                elif "reveal_bass" in nm:
                    s["volume"] = BASS_VOL
        json.dump(d, open(jf, "w"), ensure_ascii=False)


def _finalize(proj):
    import copy
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
