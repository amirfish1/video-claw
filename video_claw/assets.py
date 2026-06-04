"""Programmatic asset fetchers.

The "real assets only" rule (see SKILL.md) is strict, but most of the
imagery a slide deck needs is publicly fetchable without asking the user.
This module wraps the patterns documented in references/assets.md:

    gh:owner/repo        → GitHub OG card (1200×600 PNG)
    shot:https://...     → Headless Chrome screenshot of a public URL
    readme:owner/repo    → First <img> from the repo's README (often a
                            hand-designed hero, stronger than OG card)
    yt:VIDEO_ID          → YouTube thumbnail (maxresdefault.jpg)

All fetchers save to a project's `assets/` directory with a predictable
filename so subsequent slide HTML can reference them via `../assets/X`.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


# Chrome binaries we'll try in order. First one that exists wins. The
# MCP-style "Could not find Google Chrome executable" error often hits
# people who only have Beta or Canary installed; bypass it by shelling
# out to the actual path.
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


def _find_chrome() -> Optional[str]:
    """Return the first Chrome-class binary that exists, or None."""
    # PATH lookup first (Linux / nix users)
    for name in ("google-chrome", "chromium", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    # macOS app bundles
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _http_get(url: str, *, max_retries: int = 3, retry_wait: float = 5.0) -> bytes:
    """GET a URL with retries on transient errors. Returns body bytes."""
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "video-claw/fetch-asset"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            # Rate limit on GitHub OG endpoint comes back as 4xx with a
            # short HTML body. Retry once then give up.
            if e.code in (429, 503) and attempt + 1 < max_retries:
                time.sleep(retry_wait)
                last_err = e
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt + 1 < max_retries:
                time.sleep(retry_wait)
                last_err = e
                continue
            raise
    raise last_err or RuntimeError("http_get failed without exception")


def _slugify(s: str) -> str:
    """Make a string filesystem-safe."""
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s).strip("_")[:80]


def fetch_gh_og(spec: str, assets_dir: Path) -> Path:
    """Fetch a GitHub OG card. spec is 'owner/repo'."""
    if "/" not in spec or spec.count("/") != 1:
        raise ValueError(f"expected 'owner/repo', got {spec!r}")
    owner, repo = spec.split("/", 1)
    # any-string-as-cachebuster
    url = f"https://opengraph.githubassets.com/cb{int(time.time())}/{owner}/{repo}"
    body = _http_get(url)
    # Sanity: GH returns short text body on rate-limit / 404. Real PNGs
    # are >5KB and start with the PNG magic bytes.
    if len(body) < 1000 or not body.startswith(b"\x89PNG"):
        snippet = body[:80].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"GitHub OG fetch returned non-PNG content: {snippet!r}")
    out = assets_dir / f"gh_{_slugify(repo)}.png"
    out.write_bytes(body)
    return out


def fetch_yt_thumb(video_id: str, assets_dir: Path) -> Path:
    """Fetch a YouTube thumbnail by video ID."""
    # Strip common URL prefixes if user pasted a full URL
    m = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", video_id)
    if m:
        video_id = m.group(1)
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError(f"not a YouTube video id: {video_id!r}")
    for quality in ("maxresdefault", "hqdefault", "mqdefault"):
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            body = _http_get(url, max_retries=1)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
        if len(body) > 500:
            out = assets_dir / f"yt_{video_id}.jpg"
            out.write_bytes(body)
            return out
    raise RuntimeError(f"no thumbnail found for video {video_id}")


def fetch_readme_hero(spec: str, assets_dir: Path) -> Path:
    """Fetch the first image referenced in a repo README."""
    if "/" not in spec:
        raise ValueError(f"expected 'owner/repo', got {spec!r}")
    owner, repo = spec.split("/", 1)
    readme = None
    base = None
    for branch in ("main", "master"):
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            readme = _http_get(url, max_retries=1).decode("utf-8", errors="replace")
            base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"
            break
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    if readme is None or base is None:
        raise RuntimeError(f"no README found for {spec} on main or master")

    # Find first <img src="..."> OR ![](url) in the README body. Skip
    # GitHub-action/CI badges (they're shields, not hero imagery).
    img_url: Optional[str] = None
    for match in re.finditer(
        r'(?:<img\s+[^>]*src=["\']([^"\']+)["\'])'
        r'|(?:!\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\))',
        readme,
    ):
        candidate = match.group(1) or match.group(2)
        if not candidate:
            continue
        low = candidate.lower()
        if any(s in low for s in ("shields.io", "img.shields.io", "/badge", "github.com/.../workflows")):
            continue
        img_url = candidate
        break
    if img_url is None:
        raise RuntimeError(f"no usable image found in README for {spec}")

    # Resolve relative to raw base
    if img_url.startswith(("http://", "https://")):
        full = img_url
    elif img_url.startswith("./"):
        full = base + img_url[2:]
    elif img_url.startswith("/"):
        full = f"https://raw.githubusercontent.com/{owner}/{repo}/main{img_url}"
    else:
        full = base + img_url
    body = _http_get(full)
    # README hero images are often JPEG labelled .png; the renderer
    # doesn't care, but keep the source extension if recognizable.
    ext = ".png" if full.lower().endswith(".png") else ".jpg" if full.lower().endswith((".jpg", ".jpeg")) else ".png"
    out = assets_dir / f"readme_{_slugify(repo)}{ext}"
    out.write_bytes(body)
    return out


def fetch_shot(url: str, assets_dir: Path, *, width: int = 1920, height: int = 1080) -> Path:
    """Take a headless Chrome screenshot of a public URL."""
    chrome = _find_chrome()
    if not chrome:
        raise RuntimeError(
            "no Chrome-class binary found. Install Google Chrome, Chrome "
            "Beta, Brave, or Chromium, or set CHROME env var to the binary."
        )
    slug = _slugify(re.sub(r"^https?://", "", url))
    out = assets_dir / f"shot_{slug}.png"
    cmd = [
        chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
        f"--screenshot={out}",
        f"--window-size={width},{height}",
        "--virtual-time-budget=5000",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(
            f"chrome screenshot failed (rc={result.returncode}): "
            f"{result.stderr.strip()[:200]}"
        )
    return out


def dispatch(spec: str, assets_dir: Path) -> Path:
    """Route a 'kind:value' spec to the right fetcher."""
    kind, _, value = spec.partition(":")
    if not value:
        raise ValueError(f"spec missing colon-separated value: {spec!r}")
    handlers = {
        "gh": fetch_gh_og,
        "yt": fetch_yt_thumb,
        "readme": fetch_readme_hero,
        "shot": fetch_shot,
    }
    handler = handlers.get(kind)
    if handler is None:
        raise ValueError(f"unknown kind {kind!r}, expected one of: {', '.join(handlers)}")
    return handler(value, assets_dir)
