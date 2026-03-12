from __future__ import annotations

import argparse
import re
from pathlib import Path

from .actions import copy_to_clipboard, open_path, open_terminal
from .collectors import collect_alias_entries, collect_env_entries, collect_path_entries
from .search import to_pseudo_path
from .storage import ensure_storage, insert_entries, load_aliases, reset_index, search_entries, save_aliases

MANAGED_ENV_BEGIN = "# >>> pathi managed variables >>>"
MANAGED_ENV_END = "# <<< pathi managed variables <<<"


def normalize_env_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", name.upper())
    if not normalized:
        return "PI_PATH"
    if normalized[0].isdigit():
        return f"PI_{normalized}"
    return normalized


def is_env_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))


def replace_managed_block(content: str, block: str) -> str:
    pattern = re.compile(
        rf"\n?{re.escape(MANAGED_ENV_BEGIN)}\n.*?\n{re.escape(MANAGED_ENV_END)}\n?",
        re.DOTALL,
    )
    cleaned = re.sub(pattern, "\n", content).rstrip("\n")
    if cleaned:
        return f"{cleaned}\n\n{block}\n"
    return f"{block}\n"


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


def cmd_env_sync(args: argparse.Namespace) -> int:
    root = ensure_storage()
    db = root / "index.sqlite"
    if args.rebuild:
        build_index()

    entries = search_entries(db, "", 1_000_000)
    selected = [e for e in entries if args.source == "all" or e.source == args.source]

    out: dict[str, str] = {}
    skipped: list[str] = []
    for entry in selected:
        key = normalize_env_name(entry.name) if args.normalize else entry.name
        if not is_env_name(key):
            skipped.append(entry.name)
            continue
        out.setdefault(key, entry.path)

    lines = [MANAGED_ENV_BEGIN]
    for key in sorted(out):
        lines.append(f'{key}="{out[key]}"')
    lines.append(MANAGED_ENV_END)
    block = "\n".join(lines)

    if args.print_only:
        print(block)
    else:
        target = Path(args.file).expanduser()
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        updated = replace_managed_block(existing, block)
        target.write_text(updated, encoding="utf-8")
        print(f"Updated {target}")

    print(f"Exported {len(out)} variables")
    if skipped:
        print(f"Skipped invalid names: {len(skipped)}")
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

    env = sub.add_parser("env", help="Export index entries as environment variables")
    env_sub = env.add_subparsers(dest="env_cmd", required=True)

    e = env_sub.add_parser("sync", help="Sync variables to an env file (e.g. /etc/environment)")
    e.add_argument("--file", default="/etc/environment")
    e.add_argument("--source", choices=["all", "alias", "env", "path"], default="all")
    e.add_argument("--normalize", action="store_true", help="Convert names to valid ENV keys")
    e.add_argument("--rebuild", action="store_true", help="Rebuild index before export")
    e.add_argument("--print-only", action="store_true", help="Print managed block instead of writing file")
    e.set_defaults(func=cmd_env_sync)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
