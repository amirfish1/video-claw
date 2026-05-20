"""HTML -> PNG rendering via Chrome headless.

We look for a usable Chromium-class binary in this order:
  1. CHROME_BIN env var (explicit user override; highest precedence).
  2. macOS app bundles, stable channel first, then Beta/Dev/Canary, then
     Chromium / Brave (incl. Beta + Nightly) / Microsoft Edge.
  3. `chromium` / `google-chrome` / `chrome` / `microsoft-edge` on PATH
     (Linux + dev shells).
  4. The bundled Playwright Chromium under ~/Library/Caches/ms-playwright/
     (only used if a session previously ran `playwright install chromium`;
      not required for normal use)

The macOS candidate order is kept in sync with install.sh's check_chrome.
If you add a browser here, mirror it in install.sh too.

`render_html_to_png` writes one PNG per HTML file at the requested viewport.
Playwright is not a Python dependency of this package; the renderer shells out
to whichever Chromium binary it finds.
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

    # Keep this list aligned with install.sh:check_chrome().
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
        "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Brave Browser Beta.app/Contents/MacOS/Brave Browser Beta",
        "/Applications/Brave Browser Nightly.app/Contents/MacOS/Brave Browser Nightly",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    for name in (
        "chromium", "google-chrome", "google-chrome-stable",
        "chromium-browser", "brave-browser", "microsoft-edge", "chrome",
    ):
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
            "On macOS, install Google Chrome from https://www.google.com/chrome/.\n"
            "On Linux, install `chromium` or `google-chrome` from your package manager.\n"
            "Or point at an existing binary: CHROME_BIN=/path/to/chrome video-claw render"
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
