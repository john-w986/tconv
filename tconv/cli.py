from __future__ import annotations

import argparse
import sys

from .core import FormatError, parse_block, parse_csv, write_block, write_csv

READERS = {"csv": parse_csv, "block": parse_block}
WRITERS = {"csv": write_csv, "block": write_block}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tconv",
        description="Convert time sheet entries between csv and block formats.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="input file to read, or '-' (default) to read from stdin",
    )
    parser.add_argument(
        "--from",
        dest="from_format",
        choices=sorted(READERS),
        required=True,
        help="format of the input",
    )
    parser.add_argument(
        "--to",
        dest="to_format",
        choices=sorted(WRITERS),
        required=True,
        help="format to convert to",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="output file to write, or '-' (default) for stdout",
    )
    return parser


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_output(path: str, text: str) -> None:
    if path == "-":
        sys.stdout.write(text)
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = read_input(args.input)
        entries = READERS[args.from_format](text)
        output = WRITERS[args.to_format](entries)
    except FormatError as exc:
        print(f"tconv: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"tconv: {exc}", file=sys.stderr)
        return 1

    write_output(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
