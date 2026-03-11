from __future__ import annotations

import os
from pathlib import Path

from .storage import IndexEntry


def path_like(value: str) -> bool:
    if not value:
        return False
    p = Path(value).expanduser()
    return p.is_absolute() and p.exists()


def keywords_for(path: str, name: str) -> str:
    parts = [p for p in path.lower().split("/") if p]
    tokens = set(parts + [name.lower()])
    return " ".join(sorted(tokens))


def collect_env_entries(env: dict[str, str] | None = None) -> list[IndexEntry]:
    env = env or dict(os.environ)
    entries: list[IndexEntry] = []
    for key, value in env.items():
        if path_like(value):
            p = str(Path(value).expanduser().resolve())
            entries.append(IndexEntry(key, p, keywords_for(p, key), "env"))
    return entries


def collect_path_entries(env: dict[str, str] | None = None) -> list[IndexEntry]:
    env = env or dict(os.environ)
    path_val = env.get("PATH", "")
    entries: list[IndexEntry] = []
    for idx, raw in enumerate(path_val.split(os.pathsep), start=1):
        if path_like(raw):
            p = str(Path(raw).expanduser().resolve())
            name = f"PATH_{idx}"
            entries.append(IndexEntry(name, p, keywords_for(p, name), "path"))
    return entries


def collect_alias_entries(aliases: dict[str, str]) -> list[IndexEntry]:
    entries: list[IndexEntry] = []
    for name, raw in aliases.items():
        p = str(Path(raw).expanduser())
        if Path(p).is_absolute() and Path(p).exists():
            entries.append(IndexEntry(name, str(Path(p).resolve()), keywords_for(p, name), "alias"))
    return entries
