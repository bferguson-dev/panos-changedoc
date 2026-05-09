from __future__ import annotations


def _format_value(value: object) -> str:
    if isinstance(value, dict):
        value_type = value.get("type")
        members = value.get("members")
        if value_type and isinstance(members, list):
            return f"{value_type}: {', '.join(str(m) for m in members)}"
        return str(value)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_field_change(field: dict) -> list[str]:
    before = _format_value(field.get("before"))
    after = _format_value(field.get("after"))
    return [
        f"    Field: {field.get('path')}",
        f"      Before: {before}",
        f"      After:  {after}",
    ]


def _format_references(change: dict) -> list[str]:
    refs = change.get("references", {})
    direct = refs.get("direct", [])
    transitive = refs.get("transitive", [])
    lines: list[str] = []
    if direct:
        lines.append("    Direct references:")
        for ref in direct:
            lines.append(
                "      - "
                f"{ref.get('entity_type')} `{ref.get('entity_name')}` "
                f"field `{ref.get('field')}`"
            )
    if transitive:
        lines.append("    Transitive references:")
        for ref in transitive:
            lines.append(
                "      - "
                f"{ref.get('entity_type')} `{ref.get('entity_name')}` "
                f"field `{ref.get('field')}`"
            )
    return lines


def build_gui_diff_results(
    report: dict,
    *,
    json_path: str,
    markdown_path: str,
    evidence_bundle: str | None = None,
) -> str:
    """Build an operator-readable diff summary for the Tkinter results panel."""
    summary = report["summary"]
    before = report["inputs"]["before"]
    after = report["inputs"]["after"]
    lines = [
        "Diff completed successfully.",
        "",
        "Inputs:",
        f"- Before: {before['path']} ({before['sha256']})",
        f"- After:  {after['path']} ({after['sha256']})",
        f"- Scope:  {after['detected']['config_type']} / {after['detected']['vsys']}",
        f"- Generated at: {report['run']['generated_at']}",
        "",
        "Summary:",
        f"- Total changes: {summary['total_changes']}",
        f"- CRITICAL: {summary['by_significance']['CRITICAL']}",
        f"- HIGH: {summary['by_significance']['HIGH']}",
        f"- LOW: {summary['by_significance']['LOW']}",
        f"- Security rules: {summary['by_entity_type']['security_rule']}",
        f"- NAT rules: {summary['by_entity_type']['nat_rule']}",
        f"- Address objects: {summary['by_entity_type']['address_object']}",
        f"- Address groups: {summary['by_entity_type']['address_group']}",
        f"- Service objects: {summary['by_entity_type']['service_object']}",
        f"- Zones: {summary['by_entity_type']['zone']}",
        "",
        "Changes:",
    ]

    if report["changes"]:
        for idx, change in enumerate(report["changes"], start=1):
            entity = change["entity"]
            rulebase = entity["rulebase"] if entity["rulebase"] is not None else "n/a"
            lines.extend(
                [
                    f"{idx}. {change['title']}",
                    f"    ID: {change['id']}",
                    f"    Significance: {change['significance']}",
                    f"    Type: {change['change_type']}",
                    f"    Entity: {entity['type']} `{entity['name']}`",
                    f"    Rulebase: {rulebase}",
                    f"    XPath: {entity['xpath']}",
                ]
            )
            for field in change.get("field_changes", []):
                lines.extend(_format_field_change(field))
            lines.extend(_format_references(change))
            notes = change.get("notes", [])
            if notes:
                lines.append("    Notes:")
                lines.extend(f"      - {note}" for note in notes)
    else:
        lines.append("No supported changes were detected.")

    warnings = report.get("warnings", [])
    lines.extend(["", "Warnings:"])
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("No parser warnings.")

    unsupported = report.get("unsupported", [])
    lines.extend(["", "Unsupported Sections:"])
    if unsupported:
        for item in unsupported:
            lines.append(f"- {item.get('xpath')}: {item.get('reason')}")
    else:
        lines.append("No unsupported sections were encountered.")

    lines.extend(
        [
            "",
            "Output Files:",
            f"- JSON: {json_path}",
            f"- Markdown: {markdown_path}",
        ]
    )
    if evidence_bundle:
        lines.append(f"- Evidence bundle zip: {evidence_bundle}")
    return "\n".join(lines)
