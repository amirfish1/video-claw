# Bundled skill snapshot

This directory is a **snapshot**, not the source of truth.

The live, editable skill lives at `~/.claude/skills/video-claw/` on the
developer's machine. When you change SKILL.md or anything under
`references/`, edit it *there*, not in this bundle.

To refresh this snapshot from the live skill before tagging a release:

```
python3 scripts/sync-skill.py
```

That script mirrors `~/.claude/skills/video-claw/` into
`video_claw/skill_data/video-claw/`. The bundle is what ships in the wheel
and what `video-claw install-skill` lays down on a fresh machine, so a stale
bundle means a stale release.

There is no CI gate that catches drift. If you forget to run the sync
before tagging, the next release will ship yesterday's skill. The release
checklist is the only safety net.

To verify the bundle matches the live skill without writing anything:

```
python3 scripts/sync-skill.py --check
```

Exits non-zero if the bundle is stale.
