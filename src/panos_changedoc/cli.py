import argparse
import json
import sys

from panos_changedoc.diff.engine import diff_configs
from panos_changedoc.loader import InputFileError, XmlParseError, load_xml_file
from panos_changedoc.parsers.panos_xml import FatalModelParseError, UnsupportedScopeError, parse_standalone_vsys1
from panos_changedoc.reports.json_report import build_report, write_json_report
from panos_changedoc.reports.markdown import write_markdown
from panos_changedoc.schema import ManifestValidationError, SchemaValidationError, validate_manifest

EXIT_SUCCESS = 0
EXIT_USAGE = 2
EXIT_INPUT = 3
EXIT_XML = 4
EXIT_SCOPE = 5
EXIT_FATAL_PARSE = 6
EXIT_OUTPUT = 7
EXIT_SCHEMA = 8
EXIT_MANIFEST = 9
EXIT_UNEXPECTED = 99


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="panos-changedoc")
    subparsers = parser.add_subparsers(dest="command")
    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("--before", required=True)
    diff_parser.add_argument("--after", required=True)
    diff_parser.add_argument("--json")
    diff_parser.add_argument("--markdown")
    diff_parser.add_argument("--out")
    diff_parser.add_argument("--manifest")
    diff_parser.add_argument("--quiet", action="store_true")
    diff_parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return EXIT_USAGE

    if args.command != "diff":
        parser.print_usage()
        return EXIT_USAGE

    markdown_path = args.markdown or args.out
    if not args.json and not markdown_path:
        print("At least one output is required: --json and/or --markdown", file=sys.stderr)
        return EXIT_USAGE

    try:
        before_loaded = load_xml_file(args.before)
        after_loaded = load_xml_file(args.after)
        before_parsed = parse_standalone_vsys1(before_loaded.root)
        after_parsed = parse_standalone_vsys1(after_loaded.root)
        changes = diff_configs(before_parsed, after_parsed)
        report = build_report(before_loaded, after_loaded, before_parsed, after_parsed, changes)

        if args.manifest:
            manifest = json.loads(open(args.manifest, encoding="utf-8").read())
            validate_manifest(manifest, report)

        if args.json:
            write_json_report(args.json, report)
        if markdown_path:
            write_markdown(markdown_path, report)

        if args.verbose and not args.quiet:
            print(f"Generated report with {report['summary']['total_changes']} changes")
        return EXIT_SUCCESS
    except InputFileError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INPUT
    except XmlParseError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_XML
    except UnsupportedScopeError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_SCOPE
    except FatalModelParseError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_FATAL_PARSE
    except SchemaValidationError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_SCHEMA
    except ManifestValidationError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_MANIFEST
    except OSError as exc:
        print(f"Output write error: {exc}", file=sys.stderr)
        return EXIT_OUTPUT
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected internal error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
