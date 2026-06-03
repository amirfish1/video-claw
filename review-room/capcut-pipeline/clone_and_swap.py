#!/usr/bin/env python3
"""CapCut-owned pipeline — clone a CapCut project and swap clips by segment id.

Generalizes the proven POC (review-room/output/poc-capcut/swap_one_material.py).
Delivers a NEW CapCut project that is a clone of an existing hand-edit (e.g. `0603`:
slow-mo reveal, music A/B, re-synced VO, fades) with ONLY the named segments' source
clips replaced. The EDIT (timing, speeds, fades, music) is preserved because CapCut
stores those as separate ID-referenced material objects — repointing a clip's file
leaves them untouched.

HARD RULE discovered in the POC: CapCut.app is macOS-sandboxed and can only open media
it imported itself (per-file security-scoped bookmark) OR media living inside its own
`~/Movies/CapCut/User Data` draft tree. So every swapped clip is COPIED INTO the new
project's `Resources/import/` and referenced by that bundled path — external paths
(e.g. under review-room/) would open with a "Couldn't find media / Link media" prompt.

Usage:
  # one swap
  python3 clone_and_swap.py --source 0603 --dest 0603-v210 \
      --swap 80B344C2=/abs/path/new_reveal.mp4

  # many swaps (repeat --swap); segment ids come from `capcut-cli segments <proj>`
  python3 clone_and_swap.py --source 0603 --dest v2.10 \
      --swap 80B344C2=/abs/a.mp4 --swap 3189567F=/abs/b.mp4

Importable:  from clone_and_swap import clone_and_swap
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid

DRAFTS = os.path.expanduser(
    "~/Movies/CapCut/User Data/Projects/com.lveditor.draft")


# ---------------------------------------------------------------- helpers -----
def _ffprobe_duration_us(path):
    """Source duration in microseconds (int)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError(f"ffprobe failed on {path}: {out.stderr.strip()}")
    return int(round(float(out.stdout.strip()) * 1_000_000))


def _resolve_project_dir(name_or_path):
    """Accept a project name (under DRAFTS) or a direct folder path."""
    if os.path.isdir(name_or_path):
        return os.path.abspath(name_or_path)
    p = os.path.join(DRAFTS, name_or_path)
    if os.path.isdir(p):
        return p
    raise FileNotFoundError(f"no such project: {name_or_path}")


def _timeline_id(project_dir):
    tl = os.path.join(project_dir, "Timelines")
    if not os.path.isdir(tl):
        return None
    ids = [d for d in os.listdir(tl)
           if os.path.isdir(os.path.join(tl, d))]
    return ids[0] if ids else None


def _info_copies(project_dir):
    """Both draft_info.json copies CapCut keeps in sync (root + Timelines/<id>/)."""
    copies = []
    root = os.path.join(project_dir, "draft_info.json")
    if os.path.exists(root):
        copies.append(root)
    tlid = _timeline_id(project_dir)
    if tlid:
        ti = os.path.join(project_dir, "Timelines", tlid, "draft_info.json")
        if os.path.exists(ti):
            copies.append(ti)
    if not copies:
        raise FileNotFoundError(f"no draft_info.json in {project_dir}")
    return copies


def _find_segment(info, segment_id):
    """Return (segment, track) for a segment id (full or 8-char prefix)."""
    sid = segment_id.upper()
    for track in info.get("tracks", []):
        for seg in track.get("segments", []):
            if seg["id"].upper() == sid or seg["id"].upper().startswith(sid):
                return seg, track
    return None, None


def _find_video_material(info, material_id):
    for m in info["materials"].get("videos", []):
        if m["id"] == material_id:
            return m
    return None


def _capcut_cli():
    return shutil.which("capcut-cli") or "capcut-cli"


# ----------------------------------------------------------------- core -------
def clone_and_swap(source, dest, swaps, *, drafts_dir=DRAFTS,
                   allow_retime=False, overwrite=False):
    """Clone `source` project -> `dest`, swapping each segment's source clip.

    swaps: dict {segment_id: new_clip_abs_path}.
    Returns the destination project directory path.
    """
    src_dir = _resolve_project_dir(source)
    dst_dir = os.path.join(drafts_dir, dest)
    if os.path.exists(dst_dir):
        if not overwrite:
            raise FileExistsError(
                f"{dst_dir} exists (pass overwrite=True to replace)")
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)
    print(f"cloned {os.path.basename(src_dir)} -> {dest}")

    import_dir = os.path.join(dst_dir, "Resources", "import")
    os.makedirs(import_dir, exist_ok=True)
    info_paths = _info_copies(dst_dir)
    meta_path = os.path.join(dst_dir, "draft_meta_info.json")
    vstore_path = os.path.join(dst_dir, "draft_virtual_store.json")

    # Resolve each swap once (against the first info copy) to compute new ids,
    # bundle media, and validate durations; then apply to ALL info copies.
    base = json.load(open(info_paths[0]))
    plan = []  # list of dicts describing each swap
    for seg_id, clip in swaps.items():
        clip = os.path.abspath(clip)
        if not os.path.exists(clip):
            raise FileNotFoundError(f"clip not found: {clip}")
        seg, _ = _find_segment(base, seg_id)
        if seg is None:
            raise ValueError(f"segment {seg_id} not found in {source}")
        mat = _find_video_material(base, seg["material_id"])
        if mat is None:
            raise ValueError(
                f"segment {seg_id} has no video material ({seg['material_id']})")
        new_dur = _ffprobe_duration_us(clip)
        src_win = seg.get("source_timerange", {}).get("duration", 0)
        if new_dur < src_win and not allow_retime:
            raise ValueError(
                f"segment {seg_id}: new clip {new_dur/1e6:.2f}s is SHORTER than "
                f"its source window {src_win/1e6:.2f}s. The slow-mo/trim would run "
                f"out of footage. Use a longer clip or pass allow_retime=True "
                f"(clamps the segment to the clip length).")
        bundled = os.path.join(import_dir, os.path.basename(clip))
        n = 1
        while os.path.exists(bundled):  # avoid name collisions across swaps
            stem, ext = os.path.splitext(os.path.basename(clip))
            bundled = os.path.join(import_dir, f"{stem}_{n}{ext}")
            n += 1
        shutil.copy2(clip, bundled)
        plan.append({
            "seg_id": seg["id"], "material_id": seg["material_id"],
            "bundled": bundled, "new_dur": new_dur, "src_win": src_win,
            "new_lib_id": str(uuid.uuid4()),
            "retime": new_dur < src_win,
        })
        print(f"  swap seg {seg['id'][:8]} -> {os.path.basename(bundled)} "
              f"({new_dur/1e6:.2f}s, window {src_win/1e6:.2f}s"
              f"{', RETIME' if new_dur < src_win else ''})")

    # --- apply to every draft_info.json copy ---
    for p in info_paths:
        d = json.load(open(p))
        for sw in plan:
            mat = _find_video_material(d, sw["material_id"])
            mat["path"] = sw["bundled"]
            mat["media_path"] = sw["bundled"]
            mat["duration"] = sw["new_dur"]
            mat["material_name"] = os.path.basename(sw["bundled"])
            mat["local_material_id"] = sw["new_lib_id"]
            if sw["retime"]:
                seg, _ = _find_segment(d, sw["seg_id"])
                # clamp the segment's source window to the available footage
                seg["source_timerange"]["duration"] = sw["new_dur"]
                seg["target_timerange"]["duration"] = sw["new_dur"]
        json.dump(d, open(p, "w"), ensure_ascii=False)
    print(f"patched {len(info_paths)} draft_info.json cop"
          f"{'y' if len(info_paths) == 1 else 'ies'}")

    # --- draft_meta_info.json: add a library entry per swapped clip ---
    meta = json.load(open(meta_path))
    template = None
    for grp in meta.get("draft_materials", []):
        for v in (grp.get("value") or []):
            if v.get("metetype") == "video":
                template = (grp, v)
                break
        if template:
            break
    if template is None:
        print("WARN: no existing video library entry to clone; "
              "CapCut may prompt to relink.")
    else:
        grp, tmpl = template
        for sw in plan:
            entry = dict(tmpl)
            entry["id"] = sw["new_lib_id"]
            entry["extra_info"] = os.path.basename(sw["bundled"])
            entry["file_Path"] = sw["bundled"]
            entry["duration"] = sw["new_dur"]
            entry["roughcut_time_range"] = {"duration": sw["new_dur"], "start": 0}
            grp["value"].append(entry)
        json.dump(meta, open(meta_path, "w"), ensure_ascii=False)
        print(f"added {len(plan)} library entr"
              f"{'y' if len(plan) == 1 else 'ies'} to draft_meta_info.json")

    # --- draft_virtual_store.json: register the new library ids ---
    if os.path.exists(vstore_path):
        vs = json.load(open(vstore_path))
        for grp in vs.get("draft_virtual_store", []):
            if grp.get("type") == 1:
                have = {e.get("child_id") for e in grp["value"]}
                for sw in plan:
                    if sw["new_lib_id"] not in have:
                        grp["value"].append(
                            {"child_id": sw["new_lib_id"], "parent_id": ""})
        json.dump(vs, open(vstore_path, "w"), ensure_ascii=False)
        print("registered new ids in draft_virtual_store.json")

    # --- re-stamp clone identity + register in root_meta_info.json ---
    _restamp_identity(dst_dir, dest, drafts_dir)

    # --- lint gate ---
    res = subprocess.run([_capcut_cli(), "lint", dst_dir, "-H"],
                         capture_output=True, text=True)
    print("lint:", (res.stdout or res.stderr).strip(), f"(exit {res.returncode})")
    if res.returncode == 2:
        raise RuntimeError("capcut-cli lint reported ERRORS (exit 2) — see above")
    print(f"\nDONE -> {dst_dir}\nOpen the project '{dest}' in CapCut to verify.")
    return dst_dir


def _restamp_identity(dst_dir, dest, drafts_dir):
    new_id = str(uuid.uuid4()).upper()
    # clone meta identity
    mp = os.path.join(dst_dir, "draft_meta_info.json")
    m = json.load(open(mp))
    m["draft_name"] = dest
    m["draft_id"] = new_id
    m["draft_fold_path"] = dst_dir
    json.dump(m, open(mp, "w"), ensure_ascii=False)
    # register in root_meta_info.json (clone the source entry)
    rp = os.path.join(drafts_dir, "root_meta_info.json")
    if not os.path.exists(rp):
        print("WARN: no root_meta_info.json — CapCut may not list the project.")
        return
    shutil.copy2(rp, rp + ".bak")
    r = json.load(open(rp))
    store = r.get("all_draft_store", [])
    src_name = os.path.basename(os.path.dirname(dst_dir)) if False else None
    # find any existing entry to clone its shape
    template = store[0] if store else None
    if template is not None:
        import copy as _copy
        ne = _copy.deepcopy(template)
        for k, v in list(ne.items()):
            if isinstance(v, str) and dst_dir.rsplit("/", 1)[0] in v:
                # repoint any path that points at the drafts dir to our folder
                pass
        ne["draft_name"] = dest
        ne["draft_id"] = new_id
        ne["draft_fold_path"] = dst_dir
        ne["draft_json_file"] = os.path.join(dst_dir, "draft_info.json")
        ne["draft_cover"] = os.path.join(dst_dir, "draft_cover.jpg")
        store.append(ne)
        if isinstance(r.get("draft_ids"), list):
            r["draft_ids"].append(new_id)
        json.dump(r, open(rp, "w"), ensure_ascii=False)
        print(f"registered '{dest}' in root_meta_info.json "
              f"(backup: root_meta_info.json.bak)")


# ----------------------------------------------------------------- cli --------
def _parse_swaps(items):
    swaps = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"--swap must be SEGID=/abs/clip.mp4 (got: {it})")
        seg, clip = it.split("=", 1)
        swaps[seg.strip()] = clip.strip()
    return swaps


def main():
    ap = argparse.ArgumentParser(description="Clone a CapCut project, swap clips.")
    ap.add_argument("--source", required=True,
                    help="source project name (under drafts) or folder path")
    ap.add_argument("--dest", required=True, help="new project name")
    ap.add_argument("--swap", action="append", metavar="SEGID=CLIP",
                    help="segment id = absolute clip path (repeatable)")
    ap.add_argument("--drafts", default=DRAFTS, help="CapCut drafts dir")
    ap.add_argument("--allow-retime", action="store_true",
                    help="permit a shorter clip (clamps the segment)")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace dest if it already exists")
    a = ap.parse_args()
    swaps = _parse_swaps(a.swap)
    if not swaps:
        raise SystemExit("at least one --swap is required")
    clone_and_swap(a.source, a.dest, swaps, drafts_dir=a.drafts,
                   allow_retime=a.allow_retime, overwrite=a.overwrite)


if __name__ == "__main__":
    main()
