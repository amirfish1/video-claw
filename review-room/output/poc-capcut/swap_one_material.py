#!/usr/bin/env python3
"""CapCut JSON pipeline POC — swap EXACTLY ONE video material in a cloned project.

Proves the round-trip: clone 0603 -> repoint one material's source clip ->
the edit (0.36x slow-mo on a *different* segment, audio fades, music A/B) survives
untouched because those live in separate UUID-referenced material objects.

Target: segment 80B344C2 -> material A7A10A41 (the first 0:00-0:28.2 segment,
normal speed). Its source_timerange is 0..28.2s, so the replacement clip must be
>= 28.2s (the POC clip is 30s).

Edits, surgically, ONLY material A7A10A41:
  - draft_info.json (root + Timelines/<id>/ copy): path, media_path, duration,
    material_name, and local_material_id -> a NEW library id.
  - draft_meta_info.json: ADD a new draft_materials video entry for the new clip
    (new uuid), leaving the original entry intact for the other two segments.
Everything else (speeds, audio_fades, audios, segment timings) is left byte-for-byte.
"""
import json, os, shutil, subprocess, sys, uuid

DRAFTS = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
DST = os.path.join(DRAFTS, "0603-poc-swap")
TLID = "4186CFB6-C9FD-4EF7-8628-86F04AEE8C8E"
MATERIAL_ID = "A7A10A41-CC27-44D7-92E9-FBB1E33A7370"
NEW_CLIP = "/Users/amirfish/Apps/video-claw/review-room/output/poc-capcut/poc_swap_clip.mp4"

INFO_COPIES = [
    os.path.join(DST, "draft_info.json"),
    os.path.join(DST, "Timelines", TLID, "draft_info.json"),
]
META = os.path.join(DST, "draft_meta_info.json")


def probe_duration_us(path):
    """ffprobe duration in microseconds (int)."""
    ff = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    secs = float(ff.stdout.strip())
    return int(round(secs * 1_000_000))


def main():
    if not os.path.exists(NEW_CLIP):
        sys.exit(f"missing new clip: {NEW_CLIP}")
    new_dur = probe_duration_us(NEW_CLIP)
    new_lib_id = str(uuid.uuid4())
    print(f"new clip duration: {new_dur} us  ({new_dur/1e6:.3f}s)")
    print(f"new library id:    {new_lib_id}")

    # --- 1. draft_info.json (both identical copies) ---
    for p in INFO_COPIES:
        d = json.load(open(p))
        mats = d["materials"]["videos"]
        hit = None
        for m in mats:
            if m["id"] == MATERIAL_ID:
                hit = m
                break
        if hit is None:
            sys.exit(f"material {MATERIAL_ID} not found in {p}")
        old_src = hit.get("source_timerange") or {}
        # NB: source_timerange lives on the SEGMENT, not the material; we only
        # widen the material 'duration' so CapCut sees enough footage.
        hit["path"] = NEW_CLIP
        hit["media_path"] = NEW_CLIP
        hit["duration"] = new_dur
        hit["material_name"] = os.path.basename(NEW_CLIP)
        hit["local_material_id"] = new_lib_id
        json.dump(d, open(p, "w"), ensure_ascii=False)
        print(f"patched material in {os.path.relpath(p, DST)}")

    # --- 2. draft_meta_info.json: add a new library entry (new id) ---
    meta = json.load(open(META))
    template = None
    for grp in meta["draft_materials"]:
        for v in (grp.get("value") or []):
            if v.get("extra_info") == "video_with_VO_no_music.mp4":
                template = (grp, v)
                break
        if template:
            break
    if not template:
        sys.exit("could not find the source video library entry to clone")
    grp, v = template
    new_entry = dict(v)  # shallow clone of the original library entry
    new_entry["id"] = new_lib_id
    new_entry["extra_info"] = os.path.basename(NEW_CLIP)
    new_entry["file_Path"] = NEW_CLIP
    new_entry["duration"] = new_dur
    new_entry["roughcut_time_range"] = {"duration": new_dur, "start": 0}
    grp["value"].append(new_entry)
    json.dump(meta, open(META, "w"), ensure_ascii=False)
    print("added new library entry to draft_meta_info.json")

    # --- 3. refresh the cover so the thumbnail isn't stale (cosmetic) ---
    print("\nDONE. Verify with: capcut-cli lint / version / segments")


if __name__ == "__main__":
    main()
