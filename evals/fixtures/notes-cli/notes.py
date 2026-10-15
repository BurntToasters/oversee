import argparse
import sys
from pathlib import Path
import store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes")
    parser.add_argument("--file", type=Path, default=store.DEFAULT_PATH)
    sub = parser.add_subparsers(dest="cmd", required=True)

    add_p = sub.add_parser("add")
    add_p.add_argument("title")
    add_p.add_argument("body")

    sub.add_parser("list")

    show_p = sub.add_parser("show")
    show_p.add_argument("id", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "add":
        note = store.add_note(args.title, args.body, args.file)
        print(note["id"])
        return 0
    if args.cmd == "list":
        for note in store.load_notes(args.file):
            print(f"{note['id']}: {note['title']}")
        return 0
    if args.cmd == "show":
        note = store.get_note(args.id, args.file)
        if note is None:
            print(f"note {args.id} not found", file=sys.stderr)
            return 1
        print(f"{note['title']}\n{note['body']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
