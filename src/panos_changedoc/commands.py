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
from panos_changedoc.reports.evidence import write_evidence_bundle
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
    evidence_bundle: str | None,
    manifest: str | None,
    verbose: bool,
    quiet: bool,
) -> int:
    if not json_out and not markdown_out and not evidence_bundle:
        print(
            "At least one output is required: --json, --markdown, or --evidence-bundle",
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
        evidence_zip = None
        if evidence_bundle:
            evidence_zip = write_evidence_bundle(
                bundle_dir=evidence_bundle,
                before_loaded=before_loaded,
                after_loaded=after_loaded,
                report=report,
                command_args={
                    "before": before,
                    "after": after,
                    "json": json_out,
                    "markdown": markdown_out,
                    "evidence_bundle": evidence_bundle,
                    "manifest": manifest,
                },
            )

        if verbose and not quiet:
            message = (
                f"Generated report with {report['summary']['total_changes']} changes"
            )
            if evidence_zip:
                message += f"; evidence bundle zip: {evidence_zip}"
            print(message)
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
