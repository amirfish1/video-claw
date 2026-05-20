"""Detached HTTP server that keeps the preview gate URL alive for a TTL window.

Invoked as a child process by `preview.py` so the URL stays clickable even after
the parent CLI returns. Uses only stdlib so we don't grow the dependency surface.

Run directly:
    python -m video_claw.preview_server --dir /path/to/out --port 53012 --ttl 3600

The child:
  * Detaches from the controlling terminal (`os.setsid`).
  * Redirects stdout/stderr to ~/.cache/video-claw/preview-<port>.log.
  * Serves the directory until the TTL expires, then exits.
  * Logs a final line on shutdown so the log file tells the story.
"""
from __future__ import annotations
import argparse
import functools
import http.server
import os
import socketserver
import sys
import threading
import time
from pathlib import Path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def _cache_log_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    d = Path(base) / "video-claw"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _redirect_io(log_path: Path) -> None:
    # Detach stdin so the child can't accidentally read from the parent terminal.
    try:
        devnull = open(os.devnull, "rb")
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    except Exception:
        pass
    # Replace Python's sys.stdout/sys.stderr with line-buffered streams pointing
    # at the log file. dup2 alone isn't enough because Python's text streams have
    # their own buffering above the OS fd.
    try:
        log_fp = open(log_path, "ab", buffering=0)
        os.dup2(log_fp.fileno(), sys.stdout.fileno())
        os.dup2(log_fp.fileno(), sys.stderr.fileno())
        # Rebind the Python-level streams so `print(...)` writes through the new fd.
        sys.stdout = open(sys.stdout.fileno(), "w", buffering=1, closefd=False)
        sys.stderr = open(sys.stderr.fileno(), "w", buffering=1, closefd=False)
    except Exception:
        pass


def serve(directory: Path, port: int, ttl: int) -> int:
    log_path = _cache_log_dir() / f"preview-{port}.log"
    _redirect_io(log_path)
    # New session so closing the parent terminal doesn't reap us.
    try:
        os.setsid()
    except OSError:
        pass

    handler = functools.partial(_QuietHandler, directory=str(directory))
    started = time.time()
    try:
        with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
            print(f"[preview-server] pid={os.getpid()} dir={directory} port={port} ttl={ttl}s started={started:.0f}")
            t = threading.Thread(target=httpd.serve_forever, daemon=True)
            t.start()
            # Sleep in small chunks so a kill -TERM still exits promptly.
            remaining = ttl
            while remaining > 0:
                step = min(5, remaining)
                time.sleep(step)
                remaining -= step
            httpd.shutdown()
        print(f"[preview-server] pid={os.getpid()} ttl expired, shutting down after {ttl}s")
        return 0
    except OSError as e:
        print(f"[preview-server] FAILED to bind port {port}: {e}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="video_claw.preview_server")
    p.add_argument("--dir", required=True, help="Directory to serve.")
    p.add_argument("--port", type=int, required=True, help="Port to bind on 127.0.0.1.")
    p.add_argument("--ttl", type=int, required=True, help="Seconds to keep the server up.")
    args = p.parse_args(argv)
    return serve(Path(args.dir).resolve(), args.port, args.ttl)


if __name__ == "__main__":
    sys.exit(main())
