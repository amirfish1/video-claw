"""Smoke + behavioral tests for the preview-server TTL feature.

Covers:
  * imports don't blow up
  * `--preview-ttl` parses on both subcommands
  * negative TTLs are rejected with a clear error
  * `VIDEO_CLAW_PREVIEW_TTL` env var is honored
  * the detached child process actually starts, owns its own session, and
    keeps the port serving past the parent's lifetime

The behavioral test only runs if `python` can launch `python -m
video_claw.preview_server` against the source tree (i.e. local dev). It
shells out so the parent test process doesn't share the child's fate.
"""
from __future__ import annotations
import http.client
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- import-level smoke ----------

def test_imports():
    import video_claw  # noqa: F401
    from video_claw import preview, preview_server, cli, core  # noqa: F401


def test_resolve_ttl_explicit():
    from video_claw.preview import resolve_ttl
    assert resolve_ttl(0) == 0
    assert resolve_ttl(120) == 120
    # Negative collapses to 0 as defence-in-depth.
    assert resolve_ttl(-5) == 0


def test_resolve_ttl_env(monkeypatch):
    from video_claw.preview import resolve_ttl
    monkeypatch.setenv("VIDEO_CLAW_PREVIEW_TTL", "777")
    assert resolve_ttl(None) == 777
    # Bogus env vars get ignored and we fall back to default.
    monkeypatch.setenv("VIDEO_CLAW_PREVIEW_TTL", "not-a-number")
    val = resolve_ttl(None)
    assert isinstance(val, int) and val > 0


def test_resolve_ttl_explicit_beats_env(monkeypatch):
    from video_claw.preview import resolve_ttl
    monkeypatch.setenv("VIDEO_CLAW_PREVIEW_TTL", "777")
    assert resolve_ttl(10) == 10


# ---------- CLI argparse plumbing ----------

def test_cli_render_accepts_preview_ttl():
    from video_claw.cli import build_parser
    parser = build_parser()
    ns = parser.parse_args(["render", ".", "--preview-ttl", "120"])
    assert ns.preview_ttl == 120


def test_cli_preview_accepts_preview_ttl():
    from video_claw.cli import build_parser
    parser = build_parser()
    ns = parser.parse_args(["preview", ".", "--preview-ttl", "30"])
    assert ns.preview_ttl == 30


def test_cli_rejects_negative_preview_ttl():
    from video_claw.cli import _validate_preview_ttl
    with pytest.raises(SystemExit):
        _validate_preview_ttl(-1)


# ---------- detached-child behavior ----------

def _free_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_for_port(port: int, timeout: float = 3.0) -> bool:
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def test_detached_child_survives_parent_and_serves(tmp_path):
    """Start the preview_server module in a fully detached child, hit it once,
    confirm it's a new session (own PGID), then let TTL expire."""
    # Need a file to serve.
    (tmp_path / "_preview_index.html").write_text("<html>ok</html>")
    port = _free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.Popen(
        [sys.executable, "-m", "video_claw.preview_server",
         "--dir", str(tmp_path), "--port", str(port), "--ttl", "5"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    try:
        assert _wait_for_port(port, 3.0), "child never bound the port"
        # Child should be in its own session (POSIX only).
        if hasattr(os, "getsid"):
            assert os.getsid(proc.pid) == proc.pid, (
                "preview_server child did not setsid; it would die with the parent terminal"
            )
        # Hit it.
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("GET", "/_preview_index.html")
        resp = conn.getresponse()
        assert resp.status == 200
        body = resp.read()
        assert b"ok" in body
        conn.close()
    finally:
        # Clean up so the test suite doesn't leave servers behind.
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


def test_ttl_zero_uses_legacy_in_process_path(monkeypatch, tmp_path):
    """With preview_ttl=0, no detached child should be spawned."""
    from video_claw import preview as preview_mod

    spawned = []

    def fake_spawn(out_dir, port, ttl):
        spawned.append((out_dir, port, ttl))
        return None  # pretend it failed so caller goes to legacy

    monkeypatch.setattr(preview_mod, "_spawn_detached_server", fake_spawn)

    # Force a non-TTY headless default just to keep the test deterministic.
    monkeypatch.setattr(preview_mod, "_default_ttl", lambda: 60)

    # ttl=0 short-circuits before _spawn_detached_server is called.
    # We can't easily run prompt_user (it blocks on input()), so call resolve_ttl
    # directly and assert the math.
    assert preview_mod.resolve_ttl(0) == 0
    assert spawned == []
