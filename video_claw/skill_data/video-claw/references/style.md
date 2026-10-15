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

Set `CONFIG["tts"]["lipsync"] = "static"` to place a still circular presenter
on every slide, or set `"lipsync": "static"` on selected slides. The renderer
crops `assets/avatar.png` once and loops the transparent PNG locally. No FAL
request or avatar charge. A slide's `"lipsync": False` overrides that default.
`True` or `"fal"` explicitly requests the paid animated presenter.

Use `lipsync_avatar` on a slide or `CONFIG["lipsync"]["avatar"]` for a different
portrait. Static mode falls back to the bundled portrait if the image is
missing. The separate `avatar.static` option still supports scoped badges
(`all`, `intro`, or `flagged`) and a custom diameter. Leave the bottom-right
corner clear as described under Lipsync slide layout.

## Visual variance ratio

At least 1 image-bearing slide per 4 slides total. Counting:

- A slide with a real photo / screenshot / OG card / product hero = 1
- A slide with a stat row, vs comparison, or 4-cell grid (text-only) = 0.3
- A slide with one big quote and an attribution line = 0
- A pure title or section-divider slide = 0

If the running ratio drops below 0.25, the next slide should be
image-bearing. Sections feel "tired" when they run >4 text-only in a row.

## Narration patterns

Use these defaults for story-driven explainers; visual memes may use voice
bookends with a silent middle.

1. **Keep voiceover continuous.** Narrate the full story across slides.
   ElevenLabs renders one master take and slices it using character alignment
   so the speaker's delivery carries through cuts.
2. **Assume no prior context.** Titles are visual shorthand. Narration explains
   the meaning in plain English rather than reading each title verbatim.
3. **Keep first person consistent.** When the speaker is the protagonist, use
   first person in both narration and titles. Before rendering, run
   `rg -ni '\b(he|his|him)\b' slides --glob '*.html'` and inspect any matches
   for accidental shifts to third person; quotes and other people may be valid.
4. **Give advice plus evidence.** Prefer "Do X. The research found N winners
   doing X" to "Every winner does X." Use supported numbers and follow with
   the practical takeaway.
5. **Put the full hook on slide 0.** Its visual title states the complete
   premise that creates the curiosity gap. Opening narration expresses that
   same premise; later titles can be shorter.
6. **Spend words where the insight is.** Setup slides such as "I posted on
   Reddit" need one sentence. Insight slides get two or three: advice,
   evidence, takeaway. Give them roughly twice the narration of setup slides.
7. **Explain jargon inline.** Add a short visible pill on first use, such as
   "HN (Hacker News, run by Y Combinator)." Explain domain terms for viewers
   outside the niche without turning the slide into a paragraph.
8. **Make the recap the CTA.** Recount the arc and connect it to a specific
   next action. "Open source, link in description" alone is too detached
   from what the viewer just learned.
9. **Skip before/after recap slides.** A closing "before bad / after good"
   comparison repeats the explainer and can feel patronizing. Trust viewers
   to draw the contrast; use the outro for the recap and next action.
10. **Budget words before writing.** At natural ElevenLabs Turbo v2.5 pacing
    (~150 words/minute), target seconds × 2.5 words: 60s ≈ 150, 90s ≈ 225,
    120s ≈ 300. Allocate per-slide counts, favoring insight slides, and leave
    room for pauses. Start at `speaking_rate: 1.0` and `speed: 1.0`; when
    delivery feels rushed, remove any speedup before cutting useful words.

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
  plain, evidence-backed advice without hype. Quotes from the source are
  the exception.

## Lipsync slide layout

When `lipsync: True`, `"fal"`, or `"static"` is set on a slide (or as the
`tts.lipsync` default), the presenter circle is overlaid in the bottom-right
corner (~280px diameter, ~70px from the edges). Leave that area empty:

- `margin-right` at least 360px for headlines that extend across the canvas
- avoid placing critical content in the bottom-right ~340px square

The CSS in `_shared.css` does not handle this for you; bear it in mind when
laying out lipsync slides.
