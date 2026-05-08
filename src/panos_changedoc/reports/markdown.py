from pathlib import Path


def _code(value: object) -> str:
    text = str(value).replace("`", "\\`")
    return f"`{text}`"


def render_markdown(report: dict) -> str:
    b = report["inputs"]["before"]
    a = report["inputs"]["after"]
    s = report["summary"]
    lines = [
        "# PAN-OS Change Documentation",
        "",
        "## Summary",
        "",
        "Compared two PAN-OS XML configurations for standalone firewall scope `vsys1`.",
        "",
        "| Input | File | SHA256 |",
        "|---|---|---|",
        f"| Before | {_code(b['path'])} | {_code(b['sha256'])} |",
        f"| After | {_code(a['path'])} | {_code(a['sha256'])} |",
        "",
        f"Generated at: {_code(report['run']['generated_at'])}",
        "",
        "## Change Counts",
        "",
        "| Category | Count |",
        "|---|---:|",
        f"| Total changes | {s['total_changes']} |",
        f"| CRITICAL | {s['by_significance']['CRITICAL']} |",
        f"| HIGH | {s['by_significance']['HIGH']} |",
        f"| LOW | {s['by_significance']['LOW']} |",
        "",
    ]
    for change in report["changes"]:
        rulebase = change["entity"]["rulebase"]
        rulebase_text = "`null`" if rulebase is None else _code(rulebase)
        lines.extend([
            f"### {change['change_type'].title()}: {_code(change['entity']['name'])} ({change['entity']['type']})",
            "",
            f"**Significance:** {change['significance']}  ",
            f"**Rulebase:** {rulebase_text}  ",
            "",
        ])
        if change["fields_changed"]:
            lines.append(
                "Fields changed: "
                + ", ".join(_code(x) for x in change["fields_changed"])
            )
            lines.append("")
    lines.append("## Parser Warnings")
    lines.append("")
    if not report["warnings"]:
        lines.append("No parser warnings.")
    else:
        for item in report["warnings"]:
            code = item.get("code", "WARN")
            message = item.get("message", "")
            lines.append(f"- `{code}`: {message}")
    lines.append("")
    lines.append("## Unsupported Sections")
    lines.append("")
    if not report["unsupported"]:
        lines.append("No unsupported sections were encountered in supported v1 scope.")
    else:
        for item in report["unsupported"]:
            lines.append(f"- `{item['xpath']}`: {item['reason']}")
    lines.append("")
    return "\n".join(lines)


def write_markdown(path: str, report: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(report), encoding="utf-8")
