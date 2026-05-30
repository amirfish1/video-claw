"""Content-hash cache shared by tts / lipsync / ffmpeg_video modules.

A cache is rooted at `<workdir>/cache/<kind>/<hash>.<ext>`. Each `kind`
("tts", "m4a", "lipsync", "circle", "slide_mp4", ...) is a separate subdir
under cache/. The hash is computed from a list of inputs (scalars, bytes,
or Path objects whose bytes are mixed in).

Set `MNV_FORCE_REGEN=1` to invalidate every lookup for a single run.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import Callable, Dict, Iterable


_KINDS = ("chrome", "tts", "m4a", "lipsync", "circle", "avatar_circle", "slide_mp4", "misc")


def _force_regen() -> bool:
    return os.environ.get("MNV_FORCE_REGEN", "").lower() in ("1", "true", "yes")


class Cache:
    """Per-workdir cache. Holds simple hit/miss stats so the CLI can print them."""

    def __init__(self, workdir: Path) -> None:
        self.workdir = Path(workdir).resolve()
        self.root = self.workdir / "cache"
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in _KINDS:
            (self.root / sub).mkdir(exist_ok=True)
        self.stats: Dict[str, Dict[str, int]] = {}
        self.total_hit = 0
        self.total_miss = 0

    def _bump(self, kind: str, hit: bool) -> None:
        bucket = self.stats.setdefault(kind, {"hit": 0, "miss": 0})
        if hit:
            bucket["hit"] += 1
            self.total_hit += 1
        else:
            bucket["miss"] += 1
            self.total_miss += 1

    def hash(self, inputs: Iterable) -> str:
        h = hashlib.sha256()
        for inp in inputs:
            if isinstance(inp, Path):
                h.update(inp.read_bytes() if inp.exists() else b"<MISSING>")
            elif isinstance(inp, (bytes, bytearray)):
                h.update(inp)
            else:
                h.update(repr(inp).encode())
        return h.hexdigest()[:16]

    def path(self, kind: str, key_inputs: Iterable, ext: str) -> Path:
        """Where would `(kind, key_inputs, ext)` land? Useful for debugging."""
        if kind not in _KINDS:
            (self.root / kind).mkdir(exist_ok=True)
        digest = self.hash(key_inputs)
        return self.root / kind / f"{digest}.{ext}"

    def run(self, kind: str, key_inputs: Iterable, ext: str,
            generator: Callable[[Path], None]) -> Path:
        """Return a cached file if present; otherwise call `generator(out_path)` and cache.

        The generator MUST write its bytes to the given out_path; we don't manage
        atomic writes. Generators that may fail mid-write should write to a temp
        file and `os.rename` into place.
        """
        out_path = self.path(kind, key_inputs, ext)
        if out_path.exists() and not _force_regen():
            self._bump(kind, hit=True)
            return out_path
        self._bump(kind, hit=False)
        generator(out_path)
        if not out_path.exists():
            raise RuntimeError(
                f"cache generator for {kind} returned without producing {out_path}"
            )
        return out_path

    def summary(self) -> str:
        """One-line cache report. `tts:3/5 lipsync:0/2 ...`"""
        per_kind = " ".join(
            f"{k}:{v['hit']}/{v['hit'] + v['miss']}"
            for k, v in sorted(self.stats.items())
        )
        return f"hits={self.total_hit} misses={self.total_miss}  {per_kind}".rstrip()
