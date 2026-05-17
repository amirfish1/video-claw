# Troubleshooting

## Install

### `pip install` fails with "externally-managed-environment"

Stock Homebrew Python 3.12+ blocks system-wide pip installs (PEP 668). Use
pipx (which manages its own venv):

```
pipx install git+https://github.com/amirfish1/video-claw
```

If pipx isn't installed: `brew install pipx`.

Or use a venv:

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install git+https://github.com/amirfish1/video-claw
```

### `video-claw: command not found` after pip install

The CLI was installed to a venv that isn't on PATH. With pipx, `pipx ensurepath`
fixes this. With plain pip in a venv, source `.venv/bin/activate` before
running `video-claw`.

### "Couldn't find a Chrome/Chromium binary"

The renderer needs a Chromium-class browser to screenshot HTML.

- **macOS:** install Google Chrome from https://www.google.com/chrome/.
- **Linux:** `apt install chromium` or `apt install google-chrome-stable`.
- **Existing binary somewhere odd:** `CHROME_BIN=/path/to/chrome video-claw render`.

Playwright is not required. If you already ran `playwright install chromium`
in some other project, the package will find that binary as a last resort,
but installing Playwright just for video-claw is overkill.

## Keys

### `keys test` shows `[FAIL] ELEVENLABS_API_KEY: not set`

You need an ElevenLabs key for the default TTS provider. Get one at
https://elevenlabs.io/app/settings/api-keys, then:

```
video-claw keys set EL=sk_xxx
```

### `keys test` shows `[opt] FAL_API_KEY: not set (optional)`

That's fine. You only need a fal.ai key if some slide has `lipsync: True`.

### `keys test` shows `[opt] DEEPGRAM_API_KEY: not set (optional)`

Same. Deepgram is only needed if you've set `tts.provider="deepgram"` in
your slides.py.

## Rendering

### Caption burn fails, "ffmpeg said: No option name near..."

Stock Homebrew ffmpeg 8.x rejects the ass-filter path syntax that older
ffmpeg builds accept. The package already uses `filename='...'` quoting to
work around this; if you still see the error, it means your ffmpeg also
lacks libass entirely.

Fix: install `imageio-ffmpeg` (ships a libass-enabled static ffmpeg):

```
pipx inject video-claw imageio-ffmpeg
```

(or `pip install imageio-ffmpeg` inside your venv).

Until then the package ships the captions as an SRT sidecar at
`video_build/captions.srt`. Many players accept that as an external track.

### Browser did not auto-open at preview

The package prints the preview URL as a copy-paste banner before launching
the browser. Look for the boxed URL in the output and open it manually. If
you're in a headless session (SSH, container) that is the only way.

### Lipsync circle has a transparent-checker pattern

Your avatar PNG has an alpha channel. fal.ai's OmniHuman preserves it, and
then the circle crop bakes the checker into the corners. Re-save the
avatar onto a solid black background (RGB, no alpha).

### Slide PNG looks broken

Open the source HTML in a real browser at the canvas resolution
(1920x1080 or 1080x1920). Headless Chrome renders exactly that viewport,
so anything that's clipped, mis-sized, or missing a font in the browser
will be wrong in the PNG too.

Common fixes:
- web font hasn't loaded: bump `--virtual-time-budget` (in the renderer)
  or use a system font
- image not showing: check `file://` paths in your HTML resolve correctly
- text overflowing: shrink the font or split into two slides

## Caches

### "I changed X but the output is the same"

The content-hash cache only re-runs steps whose inputs changed. If the
TTS audio looks stale, you probably edited HTML but the narration text is
identical, so the TTS step is a cache hit (correct behavior; TTS only
re-runs on narration changes).

To bypass every cache for one run:

```
FORCE_REGEN=1 video-claw render
```

To wipe a single project's cache:

```
rm -rf video_build/
```

The next render rebuilds everything.
