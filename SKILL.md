---
name: make-narrated-video
description: Use when the user wants to produce a narrated slide video (explainer, demo, walkthrough, short, reel) with AI TTS, optional lip-synced presenter, and burned-in captions. Wraps the `make-narrated-video` CLI.
---

# Making a narrated video

This skill drives the `make-narrated-video` Python package
(https://github.com/amirfish1/make-narrated-video).

## When to use this skill

- "Make me a video about X"
- "Turn this outline into a narrated walkthrough"
- "Build a short for YouTube Shorts / TikTok / Reels"
- "Add Becky AI narration to these slides"

If the user just wants a screen recording, they don't need this skill — point
them at QuickTime or OBS instead. This skill is for slide-based, narrated,
captioned videos.

## Setup check (do this once per repo)

```
make-narrated-video --version           # confirm CLI is installed
make-narrated-video keys list           # confirm at least ELEVENLABS_API_KEY is set
```

If the CLI is missing:
```
pip install git+https://github.com/amirfish1/make-narrated-video
pip install playwright && playwright install chromium
pip install imageio-ffmpeg   # optional, fixes caption burn on stock-Homebrew ffmpeg
```

If keys are missing, ask the user for an ElevenLabs key (required) and
optionally a fal.ai key (only if they want lip-synced presenter shots):
```
make-narrated-video keys set EL=sk_xxx FAL=xxx
make-narrated-video keys test
```

## Workflow

### Step 1: Brief

Before writing anything, get these from the user:

- **Topic + audience** — what's the video about, who is it for.
- **Orientation** — horizontal (YT, LinkedIn, embeds) or short (Shorts, TT, Reels).
- **Length target** — a 60-sec short has different rhythm than a 5-min explainer.
- **Visual assets** — screenshots, diagrams, app clips. **Always ask for real assets**
  rather than mocking them. If the user has none, say so explicitly and ask if they
  can capture them, before generating slides that depend on assets that don't exist.
- **Lipsync presenter?** — yes/no. If yes, they need an avatar PNG. Flatten the
  background on solid black before saving (`assets/avatar.png`) to avoid
  transparency artifacts in the circle crop.

### Step 2: Scaffold

```
make-narrated-video init <project-name>
cd <project-name>
```

Edit `slides.py`. The `SLIDES` list is the single source of truth — narration text,
slide types, lipsync flags, speed overrides all live here. Each slide is a dict:

```python
{"type": "html", "html": "slides/intro.html",
 "narration": "...", "lipsync": True}
{"type": "image", "image": "assets/screenshot.png",
 "narration": "...", "title": "Optional title strip"}
{"type": "video", "video": "assets/clip.mp4",
 "narration": "...", "title": "..."}
```

### Step 3: Write slide HTMLs

In `slides/`, use the provided `_shared.css` for design tokens. Add a
slide-specific `<style>` block per file. Body class: `canvas h` for horizontal,
`canvas v` for short.

The narration carries the meaning. The slide is for **anchoring** — one headline
+ one supporting element (chart, stat row, quote, screenshot). Don't write
paragraphs on the slide that the narration will also speak.

### Step 4: Preview gate (mandatory before TTS spend)

```
make-narrated-video preview
```

This renders every slide to PNG and opens a local grid view in the browser. The
user inspects all slides visually before any paid API is called. Press `y` in
the terminal to proceed, anything else to abort.

If the user wants changes, edit HTML, run `preview` again. PNG rendering is
cached so re-runs are fast.

### Step 5: Render

```
make-narrated-video render
```

This re-runs the preview gate, then on `y`:
1. Calls ElevenLabs for each slide's narration (cached by text + voice + model).
2. Calls fal.ai OmniHuman for lipsync slides (cached by narration audio + avatar).
3. Stitches per-slide MP4s, concatenates, burns captions.
4. Writes `out/<name>.mp4`.

### Step 6: Review and iterate

The cache is content-hashed — re-renders only re-do what changed. Tweak a single
narration string, re-render, only that slide regenerates TTS. Same for slide HTML
(only the PNG re-renders) and lipsync (only re-runs if narration or avatar changed).

To bypass all caches: `FORCE_REGEN=1 make-narrated-video render`.

## Hard rules

- **No em-dashes anywhere.** Not in narration, not in slide text, not in titles.
  Use comma, period, or colon. (This is the project owner's standing rule.)
- **Real assets only.** Don't generate placeholder screenshots or lorem-ipsum
  diagrams. Ask the user for the actual thing.
- **Preview before TTS.** Never skip the preview gate. It costs nothing and
  catches typos, broken layouts, missing assets before the meter runs.
- **One thought per slide.** If you find yourself writing a second paragraph on
  a slide, split it into two slides.

## Costs to set expectations

Tell the user the budget up front:

- ElevenLabs Turbo v2.5: ~$0.30 / minute of audio.
- fal.ai OmniHuman 1.5: $0.16 / second of generated lipsync video.
- A typical 5-min video with 30 sec of lipsync bookends: **~$6 total**.
- Re-renders are free (content-hash cache).

## When things go wrong

- **Caption burn fails** — homebrew ffmpeg lacks libass. `pip install imageio-ffmpeg`
  installs a static ffmpeg that includes it; the package auto-detects and uses it.
- **Lipsync circle has checker pattern** — avatar PNG has transparent background.
  Flatten on solid black before saving.
- **Slide PNG looks wrong** — check the HTML in a browser at the canvas resolution
  (1920x1080 or 1080x1920). Headless Chrome will render exactly that size.

## Reference

- Package source: https://github.com/amirfish1/make-narrated-video
- README: project root
- CLI help: `make-narrated-video --help`, `make-narrated-video <subcommand> --help`
