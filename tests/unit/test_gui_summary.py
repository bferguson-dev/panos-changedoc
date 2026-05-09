from panos_changedoc.gui_summary import build_gui_diff_results


def test_gui_diff_results_include_verbose_change_details() -> None:
    report = {
        "run": {"generated_at": "2026-05-09T00:00:00+00:00"},
        "inputs": {
            "before": {
                "path": "before.xml",
                "sha256": "abc123",
                "detected": {"config_type": "standalone_firewall", "vsys": "vsys1"},
            },
            "after": {
                "path": "after.xml",
                "sha256": "def456",
                "detected": {"config_type": "standalone_firewall", "vsys": "vsys1"},
            },
        },
        "summary": {
            "total_changes": 1,
            "by_significance": {"CRITICAL": 1, "HIGH": 0, "LOW": 0},
            "by_entity_type": {
                "security_rule": 1,
                "nat_rule": 0,
                "address_object": 0,
                "address_group": 0,
                "service_object": 0,
                "zone": 0,
            },
        },
        "changes": [
            {
                "id": "chg_sec_modified_1234567890abcdef",
                "title": "Security rule `Allow-App01-HTTPS` modified",
                "significance": "CRITICAL",
                "change_type": "modified",
                "entity": {
                    "type": "security_rule",
                    "name": "Allow-App01-HTTPS",
                    "rulebase": "security",
                    "xpath": "/config/devices/entry/vsys/entry/rulebase/security",
                },
                "field_changes": [
                    {
                        "path": "destination",
                        "before": {"type": "members", "members": ["APP01-OLD"]},
                        "after": {"type": "members", "members": ["APP01"]},
                    }
                ],
                "references": {"direct": [], "transitive": []},
                "notes": [],
            }
        ],
        "warnings": [],
        "unsupported": [],
    }

    text = build_gui_diff_results(
        report,
        json_path="reports/change-summary.json",
        markdown_path="reports/change-summary.md",
        evidence_bundle="evidence/change-001.zip",
    )

    assert "Security rule `Allow-App01-HTTPS` modified" in text
    assert "Field: destination" in text
    assert "Before: members: APP01-OLD" in text
    assert "After:  members: APP01" in text
    assert "JSON: reports/change-summary.json" in text
    assert "Evidence bundle zip: evidence/change-001.zip" in text
