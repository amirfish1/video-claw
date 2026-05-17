"""Key management: XDG-style storage at ~/.config/video-claw/keys.env.

Lookup order for any provider key:
  1. Environment variable (e.g. ELEVENLABS_API_KEY)
  2. ~/.config/video-claw/keys.env
  3. None -> caller decides whether the provider is required

Never echo keys in logs; `mask()` reduces a key to a hint.
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

XDG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
CONFIG_DIR = XDG_HOME / "video-claw"
KEYS_FILE = CONFIG_DIR / "keys.env"

# Map short aliases used in CLI (`keys set EL=...`) to full env var names.
ALIASES: Dict[str, str] = {
    "EL": "ELEVENLABS_API_KEY",
    "ELEVENLABS": "ELEVENLABS_API_KEY",
    "ELEVENLABS_API_KEY": "ELEVENLABS_API_KEY",
    "FAL": "FAL_API_KEY",
    "FAL_API_KEY": "FAL_API_KEY",
    "DEEPGRAM": "DEEPGRAM_API_KEY",
    "DEEPGRAM_API_KEY": "DEEPGRAM_API_KEY",
    "DG": "DEEPGRAM_API_KEY",
}


def mask(value: str) -> str:
    """Return a short hint for a key — safe to print. `sk_3cea...8ba6` style."""
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def _parse_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        out[k] = v
    return out


def load_keys() -> Dict[str, str]:
    """Merge XDG keys.env over env vars (env wins). Returns a {NAME: value} dict."""
    file_keys = _parse_env_file(KEYS_FILE)
    merged: Dict[str, str] = {}
    for name in ("ELEVENLABS_API_KEY", "FAL_API_KEY", "DEEPGRAM_API_KEY"):
        env_val = os.environ.get(name)
        if env_val:
            merged[name] = env_val
        elif name in file_keys:
            merged[name] = file_keys[name]
    return merged


def get(name: str) -> Optional[str]:
    """Get a single key by full name or alias."""
    canonical = ALIASES.get(name.upper(), name)
    return load_keys().get(canonical)


def save_keys(updates: Dict[str, str]) -> Path:
    """Merge `updates` into the keys file. Creates dir with 0700, file with 0600."""
    CONFIG_DIR.mkdir(mode=0o700, exist_ok=True, parents=True)
    existing = _parse_env_file(KEYS_FILE)
    canonical_updates: Dict[str, str] = {}
    for raw, val in updates.items():
        canonical = ALIASES.get(raw.upper(), raw.upper())
        canonical_updates[canonical] = val
    merged = {**existing, **canonical_updates}
    body = "# video-claw API keys. Do not check this file in.\n"
    body += "# Edit via: video-claw keys set NAME=value\n"
    for k, v in sorted(merged.items()):
        body += f"{k}={v}\n"
    KEYS_FILE.write_text(body)
    try:
        KEYS_FILE.chmod(0o600)
    except OSError:
        pass
    return KEYS_FILE


def test_elevenlabs(api_key: str) -> tuple[bool, str]:
    """Hit ElevenLabs voices endpoint. Cheap. Returns (ok, message)."""
    if not api_key:
        return False, "no key"
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        tier = (data.get("subscription") or {}).get("tier", "unknown")
        return True, f"ok (tier: {tier})"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode(errors='ignore')[:120]}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def test_fal(api_key: str) -> tuple[bool, str]:
    """Try to initiate a fal storage upload — tests auth without spending tokens.

    fal returns 200 with a presigned upload URL on success; 401/403 on bad key.
    We never PUT the bytes; the initiate call alone validates the credential.
    """
    if not api_key:
        return False, "no key"
    body = json.dumps({"file_name": "ping.txt", "content_type": "text/plain"}).encode()
    req = urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        data=body,
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            json.load(r)
        return True, "ok"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode(errors='ignore')[:120]}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def test_deepgram(api_key: str) -> tuple[bool, str]:
    """Hit Deepgram /v1/projects. Free, validates the key."""
    if not api_key:
        return False, "no key"
    req = urllib.request.Request(
        "https://api.deepgram.com/v1/projects",
        headers={"Authorization": f"Token {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            json.load(r)
        return True, "ok"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode(errors='ignore')[:120]}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


TESTERS = {
    "ELEVENLABS_API_KEY": test_elevenlabs,
    "FAL_API_KEY": test_fal,
    "DEEPGRAM_API_KEY": test_deepgram,
}


def test_all() -> Dict[str, tuple[bool, str]]:
    """Test every key currently configured. Returns {NAME: (ok, msg)}."""
    keys = load_keys()
    out: Dict[str, tuple[bool, str]] = {}
    for name, tester in TESTERS.items():
        val = keys.get(name)
        if not val:
            out[name] = (False, "not set")
            continue
        out[name] = tester(val)
    return out
