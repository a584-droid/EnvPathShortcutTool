from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class IndexEntry:
    name: str
    path: str
    keywords: str
    source: str


def data_dir() -> Path:
    if os.name == "nt":
        base = os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "pathindex"
    if sys_platform() == "darwin":
        return Path.home() / "Library" / "Application Support" / "pathindex"
    xdg = os.getenv("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "pathindex"
    return Path.home() / ".local" / "share" / "pathindex"


def sys_platform() -> str:
    import sys

    return sys.platform


def ensure_storage() -> Path:
    root = data_dir()
    root.mkdir(parents=True, exist_ok=True)
    (root / "cache.json").write_text("{}", encoding="utf-8") if not (root / "cache.json").exists() else None
    if not (root / "aliases.json").exists():
        (root / "aliases.json").write_text("{}", encoding="utf-8")
    init_db(root / "index.sqlite")
    return root


def init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              path TEXT NOT NULL,
              keywords TEXT NOT NULL,
              source TEXT NOT NULL,
              UNIQUE(name, path, source)
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_entries_name ON entries(name)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_entries_path ON entries(path)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_entries_keywords ON entries(keywords)")


def reset_index(db_path: Path) -> None:
    with sqlite3.connect(db_path) as con:
        con.execute("DELETE FROM entries")


def insert_entries(db_path: Path, entries: Iterable[IndexEntry]) -> int:
    rows = [(e.name, e.path, e.keywords, e.source) for e in entries]
    if not rows:
        return 0
    with sqlite3.connect(db_path) as con:
        before = con.total_changes
        con.executemany(
            "INSERT OR IGNORE INTO entries(name, path, keywords, source) VALUES (?, ?, ?, ?)",
            rows,
        )
        return con.total_changes - before


def search_entries(db_path: Path, query: str, limit: int = 30) -> list[IndexEntry]:
    q = f"%{query.lower()}%"
    with sqlite3.connect(db_path) as con:
        cur = con.execute(
            """
            SELECT name, path, keywords, source
            FROM entries
            WHERE lower(name) LIKE ? OR lower(path) LIKE ? OR lower(keywords) LIKE ?
            ORDER BY
                CASE WHEN lower(name) = lower(?) THEN 0 ELSE 1 END,
                CASE WHEN lower(name) LIKE lower(?) THEN 0 ELSE 1 END,
                length(path) ASC
            LIMIT ?
            """,
            (q, q, q, query, f"{query}%", limit),
        )
        return [IndexEntry(*r) for r in cur.fetchall()]


def load_aliases(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_aliases(path: Path, aliases: dict[str, str]) -> None:
    path.write_text(json.dumps(aliases, indent=2, ensure_ascii=False), encoding="utf-8")
