from __future__ import annotations

import json
import sys

from panos_changedoc.diff.engine import diff_configs
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
from panos_changedoc.loader import InputFileError, XmlParseError, load_xml_file
from panos_changedoc.parsers.panos_xml import (
    FatalModelParseError,
    UnsupportedScopeError,
    parse_standalone_vsys1,
)
from panos_changedoc.reports.json_report import build_report, write_json_report
from panos_changedoc.reports.markdown import write_markdown
from panos_changedoc.schema import (
    ManifestValidationError,
    SchemaValidationError,
    validate_manifest,
)


def run_diff(
    *,
    before: str,
    after: str,
    json_out: str | None,
    markdown_out: str | None,
    manifest: str | None,
    verbose: bool,
    quiet: bool,
) -> int:
    if not json_out and not markdown_out:
        print(
            "At least one output is required: --json and/or --markdown",
            file=sys.stderr,
        )
        return EXIT_USAGE

    try:
        before_loaded = load_xml_file(before)
        after_loaded = load_xml_file(after)
        before_parsed = parse_standalone_vsys1(before_loaded.root)
        after_parsed = parse_standalone_vsys1(after_loaded.root)
        changes = diff_configs(before_parsed, after_parsed)
        report = build_report(
            before_loaded,
            after_loaded,
            before_parsed,
            after_parsed,
            changes,
        )

        if manifest:
            try:
                with open(manifest, encoding="utf-8") as fh:
                    manifest_doc = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                raise ManifestValidationError(str(exc)) from exc
            validate_manifest(manifest_doc, report)

        if json_out:
            write_json_report(json_out, report)
        if markdown_out:
            write_markdown(markdown_out, report)

        if verbose and not quiet:
            print(
                f"Generated report with {report['summary']['total_changes']} "
                "changes"
            )
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
