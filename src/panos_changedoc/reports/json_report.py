import json
import os
from datetime import datetime, timezone
from pathlib import Path

from panos_changedoc.diff.ordering import sort_changes
from panos_changedoc.diff.references import attach_references
from panos_changedoc.ids import build_change_id
from panos_changedoc.models.changes import Change
from panos_changedoc.schema import validate_report


def _entity_record(change: Change) -> dict:
    return {
        "type": change.entity_type,
        "name": change.entity_name,
        "scope": change.scope,
        "vsys": change.vsys,
        "rulebase": change.rulebase,
        "xpath": change.xpath,
        "collection_xpath": change.collection_xpath,
    }


def _change_record(change: Change) -> dict:
    record = {
        "id": build_change_id(change),
        "change_type": change.change_type,
        "entity": _entity_record(change),
        "significance": change.significance,
        "title": change.title,
        "fields_changed": list(change.fields_changed),
        "references": {"direct": [], "transitive": [], "truncated": False, "max_depth": 3},
        "notes": [],
    }
    if change.snapshot is not None:
        record["snapshot"] = change.snapshot
    return record


def _input_record(role: str, loaded, parsed) -> dict:
    return {
        "role": role,
        "path": str(loaded.path),
        "filename": loaded.filename,
        "sha256": loaded.sha256_hex,
        "size_bytes": loaded.size_bytes,
        "detected": {
            "config_type": "standalone_firewall",
            "device_entry_name": parsed.device_entry_name,
            "hostname": parsed.hostname,
            "config_version": parsed.config_version,
            "panos_version": parsed.panos_version,
            "vsys": parsed.vsys,
            "base_xpath": parsed.base_xpath,
        },
    }


def _summary(changes: list[dict]) -> dict:
    by_entity = {k: 0 for k in ["security_rule", "nat_rule", "address_object", "address_group", "service_object", "zone"]}
    by_sig = {"CRITICAL": 0, "HIGH": 0, "LOW": 0}
    for ch in changes:
        by_entity[ch["entity"]["type"]] += 1
        by_sig[ch["significance"]] += 1
    return {"total_changes": len(changes), "by_significance": by_sig, "by_entity_type": by_entity}


def build_report(before_loaded, after_loaded, before_parsed, after_parsed, changes: list[Change]) -> dict:
    generated_at = os.getenv("PANOS_CHANGEDOC_GENERATED_AT")
    if not generated_at:
        generated_at = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
    records = [_change_record(c) for c in changes]
    records = sort_changes(records)
    records, ref_warnings = attach_references(records, before_parsed, after_parsed)
    report = {
        "schema_version": "1.0",
        "tool": {"name": "panos-changedoc", "version": "0.1.0"},
        "run": {"generated_at": generated_at},
        "inputs": {
            "before": _input_record("before", before_loaded, before_parsed),
            "after": _input_record("after", after_loaded, after_parsed),
        },
        "summary": _summary(records),
        "changes": records,
        "warnings": list(before_parsed.warnings) + list(after_parsed.warnings) + ref_warnings,
        "unsupported": list(before_parsed.unsupported) + list(after_parsed.unsupported),
        "errors": [],
    }
    validate_report(report)
    return report


def write_json_report(path: str, report: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
