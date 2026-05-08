from panos_changedoc.reports.markdown import render_markdown


def test_markdown_escapes_backticks_in_names() -> None:
    report = {
        "inputs": {
            "before": {"path": "a`b.xml", "sha256": "x"},
            "after": {"path": "c.xml", "sha256": "y"},
        },
        "run": {"generated_at": "2026-05-08T00:00:00+00:00"},
        "summary": {
            "total_changes": 1,
            "by_significance": {"CRITICAL": 1, "HIGH": 0, "LOW": 0},
        },
        "changes": [
            {
                "change_type": "modified",
                "entity": {
                    "name": "Rule`A",
                    "type": "security_rule",
                    "rulebase": "security",
                },
                "significance": "CRITICAL",
                "fields_changed": ["dest`ination"],
            }
        ],
        "warnings": [],
        "unsupported": [],
    }
    md = render_markdown(report)
    assert "`Rule\\`A`" in md
    assert "`dest\\`ination`" in md
    assert "`a\\`b.xml`" in md
