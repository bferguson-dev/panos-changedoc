from pathlib import Path


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
        f"| Before | `{b['path']}` | `{b['sha256']}` |",
        f"| After | `{a['path']}` | `{a['sha256']}` |",
        "",
        f"Generated at: `{report['run']['generated_at']}`",
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
        lines.extend([
            f"### {change['change_type'].title()}: `{change['entity']['name']}` ({change['entity']['type']})",
            "",
            f"**Significance:** {change['significance']}  ",
            f"**Rulebase:** {change['entity']['rulebase']}  ",
            "",
        ])
        if change["fields_changed"]:
            lines.append("Fields changed: " + ", ".join(f"`{x}`" for x in change["fields_changed"]))
            lines.append("")
    lines.append("## Parser Warnings")
    lines.append("")
    lines.append("No parser warnings." if not report["warnings"] else "Warnings present.")
    lines.append("")
    lines.append("## Unsupported Sections")
    lines.append("")
    lines.append("No unsupported sections were encountered in supported v1 scope." if not report["unsupported"] else "Unsupported sections encountered.")
    lines.append("")
    return "\n".join(lines)


def write_markdown(path: str, report: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(report), encoding="utf-8")
