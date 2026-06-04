#!/usr/bin/env python3
"""v2.10-capcut-v3 — the CODIFIED build folding in the user's revisions + the reveal move.

Over v2:
  1. REVEAL ENTRY (user task 1): the hub room is now `reveal_hub_from_live.mp4` — the live
     bustling hub dissolves into the empty hub (the v2.9.1/0603 "part 1 -> part 2" move),
     trimmed to 4.0s so the reveal block stays 12s (no downstream re-sync needed).
  2. VIBRANT MUSIC (user edit): music B (triumph) enters EARLY at 35.5s with a ~2.8s
     FADE-IN (two volume keyframes), leading into the diagram — was a hard cut at 38.
  3. ROOM TONES louder (user cranked them up in v2): 0.4 -> 1.0.

NOT here (needs the render, not CapCut): the user's 0.5x DEBATE slow-mo. capcut-cli `speed`
does NOT ripple downstream, so a clean slow-mo must be baked into the assembler (re-renders
the vo_track in sync). Tracked as the next step.
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
DEST = "v2.10-capcut-v3"
CC = shutil.which("capcut-cli") or "capcut-cli"

# reveal hub = live->empty dissolve clip (trimmed to 4.0 to hold the 12s reveal block)
VIDEO = [
    (BEATS / "beat_01.mp4", 5.0, None),
    (BEATS / "beat_02.mp4", 4.5, None),
    (BEATS / "beat_03a.mp4", 3.5, None),
    (BEATS / "beat_03b.mp4", 3.5, None),
    (BEATS / "beat_04.mp4", 5.0, None),
    (BEATS / "beat_05.mp4", 4.5, None),
    (A210 / "reveal_hub_from_live.mp4", 4.0, "room"),   # live -> empty dissolve
    (A210 / "kenburns_debate.mp4", 4.0, "room"),
    (A210 / "kenburns_meeting.mp4", 4.0, "room"),
    (BEATS / "beat_07.mp4", 6.0, None),
    (BEATS / "beat_08.mp4", 5.4, None),
    (BEATS / "beat_09.mp4", 5.0, None),
    (BEATS / "beat_10.mp4", 4.0, None),
    (BEATS / "beat_11.mp4", 4.0, None),
]
MUSIC_B_START, MUSIC_B_FADE = 35.5, 2.8
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
    rooms = []
    for path, d, kind in VIDEO:
        res = cc("add-video", str(proj), str(path), round(t, 3), d, "--track-name", "video")
        # fade-in on the 2nd/3rd rooms (kenburns); hub already has the baked dissolve
        if kind == "room" and "kenburns" in path.name and res.get("segment_id"):
            rooms.append(res["segment_id"])
        t += d
    total = t
    for sid in rooms:
        cc("image-anim", str(proj), sid, "--intro", "fade-in", "--intro-duration", 1.0)
    print(f"video: {len(VIDEO)} beats incl. live->empty reveal, total {total:.1f}s")

    # VO (full, synced) + music + room tones
    cc("add-audio", str(proj), str(RAW / "v2.10_vo_track.m4a"), 0, round(dur(RAW / "v2.10_vo_track.m4a"), 3), "--track-name", "VO", "--volume", "1.0")
    cc("add-audio", str(proj), str(STEMS / "music_A_suspense.mp3"), 0, 26.0, "--track-name", "music", "--volume", "0.8")
    bseg = cc("add-audio", str(proj), str(STEMS / "music_B_triumph.mp3"), MUSIC_B_START, round(total - MUSIC_B_START, 3), "--track-name", "music", "--volume", "0.85")
    # vibrant-music fade-IN: two volume keyframes (relative to the segment start)
    if bseg.get("segment_id"):
        cc("keyframe", str(proj), bseg["segment_id"], "volume", 0.0, "0%")
        cc("keyframe", str(proj), bseg["segment_id"], "volume", MUSIC_B_FADE, "85%")
    for name, start in (("hub", 26.0), ("debate", 30.0), ("meeting", 34.0)):
        cc("add-audio", str(proj), str(A210 / f"roomtone_{name}.wav"), start, 4.0, "--track-name", "room tone", "--volume", str(ROOM_TONE_VOL))

    _finalize(proj)
    r = subprocess.run([CC, "lint", str(proj), "-H"], capture_output=True, text=True)
    print("lint:", (r.stdout or r.stderr).strip())
    subprocess.run([CC, "tracks", str(proj), "-H"])
    print("DONE ->", proj)


def _finalize(proj):
    import uuid, copy
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
