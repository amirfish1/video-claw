"""Local preview server with a slide-grid HTML. Used to gate expensive TTS/fal calls.

Workflow:
  1. Engine has rendered every slide PNG into `out_dir`.
  2. We spawn a detached child process that serves `out_dir` on a random free port.
  3. Open the user's browser to the grid view.
  4. Wait for `input()` ("y" to proceed, anything else to abort).
  5. Render continues in the parent. The child server stays up for `preview_ttl`
     seconds so the URL remains clickable long after `video-claw render` returns.

TTL resolution order:
  * explicit `preview_ttl` argument to `prompt_user`
  * env var `VIDEO_CLAW_PREVIEW_TTL`
  * default: 3600 (interactive TTY) or 60 (headless / CI)

`preview_ttl=0` keeps the legacy behavior: server dies the instant the user
confirms or aborts. Negative values are rejected at the CLI parser.
"""
from __future__ import annotations
import contextlib
import functools
import http.server
import os
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_TTL_INTERACTIVE = 3600
DEFAULT_TTL_HEADLESS = 60


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _default_ttl() -> int:
    # Headless / CI fallback: don't let a forgotten preview hog a port forever.
    try:
        tty = os.isatty(0)
    except Exception:
        tty = False
    return DEFAULT_TTL_INTERACTIVE if tty else DEFAULT_TTL_HEADLESS


def resolve_ttl(explicit: Optional[int]) -> int:
    """Pick the TTL value, honoring the explicit arg, then env, then the default.

    Negative values are normalized to 0 here as a defence-in-depth check —
    the CLI parser already rejects negatives with a clear error.
    """
    if explicit is not None:
        return max(0, int(explicit))
    env_val = os.environ.get("VIDEO_CLAW_PREVIEW_TTL")
    if env_val is not None and env_val.strip() != "":
        try:
            return max(0, int(env_val))
        except ValueError:
            print(
                f"[preview] ignoring invalid VIDEO_CLAW_PREVIEW_TTL={env_val!r} "
                "(want an integer number of seconds)",
                file=sys.stderr,
            )
    return _default_ttl()


def _fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m{s}s" if s else f"{m}m"
    h, rem = divmod(seconds, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h{m}m" if m else f"{h}h"


def _build_index(out_dir: Path, slides: Iterable[dict], orientation: str) -> Path:
    """Write a one-shot index.html grid of slide PNGs into out_dir."""
    rows = []
    for idx, slide in enumerate(slides):
        png = out_dir / f"slide_{idx:02d}.png"
        narration = (slide.get("narration") or "").strip()
        title = slide.get("title") or slide.get("html") or slide.get("image") or slide.get("video") or f"slide {idx}"
        narration_html = narration.replace("<", "&lt;").replace(">", "&gt;")
        if png.exists():
            img_tag = f'<img src="slide_{idx:02d}.png" loading="lazy">'
        else:
            img_tag = '<div class="missing">(no PNG yet)</div>'
        rows.append(
            f'''<div class="card">
  <div class="hd"><span class="idx">#{idx:02d}</span> <span class="ttl">{title}</span></div>
  {img_tag}
  <div class="narr">{narration_html}</div>
</div>'''
        )

    grid_template = (
        "grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));"
        if orientation == "horizontal"
        else "grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));"
    )

    html = f"""<!doctype html>
<meta charset="utf-8">
<title>video-claw preview</title>
<style>
  :root {{
    --bg: #0f1216; --panel: #161b22; --line: #2c333d;
    --text: #ebebe8; --muted: #8c919a; --accent: #fac85a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 28px 36px;
    background: var(--bg); color: var(--text);
    font: 14px/1.5 -apple-system, "SF Pro Text", Inter, system-ui, sans-serif;
  }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  .lede {{ color: var(--muted); margin-bottom: 26px; }}
  .lede code {{ background: rgba(250,200,90,0.08); color: var(--accent); padding: 2px 6px; border-radius: 4px; }}
  .grid {{
    display: grid; gap: 24px;
    {grid_template}
  }}
  .card {{
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
    overflow: hidden; display: flex; flex-direction: column;
  }}
  .card .hd {{ padding: 10px 14px; border-bottom: 1px solid var(--line); display: flex; gap: 10px; }}
  .card .idx {{ color: var(--accent); font-weight: 700; }}
  .card .ttl {{ color: var(--text); }}
  .card img {{ width: 100%; height: auto; display: block; background: #000; }}
  .card .missing {{
    padding: 60px 20px; text-align: center; color: var(--muted); background: #000;
  }}
  .card .narr {{
    padding: 12px 14px; color: var(--muted); font-size: 13px;
    border-top: 1px solid var(--line); max-height: 8em; overflow: auto;
  }}
  .pill {{
    position: fixed; top: 16px; right: 16px;
    background: var(--accent); color: #0a0d10; font-weight: 700;
    padding: 8px 16px; border-radius: 99px; font-size: 13px;
  }}
</style>
<div class="pill">Preview gate. Switch to your terminal to continue.</div>
<h1>Slide preview ({orientation})</h1>
<div class="lede">
  Inspect every slide visually before paying for TTS / lipsync.
  Press <code>y</code> in your terminal to continue, anything else to abort.
</div>
<div class="grid">
{chr(10).join(rows)}
</div>
"""
    idx_path = out_dir / "_preview_index.html"
    idx_path.write_text(html)
    return idx_path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003 - matching parent signature
        return  # swallow per-request stdout chatter


def _open_browser(url: str) -> None:
    """Best-effort browser launch with a macOS `open` fallback.

    `webbrowser.open` sometimes returns success without actually doing anything
    (headless SSH, kiosk-mode terminal, missing default browser). On macOS we
    fall back to `/usr/bin/open`. If both fail, the caller has already printed
    the URL banner so the user can copy-paste.
    """
    opened = False
    try:
        opened = bool(webbrowser.open(url))
    except Exception:  # noqa: BLE001
        opened = False
    if not opened and sys.platform == "darwin" and shutil.which("open"):
        try:
            subprocess.run(["open", url], check=False)
            opened = True
        except Exception:  # noqa: BLE001
            pass
    if not opened:
        print("[preview] could not auto-open a browser; copy the URL above.")


def _spawn_detached_server(out_dir: Path, port: int, ttl: int) -> Optional[subprocess.Popen]:
    """Fork a detached `python -m video_claw.preview_server` that owns the socket.

    Returns the Popen handle (mostly for tests). The child is fully detached via
    `start_new_session=True`; closing the parent terminal will not reap it.
    Returns None if Popen itself fails — caller falls back to the legacy
    in-process server lifetime.
    """
    cmd = [
        sys.executable, "-m", "video_claw.preview_server",
        "--dir", str(out_dir),
        "--port", str(port),
        "--ttl", str(ttl),
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # equivalent to os.setsid in the child
            close_fds=True,
        )
    except Exception as e:
        print(f"[preview] failed to spawn detached server: {e}", file=sys.stderr)
        return None
    # Give the child a moment to bind the port before the browser request lands.
    time.sleep(0.3)
    return proc


def prompt_user(
    out_dir: Path,
    slides: Iterable[dict],
    orientation: str,
    *,
    auto_yes: bool = False,
    cost_note: Optional[str] = None,
    preview_ttl: Optional[int] = None,
) -> bool:
    """Open the preview, wait on stdin, return True if the user typed 'y' or 'yes'.

    The HTTP server is run in a detached child process so the URL stays clickable
    for `preview_ttl` seconds after the user confirms (default 1h interactive,
    60s headless). Pass `preview_ttl=0` to restore the legacy "die on confirm"
    behavior.
    """
    slides = list(slides)
    idx_path = _build_index(out_dir, slides, orientation)
    ttl = resolve_ttl(preview_ttl)
    if cost_note:
        print(f"[preview] {cost_note}")

    if auto_yes:
        # Still honor the TTL: spin up a detached server so the URL works
        # even when no human is pressing y (useful for "render then look later").
        if ttl > 0:
            port = _free_port()
            proc = _spawn_detached_server(out_dir, port, ttl)
            if proc is not None:
                url = f"http://127.0.0.1:{port}/{idx_path.name}"
                print(f"[preview] --yes flag set; skipping interactive gate.")
                print(f"[preview] gate kept open at {url} for {_fmt_duration(ttl)} after confirm")
        else:
            print("[preview] --yes flag set; skipping interactive gate.")
        return True

    if ttl > 0:
        # Detached-child flow: child owns the server, parent only handles stdin.
        port = _free_port()
        proc = _spawn_detached_server(out_dir, port, ttl)
        if proc is None:
            # Fall back to legacy in-process flow.
            return _prompt_user_legacy(out_dir, idx_path, slides=slides)
        url = f"http://127.0.0.1:{port}/{idx_path.name}"
        file_url = f"file://{idx_path.resolve()}"
        # Copy-paste banner first so the URL is always visible. Show the
        # file:// URL too — it survives any server lifecycle (abort, exit,
        # crash) and the index references images by relative path, so it
        # works identically as a fallback users can bookmark.
        bar = "=" * (max(len(url), len(file_url)) + 18)
        print(bar)
        print(f"  preview at:  {url}")
        print(f"  stable URL:  {file_url}")
        print(bar)
        _open_browser(url)
        # Label the gate based on what will actually run. Lipsync is per-slide
        # opt-in; if no slide sets `lipsync: True`, only ElevenLabs/Deepgram
        # TTS will charge — fal.ai is not called. Naming the actual cost
        # surface up front avoids the "wait, will this charge me $40?" pause.
        has_lipsync = any(s.get("lipsync") for s in slides)
        gate_label = "TTS + lipsync" if has_lipsync else "TTS"
        try:
            ans = input(f"[preview] Proceed with {gate_label}? [y/N] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            ans = ""
        if ans in ("y", "yes"):
            print(f"[preview] gate kept open at {url} for {_fmt_duration(ttl)} after confirm")
            return True
        # On abort: let the child server live out its TTL instead of killing
        # it. The user bailed on TTS spend, not on looking at the preview —
        # they likely want to keep inspecting / iterating. The file:// URL
        # above is also always valid.
        print(
            f"[preview] aborted by user. http URL stays live for {_fmt_duration(ttl)}; "
            f"file:// URL is permanent.",
            file=sys.stderr,
        )
        return False

    # ttl == 0 → legacy behavior: in-process server, killed on input return.
    return _prompt_user_legacy(out_dir, idx_path, slides=slides)


def _prompt_user_legacy(
    out_dir: Path, idx_path: Path, *, slides: Optional[List[dict]] = None
) -> bool:
    """Original behavior: in-process server, torn down the instant input returns.

    Used when `preview_ttl=0` (explicit opt-in to legacy) or when spawning the
    detached child failed for some reason. `slides` is optional so older
    fallback callers still work; passing it enables the accurate gate label.
    """
    port = _free_port()
    handler = functools.partial(_QuietHandler, directory=str(out_dir))
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        url = f"http://127.0.0.1:{port}/{idx_path.name}"
        # Print a copy-paste banner FIRST so users always see the URL,
        # even if the browser launcher silently fails (headless session,
        # missing default browser, SSH, etc.).
        bar = "=" * (len(url) + 18)
        print(bar)
        print(f"  preview at:  {url}")
        print(bar)
        # Give the server a tick to spin up before opening the browser.
        time.sleep(0.2)
        _open_browser(url)
        # Accurate label: lipsync only charges when at least one slide opts in.
        has_lipsync = any(s.get("lipsync") for s in (slides or []))
        gate_label = "TTS + lipsync" if has_lipsync else "TTS"
        try:
            ans = input(f"[preview] Proceed with {gate_label}? [y/N] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            ans = ""
        httpd.shutdown()
    if ans in ("y", "yes"):
        return True
    print("[preview] aborted by user.", file=sys.stderr)
    return False
