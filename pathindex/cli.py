from __future__ import annotations

import argparse
from pathlib import Path

from .actions import copy_to_clipboard, open_path, open_terminal
from .collectors import collect_alias_entries, collect_env_entries, collect_path_entries
from .search import to_pseudo_path
from .storage import ensure_storage, insert_entries, load_aliases, reset_index, search_entries, save_aliases


def build_index() -> int:
    root = ensure_storage()
    db = root / "index.sqlite"
    aliases = load_aliases(root / "aliases.json")
    entries = [*collect_env_entries(), *collect_path_entries(), *collect_alias_entries(aliases)]
    reset_index(db)
    return insert_entries(db, entries)


def cmd_index(_: argparse.Namespace) -> int:
    count = build_index()
    print(f"Indexed {count} entries")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = ensure_storage()
    db = root / "index.sqlite"
    if args.rebuild:
        build_index()
    results = search_entries(db, args.query, args.limit)
    if not results:
        print("No matches")
        return 1
    for i, r in enumerate(results, start=1):
        print(f"{i:>2}  {r.name:<20} {r.path}")
    return 0


def cmd_pseudo(args: argparse.Namespace) -> int:
    root = ensure_storage()
    aliases = load_aliases(root / "aliases.json")
    mapping = {**aliases}
    # include env-derived aliases for pseudo-path resolution
    for k, v in dict(__import__("os").environ).items():
        mapping.setdefault(k, v)
    print(to_pseudo_path(args.path, mapping))
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    root = ensure_storage()
    db = root / "index.sqlite"
    results = search_entries(db, args.query, 1)
    if not results:
        print("No matches")
        return 1
    open_path(results[0].path)
    print(results[0].path)
    return 0


def cmd_copy(args: argparse.Namespace) -> int:
    root = ensure_storage()
    db = root / "index.sqlite"
    results = search_entries(db, args.query, 1)
    if not results:
        print("No matches")
        return 1
    text = results[0].path
    if args.pseudo:
        aliases = load_aliases(root / "aliases.json")
        mapping = {**aliases, **dict(__import__("os").environ)}
        text = to_pseudo_path(text, mapping)
    if copy_to_clipboard(text):
        print(text)
        return 0
    print("Clipboard tool not found")
    return 2


def cmd_terminal(args: argparse.Namespace) -> int:
    root = ensure_storage()
    db = root / "index.sqlite"
    results = search_entries(db, args.query, 1)
    if not results:
        print("No matches")
        return 1
    open_terminal(results[0].path)
    print(results[0].path)
    return 0


def cmd_alias_add(args: argparse.Namespace) -> int:
    root = ensure_storage()
    alias_file = root / "aliases.json"
    aliases = load_aliases(alias_file)
    p = str(Path(args.path).expanduser())
    if not Path(p).is_absolute():
        print("Alias path must be absolute")
        return 2
    aliases[args.name] = p
    save_aliases(alias_file, aliases)
    print(f"Added alias {args.name} -> {p}")
    return 0


def cmd_alias_list(_: argparse.Namespace) -> int:
    root = ensure_storage()
    aliases = load_aliases(root / "aliases.json")
    for k, v in sorted(aliases.items()):
        print(f"{k:<20} {v}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pathi", description="Path Index CLI")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("index", help="Rebuild index")
    s.set_defaults(func=cmd_index)

    s = sub.add_parser("search", help="Search indexed paths")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--rebuild", action="store_true")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("pseudo", help="Convert absolute path to pseudo-path")
    s.add_argument("path")
    s.set_defaults(func=cmd_pseudo)

    s = sub.add_parser("open", help="Open top match")
    s.add_argument("query")
    s.set_defaults(func=cmd_open)

    s = sub.add_parser("copy", help="Copy top match path")
    s.add_argument("query")
    s.add_argument("--pseudo", action="store_true")
    s.set_defaults(func=cmd_copy)

    s = sub.add_parser("terminal", help="Open terminal in top match")
    s.add_argument("query")
    s.set_defaults(func=cmd_terminal)

    alias = sub.add_parser("alias", help="Manage aliases")
    alias_sub = alias.add_subparsers(dest="alias_cmd", required=True)

    a = alias_sub.add_parser("add", help="Add alias")
    a.add_argument("name")
    a.add_argument("path")
    a.set_defaults(func=cmd_alias_add)

    a = alias_sub.add_parser("list", help="List aliases")
    a.set_defaults(func=cmd_alias_list)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
