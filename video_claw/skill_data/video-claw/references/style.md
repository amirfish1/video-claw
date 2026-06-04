# Slide style guide

This guide is for Claude (or any LLM driving video-claw) when authoring slide
HTML. It captures the design tokens, the typography hierarchy, and the layout
patterns that ship with the package.

## Canvas

```html
<body class="canvas h">  <!-- horizontal: 1920x1080 -->
<body class="canvas v">  <!-- short: 1080x1920 -->
```

The body has fixed `width` and `height`. Headless Chrome screenshots that
exact box. No scrolling, no overflow. Anything outside the canvas is clipped.

Padding is `64px 96px` for horizontal, `96px 72px` for short.

## Design tokens (defined in `slides/_shared.css`)

| Var | Hex | Use |
| --- | --- | --- |
| `--bg` | `#0f1216` | Page background. Don't change. |
| `--panel` | `#161b22` | Cards, code blocks, stat tiles. |
| `--line` | `#2c333d` | Borders, dividers. |
| `--text` | `#ebebe8` | Primary text. |
| `--muted` | `#8c919a` | Secondary text, captions on slides. |
| `--accent` | `#fac85a` | Amber. Main highlight color. |
| `--strike` | `#d97757` | Warm red-orange. "Bad" numbers, struck-through. |
| `--good` | `#7cb37c` | Green. "Good" numbers, success. |

## Type hierarchy

| Element | Horizontal | Short |
| --- | --- | --- |
| `.eyebrow` | 18px, 0.22em tracking, uppercase, amber | 22px |
| `h1` | 64px, 800 weight, -0.02em tracking | 76px |
| `h2` | 40px, 700 weight | 48px |
| `p` | 24px, 1.5 line-height | 30px |

## Helper classes

- `.accent`: amber text
- `.strike`: warm red-orange text
- `.good`: green text
- `.muted`: secondary gray text

## Layout patterns

**Hero (intro/outro).** A centered flex column with eyebrow + h1 + tagline.

```html
<body class="canvas h">
  <div class="hero">
    <div class="title-row">
      <div class="eyebrow">Intro</div>
      <h1>Your hook goes here.</h1>
      <div class="tagline">One sentence frames the topic.</div>
    </div>
  </div>
</body>
```

**Point with stats.** Eyebrow + h1, a supporting paragraph, three stat tiles.

```html
<div class="eyebrow">Section 1</div>
<h1>The point you're making.</h1>
<p>One supporting paragraph. Two sentences max.</p>
<div class="stat-row">
  <div class="stat"><div class="v">42%</div><div class="l">label</div></div>
  ...
</div>
```

**Code or command callout.** A panel with monospaced text. Useful when
demoing CLI usage or a snippet of config.

```html
<div class="code">
  <span class="kw">SLIDES</span> = [...]
</div>
```

Use SF Mono / ui-monospace for the font, ~28px on horizontal, ~36px on short.

## Layout pattern: split (text-left, image-right)

The workhorse pattern for any slide that pairs content with a real-world
asset (product hero, GitHub OG card, README image, site screenshot).

```css
.wrap { display: grid; grid-template-columns: 1fr 720px; gap: 44px;
        height: 100%; align-items: center; }
.left { display: flex; flex-direction: column; justify-content: center; }
.site-img {
  width: 100%; height: auto;
  border-radius: 12px; border: 1px solid var(--line);
  box-shadow: 0 18px 40px rgba(0,0,0,0.45);
}
```

Tweak the right column to 620px when the left side is dense, 720px for
the default. Use `<img src="../assets/X.png" class="site-img">` for img
tags, or set the same background-image rules on a `<div class="shot">`
when you need `background-size: cover` + custom positioning.

## Layout pattern: 2x2 image grid

For "worth bookmarking" / community-OSS / "tools to know" slides:

```css
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px;
        flex: 1; align-items: stretch; }
.card { background: var(--panel); border: 1px solid var(--line);
        border-radius: 14px; overflow: hidden;
        box-shadow: 0 12px 28px rgba(0,0,0,0.35); }
.card img { width: 100%; height: 100%; object-fit: cover; }
```

Each card gets one image (typically a GitHub OG card). Eyebrow + h1 +
one-line subtitle goes above the grid.

## Layout pattern: vs comparison with real product imagery

Use when two products solve different problems and a side-by-side helps:

```css
.face-off { display: grid; grid-template-columns: 1fr 60px 1fr;
            gap: 14px; flex: 1; }
.pane { background: var(--panel); border: 1px solid var(--line);
        border-radius: 16px; overflow: hidden; }
.pane .img { width: 100%; height: 460px;
             background-size: cover; background-position: center; }
.pane .body { padding: 22px 28px; }
.vs { display: flex; align-items: center; justify-content: center;
      font-size: 36px; font-weight: 800; color: var(--strike); }
```

Each pane stacks an image area (background-image set per pane via inline
or pane-specific class) + a body with name, tag, and one-line description.

## Static presenter avatar (corner overlay)

When you want Becky (or any avatar) visible on every slide WITHOUT the
fal.ai lipsync charge ($0.16/sec), inject this rule into `_shared.css`:

```css
body.canvas::after {
  content: "";
  position: absolute;
  right: 48px; bottom: 48px;
  width: 132px; height: 132px;
  border-radius: 50%;
  background: #000 url('../assets/avatar.png') no-repeat center / cover;
  border: 3px solid var(--accent);
  box-shadow: 0 14px 32px rgba(0,0,0,0.55);
  z-index: 9999;
}
body.canvas.v::after { width: 150px; height: 150px; right: 60px; bottom: 60px; }
```

Zero cost (pure CSS), no per-slide HTML changes. Differs from the
fal.ai-driven lipsync avatar (which is animated but charged per second).

## Visual variance ratio

At least 1 image-bearing slide per 4 slides total. Counting:

- A slide with a real photo / screenshot / OG card / product hero = 1
- A slide with a stat row, vs comparison, or 4-cell grid (text-only) = 0.3
- A slide with one big quote and an attribution line = 0
- A pure title or section-divider slide = 0

If the running ratio drops below 0.25, the next slide should be
image-bearing. Sections feel "tired" when they run >4 text-only in a row.

## Hard rules

- **No em-dashes.** Use comma, period, or colon.
- **One headline + one supporting element per slide.** If you are tempted
  to add a second paragraph below a stat row, that is a second slide.
- **The narration carries the meaning.** Slides anchor visually. Don't
  paste the entire narration onto the slide.
- **Real assets.** No lorem ipsum, no placeholder screenshots. See
  `assets.md` for programmatic sources before asking the user.
- **No curator's voice.** "Killer line", "single biggest thing", "your
  stack", "you already did" — these reveal human ranking. Default to
  flat observational tone. Quotes from the source are the exception.

## Lipsync slide layout

When `lipsync: True` is set on a slide, the fal.ai presenter circle is
overlaid in the bottom-right corner (~280px diameter, ~70px from the
edges). Leave that area empty:

- `margin-right` at least 360px for headlines that extend across the canvas
- avoid placing critical content in the bottom-right ~340px square

The CSS in `_shared.css` does not handle this for you; bear it in mind when
laying out lipsync slides.
