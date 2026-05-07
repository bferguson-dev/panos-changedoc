from pathlib import Path

from panos_changedoc.diff.rules import diff_security_rules
from panos_changedoc.loader import load_xml_file
from panos_changedoc.parsers.panos_xml import parse_standalone_vsys1


def test_lcs_reorder_no_cascade_on_insertion_removal() -> None:
    before = parse_standalone_vsys1(load_xml_file(str(Path(__file__).resolve().parents[1] / "fixtures" / "before_basic.xml")).root)
    after = parse_standalone_vsys1(load_xml_file(str(Path(__file__).resolve().parents[1] / "fixtures" / "after_basic.xml")).root)
    changes = diff_security_rules(before.security_rules, after.security_rules)
    reordered = [c for c in changes if c.change_type == "reordered"]
    assert len(reordered) == 1
    assert reordered[0].entity_name in {"RuleA", "RuleB"}
