"""Exercise both launchers and every preview-server path without launching a browser."""
import json

import pytest

from video_claw import cli, core, preview


@pytest.mark.parametrize("flow", ["detached", "legacy", "spawn_failure"])
@pytest.mark.parametrize("flag, env, opens", [
    (True, "0", False), (False, "1", False), (False, " TRUE ", False),
    (False, "yes", False), (False, "0", True), (False, "", True),
])
def test_browser_opt_out_preserves_gate_and_url(
    tmp_path, monkeypatch, capsys, flow, flag, env, opens,
):
    monkeypatch.setenv("VIDEO_CLAW_NO_BROWSER", env)
    monkeypatch.setattr(preview, "_spawn_detached_server",
                        lambda *args: None if flow == "spawn_failure" else object())
    # Avoid real desktop launches, including the macOS fallback.
    launchers = []
    monkeypatch.setattr(preview.webbrowser, "open", lambda url: launchers.append(url))
    monkeypatch.setattr(preview.sys, "platform", "darwin")
    monkeypatch.setattr(preview.shutil, "which", lambda cmd: "/usr/bin/open")
    monkeypatch.setattr(preview.subprocess, "run", lambda cmd, **kw: launchers.append(cmd))
    prompts = []

    def answer(prompt):
        prompts.append(prompt)
        return "n"

    monkeypatch.setattr("builtins.input", answer)
    assert preview.prompt_user(
        tmp_path, [{"narration": "Hello"}], "horizontal",
        preview_ttl=0 if flow == "legacy" else 60, no_browser=flag,
    ) is False
    assert len(prompts) == 1
    assert "preview at:  http://127.0.0.1:" in capsys.readouterr().out
    assert len(launchers) == (2 if opens else 0)
    assert (tmp_path / "_preview_index.html").exists()


@pytest.mark.parametrize("command", ["render", "preview"])
@pytest.mark.parametrize("flag", [False, True])
def test_cli_forwards_no_browser(tmp_path, monkeypatch, command, flag):
    (tmp_path / "project.json").write_text(json.dumps({
        "slides": [{"narration": "Hello"}], "config": {},
    }))
    calls = []
    monkeypatch.setattr(cli, "_ensure_keys_for", lambda project: None)
    monkeypatch.setattr(core, "make_video", lambda *a, **kw: calls.append(kw))
    monkeypatch.setattr(core, "render_pngs", lambda *a, **kw: None)
    monkeypatch.setattr(preview, "prompt_user", lambda *a, **kw: calls.append(kw))
    argv = [command, str(tmp_path)] + (["--no-browser"] if flag else [])
    assert cli.main(argv) == 0
    assert calls[0]["no_browser"] is flag


def test_no_browser_auto_yes_still_skips_input(tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("unexpected input gate"))
    monkeypatch.setattr(preview, "_open_browser", lambda *a: pytest.fail("browser launch"))
    assert preview.prompt_user(tmp_path, [], "horizontal", auto_yes=True,
                               no_browser=True, preview_ttl=0)
