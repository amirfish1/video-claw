"""Command-line entry point for make-narrated-video.

Subcommands:
  init      Scaffold a new project in the current (or given) directory.
  keys      Manage API keys at ~/.config/make-narrated-video/keys.env.
              keys list                 Show which keys are set (masked).
              keys set NAME=value ...   Save one or more keys.
              keys test                 Hit each provider once to verify.
              keys path                 Print the keys file path.
  render    Render the video for a project directory.
  preview   Render slide PNGs and open the local preview gate without spending TTS.

Most users do:
  make-narrated-video init my-vid
  cd my-vid
  make-narrated-video render

Keys can be supplied via env vars (ELEVENLABS_API_KEY / FAL_API_KEY / DEEPGRAM_API_KEY)
or stored once with `make-narrated-video keys set EL=sk_...`.
"""
from __future__ import annotations
import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from . import config as cfg_mod
from . import core
from . import keys as keys_mod


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "narrated-video"


def _templates_dir() -> Path:
    return Path(__file__).parent / "templates"


def _assets_dir() -> Path:
    return Path(__file__).parent / "assets"


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    target.mkdir(parents=True, exist_ok=True)
    title = args.title or target.name
    slug = _slugify(title)
    orientation = args.orientation

    slides_dir = target / "slides"
    assets_dir = target / "assets"
    out_dir = target / "out"
    for d in (slides_dir, assets_dir, out_dir):
        d.mkdir(exist_ok=True)

    # Copy the shared stylesheet + three starter HTML templates.
    tpl = _templates_dir()
    shared_css = tpl / "_shared.css"
    if shared_css.exists():
        shutil.copyfile(shared_css, slides_dir / "_shared.css")
    for name in ("intro.html", "point_one.html", "outro.html"):
        src = tpl / name
        if src.exists():
            shutil.copyfile(src, slides_dir / name)

    # Drop a starter slides.py.
    slides_py = target / "slides.py"
    if slides_py.exists():
        print(f"[init] slides.py already exists, leaving it alone")
    else:
        slides_py.write_text(cfg_mod.SAMPLE_SLIDES_PY % {
            "title": title, "slug": slug, "orientation": orientation,
        })

    # Sample avatar (optional). If a packaged avatar.png exists, copy it.
    avatar_src = _assets_dir() / "avatar.png"
    avatar_dst = assets_dir / "avatar.png"
    if avatar_src.exists() and not avatar_dst.exists():
        shutil.copyfile(avatar_src, avatar_dst)

    print(f"[init] scaffolded project at {target}")
    print(f"       orientation: {orientation}")
    print(f"       edit:        {slides_py}")
    print(f"       slides:      {slides_dir}/")
    print(f"")
    print(f"Next steps:")
    print(f"  1. cd {target}")
    print(f"  2. make-narrated-video keys set EL=sk_...   # if not in env")
    print(f"  3. make-narrated-video render")
    return 0


def cmd_keys(args: argparse.Namespace) -> int:
    action = args.action

    if action == "path":
        print(keys_mod.KEYS_FILE)
        return 0

    if action == "list":
        all_keys = keys_mod.load_keys()
        if not all_keys:
            print("(no keys configured)")
            print(f"Set with: make-narrated-video keys set EL=sk_... FAL=...")
            print(f"Or export ELEVENLABS_API_KEY / FAL_API_KEY / DEEPGRAM_API_KEY.")
            return 0
        print(f"keys file: {keys_mod.KEYS_FILE}")
        for name in ("ELEVENLABS_API_KEY", "FAL_API_KEY", "DEEPGRAM_API_KEY"):
            val = all_keys.get(name)
            if val:
                print(f"  {name} = {keys_mod.mask(val)}")
            else:
                print(f"  {name} = (not set)")
        return 0

    if action == "set":
        pairs = args.assignments
        if not pairs:
            print("error: keys set requires NAME=value pairs", file=sys.stderr)
            return 2
        updates = {}
        for pair in pairs:
            if "=" not in pair:
                print(f"error: bad assignment {pair!r} (need NAME=value)", file=sys.stderr)
                return 2
            k, v = pair.split("=", 1)
            updates[k.strip()] = v.strip()
        path = keys_mod.save_keys(updates)
        for k, v in updates.items():
            canonical = keys_mod.ALIASES.get(k.upper(), k.upper())
            print(f"  saved {canonical} = {keys_mod.mask(v)}")
        print(f"  -> {path}")
        return 0

    if action == "test":
        results = keys_mod.test_all()
        any_failed = False
        for name, (ok, msg) in results.items():
            mark = "ok " if ok else "FAIL"
            print(f"  [{mark}] {name}: {msg}")
            if not ok and msg != "not set":
                any_failed = True
        return 1 if any_failed else 0

    print(f"unknown keys action: {action}", file=sys.stderr)
    return 2


def _ensure_keys_for(project: cfg_mod.Project) -> Optional[str]:
    """Promote configured keys into os.environ before the engine runs.

    Returns an error string if a required key is missing, else None.
    """
    import os
    all_keys = keys_mod.load_keys()
    for name, val in all_keys.items():
        os.environ.setdefault(name, val)

    tts_provider = project.config.get("tts", {}).get("provider", "elevenlabs").lower()
    needs_lipsync = any(s.get("lipsync") for s in project.slides)

    missing: List[str] = []
    if tts_provider.startswith("eleven") and not os.environ.get("ELEVENLABS_API_KEY"):
        missing.append("ELEVENLABS_API_KEY (for ElevenLabs TTS)")
    if tts_provider.startswith("deepgram") and not os.environ.get("DEEPGRAM_API_KEY"):
        missing.append("DEEPGRAM_API_KEY (for Deepgram TTS)")
    if needs_lipsync and not os.environ.get("FAL_API_KEY"):
        missing.append("FAL_API_KEY (for fal.ai lipsync)")
    if missing:
        return (
            "Missing API keys:\n  - " + "\n  - ".join(missing)
            + "\nSet via: make-narrated-video keys set EL=sk_... FAL=..."
        )
    return None


def cmd_render(args: argparse.Namespace) -> int:
    project = cfg_mod.load(Path(args.project_dir))
    err = _ensure_keys_for(project)
    if err:
        print(err, file=sys.stderr)
        return 2

    workdir = project.out_dir
    workdir.mkdir(parents=True, exist_ok=True)

    out_path = project.out_path
    if args.out:
        out_path = Path(args.out).resolve()

    print(f"[render] project: {project.project_dir}")
    print(f"[render] slides:  {len(project.slides)}  orientation: {project.orientation}")
    print(f"[render] output:  {out_path}")

    try:
        core.make_video(
            project.slides,
            workdir=workdir,
            orientation=project.orientation,
            project_dir=project.project_dir,
            out_path=out_path,
            tts_cfg=project.config.get("tts"),
            lipsync_cfg=project.config.get("lipsync"),
            auto_yes=args.yes,
            skip_preview=args.no_preview,
        )
    except SystemExit as e:
        print(f"[render] {e}", file=sys.stderr)
        return 1
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """Render slide PNGs and open the preview gate without doing TTS or lipsync."""
    project = cfg_mod.load(Path(args.project_dir))
    workdir = project.out_dir
    workdir.mkdir(parents=True, exist_ok=True)

    core.render_pngs(
        project.slides,
        workdir=workdir,
        project_dir=project.project_dir,
        dimensions=project.dimensions,
    )
    from . import preview as preview_mod
    preview_mod.prompt_user(workdir, project.slides, project.orientation, auto_yes=False)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="make-narrated-video",
        description="Render narrated slide videos from HTML + a slide list.",
    )
    p.add_argument("--version", action="version", version=f"make-narrated-video {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="Scaffold a new project directory.")
    pi.add_argument("path", nargs="?", default=".", help="Project directory (default: .)")
    pi.add_argument("--title", default=None, help="Project title (default: directory name)")
    pi.add_argument(
        "--orientation", choices=["horizontal", "short"], default="horizontal",
        help="Video aspect (horizontal=1920x1080, short=1080x1920).",
    )
    pi.set_defaults(func=cmd_init)

    pk = sub.add_parser("keys", help="Manage API keys.")
    pk.add_argument("action", choices=["list", "set", "test", "path"])
    pk.add_argument("assignments", nargs="*", help="NAME=value pairs (for `set`).")
    pk.set_defaults(func=cmd_keys)

    pr = sub.add_parser("render", help="Render the video for a project.")
    pr.add_argument("project_dir", nargs="?", default=".",
                    help="Project directory (default: .)")
    pr.add_argument("--out", default=None, help="Override the output MP4 path.")
    pr.add_argument("--yes", "-y", action="store_true",
                    help="Skip the interactive preview gate.")
    pr.add_argument("--no-preview", action="store_true",
                    help="Render without opening the preview at all.")
    pr.set_defaults(func=cmd_render)

    pp = sub.add_parser("preview", help="Render slide PNGs and open the preview gate only.")
    pp.add_argument("project_dir", nargs="?", default=".")
    pp.set_defaults(func=cmd_preview)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
