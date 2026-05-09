from jsonschema import Draft202012Validator, ValidationError

CHANGE_TYPES = ["added", "removed", "modified", "reordered", "enabled", "disabled"]
ENTITY_TYPES = [
    "security_rule",
    "nat_rule",
    "address_object",
    "address_group",
    "service_object",
    "zone",
]
SIGNIFICANCE = ["CRITICAL", "HIGH", "LOW"]

REPORT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "schema_version",
        "tool",
        "run",
        "inputs",
        "summary",
        "changes",
        "warnings",
        "unsupported",
        "errors",
    ],
    "properties": {
        "schema_version": {"const": "1.0"},
        "tool": {"type": "object", "required": ["name", "version"]},
        "run": {"type": "object", "required": ["generated_at"]},
        "inputs": {
            "type": "object",
            "required": ["before", "after"],
        },
        "summary": {"type": "object"},
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "change_type",
                    "entity",
                    "significance",
                    "title",
                    "fields_changed",
                    "references",
                    "notes",
                ],
                "properties": {
                    "change_type": {"enum": CHANGE_TYPES},
                    "significance": {"enum": SIGNIFICANCE},
                    "entity": {
                        "type": "object",
                        "required": [
                            "type",
                            "name",
                            "scope",
                            "vsys",
                            "rulebase",
                            "xpath",
                            "collection_xpath",
                        ],
                        "properties": {"type": {"enum": ENTITY_TYPES}},
                    },
                },
            },
        },
        "warnings": {"type": "array"},
        "unsupported": {"type": "array"},
        "errors": {"type": "array"},
    },
}

MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["expected"],
    "properties": {
        "expected": {
            "type": "object",
            "required": ["total_changes"],
            "properties": {"total_changes": {"type": "integer", "minimum": 0}},
        }
    },
}


class SchemaValidationError(Exception):
    pass


class ManifestValidationError(Exception):
    pass


def validate_report(report: dict) -> None:
    validator = Draft202012Validator(REPORT_SCHEMA)
    errors = sorted(validator.iter_errors(report), key=lambda e: list(e.path))
    if errors:
        raise SchemaValidationError(errors[0].message)


def validate_manifest(manifest: dict, report: dict) -> None:
    try:
        Draft202012Validator(MANIFEST_SCHEMA).validate(manifest)
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc
    expected = manifest["expected"]["total_changes"]
    actual = report["summary"]["total_changes"]
    if expected != actual:
        raise ManifestValidationError(
            f"Manifest expected total_changes={expected}, got {actual}"
        )
