# make-narrated-video

Render narrated slide videos from a list of HTML slides + narration text. Optional lip-synced AI presenter via fal.ai OmniHuman. Burned-in word-aligned captions via ElevenLabs.

Built for macOS. Works on Linux. Single Python package, single CLI.

```
make-narrated-video init my-vid
cd my-vid
make-narrated-video keys set EL=sk_...   # or export ELEVENLABS_API_KEY
make-narrated-video render
```

## What you get

- **HTML slides** — write them like web pages with full CSS. No bespoke DSL.
- **Two orientations** — `horizontal` (1920×1080) and `short` (1080×1920) for Shorts/TikTok/Reels.
- **Two TTS providers** — ElevenLabs (default, with timestamps for captions) or Deepgram (cheap fallback, no captions).
- **Optional lipsync** — set `lipsync: True` on intro/outro slides; fal.ai renders a circular presenter badge.
- **Word-aligned captions** — burned in via libass.
- **Preview gate** — local web server shows every slide PNG in a grid before any paid API is hit.
- **Content-hash cache** — re-runs are seconds, not minutes. Iterate freely.

## Install

```
pip install git+https://github.com/amirfish1/make-narrated-video
```

You also need:

- **Python 3.10+**
- **Playwright** (for HTML → PNG): `pip install playwright && playwright install chromium`
- **ffmpeg + ffprobe** in PATH. Homebrew ffmpeg works for everything except caption burn-in. The package detects `imageio-ffmpeg` (`pip install imageio-ffmpeg`) and uses its bundled full-featured ffmpeg for the caption step if your system ffmpeg lacks libass.

## API keys

You need at least one TTS provider key. Lipsync is opt-in.

| Key | What for | Where to get it |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | Default TTS + word-level captions | https://elevenlabs.io/app/settings/api-keys |
| `FAL_API_KEY` | Optional lipsync (OmniHuman 1.5) | https://fal.ai/dashboard/keys |
| `DEEPGRAM_API_KEY` | Optional cheaper TTS (no captions) | https://console.deepgram.com/project/_/api-keys |

Store them once at `~/.config/make-narrated-video/keys.env` (mode 0600):

```
make-narrated-video keys set EL=sk_xxx FAL=xxx
make-narrated-video keys test
```

Or just export as env vars: `ELEVENLABS_API_KEY=...`. Env wins over the file.

## Cost

For a typical 5-minute narrated video with ~30 sec of lipsync bookends:

| Item | Rate | 5-min video |
| --- | --- | --- |
| ElevenLabs Turbo v2.5 (with-timestamps) | ~$0.30 / min of audio | $1.50 |
| fal.ai OmniHuman 1.5 lipsync | $0.16 / sec of generated video | $4.80 (30 sec) |
| **Total** | | **~$6.30** |

Deepgram Aura-2 TTS is ~$0.015/1k chars and skips captions; for a 5-min video that's roughly $0.10. Captions need ElevenLabs.

The content-hash cache means you only pay once per unique narration string + voice + speed. Re-render to fix a CSS typo: free.

## Project layout

A project is a directory. After `make-narrated-video init my-vid`:

```
my-vid/
├── slides.py          # SLIDES = [...] and CONFIG = {...}
├── slides/
│   ├── _shared.css    # design tokens
│   ├── intro.html
│   ├── point_one.html
│   └── outro.html
├── assets/
│   └── avatar.png     # only used if a slide has lipsync: True
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
        "narration": "Hi, I'm Becky. Here is what we're covering today.",
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

- `html` — Chromium renders the file at canvas size. Use `_shared.css` for tokens.
- `image` — wrapped in a Chromium template; gets a title strip if `title` is set.
- `video` — drawn as a backdrop with a viewport rectangle; the clip is composited via ffmpeg.

Optional fields on any slide:

- `lipsync: True` — overlay a fal.ai OmniHuman circle on this slide (requires FAL_API_KEY + `assets/avatar.png`).
- `speed: 1.2` — override `tts.speaking_rate` for this slide only.
- `title: "..."` — drawn as an amber-accented title strip for image/video slides.

## Commands

```
make-narrated-video init [path]       # scaffold a project
make-narrated-video render            # the main command
make-narrated-video preview           # render slide PNGs only, no TTS spend
make-narrated-video keys list         # show configured keys (masked)
make-narrated-video keys set EL=sk_x  # save a key
make-narrated-video keys test         # verify each key against its provider
make-narrated-video keys path         # print the keys.env path
```

`render` flags:

- `--yes` / `-y` — skip the interactive preview gate
- `--no-preview` — render without even opening the preview server
- `--out path.mp4` — override the output path

## How it renders (one cycle)

1. For each slide: HTML/image/video → PNG (cached by content hash).
2. Open `http://127.0.0.1:<random>/_preview_index.html` and wait for `y` in the terminal.
3. For each slide: TTS → mp3 + alignment.json → m4a with silenceremove + atempo (cached).
4. For slides with `lipsync: True`: upload narration mp3 + avatar PNG to fal.ai, poll for the lipsync MP4, crop it to a transparent circle (cached).
5. Per-slide MP4: PNG backdrop + m4a audio + optional lipsync circle overlay (cached).
6. Concat all slide MP4s.
7. If ElevenLabs alignment data exists: build an .ass subtitle file and burn it in with libass.
8. Final MP4 at `out/<name>.mp4`.

## Troubleshooting

**"subtitles filter not available"** — your ffmpeg lacks libass. Install `imageio-ffmpeg` (`pip install imageio-ffmpeg`); the package will auto-use its bundled binary just for the caption burn step.

**Circle lipsync looks washed out** — the avatar source PNG has a transparent background. OmniHuman preserves transparency; the circle crop then has artifacts. Fix: flatten the avatar onto solid black before saving it to `assets/avatar.png`.

**Stale cache** — set `FORCE_REGEN=1` in the environment to bypass every cache layer.

**Playwright fails on `chromium not found`** — `playwright install chromium` (the install step is separate from the pip install).

## License

MIT. See `LICENSE`.
