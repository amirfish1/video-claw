"""Local preview server with a slide-grid HTML. Used to gate expensive TTS/fal calls.

Workflow:
  1. Engine has rendered every slide PNG into `out_dir`.
  2. We start an HTTP server on 127.0.0.1 (random free port).
  3. Open the user's browser to the grid view.
  4. Wait for `input()` ("y" to proceed, anything else to abort).
  5. Shut the server down.
"""
from __future__ import annotations
import contextlib
import functools
import http.server
import socket
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Iterable


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


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
<div class="pill">Preview gate — switch to your terminal to continue</div>
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


def prompt_user(out_dir: Path, slides: Iterable[dict], orientation: str, *, auto_yes: bool = False) -> bool:
    """Open the preview, wait on stdin, return True if the user typed 'y' or 'yes'."""
    slides = list(slides)
    idx_path = _build_index(out_dir, slides, orientation)

    if auto_yes:
        print("[preview] --yes flag set; skipping interactive gate.")
        return True

    port = _free_port()
    handler = functools.partial(_QuietHandler, directory=str(out_dir))

    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        url = f"http://127.0.0.1:{port}/{idx_path.name}"
        print(f"[preview] Opening {url}")
        # Give the server a tick to spin up before opening the browser.
        time.sleep(0.2)
        with contextlib.suppress(Exception):
            webbrowser.open(url)
        try:
            ans = input("[preview] Proceed with TTS + lipsync? [y/N] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            ans = ""
        httpd.shutdown()

    if ans in ("y", "yes"):
        return True
    print("[preview] aborted by user.", file=sys.stderr)
    return False
