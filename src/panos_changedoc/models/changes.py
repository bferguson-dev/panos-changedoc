from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldChange:
    path: str
    before: Any
    after: Any


@dataclass(frozen=True)
class Change:
    change_type: str
    entity_type: str
    entity_name: str
    scope: str
    vsys: str
    rulebase: str | None
    xpath: str
    collection_xpath: str
    significance: str
    title: str
    fields_changed: tuple[str, ...]
    field_changes: tuple[FieldChange, ...]
    snapshot: dict | None = None
