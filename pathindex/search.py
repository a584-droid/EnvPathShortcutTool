from __future__ import annotations

from pathlib import Path


def to_pseudo_path(target: str, mapping: dict[str, str]) -> str:
    target_path = str(Path(target).expanduser().resolve())
    best_name = ""
    best_path = ""
    for name, raw in mapping.items():
        try:
            candidate = str(Path(raw).expanduser().resolve())
        except FileNotFoundError:
            candidate = str(Path(raw).expanduser())
        if target_path == candidate or target_path.startswith(candidate.rstrip("/") + "/"):
            if len(candidate) > len(best_path):
                best_name = name
                best_path = candidate
    if not best_name:
        return target_path
    suffix = target_path[len(best_path) :].lstrip("/")
    return f"${best_name}/{suffix}" if suffix else f"${best_name}"
