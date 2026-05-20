#!/usr/bin/env python3
"""Refresh the bundled skill snapshot from the live ~/.claude/skills/video-claw/.

The package ships SKILL.md + references/ inside `video_claw/skill_data/video-claw/`
so that `video-claw install-skill` can lay them down on a fresh machine via
`importlib.resources`. That bundled snapshot is a copy of the *live* skill the
developer edits at `~/.claude/skills/video-claw/`. Two sources, no symlink.

This helper is the one-way sync: live -> bundle. Run it before tagging a release
(or any time you've edited the live skill and want the change to ship in the
next wheel). It is intentionally manual — there is no CI gate enforcing it, so
forgetting it means the next release ships stale skill content. The release
checklist in CONTRIBUTING / the Makefile is the only safety net.

Usage:
    python3 scripts/sync-skill.py            # copy live -> bundle, report diff
    python3 scripts/sync-skill.py --check    # exit 1 if bundle is stale; do not write

Exit codes:
    0  bundle is up to date (or just got refreshed)
    1  --check: bundle is stale relative to the live skill
    2  the live skill directory is missing — nothing to sync from
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SKILL_NAME = "video-claw"
LIVE = Path.home() / ".claude" / "skills" / SKILL_NAME
REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE = REPO_ROOT / "video_claw" / "skill_data" / SKILL_NAME


def _iter_files(root: Path) -> list[Path]:
    """Return relative paths of every file under `root`, sorted for stable diff."""
    return sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file())


def _is_stale() -> tuple[bool, list[str]]:
    """Return (stale?, human-readable reasons)."""
    reasons: list[str] = []
    if not BUNDLE.exists():
        return True, [f"bundle dir does not exist: {BUNDLE}"]

    live_files = set(_iter_files(LIVE))
    bundle_files = set(_iter_files(BUNDLE))

    only_live = live_files - bundle_files
    only_bundle = bundle_files - live_files
    common = live_files & bundle_files

    for rel in sorted(only_live):
        reasons.append(f"missing from bundle: {rel}")
    for rel in sorted(only_bundle):
        reasons.append(f"stale in bundle (not in live skill): {rel}")
    for rel in sorted(common):
        if not filecmp.cmp(LIVE / rel, BUNDLE / rel, shallow=False):
            reasons.append(f"content differs: {rel}")

    return (bool(reasons), reasons)


def _sync() -> int:
    """Mirror LIVE -> BUNDLE. Preserves the snapshot README we wrote by hand."""
    # We keep a hand-written README.md at the root of skill_data/ (one level
    # *above* the per-skill bundle dir) to warn editors. The per-skill dir is
    # mirrored wholesale — no carve-outs.
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    shutil.copytree(LIVE, BUNDLE)

    n = sum(1 for _ in BUNDLE.rglob("*") if _.is_file())
    print(f"[sync-skill] copied {n} file(s) from {LIVE} -> {BUNDLE}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--check", action="store_true",
        help="Exit 1 if the bundle is stale; do not modify anything.",
    )
    args = ap.parse_args(argv)

    if not LIVE.is_dir():
        print(
            f"[sync-skill] error: live skill dir not found at {LIVE}\n"
            "  This script is meant for developers who maintain the skill in their\n"
            "  Claude Code config. End users don't need to run it.",
            file=sys.stderr,
        )
        return 2

    stale, reasons = _is_stale()

    if args.check:
        if stale:
            print("[sync-skill] bundle is STALE relative to the live skill:", file=sys.stderr)
            for r in reasons:
                print(f"  - {r}", file=sys.stderr)
            print(
                "[sync-skill] run `python3 scripts/sync-skill.py` to refresh.",
                file=sys.stderr,
            )
            return 1
        print("[sync-skill] bundle is in sync with the live skill.")
        return 0

    if not stale:
        print("[sync-skill] bundle already in sync; nothing to do.")
        return 0

    print("[sync-skill] differences detected:")
    for r in reasons:
        print(f"  - {r}")
    return _sync()


if __name__ == "__main__":
    sys.exit(main())
