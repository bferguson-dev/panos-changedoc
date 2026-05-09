from panos_changedoc.reports.markdown import render_markdown


def _base_report() -> dict:
    return {
        "inputs": {
            "before": {"path": "before.xml", "sha256": "abc"},
            "after": {"path": "after.xml", "sha256": "def"},
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
                    "name": "ObjA",
                    "type": "address_object",
                    "rulebase": None,
                },
                "significance": "CRITICAL",
                "fields_changed": ["value"],
            }
        ],
        "warnings": [],
        "unsupported": [],
    }


def test_markdown_renders_rulebase_null_for_non_rule_entities() -> None:
    md = render_markdown(_base_report())
    assert "**Rulebase:** `null`" in md


def test_markdown_lists_warnings_and_unsupported_entries() -> None:
    report = _base_report()
    report["warnings"] = [{"code": "W1", "message": "warn msg"}]
    report["unsupported"] = [{"xpath": "/x", "reason": "unsupported"}]
    md = render_markdown(report)
    assert "- `W1`: warn msg" in md
    assert "- `/x`: unsupported" in md
