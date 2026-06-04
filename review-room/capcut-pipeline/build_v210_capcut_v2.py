#!/usr/bin/env python3
"""v2.10-capcut-v2 — same as build_v210_capcut.py but the REVEAL ships as 3 SEPARATE
room segments (kenburns_hub/debate/meeting) each with a fade-in, so the 3 empty rooms
have 0603-style soft fade-ins AND per-room control in CapCut (the user asked for this).

The whole video track is the per-beat raw clips (fade-free) so every beat is independently
editable; the baked-reveal beat_06 is replaced by the 3 room clips. Audio layout matches
v1 (clean timing). Uses image-anim --intro fade-in (timing-safe; does NOT shorten the
segment the way a transition would, so audio stays in sync). Leaves the user's project
v2.10-capcut untouched.
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
DEST = "v2.10-capcut-v2"
CC = shutil.which("capcut-cli") or "capcut-cli"

# video beats in order; reveal beat_06 -> 3 separate room clips (marked room=True)
VIDEO = [
    (BEATS / "beat_01.mp4", 5.0, False),
    (BEATS / "beat_02.mp4", 4.5, False),
    (BEATS / "beat_03a.mp4", 3.5, False),
    (BEATS / "beat_03b.mp4", 3.5, False),
    (BEATS / "beat_04.mp4", 5.0, False),
    (BEATS / "beat_05.mp4", 4.5, False),
    (A210 / "kenburns_hub.mp4", 4.0, True),
    (A210 / "kenburns_debate.mp4", 4.0, True),
    (A210 / "kenburns_meeting.mp4", 4.0, True),
    (BEATS / "beat_07.mp4", 6.0, False),
    (BEATS / "beat_08.mp4", 5.4, False),
    (BEATS / "beat_09.mp4", 5.0, False),
    (BEATS / "beat_10.mp4", 4.0, False),
    (BEATS / "beat_11.mp4", 4.0, False),
]
FADE = 1.0  # per-room fade-in seconds


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


def cc(*args):
    r = subprocess.run([CC, *map(str, args)], capture_output=True, text=True)
    if r.returncode == 2:
        print(f"!! {args[0]} exit 2: {(r.stderr or r.stdout).strip()[:200]}"); raise SystemExit(1)
    try:
        return json.loads(r.stdout)
    except Exception:
        print(f"  + {args[0]}: {(r.stdout or r.stderr).strip()[:90]}"); return {}


def main():
    proj = DRAFTS / DEST
    if proj.exists():
        shutil.rmtree(proj)
    cc("init", DEST, "--template", str(TPL))

    # video track (add-video copies each clip into the project's assets/ — sandbox-safe)
    t = 0.0
    room_segs = []
    for path, d, is_room in VIDEO:
        res = cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        if is_room and res.get("segment_id"):
            room_segs.append(res["segment_id"])
        t += d
    total = t
    # fade-in on each room (timing-safe intro animation)
    for sid in room_segs:
        cc("image-anim", str(proj), sid, "--intro", "fade-in", "--intro-duration", FADE)
    print(f"video: {len(VIDEO)} beats, {len(room_segs)} room fade-ins, total {total:.1f}s")

    # audio: VO + music A/B + room tones (clean timing)
    cc("add-audio", str(proj), str(RAW / "v2.10_vo_track.m4a"), 0, round(dur(RAW / "v2.10_vo_track.m4a"), 3), "--track-name", "VO", "--volume", "1.0")
    cc("add-audio", str(proj), str(STEMS / "music_A_suspense.mp3"), 0, 26.0, "--track-name", "music", "--volume", "0.8")
    cc("add-audio", str(proj), str(STEMS / "music_B_triumph.mp3"), 38.0, round(total - 38.0, 3), "--track-name", "music", "--volume", "0.85")
    for name, start in (("hub", 26.0), ("debate", 30.0), ("meeting", 34.0)):
        cc("add-audio", str(proj), str(A210 / f"roomtone_{name}.wav"), start, 4.0, "--track-name", "room tone", "--volume", "0.4")

    _finalize(proj)
    r = subprocess.run([CC, "lint", str(proj), "-H"], capture_output=True, text=True)
    print("lint:", (r.stdout or r.stderr).strip())
    subprocess.run([CC, "tracks", str(proj), "-H"])
    print("DONE ->", proj)


def _finalize(proj):
    import uuid, copy
    new_id = str(uuid.uuid4()).upper()
    mp = proj / "draft_meta_info.json"
    m = json.load(open(mp)); m["draft_id"] = new_id; m["draft_name"] = proj.name; m["draft_fold_path"] = str(proj)
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
    print("registered", proj.name, "id", new_id)


if __name__ == "__main__":
    main()
