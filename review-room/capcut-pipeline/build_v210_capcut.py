#!/usr/bin/env python3
"""Build v2.10 as a fresh CapCut project (capcut-cli init + add-video/add-audio).

Uses only tested write commands (no fragile segment surgery on a 0603 clone). All media
is bundled inside the project's Resources/import/ (CapCut sandbox rule — external paths
won't open). Layout mirrors the user's 0603 intent, retimed for v2.10:
  - video : v2.10 clean master, full 62.4s, 1:1 (NO slow-mo — the Ken Burns reveal is
            natively ~12s, replacing the 0603 0.36x stretch hack).
  - VO    : v2.10 vo_track (perfectly synced to the v2.10 picture), full length.
  - music : A (suspense) 0 -> ~26 (out by the reveal); SILENCE ~26-38; B (triumph)
            38 -> end. User slides to taste.
  - tone  : per-room ambience under the reveal (hub 26 / debate 30 / meeting 34),
            filling the music gap (replaces the sub-bass hack).
Captions: import `raw-export/v2.10_captions.srt` in CapCut (File > captions) — left manual.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RR = ROOT / "review-room"
A210 = RR / "v2.10" / "assets"
RAW = RR / "v2.10" / "raw-export"
STEMS = RR / "output" / "stems-v2.9.1"
TPL = RR / "capcut-pipeline" / "template"            # in-repo template (init fallback)
DRAFTS = Path(os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft"))
DEST = "v2.10-capcut"
CC = shutil.which("capcut-cli") or "capcut-cli"


def dur(p):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True).stdout.strip())


def cc(*args):
    r = subprocess.run([CC, *map(str, args)], capture_output=True, text=True)
    tag = " ".join(str(a) for a in args[:2])
    if r.returncode not in (0, 1):  # 0 ok, 1 = warnings (lint); 2 = error
        print(f"!! capcut-cli {tag} exit {r.returncode}: {(r.stderr or r.stdout).strip()[:300]}")
        raise SystemExit(1)
    print(f"  + {tag}: {(r.stdout or r.stderr).strip()[:120]}")
    return r


def main():
    proj = DRAFTS / DEST
    if proj.exists():
        shutil.rmtree(proj)
    # fresh empty project (use the in-repo template explicitly — survives node_modules wipes)
    cc("init", DEST, "--template", str(TPL))

    imp = proj / "Resources" / "import"
    imp.mkdir(parents=True, exist_ok=True)

    master = RAW / "v2.10_clean_master.mp4"
    vo = RAW / "v2.10_vo_track.m4a"
    music_a = STEMS / "music_A_suspense.mp3"
    music_b = STEMS / "music_B_triumph.mp3"
    tones = [("hub", 26.0), ("debate", 30.0), ("meeting", 34.0)]

    def bundle(src):
        d = imp / Path(src).name
        shutil.copy2(src, d)
        return d

    bmaster, bvo = bundle(master), bundle(vo)
    bma, bmb = bundle(music_a), bundle(music_b)
    btones = {name: bundle(A210 / f"roomtone_{name}.wav") for name, _ in tones}

    md, vd = dur(bmaster), dur(bvo)
    print(f"master {md:.2f}s  vo {vd:.2f}s")

    # video track
    cc("add-video", proj, bmaster, 0, round(md, 3), "--track-name", "video")
    # VO track
    cc("add-audio", proj, bvo, 0, round(vd, 3), "--track-name", "VO", "--volume", "1.0")
    # music: A out by the reveal (~26), B from the diagram (~38) to end
    cc("add-audio", proj, bma, 0, 26.0, "--track-name", "music", "--volume", "0.8")
    cc("add-audio", proj, bmb, 38.0, round(md - 38.0, 3), "--track-name", "music", "--volume", "0.85")
    # per-room tones under the reveal (fills the 26-38 music gap)
    for name, start in tones:
        cc("add-audio", proj, btones[name], start, 4.0, "--track-name", "room tone", "--volume", "0.4")

    _finalize(proj)
    # verify
    cc("lint", proj, "-H")
    print("\nTRACKS:"); subprocess.run([CC, "tracks", str(proj), "-H"])
    print("\nDONE ->", proj, "\nOpen 'v2.10-capcut' in CapCut. Import captions from",
          RAW / "v2.10_captions.srt")


def _finalize(proj):
    """Give the project a UNIQUE draft_meta_info.draft_id (the template's is shared) and
    register it in root_meta_info so CapCut lists it. IMPORTANT: do NOT touch
    draft_info.json's `id` — add-video/add-audio key their `##_draftpath_placeholder_<id>_##`
    media paths to it; changing it breaks media resolution."""
    import uuid, copy
    new_id = str(uuid.uuid4()).upper()
    mp = proj / "draft_meta_info.json"
    m = json.load(open(mp))
    m["draft_id"] = new_id
    m["draft_name"] = proj.name
    m["draft_fold_path"] = str(proj)
    json.dump(m, open(mp, "w"), ensure_ascii=False)
    rp = DRAFTS / "root_meta_info.json"
    if not rp.exists():
        print("WARN: no root_meta_info.json — CapCut may not list the project."); return
    shutil.copy2(rp, str(rp) + ".bak")
    r = json.load(open(rp))
    store = r.setdefault("all_draft_store", [])
    store[:] = [e for e in store if e.get("draft_name") != proj.name]  # de-dup re-runs
    ne = copy.deepcopy(store[0]) if store else {}
    ne["draft_name"] = proj.name
    ne["draft_id"] = new_id
    ne["draft_fold_path"] = str(proj)
    ne["draft_json_file"] = str(proj / "draft_info.json")
    ne["draft_cover"] = str(proj / "draft_cover.jpg")
    store.append(ne)
    json.dump(r, open(rp, "w"), ensure_ascii=False)
    print(f"finalized: meta draft_id {new_id}, registered in root_meta_info")


if __name__ == "__main__":
    main()
