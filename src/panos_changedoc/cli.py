from __future__ import annotations

import argparse
import json
import sys

from panos_changedoc.commands import run_diff
from panos_changedoc.exit_codes import (
    EXIT_FATAL_PARSE,
    EXIT_INPUT,
    EXIT_MANIFEST,
    EXIT_OUTPUT,
    EXIT_SCHEMA,
    EXIT_SCOPE,
    EXIT_SUCCESS,
    EXIT_UNEXPECTED,
    EXIT_USAGE,
    EXIT_XML,
)
from panos_changedoc.generate import (
    build_from_spec,
    list_change_templates,
    load_spec,
    write_default_spec,
    write_outputs,
)

__all__ = [
    "EXIT_SUCCESS",
    "EXIT_USAGE",
    "EXIT_INPUT",
    "EXIT_XML",
    "EXIT_SCOPE",
    "EXIT_FATAL_PARSE",
    "EXIT_OUTPUT",
    "EXIT_SCHEMA",
    "EXIT_MANIFEST",
    "EXIT_UNEXPECTED",
    "main",
]


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

    gen_parser = subparsers.add_parser("generate")
    gen_parser.add_argument("--spec")
    gen_parser.add_argument(
        "--before-out", default="sample_configs/before.xml"
    )
    gen_parser.add_argument("--after-out", default="sample_configs/after.xml")
    gen_parser.add_argument(
        "--manifest-out", default="sample_configs/manifest.json"
    )
    gen_parser.add_argument("--validate-only", action="store_true")
    gen_parser.add_argument("--write-default-spec")
    gen_parser.add_argument("--list-templates", action="store_true")
    gen_parser.add_argument(
        "--format",
        choices=("json", "yaml"),
        default="json",
        help="Output format for --list-templates.",
    )

    subparsers.add_parser("gui")
    subparsers.add_parser("list-templates")
    return parser


def run_generate(args: argparse.Namespace) -> int:
    try:
        if args.list_templates:
            templates = list_change_templates()
            if args.format == "yaml":
                import yaml

                print(yaml.safe_dump(templates, sort_keys=False))
            else:
                print(json.dumps(templates, indent=2))
            return EXIT_SUCCESS

        if args.write_default_spec:
            write_default_spec(args.write_default_spec)
            print(f"Wrote default spec to {args.write_default_spec}")
            return EXIT_SUCCESS

        if not args.spec:
            print("--spec is required unless --write-default-spec is used.")
            return EXIT_USAGE

        spec = load_spec(args.spec)
        before_xml, after_xml, manifest = build_from_spec(spec)

        if args.validate_only:
            print("Spec validated successfully.")
            return EXIT_SUCCESS

        write_outputs(
            before_xml=before_xml,
            after_xml=after_xml,
            manifest=manifest,
            before_out=args.before_out,
            after_out=args.after_out,
            manifest_out=args.manifest_out,
        )
        print(
            "Generated files:\n"
            f"- before: {args.before_out}\n"
            f"- after: {args.after_out}\n"
            f"- manifest: {args.manifest_out}"
        )
        return EXIT_SUCCESS
    except OSError as exc:
        print(f"Output write error: {exc}", file=sys.stderr)
        return EXIT_OUTPUT
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        if "validation failed" in str(exc).lower():
            return EXIT_MANIFEST
        return EXIT_FATAL_PARSE


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else EXIT_USAGE
        return code

    if args.command == "diff":
        markdown_out = args.markdown or args.out
        return run_diff(
            before=args.before,
            after=args.after,
            json_out=args.json,
            markdown_out=markdown_out,
            manifest=args.manifest,
            verbose=args.verbose,
            quiet=args.quiet,
        )
    if args.command == "generate":
        return run_generate(args)
    if args.command == "gui":
        from panos_changedoc.gui import launch_gui

        return launch_gui()
    if args.command == "list-templates":
        print(json.dumps(list_change_templates(), indent=2))
        return EXIT_SUCCESS

    parser.print_usage()
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
