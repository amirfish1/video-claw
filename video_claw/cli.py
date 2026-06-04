"""Command-line entry point for video-claw.

Subcommands:
  init           Scaffold a new project in the current (or given) directory.
  install-skill  Register the bundled Claude Code skill into ~/.claude/skills/.
  setup          Interactive wizard: prompts for API keys, explains cost.
                   setup           Interactive; reads from /dev/tty if needed.
                   setup --check   Non-interactive status. Used by install.sh.
  keys           Manage API keys at ~/.config/video-claw/keys.env.
                   keys list                 Show which keys are set (masked).
                   keys set NAME=value ...   Save one or more keys.
                   keys test                 Hit each provider once to verify.
                   keys path                 Print the keys file path.
  render         Render the video for a project directory.
  preview        Render slide PNGs and open the local preview gate without spending TTS.

The intended workflow is Claude-driven: after `pipx install` and
`video-claw install-skill`, the user opens Claude Code and asks for a video
in natural language. Claude drives `init` / `render` for them. The CLI is
fully usable manually too; see the README for the manual flow.

Keys can be supplied via env vars (ELEVENLABS_API_KEY / FAL_API_KEY / DEEPGRAM_API_KEY)
or stored once with `video-claw keys set EL=sk_...`.
"""
from __future__ import annotations
import argparse
import importlib.resources
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from . import assets as assets_mod
from . import config as cfg_mod
from . import core
from . import keys as keys_mod
from . import tts as tts_mod
from . import setup_wizard


SKILL_NAME = "video-claw"
SKILL_TARGET = Path.home() / ".claude" / "skills" / SKILL_NAME


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
    for name in ("intro.html", "tell_claude.html", "claude_writes.html", "outro.html"):
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
    print(f"  2. video-claw keys set EL=sk_...   # if not in env")
    print(f"  3. video-claw preview              # eyeball the slides first")
    print(f"  4. video-claw render               # spends EL + optional fal")
    print(f"")
    print(f"If Claude Code is in the picture, run `video-claw install-skill` once")
    print(f"so it knows to drive this for you on natural-language requests.")
    return 0


def _iter_skill_files() -> List[Path]:
    """List every file the bundled skill ships with, as relative paths."""
    root = importlib.resources.files("video_claw") / "skill_data" / SKILL_NAME
    out: List[Path] = []
    for entry in root.iterdir():
        if entry.is_file():
            out.append(Path(entry.name))
        elif entry.is_dir():
            for sub in entry.iterdir():
                if sub.is_file():
                    out.append(Path(entry.name) / sub.name)
    return out


def cmd_install_skill(args: argparse.Namespace) -> int:
    """Copy the bundled skill from package data into ~/.claude/skills/video-claw/.

    Idempotent: re-runs overwrite files we own. If the target directory exists
    and contains files NOT in the package manifest, refuses unless --force.
    `--target` overrides the destination (used by tests and power users who
    keep their skills in an alternate location).
    """
    source_root = importlib.resources.files("video_claw") / "skill_data" / SKILL_NAME
    if not source_root.is_dir():
        print(
            "error: bundled skill data not found in the installed package.\n"
            "This usually means an old install. Try: pipx upgrade video-claw",
            file=sys.stderr,
        )
        return 2

    owned = {str(p) for p in _iter_skill_files()}
    target = Path(args.target).expanduser().resolve() if args.target else SKILL_TARGET

    if target.exists():
        existing = []
        for p in target.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(target))
                existing.append(rel)
        foreign = [p for p in existing if p not in owned]
        if foreign and not args.force:
            print(
                f"error: {target} contains files not from this package.\n"
                f"  conflicts: {', '.join(sorted(foreign))}\n"
                f"  re-run with --force to overwrite anyway.",
                file=sys.stderr,
            )
            return 2

    target.mkdir(parents=True, exist_ok=True)
    for rel in _iter_skill_files():
        src = source_root.joinpath(*rel.parts)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    print(f"  installed: {target}")
    print(f"  files:     {len(owned)}")
    print(f"  Claude Code will pick up the skill next time you start a session.")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    if args.check:
        return setup_wizard.run_check()
    return setup_wizard.run_wizard()


def cmd_keys(args: argparse.Namespace) -> int:
    action = args.action

    if action == "path":
        print(keys_mod.KEYS_FILE)
        return 0

    if action == "list":
        all_keys = keys_mod.load_keys()
        if not all_keys:
            print("(no keys configured)")
            print(f"Set with: video-claw keys set EL=sk_... FAL=...")
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
        # Required vs. optional. DEEPGRAM is only needed if you've configured
        # the Deepgram TTS provider, so a missing DG key is not a failure.
        optional_when_unset = {"DEEPGRAM_API_KEY", "FAL_API_KEY"}
        any_failed = False
        for name, (ok, msg) in results.items():
            if ok:
                mark = "ok "
            elif msg == "not set" and name in optional_when_unset:
                mark = "opt"
                msg = "not set (optional)"
            else:
                mark = "FAIL"
                any_failed = True
            print(f"  [{mark}] {name}: {msg}")
        return 1 if any_failed else 0

    print(f"unknown keys action: {action}", file=sys.stderr)
    return 2


def _ensure_keys_for(project: cfg_mod.Project) -> Optional[str]:
    """Promote configured keys into os.environ, resolve the effective TTS
    provider, and fail fast only when there is genuinely no usable TTS path.

    Progressive enhancement: `provider:"auto"` degrades to macOS local TTS when
    no paid key is present, so a keyless render is allowed (on a Mac). A pinned
    paid provider with no key, or `auto` on Linux with no key, is a hard error.
    Lipsync without a FAL key is a warning, not a blocker — it degrades
    gracefully at render time.

    Returns an error string if there is no usable TTS path, else None.
    """
    import os
    import platform
    all_keys = keys_mod.load_keys()
    for name, val in all_keys.items():
        os.environ.setdefault(name, val)

    try:
        provider = tts_mod.resolve_provider(project.config.get("tts", {}))
    except RuntimeError as e:
        return str(e)

    if provider.startswith("eleven") and not os.environ.get("ELEVENLABS_API_KEY"):
        return ("Missing ELEVENLABS_API_KEY (for ElevenLabs TTS).\n"
                "Set via: video-claw keys set EL=sk_..., or use provider 'auto'/'macos'.")
    if provider.startswith("deepgram") and not os.environ.get("DEEPGRAM_API_KEY"):
        return ("Missing DEEPGRAM_API_KEY (for Deepgram TTS).\n"
                "Set via: video-claw keys set DG=..., or use provider 'auto'/'macos'.")
    if provider in ("macos", "say", "macos-say") and platform.system() != "Darwin":
        return ("macOS local TTS selected but this is not macOS.\n"
                "Use 'elevenlabs' or 'deepgram' on Linux.")

    if any(s.get("lipsync") for s in project.slides) and not os.environ.get("FAL_API_KEY"):
        print("  [keys] FAL_API_KEY not set; lipsync slides will render without "
              "the avatar overlay.")
    return None


def _validate_preview_ttl(raw: Optional[int]) -> Optional[int]:
    """Reject negative TTLs with a clear error. None means 'use default'."""
    if raw is None:
        return None
    if raw < 0:
        raise SystemExit(
            f"error: --preview-ttl must be >= 0 (got {raw}); use 0 to disable, "
            "positive for seconds."
        )
    return raw


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
            avatar_cfg=project.config.get("avatar"),
            captions_cfg=project.config.get("captions"),
            free=(project.config.get("mode") == "free"),
            auto_yes=args.yes,
            skip_preview=args.no_preview,
            preview_ttl=_validate_preview_ttl(args.preview_ttl),
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
    preview_mod.prompt_user(
        workdir, project.slides, project.orientation,
        auto_yes=False,
        preview_ttl=_validate_preview_ttl(args.preview_ttl),
    )
    return 0


def cmd_fetch_asset(args: argparse.Namespace) -> int:
    """Fetch one or more assets from programmatic sources into ./assets/.

    Spec format: KIND:VALUE. Supported kinds:
      gh:owner/repo       GitHub OG card (1200×600 PNG)
      shot:https://...    Headless Chrome screenshot
      readme:owner/repo   First image from the repo README (often a hero)
      yt:VIDEO_ID         YouTube thumbnail (handles full URLs too)
    """
    project_dir = Path(args.project_dir).resolve()
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if args.list:
        if not assets_dir.exists():
            print(f"(no assets dir at {assets_dir})")
            return 0
        files = sorted(p for p in assets_dir.iterdir() if p.is_file())
        if not files:
            print(f"(empty: {assets_dir})")
            return 0
        for f in files:
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name:40s} {size_kb:8.1f} KB")
        return 0

    if not args.specs:
        print("error: provide one or more SPECs (e.g. 'gh:owner/repo'), or --list",
              file=sys.stderr)
        return 2

    failures = 0
    for spec in args.specs:
        try:
            path = assets_mod.dispatch(spec, assets_dir)
            rel = path.relative_to(project_dir) if path.is_relative_to(project_dir) else path
            print(f"  ✓ {spec}  →  {rel}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {spec}: {e}", file=sys.stderr)
            failures += 1
    return 0 if failures == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="video-claw",
        description="Render narrated slide videos from HTML + a slide list.",
    )
    p.add_argument("--version", action="version", version=f"video-claw {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="Scaffold a new project directory.")
    pi.add_argument("path", nargs="?", default=".", help="Project directory (default: .)")
    pi.add_argument("--title", default=None, help="Project title (default: directory name)")
    pi.add_argument(
        "--orientation", choices=["horizontal", "short"], default="horizontal",
        help="Video aspect (horizontal=1920x1080, short=1080x1920).",
    )
    pi.set_defaults(func=cmd_init)

    ps = sub.add_parser(
        "install-skill",
        help="Register the bundled Claude Code skill into ~/.claude/skills/.",
    )
    ps.add_argument(
        "--target", default=None, metavar="PATH",
        help=(
            "Destination directory (default: ~/.claude/skills/video-claw). "
            "Useful for testing or non-standard Claude Code setups."
        ),
    )
    ps.add_argument(
        "--force", action="store_true",
        help="Overwrite the target dir even if it contains foreign files.",
    )
    ps.set_defaults(func=cmd_install_skill)

    pst = sub.add_parser(
        "setup",
        help="Interactive key wizard with per-provider cost notes.",
    )
    pst.add_argument(
        "--check", action="store_true",
        help="Non-interactive status only; print key health and exit.",
    )
    pst.set_defaults(func=cmd_setup)

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
    pr.add_argument(
        "--preview-ttl", type=int, default=None, metavar="SECONDS",
        help=(
            "Keep the preview server alive this many seconds after the gate "
            "confirms (default: 3600 interactive / 60 headless). "
            "0 disables (server dies on confirm). "
            "Env: VIDEO_CLAW_PREVIEW_TTL."
        ),
    )
    pr.set_defaults(func=cmd_render)

    pfa = sub.add_parser(
        "fetch-asset",
        help="Download real product imagery (GitHub OG cards, screenshots, READMEs, YouTube thumbs) into ./assets/.",
    )
    pfa.add_argument(
        "specs", nargs="*",
        help="One or more KIND:VALUE specs (gh:owner/repo, shot:URL, readme:owner/repo, yt:VIDEO_ID).",
    )
    pfa.add_argument(
        "--project-dir", default=".",
        help="Project directory containing assets/ (default: .)",
    )
    pfa.add_argument(
        "--list", action="store_true",
        help="Show what's already in assets/ and exit.",
    )
    pfa.set_defaults(func=cmd_fetch_asset)

    pp = sub.add_parser("preview", help="Render slide PNGs and open the preview gate only.")
    pp.add_argument("project_dir", nargs="?", default=".")
    pp.add_argument(
        "--preview-ttl", type=int, default=None, metavar="SECONDS",
        help=(
            "Keep the preview server alive this many seconds after the gate "
            "confirms (default: 3600 interactive / 60 headless). "
            "0 disables. Env: VIDEO_CLAW_PREVIEW_TTL."
        ),
    )
    pp.set_defaults(func=cmd_preview)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
