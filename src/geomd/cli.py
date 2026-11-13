"""Command line interface: ``geomd convert``, ``geomd check``, ``geomd formats``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import __version__
from .errors import GeoMdError, InvalidDocumentError
from .geometry import GEOMETRY_TYPES
from .registry import DESTINATION_FORMATS, SOURCE_FORMATS, convert
from .validation import Issue, check_text

_MARKDOWN_SUFFIXES = {".md", ".markdown", ".geomd"}
_JSON_SUFFIXES = {".json", ".geojson"}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging()
    try:
        return args.handler(args)
    except GeoMdError as exc:
        print(f"geomd: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"geomd: {exc}", file=sys.stderr)
        return 2


def _setup_logging() -> None:
    """Report what the library had to drop, on stderr, once per run."""
    logger = logging.getLogger("geomd")
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("geomd: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.WARNING)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geomd",
        description="Convert between GeoMarkdown, Markdown, JSON and GeoJSON.",
    )
    parser.add_argument("--version", action="version", version=f"geomd {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser(
        "convert", help="convert a document from one format to another"
    )
    convert_parser.add_argument("input", help="input file, or '-' for standard input")
    convert_parser.add_argument(
        "-f", "--from", dest="src", choices=SOURCE_FORMATS, help="source format (default: guess)"
    )
    convert_parser.add_argument(
        "-t", "--to", dest="dst", choices=DESTINATION_FORMATS, help="destination format (default: guess)"
    )
    convert_parser.add_argument("-o", "--output", help="output file (default: standard output)")
    convert_parser.add_argument(
        "--indent", type=int, default=2, help="indentation of JSON output (default: 2)"
    )
    convert_parser.add_argument(
        "--compact", action="store_true", help="write JSON without indentation"
    )
    convert_parser.add_argument(
        "--force",
        action="store_true",
        help="convert even when the document has errors (a broken geometry block is then dropped)",
    )
    convert_parser.set_defaults(handler=_convert)

    check_parser = subparsers.add_parser(
        "check", help="report geometry blocks and sections that would not convert"
    )
    check_parser.add_argument("input", help="input file, or '-' for standard input")
    check_parser.add_argument(
        "-f", "--from", dest="src", choices=SOURCE_FORMATS, help="source format (default: guess)"
    )
    check_parser.add_argument("--json", action="store_true", help="print the issues as JSON")
    check_parser.set_defaults(handler=_check)

    formats_parser = subparsers.add_parser("formats", help="list the supported formats")
    formats_parser.set_defaults(handler=_formats)

    return parser


def guess_format(text: str, name: str) -> str:
    """Pick the source format from the file name, falling back to the content."""
    suffix = Path(name).suffix.lower()

    if suffix in _MARKDOWN_SUFFIXES:
        return "geomd"

    if suffix in _JSON_SUFFIXES:
        kind = _json_kind(text)
        if kind in (None, "json"):
            return "json"
        return "geojson"

    kind = _json_kind(text)
    if kind == "geojson":
        return "geojson"
    if kind == "json":
        return "json"
    return "geomd"


def _json_kind(text: str) -> str | None:
    """Return ``geojson``, ``json`` or ``None`` when the text is not JSON."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return "json"
    if data.get("type") in ("FeatureCollection", "Feature", *GEOMETRY_TYPES):
        return "geojson"
    return "json"


def default_destination(src: str) -> str:
    return "geomd" if src == "geojson" else "geojson"


def _convert(args: argparse.Namespace) -> int:
    text = _read(args.input)

    issues = check_text(text, args.src or guess_format(text, args.input))
    errors = [issue for issue in issues if issue.is_error]
    if errors and not args.force:
        for issue in errors:
            print(f"geomd: {issue}", file=sys.stderr)
        print(
            "geomd: refusing to convert; fix the errors above or pass --force",
            file=sys.stderr,
        )
        return 1

    src = args.src or guess_format(text, args.input)
    dst = args.dst or default_destination(src)

    result = convert(text, src=src, dst=dst, as_dict=dst in ("json", "geojson"))
    if dst in ("json", "geojson"):
        indent = None if args.compact else args.indent
        output = json.dumps(result, indent=indent, ensure_ascii=False) + "\n"
    else:
        output = result if isinstance(result, str) else str(result)

    _write(args.output, output)
    return 0


def _check(args: argparse.Namespace) -> int:
    text = _read(args.input)
    src = args.src or guess_format(text, args.input)
    # Issues are reported structurally below; keep the parser's own log quiet.
    logging.getLogger("geomd").setLevel(logging.ERROR)
    issues = check_text(text, src)

    if args.json:
        payload = [
            {"level": issue.level, "line": issue.line, "message": issue.message}
            for issue in issues
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for issue in issues:
            print(issue)
        if not issues:
            print(f"{args.input}: no problems found ({src})")

    return 1 if any(issue.is_error for issue in issues) else 0


def _formats(args: argparse.Namespace) -> int:
    print(f"source formats:      {', '.join(SOURCE_FORMATS)}")
    print(f"destination formats: {', '.join(DESTINATION_FORMATS)}")
    return 0


def _read(name: str) -> str:
    text = sys.stdin.read() if name == "-" else Path(name).read_text(encoding="utf-8")
    if not text.strip():
        raise InvalidDocumentError(f"{name} is empty")
    return text


def _write(name: str | None, output: str) -> None:
    if name in (None, "-"):
        sys.stdout.write(output)
        return
    Path(name).write_text(output, encoding="utf-8")


def _format_issue(issue: Issue) -> str:  # pragma: no cover - kept for callers
    return str(issue)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
