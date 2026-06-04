# Asset sourcing

The SKILL.md "real assets only" rule is hard: no placeholders, no
lorem-ipsum screenshots. But "ask the user for the asset" should be the
LAST resort. Most useful product imagery is publicly fetchable in seconds.
Try these programmatic sources first.

## Quick decision tree

1. Does the slide mention a GitHub repo? → **GitHub OG card** (below)
2. Does the slide mention a product or landing page? → **Headless Chrome screenshot**
3. Does the slide mention an OSS project with a polished README? → **README hero image**
4. Does the slide mention a YouTube video? → **YouTube thumbnail**
5. None of the above? → Ask the user for the actual asset.

---

## 1. GitHub OG cards

GitHub generates a 1200×600 social preview card for every public repo.
Predictable URL pattern, no auth required:

```
https://opengraph.githubassets.com/{anyhash}/{owner}/{repo}
```

Any string works as `{anyhash}` (it's just a cache-buster). The result
is a PNG that shows repo name, description, contributor / star / fork
counts, and the project's social-preview image if one is configured.

Example:
```bash
curl -sL -o "assets/gh_memongo.png" \
  "https://opengraph.githubassets.com/abc/romiluz13/Memongo"
```

**Rate limit:** ~10 requests/min per IP. On 429-ish responses (or a
42-byte HTML "Too many requests" body), wait 5 seconds and retry.

**Use:** put these in side-panel position in a split layout, or stack
2x2 / 3x1 grids for "Worth bookmarking" / community-OSS slides.

---

## 2. Headless Chrome screenshots

For any public landing page, hero, or product site:

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --screenshot=assets/X.png \
  --window-size=1920,1080 \
  --virtual-time-budget=5000 \
  "https://example.com"
```

**Binary fallbacks** (if stable Chrome isn't installed):
- `/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta`
- `/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary`
- `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`
- `/Applications/Chromium.app/Contents/MacOS/Chromium`

Use `command -v` or `[ -f ... ]` to pick whichever exists.

**The chrome-devtools MCP fails when the .app exists but its binary is
named differently** (e.g. Chrome Beta installed as "Google Chrome.app"
but the executable inside is "Google Chrome Beta"). Bypass the MCP and
shell out directly to the real path.

**Cropping:** Chrome captures the visible viewport at the given window
size. For hero shots, 1920×1080 works. For card-sized insets, capture
at 1280×720 then let CSS `object-fit: cover` handle the rest.

**Light vs dark sites:** if a slide uses the dark theme tokens and the
captured site is light, frame the image with a white panel + drop shadow
so it doesn't fight the slide. Don't try to invert it.

---

## 3. Repo README hero images

The strongest single asset for a polished OSS project is usually the
hand-designed hero image in its README, not the OG card.

```bash
# Fetch README, find first img tag, download
curl -sL "https://raw.githubusercontent.com/{owner}/{repo}/main/README.md" \
  | grep -m1 -oE '<img src="[^"]+"|!\[[^]]*\]\([^)]+\)'
# Parse the src, resolve relative paths against raw.githubusercontent.com/{owner}/{repo}/main/
```

Fall back to `/master/README.md` if `/main/` 404s.

**Gotcha:** the file extension is often unreliable. README hero images
labelled `.png` are frequently JPEG. Use `file <path>` to verify, but
HTML `<img>` tags handle either transparently — the slide will render
correctly either way.

**When to prefer this over the OG card:** when the project has a strong
brand identity and the README hero is hand-designed. Most serious OSS
authors invest in this. Indicators: filenames like `hero.png`, `banner.png`,
`README-hero.png`, or `assets/og-image.png` near the top of the README.

---

## 4. YouTube thumbnails

Predictable URL — no API key, no scraping:

```
https://img.youtube.com/vi/{VIDEO_ID}/maxresdefault.jpg
```

The video ID is the 11-character string after `v=` in the watch URL,
or the path segment in `youtu.be/{ID}`. Falls back to:
- `hqdefault.jpg` if `maxresdefault` 404s (some old videos lack the
  1280×720 thumbnail)

---

## 5. When all programmatic sources fail

Then ask the user, per the SKILL.md "real assets only" rule. Don't
generate a placeholder.

If the user can't provide one and the slide is conceptual (a quote,
a stat, a comparison), the no-image text layout is fine — use the
"variance ratio" rule (at least 1 image per 4 slides) to decide whether
the next slide needs imagery to compensate.

---

## Misc gotchas

- **pipx editable installs.** If video-claw is installed via pipx in
  editable mode (`pipx install -e ~/path/to/video-claw`), the venv's
  `site-packages/video_claw/` is a DEAD copy. The actual loaded code
  lives at the editable source path. Confirm with:
  ```bash
  $(which video-claw)... -c "import video_claw; print(video_claw.__file__)"
  ```
  before editing source files. Or use the `fetch-asset` CLI (Layer 3)
  which abstracts this away.

- **Naming convention.** Use `assets/gh_<owner>_<repo>.png` for GH OG
  cards, `assets/shot_<sluggified_url>.png` for screenshots, and
  `assets/readme_<repo>.png` for README hero images. Makes them easy
  to find later and avoids name collisions.
