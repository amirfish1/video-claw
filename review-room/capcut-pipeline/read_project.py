#!/usr/bin/env python3
"""Read a CapCut project's EDIT into a structured summary — the round-trip half of the
pipeline. Surfaces, per segment: material, timeline + source ranges, speed, audio
fade in/out, transitions, keyframes, volume. Use it to (a) capture what the user
changed by hand and (b) carry that edit forward into the next version.

Usage: python3 read_project.py <project-name-or-path> [--json]
"""
import argparse, json, os, sys
from pathlib import Path

DRAFTS = Path(os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft"))


def _proj(name):
    p = Path(name)
    if p.is_dir():
        return p
    if (DRAFTS / name).is_dir():
        return DRAFTS / name
    raise FileNotFoundError(name)


def _us(v):
    return round((v or 0) / 1_000_000, 3)


def read(proj):
    d = json.load(open(_proj(proj) / "draft_info.json"))
    mats = d.get("materials", {})
    vids = {m["id"]: m for m in mats.get("videos", [])}
    auds = {m["id"]: m for m in mats.get("audios", [])}
    speeds = {m["id"]: m for m in mats.get("speeds", [])}
    fades = {m["id"]: m for m in mats.get("audio_fades", [])}
    trans = {m["id"]: m for m in mats.get("transitions", [])}
    anims = {m["id"]: m for m in mats.get("material_animations", [])}
    out = {"project": str(_proj(proj).name), "duration_s": _us(d.get("duration")), "tracks": []}
    for ti, tr in enumerate(d.get("tracks", [])):
        T = {"index": ti, "type": tr.get("type"), "name": tr.get("name"), "segments": []}
        for seg in tr.get("segments", []):
            mat = vids.get(seg.get("material_id")) or auds.get(seg.get("material_id")) or {}
            name = mat.get("material_name") or Path(mat.get("path", "")).name or seg.get("material_id", "")[:8]
            S = {
                "id": seg["id"][:8],
                "material": name,
                "timeline": [_us(seg.get("target_timerange", {}).get("start")),
                             _us((seg.get("target_timerange", {}).get("start", 0)) + (seg.get("target_timerange", {}).get("duration", 0)))],
                "source": [_us(seg.get("source_timerange", {}).get("start")),
                           _us((seg.get("source_timerange", {}).get("start", 0)) + (seg.get("source_timerange", {}).get("duration", 0)))],
                "speed": seg.get("speed", 1),
            }
            # companion materials via extra_material_refs
            fin = fout = 0.0; tname = None; tdur = None; aname = []
            for rid in seg.get("extra_material_refs", []):
                if rid in speeds and speeds[rid].get("speed", 1) != 1:
                    S["speed_mat"] = speeds[rid]["speed"]
                if rid in fades:
                    fin = _us(fades[rid].get("fade_in_duration"))
                    fout = _us(fades[rid].get("fade_out_duration"))
                if rid in trans:
                    tname = trans[rid].get("name"); tdur = _us(trans[rid].get("duration"))
                if rid in anims:
                    for a in anims[rid].get("animations", []):
                        aname.append(f"{a.get('type')}:{a.get('name')}({_us(a.get('duration'))}s)")
            if fin or fout:
                S["audio_fade_in_out_s"] = [fin, fout]
            if tname:
                S["transition"] = {"name": tname, "dur_s": tdur}
            if aname:
                S["anim"] = aname
            kf = seg.get("common_keyframes") or seg.get("keyframe_refs") or []
            if kf:
                props = [k.get("property_type", k) if isinstance(k, dict) else k for k in kf]
                S["keyframes"] = len(kf)
            if seg.get("volume", 1) != 1:
                S["volume"] = seg.get("volume")
            T["segments"].append(S)
        out["tracks"].append(T)
    return out


def _fmt(o):
    lines = [f"# {o['project']}  ({o['duration_s']}s)"]
    for t in o["tracks"]:
        lines.append(f"\n[{t['index']}] {t['type']} '{t['name']}'  ({len(t['segments'])} segs)")
        for s in t["segments"]:
            extra = []
            if s.get("speed", 1) != 1 or s.get("speed_mat"):
                extra.append(f"speed={s.get('speed_mat', s['speed'])}x")
            if "audio_fade_in_out_s" in s:
                extra.append(f"fade={s['audio_fade_in_out_s']}")
            if "transition" in s:
                extra.append(f"xition={s['transition']['name']}/{s['transition']['dur_s']}s")
            if "anim" in s:
                extra.append("anim=" + ",".join(s["anim"]))
            if "keyframes" in s:
                extra.append(f"kf={s['keyframes']}")
            if "volume" in s:
                extra.append(f"vol={s['volume']}")
            tl = s["timeline"]
            lines.append(f"   {s['id']}  {tl[0]:>6.2f}-{tl[1]:>6.2f}  {s['material'][:34]:<34} "
                         + "  ".join(extra))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    o = read(a.project)
    print(json.dumps(o, indent=2) if a.json else _fmt(o))


if __name__ == "__main__":
    main()
