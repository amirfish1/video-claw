"""HTML -> PNG rendering via Chrome headless or Playwright Chromium fallback.

We look for a usable Chromium-class binary in this order:
  1. CHROME_BIN env var (explicit user override)
  2. /Applications/Google Chrome.app/Contents/MacOS/Google Chrome  (macOS)
  3. /Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta
  4. /Applications/Chromium.app/Contents/MacOS/Chromium
  5. `chromium` / `google-chrome` / `chrome` on PATH (Linux/dev)
  6. The bundled Playwright Chromium under ~/Library/Caches/ms-playwright/

`render_html_to_png` writes one PNG per HTML file at the requested viewport.
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _find_chrome_binary() -> Optional[str]:
    explicit = os.environ.get("CHROME_BIN")
    if explicit and Path(explicit).exists():
        return explicit

    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    for name in ("chromium", "google-chrome", "chrome", "google-chrome-stable"):
        p = shutil.which(name)
        if p:
            return p

    # Playwright cache fallback (macOS Library, Linux ~/.cache)
    pw_root_candidates = [
        Path.home() / "Library/Caches/ms-playwright",
        Path.home() / ".cache/ms-playwright",
    ]
    for root in pw_root_candidates:
        if not root.exists():
            continue
        # Prefer full chromium over headless_shell because headless_shell
        # has historically lacked the --screenshot flag we use.
        for prefix in ("chromium-", "chromium_headless_shell-"):
            matches = sorted(root.glob(f"{prefix}*"))
            if not matches:
                continue
            latest = matches[-1]
            for rel in (
                "chrome-mac/Chromium.app/Contents/MacOS/Chromium",
                "chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium",
                "chrome-linux/chrome",
            ):
                candidate = latest / rel
                if candidate.exists():
                    return str(candidate)
    return None


def render_html_to_png(html_path: Path, png_path: Path, width: int, height: int) -> Path:
    """Render `html_path` (a local file) to `png_path` at the given viewport.

    Uses Chrome headless. The HTML can `<link>`/`<img>` neighbouring files via
    relative paths because we pass a `file://` URL pointing at the actual file.
    """
    chrome = _find_chrome_binary()
    if chrome is None:
        raise RuntimeError(
            "Couldn't find a Chrome/Chromium binary to render HTML.\n"
            "Install Google Chrome (https://www.google.com/chrome/), set $CHROME_BIN,\n"
            "or run: npx -y playwright install chromium\n"
        )

    html_path = html_path.resolve()
    png_path = png_path.resolve()
    png_path.parent.mkdir(parents=True, exist_ok=True)

    url = f"file://{html_path}"
    cmd = [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--hide-scrollbars",
        "--disable-gpu",
        "--force-device-scale-factor=1",
        f"--window-size={width},{height}",
        f"--screenshot={png_path}",
        # Give web fonts and images a beat to load before snapshot.
        "--virtual-time-budget=2000",
        "--default-background-color=00000000",
        url,
    ]
    # Chrome writes the screenshot to cwd by default unless --screenshot=PATH is absolute.
    # We pass absolute paths above so cwd doesn't matter.
    res = subprocess.run(cmd, capture_output=True, timeout=60)
    if not png_path.exists():
        raise RuntimeError(
            f"Chrome screenshot failed for {html_path.name}.\n"
            f"stderr: {res.stderr.decode(errors='ignore')[-600:]}"
        )
    return png_path


def render_all(slide_dir: Path, png_dir: Path, slides: list, width: int, height: int) -> list[Path]:
    """Render every HTML-typed slide to a PNG. Image / video slides skip rendering.
    Returns the per-slide PNG path (or None for non-HTML slides, in order).
    """
    pngs: list[Optional[Path]] = []
    for idx, slide in enumerate(slides):
        kind = slide.get("type", "image")
        if kind == "html":
            src = slide.get("html")
            if not src:
                raise ValueError(f"slide {idx}: type=html requires `html` field")
            html_path = (slide_dir / src).resolve()
            if not html_path.exists():
                raise FileNotFoundError(f"slide {idx}: HTML file not found: {html_path}")
            png_path = png_dir / f"slide_{idx:02d}.png"
            print(f"  [html->png] slide {idx:02d}: {src} -> {png_path.name}")
            render_html_to_png(html_path, png_path, width, height)
            pngs.append(png_path)
        else:
            pngs.append(None)
    return pngs
