import hashlib
import json
from typing import Any

from panos_changedoc.models.changes import Change

ENTITY_ABBREVIATIONS = {
    "security_rule": "sec",
    "nat_rule": "nat",
    "address_object": "addr",
    "address_group": "agrp",
    "service_object": "svc",
    "zone": "zone",
}


class IdGenerationError(Exception):
    pass


def build_change_id(change: Change) -> str:
    abbrev = ENTITY_ABBREVIATIONS.get(change.entity_type)
    if abbrev is None:
        raise IdGenerationError(f"Unsupported entity type for ID: {change.entity_type}")
    canonical_payload: dict[str, Any] = {
        "id_contract_version": "1.0",
        "change_type": change.change_type,
        "entity_type": change.entity_type,
        "entity_name": change.entity_name,
        "scope": change.scope,
        "vsys": change.vsys,
        "rulebase": change.rulebase,
        "collection_xpath": change.collection_xpath,
        "field_changes": [{"path": fc.path, "before": fc.before, "after": fc.after} for fc in change.field_changes],
    }
    canonical_json = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    digest16 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:16]
    return f"chg_{abbrev}_{change.change_type}_{digest16}"
