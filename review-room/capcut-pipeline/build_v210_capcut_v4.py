#!/usr/bin/env python3
"""v2.10-capcut-v4 — folds in the user's round-2 feedback (all codified):
  1) reveal dissolves for ALL THREE rooms (live -> empty): hub=sample3, debate=sample5,
     meeting=founder_motion (the founder review IS the meeting — people vanish from the table).
  2) music B cropped to start at SOURCE 6.133s (not 0) + 2.8s fade-in, at 35.5s.
  3) reveal sub-bass drone (reveal_bass.wav) under the turn so it doesn't feel empty.
  4) (debate slow-mo left out — was only a face/voice-match compromise; can re-add.)
  5) VO ending fixed: endcard +2s and last line moved to 58.8 so "Kneaded A.I." finishes
     (regenerated beats + vo_track; film now ~64.4s).
Room tones louder (1.0). Built fresh via capcut-cli init + add-*; media bundled inside.
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
DEST = "v2.10-capcut-v4"
CC = shutil.which("capcut-cli") or "capcut-cli"

VIDEO = [
    (BEATS / "beat_01.mp4", 5.0, None),
    (BEATS / "beat_02.mp4", 4.5, None),
    (BEATS / "beat_03a.mp4", 3.5, None),
    (BEATS / "beat_03b.mp4", 3.5, None),
    (BEATS / "beat_04.mp4", 5.0, None),
    (BEATS / "beat_05.mp4", 4.5, None),
    (A210 / "reveal_hub_from_live.mp4", 4.0, "dissolve"),      # live bustling -> empty hub
    (A210 / "reveal_debate_from_live.mp4", 4.0, "dissolve"),   # live debate -> empty table
    (A210 / "reveal_meeting_from_live.mp4", 4.0, "dissolve"),  # founder review -> empty meeting
    (BEATS / "beat_07.mp4", 6.0, None),
    (BEATS / "beat_08.mp4", 5.4, None),
    (BEATS / "beat_09.mp4", 5.0, None),
    (BEATS / "beat_10.mp4", 4.0, None),
    (BEATS / "beat_11.mp4", 6.0, None),    # endcard extended so final "A.I." finishes
]
MB_START, MB_SRC, MB_DUR, MB_FADE = 35.5, 6.133, 18.3, 2.8   # user's music crop
BASS_START, BASS_DUR, BASS_VOL = 25.3, 13.0, 0.55
ROOM_TONE_VOL = 1.0


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
    fades = []
    for path, d, kind in VIDEO:
        res = cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        if kind == "fade" and res.get("segment_id"):
            fades.append(res["segment_id"])
        t += d
    total = t
    for sid in fades:
        cc("image-anim", str(proj), sid, "--intro", "fade-in", "--intro-duration", 1.0)
    print(f"video: {len(VIDEO)} beats (hub+debate dissolves), total {total:.1f}s")

    # VO (full, fixed ending)
    cc("add-audio", str(proj), str(RAW / "v2.10_vo_track.m4a"), 0, round(dur(RAW / "v2.10_vo_track.m4a"), 3), "--track-name", "VO", "--volume", "1.0")
    # music A then vibrant B (cropped to source 6.133 + fade-in)
    cc("add-audio", str(proj), str(STEMS / "music_A_suspense.mp3"), 0, 26.0, "--track-name", "music", "--volume", "0.8")
    bseg = cc("add-audio", str(proj), str(STEMS / "music_B_triumph.mp3"), MB_START, MB_DUR, "--track-name", "music", "--volume", "0.85")
    if bseg.get("segment_id"):
        cc("trim", str(proj), bseg["segment_id"], MB_SRC, MB_DUR)          # start from source 6.133s
        cc("keyframe", str(proj), bseg["segment_id"], "volume", 0.0, "0%")
        cc("keyframe", str(proj), bseg["segment_id"], "volume", MB_FADE, "85%")
    # reveal sub-bass drone (fills the empty rooms)
    cc("add-audio", str(proj), str(A210 / "reveal_bass.wav"), BASS_START, BASS_DUR, "--track-name", "bass", "--volume", str(BASS_VOL))
    # per-room tones (louder)
    for name, start in (("hub", 26.0), ("debate", 30.0), ("meeting", 34.0)):
        cc("add-audio", str(proj), str(A210 / f"roomtone_{name}.wav"), start, 4.0, "--track-name", "room tone", "--volume", str(ROOM_TONE_VOL))

    # captions: import our exact SRT (our text + timing) as a real subtitle track.
    # NB: import-srt re-stamps draft_info.id; _finalize() restores it to the media-placeholder id.
    cc("import-srt", str(proj), str(RAW / "v2.10_captions.srt"), "--track-name", "captions")

    _finalize(proj)
    r = subprocess.run([CC, "lint", str(proj), "-H"], capture_output=True, text=True)
    print("lint:", (r.stdout or r.stderr).strip())
    subprocess.run([CC, "tracks", str(proj), "-H"])
    print("DONE ->", proj)


def _finalize(proj):
    import uuid, copy, re
    # 1) restore draft_info.id to the id the media placeholders use (import-srt/others
    #    may have re-stamped it, which breaks ##_draftpath_placeholder_<id>_## resolution).
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
