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

- `.accent` — amber text
- `.strike` — warm red-orange text
- `.good` — green text
- `.muted` — secondary gray text

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

## Hard rules

- **No em-dashes.** Use comma, period, or colon.
- **One headline + one supporting element per slide.** If you are tempted
  to add a second paragraph below a stat row, that is a second slide.
- **The narration carries the meaning.** Slides anchor visually. Don't
  paste the entire narration onto the slide.
- **Real assets.** No lorem ipsum, no placeholder screenshots.

## Lipsync slide layout

When `lipsync: True` is set on a slide, the fal.ai presenter circle is
overlaid in the bottom-right corner (~280px diameter, ~70px from the
edges). Leave that area empty:

- `margin-right` at least 360px for headlines that extend across the canvas
- avoid placing critical content in the bottom-right ~340px square

The CSS in `_shared.css` does not handle this for you; bear it in mind when
laying out lipsync slides.
