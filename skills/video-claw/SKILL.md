---
name: video-claw
description: Use when the user wants to produce a narrated slide video (explainer, demo, walkthrough, short, reel) with AI TTS, optional lip-synced presenter, and burned-in captions. Wraps the `video-claw` CLI. Triggers on phrases like "make a video about X", "turn this into a narrated walkthrough", "build a short for Shorts/TikTok/Reels", "add narration to these slides".
---

# Making a narrated video

This skill drives the `video-claw` Python package
(https://github.com/amirfish1/video-claw). The user describes what they want.
You write the slides and narration. The CLI ships the MP4.

## When to use this skill

- "Make me a video about X"
- "Turn this outline into a narrated walkthrough"
- "Build a short for YouTube Shorts / TikTok / Reels"
- "Add narration to these slides"

If the user wants a screen recording, point them at QuickTime or OBS instead.
This skill is for slide-based, narrated, captioned videos.

## Setup check (once per machine)

```
video-claw --version           # confirm CLI is installed
video-claw keys list           # confirm at least ELEVENLABS_API_KEY is set
```

If the CLI is missing:
```
pipx install git+https://github.com/amirfish1/video-claw
```

`pipx` puts the CLI on PATH in its own venv, so it works on stock Homebrew
Python (which blocks `pip install` outside a venv via PEP 668). If pipx is
not installed, `brew install pipx` first. Plain pip works inside an explicit
venv: `python3 -m venv .venv && source .venv/bin/activate && pip install git+...`.

You also need a Chromium-class browser somewhere on disk (Google Chrome,
Chromium, or Brave). On macOS, Google Chrome is the assumed default. The
renderer shells out to whichever binary it finds; no Playwright install is
required.

Optional, only if you want captions burned into the MP4 vs the SRT sidecar:
```
pipx inject video-claw imageio-ffmpeg
```
Stock Homebrew ffmpeg lacks libass, so the burn step falls back to shipping
an SRT sidecar by default. `imageio-ffmpeg` carries a libass-enabled binary.

## API keys

The minimum is one TTS key. Lipsync is opt-in per slide.

| Key | Required when | Where |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | Default TTS (also drives word-level captions) | https://elevenlabs.io/app/settings/api-keys |
| `FAL_API_KEY` | Any slide has `lipsync: True` | https://fal.ai/dashboard/keys |
| `DEEPGRAM_API_KEY` | Only if `tts.provider="deepgram"` (cheaper, no captions) | https://console.deepgram.com |

Resolution order at runtime: env var, then `~/.config/video-claw/keys.env`
(mode 0600). Set once with:
```
video-claw keys set EL=sk_xxx FAL=xxx
video-claw keys test
```

`keys test` marks unset optional keys as `[opt]`, not failures. Only required
keys fail loudly.

## Workflow

### Step 1: Brief

Before writing anything, get these from the user:

- **Topic + audience.** What's the video about, who is it for.
- **Orientation.** `horizontal` (YouTube, LinkedIn, embeds) or `short`
  (Shorts, TikTok, Reels).
- **Length target.** A 60-second short has different rhythm than a 5-minute
  explainer. Aim for ~10 seconds of narration per slide.
- **Visual assets.** Screenshots, diagrams, app clips. **Ask for real
  assets.** Do not generate placeholder screenshots. If the user has none,
  say so and ask whether they can capture them, before drafting slides
  that depend on assets that don't exist.
- **Lipsync presenter?** Yes/no. If yes, they need an avatar PNG at
  `assets/avatar.png`. Flatten the background on solid black before saving;
  transparent PNGs cause checker-pattern artifacts in the circle crop. The
  package ships a default Becky avatar that you can keep.

### Step 2: Scaffold

```
video-claw init <project-name>
cd <project-name>
```

This drops a `slides.py` (with `SLIDES = [...]` and `CONFIG = {...}`), three
starter HTML slides under `slides/`, and the default `assets/avatar.png`.

### Step 3: Author slides.py

`slides.py` is the source of truth. Narration text, slide types, lipsync
flags, speed overrides all live here. Slide schema:

```python
{"type": "html", "html": "slides/intro.html",
 "narration": "...", "lipsync": True}
{"type": "image", "image": "assets/screenshot.png",
 "narration": "...", "title": "Optional title strip"}
{"type": "video", "video": "assets/clip.mp4",
 "narration": "...", "title": "..."}
```

Optional per-slide fields: `lipsync: True`, `speed: 1.2`, `title: "..."`.

### Step 4: Write slide HTMLs

In `slides/`, use the provided `_shared.css` for design tokens. Body class:
`canvas h` for horizontal, `canvas v` for short. Add a slide-specific
`<style>` block per file.

The narration carries the meaning. The slide is for **anchoring**: one
headline plus one supporting element (chart, stat row, quote, screenshot).
Do not write paragraphs on the slide that the narration will also speak.

See `references/style.md` for layout patterns and the design token palette.

### Step 5: Preview gate (mandatory before TTS spend)

```
video-claw preview
```

Renders every slide to PNG and opens a local grid in the browser. The user
inspects all slides visually before any paid API is called. Press `y` in the
terminal to proceed, anything else to abort.

If the user wants changes, edit HTML, run `preview` again. PNG rendering is
cached so re-runs are fast.

### Step 6: Render

```
video-claw render
```

Re-runs the preview gate, then on `y`:

1. ElevenLabs TTS per slide (cached by text + voice + model).
2. fal.ai OmniHuman lipsync for slides marked `lipsync: True` (cached by
   narration audio + avatar).
3. Stitches per-slide MP4s, concatenates, burns captions if libass is
   available (otherwise ships an SRT sidecar).
4. Writes `out/<name>.mp4`.

### Step 7: Iterate

The cache is content-hashed. Tweak a single narration string and re-render;
only that slide regenerates TTS. Same for slide HTML (only that PNG
re-renders) and lipsync (only re-runs if narration audio or avatar changed).

To bypass all caches: `FORCE_REGEN=1 video-claw render`.

## Hard rules

- **No em-dashes anywhere.** Not in narration, not in slide text, not in
  titles. Use comma, period, or colon. (Project owner's standing rule.)
- **Real assets only.** No placeholder screenshots, no lorem-ipsum diagrams.
  Ask the user for the actual thing.
- **Preview before TTS.** Never skip the preview gate. Costs nothing,
  catches typos, broken layouts, and missing assets before the meter runs.
- **One thought per slide.** If you find yourself writing a second paragraph
  on a slide, split it into two slides.

## Costs to set expectations

Tell the user the budget up front:

- ElevenLabs Turbo v2.5: ~$0.30 per minute of audio.
- fal.ai OmniHuman 1.5: $0.16 per second of generated lipsync video.
- A typical 5-minute video with 30 seconds of lipsync bookends: ~$6 total.
- Re-renders are free (content-hash cache).

## When things go wrong

- **Caption burn fails.** Stock Homebrew ffmpeg lacks libass. Run
  `pipx inject video-claw imageio-ffmpeg` (or `pip install imageio-ffmpeg`
  inside the same venv). The package auto-detects and uses its bundled
  binary just for the caption step. Until then the package ships an SRT
  sidecar at `video_build/captions.srt`.
- **Browser preview did not open.** The package prints the URL as a
  copy-paste banner before trying to launch the browser. Copy that URL.
- **Lipsync circle has checker pattern.** Avatar PNG has a transparent
  background. Flatten on solid black before saving.
- **Slide PNG looks wrong.** Check the HTML in a real browser at the canvas
  resolution (1920x1080 or 1080x1920). Headless Chrome will render exactly
  that size.

See `references/troubleshooting.md` for the full failure-mode catalog.

## Reference

- Package source: https://github.com/amirfish1/video-claw
- README: project root
- CLI help: `video-claw --help`, `video-claw <subcommand> --help`
- Design tokens and layout patterns: `references/style.md`
- Common error messages and fixes: `references/troubleshooting.md`
