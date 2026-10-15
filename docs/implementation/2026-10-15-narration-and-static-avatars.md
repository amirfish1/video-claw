# Continuous narration and static presenters

Implements GitHub issues #5, #7, #8, and #10.

## Product decisions

- `tts.lipsync` accepts `false`, `true`, `"fal"`, and `"static"`. A slide's
  explicit value wins, including `false`. Invalid strings fail before render
  or spend; truthiness must never select a paid provider accidentally.
- Reuse the existing cached circular PNG and still-image compositor for static
  mode instead of manufacturing a MOV. Crop once per portrait per render;
  missing static portraits fall back to the bundled image. Embedded video
  slides support the same presenter. Existing `avatar.static` remains a
  separate scoped-badge option.
- ElevenLabs receives one script joined with two newlines. Cache the complete
  response atomically, including audio and original-text alignment. Rate
  changes reuse the master. Text, voice, or model changes invalidate it.
- Divide separator pauses halfway between adjacent spoken spans, preserving
  the master timeline and initial lead-in. Slice raw audio before applying each
  slide's rate. Duration is `(end - start) / rate`; no per-cut ffprobe and no
  silence removal. Caption sidecars contain raw local timestamps; captions.py
  performs the existing rate division exactly once.
- Require valid original-text alignment. Normalized-text character offsets
  cannot safely index the script. An unusable response remains cached and
  fails clearly on rerun, avoiding another paid request for the same audio.
  Long scripts remain subject to the selected model's single-request limit;
  no automatic paid fallback or batching is introduced.
- Scaffold slides use natural 1.0 pacing. Narrative guidance lives in the
  requested bundled `references/style.md`, linked from its SKILL.md.

## Repository and release scope

No CLAUDE.md, AGENTS.md, or CLAUDE.local.md was present in this repository or its
parent directories when this work started. The global git hooks are retained.
All changes were made in an isolated worktree.

`skills/README.md` calls the package bundle canonical, while the older
`video_claw/skill_data/README.md` describes it as a snapshot of an external
user-installed skill. This change follows the explicit issue destination and
updates the versioned package bundle directly; it does not modify shared home
configuration or sync unrelated local skill content into the repository.

Merging updates repository code and packaged skill sources. It does not publish
a package release or update existing pipx installations or installed skills.
Users reinstall/update video-claw and run `video-claw install-skill` to pick up
the bundled instructions.

## Validation

Targeted pytest coverage uses mocked HTTP/provider calls, checks one master
request and cache reuse, rate changes, validation before spend, final-segment
extraction, caption offsets, static/fal routing, free-mode defaults, scaffold
pacing, and video-slide overlay composition. A tiny real ffmpeg test decodes
sliced synthetic audio; no paid API calls or production data are used.
