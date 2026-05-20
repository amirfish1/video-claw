# video-claw

Narrated slide videos for people who would rather describe a video than
storyboard one. You tell Claude Code what you want. Claude writes the
slides and narration. video-claw ships the MP4.

Optional lip-synced AI presenter via fal.ai OmniHuman. Optional burned-in
word-aligned captions via ElevenLabs.

Built for macOS. Works on Linux.

## Quickstart

```
# One command: install, then walk you through API key setup.
curl -fsSL https://raw.githubusercontent.com/amirfish1/video-claw/main/install.sh | bash
```

Or the manual two-step:

```
pipx install git+https://github.com/amirfish1/video-claw
video-claw setup            # interactive key wizard with cost notes
video-claw install-skill    # optional: register the Claude Code skill
```

Then open Claude Code in any directory and say:

> "Make me a 30-second video about how SSDs work."

Claude reads the video-claw skill, drafts `slides.py` + the HTML files,
asks for any missing API keys, runs `video-claw render`, and hands you the
MP4 in `out/`. You never touch the CLI directly unless you want to.

The skill triggers on natural-language prompts like "make a video about X",
"turn this outline into a narrated walkthrough", "build a short for
Shorts/TikTok/Reels". No slash command, no remembered syntax.

## What you get

- **HTML slides.** Write them like web pages with full CSS. No bespoke DSL.
- **Two orientations.** `horizontal` (1920x1080) for YouTube and embeds,
  `short` (1080x1920) for Shorts, TikTok, Reels.
- **Two TTS providers.** ElevenLabs (default, with timestamps for captions)
  or Deepgram (cheaper, no captions).
- **Optional lipsync.** Set `lipsync: True` on any slide; fal.ai overlays a
  circular AI presenter in the bottom-right.
- **Word-aligned captions.** Burned in via libass when available, otherwise
  shipped as an SRT sidecar.
- **Preview gate.** Local web server shows every slide PNG in a grid before
  any paid API is hit. Press `y` to spend, anything else to abort.
- **Content-hash cache.** Re-runs are seconds, not minutes. Iterate freely.
- **Claude skill ships in the box.** `video-claw install-skill` copies the
  bundled skill into `~/.claude/skills/video-claw/`. Any Claude Code
  session, in any directory, can drive video-claw on natural-language
  prompts after that.

## Install

```
pipx install git+https://github.com/amirfish1/video-claw
video-claw install-skill
```

`pipx` puts the CLI on PATH in its own venv (works on stock Homebrew Python
where plain `pip install` would fail via PEP 668). If pipx is missing:
`brew install pipx`.

When you upgrade with `pipx upgrade video-claw`, re-run `video-claw
install-skill` to pick up the latest SKILL.md.

### Manual venv install (if you don't want pipx)

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install git+https://github.com/amirfish1/video-claw
video-claw install-skill
```

### Prerequisites

- **Python 3.10+**.
- **A Chromium-class browser** on disk. Google Chrome, Chromium, or Brave
  all work. The renderer shells out to whichever it finds. Playwright is not
  required.
- **ffmpeg + ffprobe** on PATH. Homebrew ffmpeg handles everything except
  caption burn-in. The package falls back to shipping an SRT sidecar in that
  case. To burn captions into the MP4, install `imageio-ffmpeg` (which carries
  a libass-enabled binary): `pipx inject video-claw imageio-ffmpeg`.

## API keys

The minimum is one TTS key. Lipsync is opt-in per slide.

| Key | Required when | Where to get it |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | Default TTS, also drives word-level captions | https://elevenlabs.io/app/settings/api-keys |
| `FAL_API_KEY` | Any slide has `lipsync: True` | https://fal.ai/dashboard/keys |
| `DEEPGRAM_API_KEY` | Only when `tts.provider="deepgram"` (cheaper, no captions) | https://console.deepgram.com |

Resolution order: env var, then `~/.config/video-claw/keys.env` (mode 0600,
created automatically when you run `keys set`).

```
video-claw keys set EL=sk_xxx FAL=xxx
video-claw keys test
```

`keys test` shows `[opt]` for optional keys that aren't set; only required
keys fail.

## Cost

Typical 5-minute narrated video with ~30 seconds of lipsync bookends:

| Item | Rate | 5-min video |
| --- | --- | --- |
| ElevenLabs Turbo v2.5 (with timestamps) | ~$0.30 / min of audio | ~$1.50 |
| fal.ai OmniHuman 1.5 lipsync | $0.16 / sec of generated video | ~$4.80 (30 sec) |
| **Total** | | **~$6.30** |

Deepgram Aura-2 TTS is ~$0.015 / 1k chars and skips captions; for a 5-min
video that's roughly $0.10. Captions need ElevenLabs.

The content-hash cache means you only pay once per unique narration +
voice + speed. Re-render to fix a CSS typo: free.

## Manual CLI (without Claude)

You can drive video-claw directly from the shell if you want. This is the
loop Claude runs for you under the hood:

```
video-claw init my-vid          # scaffold a project directory
cd my-vid
video-claw keys set EL=sk_...   # or export ELEVENLABS_API_KEY
video-claw preview              # eyeball the slide PNGs first (no spend)
video-claw render               # spends EL + optional fal, ships out/<name>.mp4
```

Out of the box, `init` scaffolds a 4-slide self-referential demo. Running
`video-claw render` immediately produces a working ~30-second video about
what video-claw does, useful as a sanity check on your install. To make
your own video, overwrite `slides.py` and the HTML files in `slides/`
(by hand, or by asking Claude).

## Project layout

A project is a directory. After `video-claw init my-vid`:

```
my-vid/
├── slides.py          # SLIDES = [...] and CONFIG = {...}
├── slides/
│   ├── _shared.css    # design tokens
│   ├── intro.html
│   ├── tell_claude.html
│   ├── claude_writes.html
│   └── outro.html
├── assets/
│   └── avatar.png     # used by slides with lipsync: True
├── out/
│   └── video.mp4      # final output
└── video_build/       # cache + intermediates (safe to delete)
```

`slides.py`:

```python
CONFIG = {
    "title": "My demo",
    "orientation": "horizontal",   # or "short"
    "out_path": "out/demo.mp4",
    "tts": {
        "provider": "elevenlabs",
        "voice_id": "cgSgspJ2msm6clMCkdW9",   # Jessica
        "model": "eleven_turbo_v2_5",
        "speaking_rate": 1.2,
    },
}

SLIDES = [
    {
        "type": "html",
        "html": "slides/intro.html",
        "narration": "Hi. Here is what we're covering today.",
        "lipsync": True,
    },
    {
        "type": "html",
        "html": "slides/point_one.html",
        "narration": "Point one. The hook.",
    },
    {
        "type": "image",
        "image": "assets/screenshot.png",
        "narration": "This is the dashboard.",
        "title": "Dashboard",
    },
    {
        "type": "video",
        "video": "assets/demo.mp4",
        "narration": "Here is a five-second clip of the app.",
        "title": "Live demo",
    },
    {
        "type": "html",
        "html": "slides/outro.html",
        "narration": "Thanks for watching.",
        "lipsync": True,
    },
]
```

Slide types:

- `html`. Chromium renders the file at canvas size. Use `_shared.css` for tokens.
- `image`. Wrapped in a Chromium template, gets a title strip if `title` is set.
- `video`. Drawn as a backdrop with a viewport rectangle; the clip is composited via ffmpeg.

Optional fields on any slide:

- `lipsync: True`. Overlay a fal.ai OmniHuman circle on this slide (requires
  `FAL_API_KEY` and `assets/avatar.png`).
- `speed: 1.2`. Override `tts.speaking_rate` for this slide only.
- `title: "..."`. Drawn as an amber-accented title strip for image/video slides.

## Commands

```
video-claw init [path]       # scaffold a project
video-claw render            # the main command
video-claw preview           # render slide PNGs only, no TTS spend
video-claw keys list         # show configured keys (masked)
video-claw keys set EL=sk_x  # save a key
video-claw keys test         # verify each key against its provider
video-claw keys path         # print the keys.env path
```

`render` flags:

- `--yes` / `-y`. Skip the interactive preview gate.
- `--no-preview`. Render without even opening the preview server.
- `--out path.mp4`. Override the output path.

## How it renders (one cycle)

1. For each slide: HTML/image/video to PNG (cached by content hash).
2. Open `http://127.0.0.1:<random>/_preview_index.html` and wait for `y` in
   the terminal. The URL is also printed as a copy-paste banner.
3. For each slide: TTS to mp3 + alignment.json, then to m4a with silenceremove
   plus atempo (cached).
4. For slides with `lipsync: True`: upload narration mp3 + avatar PNG to fal.ai,
   poll for the lipsync MP4, crop it to a transparent circle (cached).
5. Per-slide MP4: PNG backdrop + m4a audio + optional lipsync circle overlay (cached).
6. Concat all slide MP4s.
7. If ElevenLabs alignment data exists: build an .ass subtitle file and burn
   it in with libass. Falls back to an SRT sidecar if libass is unavailable.
8. Final MP4 at `out/<name>.mp4`.

## Troubleshooting

**"Couldn't find a Chrome/Chromium binary"**. Install Google Chrome
(https://www.google.com/chrome/), or set `CHROME_BIN=/path/to/chrome`.

**Caption burn fails**. Stock Homebrew ffmpeg lacks libass. Install
`imageio-ffmpeg` (`pipx inject video-claw imageio-ffmpeg`, or
`pip install imageio-ffmpeg` inside your venv). The package will auto-use
its bundled binary just for the caption burn step. Until then, the SRT
sidecar at `video_build/captions.srt` is your captions track.

**Preview did not open in browser**. The URL is printed as a banner before
the launcher fires. Copy it from the terminal. Headless sessions (SSH,
containers) will always need this path.

**Circle lipsync looks washed out**. The avatar source PNG has a transparent
background. OmniHuman preserves transparency; the circle crop then has
artifacts. Fix: flatten the avatar onto solid black before saving it to
`assets/avatar.png`. The bundled default avatar is already flat.

**Stale cache**. Set `FORCE_REGEN=1` in the environment to bypass every
cache layer. Or `rm -rf video_build/`.

## License

MIT. See `LICENSE`.
