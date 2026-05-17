# Quickstart example: 30-second explainer

A minimal 3-slide narrated video to verify everything works end-to-end.

## Run it

```
cd examples/quickstart
make-narrated-video render
```

You'll see the preview gate in your browser. Press `y` in the terminal to
proceed. Render time: roughly 30 seconds (mostly TTS + Chromium boot).

Output: `out/quickstart.mp4`.

## What's in it

```
quickstart/
├── slides.py            # SLIDES list (intro, point, outro) + CONFIG
├── slides/
│   ├── _shared.css      # design tokens (copied from package)
│   ├── intro.html
│   ├── point.html
│   └── outro.html
└── assets/              # empty — no images used in this example
```

Three slides, ~30 sec total, no lipsync, no images. Tests:

- Chromium HTML → PNG rendering for both orientations (toggle `CONFIG.orientation`).
- ElevenLabs TTS with timestamps.
- Caption alignment + burn via libass.
- Cache layer (re-run: should complete in under 2 seconds).

## After it works

Try:

- Edit `slides.py`: change the narration on `point`, re-render. Only that slide's
  TTS regenerates. Other two come from cache.
- Toggle `CONFIG.orientation = "short"`, re-render. PNGs regenerate; TTS reused.
- Add `"lipsync": True` on the intro slide (requires `FAL_API_KEY` + a flattened
  PNG at `assets/avatar.png`).
