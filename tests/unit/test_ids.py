from panos_changedoc.ids import build_change_id
from panos_changedoc.models.changes import Change, FieldChange


def test_change_id_is_deterministic() -> None:
    change = Change(
        change_type="modified",
        entity_type="security_rule",
        entity_name="Allow-App01-HTTPS",
        scope="local",
        vsys="vsys1",
        rulebase="security",
        xpath="/x",
        collection_xpath="/c",
        significance="CRITICAL",
        title="t",
        fields_changed=("destination",),
        field_changes=(
            FieldChange(
                path="destination",
                before={"type": "members", "members": ["APP01-OLD"]},
                after={"type": "members", "members": ["APP01"]},
            ),
        ),
    )

    first = build_change_id(change)
    second = build_change_id(change)
    assert first == second
    assert first.startswith("chg_sec_modified_")
    assert len(first.split("_")[-1]) == 16
