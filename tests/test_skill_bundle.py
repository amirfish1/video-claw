"""The bundled Claude Code skill must ship inside the installed wheel.

If `pyproject.toml` stops shipping `video_claw/skill_data/**/*` as package data,
`video-claw install-skill` breaks for everyone who pipx-installed from a wheel.
These tests guard the bundle: SKILL.md and the references/ tree must be
reachable via `importlib.resources` from the installed package.
"""
from __future__ import annotations

import importlib.resources
import tempfile
from pathlib import Path

import pytest


SKILL_NAME = "video-claw"


def _bundle_root():
    """importlib.resources Traversable pointing at the bundled skill dir."""
    return importlib.resources.files("video_claw") / "skill_data" / SKILL_NAME


def test_skill_md_is_in_the_bundle():
    """SKILL.md must be importable as package data — this is the load-bearing file."""
    skill_md = _bundle_root() / "SKILL.md"
    assert skill_md.is_file(), (
        f"SKILL.md not found in package data at video_claw/skill_data/{SKILL_NAME}/. "
        "Check pyproject.toml [tool.setuptools.package-data] includes skill_data/**/*."
    )


def test_skill_md_has_frontmatter():
    """A skill without YAML frontmatter won't load in Claude Code."""
    text = (_bundle_root() / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---"), (
        "SKILL.md must start with YAML frontmatter (`---` on line 1). "
        "Run `python3 scripts/sync-skill.py` to refresh from the live skill."
    )
    # The two required keys.
    assert "\nname:" in text, "SKILL.md frontmatter missing `name:` key."
    assert "\ndescription:" in text, "SKILL.md frontmatter missing `description:` key."


def test_references_dir_is_in_the_bundle():
    """references/ ships supporting docs the skill loads on demand."""
    refs = _bundle_root() / "references"
    assert refs.is_dir(), (
        "references/ directory missing from package data. "
        "Check pyproject.toml [tool.setuptools.package-data] glob covers it."
    )
    md_files = [p for p in refs.iterdir() if p.name.endswith(".md") and p.is_file()]
    assert md_files, "references/ exists but ships no .md files — bundle is empty."


def test_install_skill_target_flag_overrides_destination(tmp_path):
    """--target PATH must redirect the install away from ~/.claude/skills/."""
    from video_claw import cli

    target = tmp_path / "alt-location"
    class _Args:
        force = False
        target = str(tmp_path / "alt-location")
    rc = cli.cmd_install_skill(_Args())
    assert rc == 0
    assert (target / "SKILL.md").is_file()
    assert (target / "references").is_dir()


def test_install_skill_lays_down_files_to_a_target(tmp_path):
    """End-to-end: invoke the CLI handler and confirm SKILL.md + references/ land."""
    # Lazy import: importing cli triggers the whole package, which is fine but
    # not free, so we keep it scoped to this test.
    from video_claw import cli

    target = tmp_path / "skill-install-test"

    # Monkey-patch the install target. The CLI handler hardcodes
    # ~/.claude/skills/<name>/; for a hermetic test we redirect to tmp_path.
    orig_target = cli.SKILL_TARGET
    cli.SKILL_TARGET = target
    try:
        class _Args:
            force = False
            target = None
        rc = cli.cmd_install_skill(_Args())
    finally:
        cli.SKILL_TARGET = orig_target

    assert rc == 0, f"install-skill returned {rc} (expected 0)"
    assert (target / "SKILL.md").is_file(), "SKILL.md was not laid down"
    assert (target / "references").is_dir(), "references/ was not laid down"


def test_install_skill_is_idempotent_on_rerun(tmp_path):
    """Running install-skill twice into the same dir must succeed without --force."""
    from video_claw import cli

    target = tmp_path / "skill-install-rerun"
    orig_target = cli.SKILL_TARGET
    cli.SKILL_TARGET = target
    try:
        class _Args:
            force = False
            target = None
        assert cli.cmd_install_skill(_Args()) == 0
        # Second run: target exists, files are ours (not foreign), should succeed.
        assert cli.cmd_install_skill(_Args()) == 0
    finally:
        cli.SKILL_TARGET = orig_target


def test_install_skill_refuses_foreign_files_without_force(tmp_path):
    """If the user has hand-edited / dropped extra files, refuse to clobber."""
    from video_claw import cli

    target = tmp_path / "skill-install-foreign"
    target.mkdir()
    (target / "user-notes.md").write_text("my own scratch notes\n")

    orig_target = cli.SKILL_TARGET
    cli.SKILL_TARGET = target
    try:
        class _Args:
            force = False
            target = None
        assert cli.cmd_install_skill(_Args()) == 2, (
            "Expected non-zero exit when foreign files are present without --force."
        )
        # User's file must still be there — we refused, we didn't delete.
        assert (target / "user-notes.md").is_file()

        class _ForceArgs:
            force = True
            target = None
        assert cli.cmd_install_skill(_ForceArgs()) == 0
        # SKILL.md now exists alongside the user's file (we don't delete foreign files,
        # we just overwrite our own paths).
        assert (target / "SKILL.md").is_file()
        assert (target / "user-notes.md").is_file()
    finally:
        cli.SKILL_TARGET = orig_target
