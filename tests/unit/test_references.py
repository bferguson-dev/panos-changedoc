from pathlib import Path

from panos_changedoc.diff.engine import diff_configs
from panos_changedoc.loader import load_xml_file
from panos_changedoc.parsers.panos_xml import parse_standalone_vsys1
from panos_changedoc.reports.json_report import build_report


def test_reference_graph_direct_links_present() -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    b = load_xml_file(str(fixtures / "before_basic.xml"))
    a = load_xml_file(str(fixtures / "after_basic.xml"))
    pb = parse_standalone_vsys1(b.root)
    pa = parse_standalone_vsys1(a.root)
    report = build_report(b, a, pb, pa, diff_configs(pb, pa))
    addr_changes = [
        c
        for c in report["changes"]
        if c["entity"]["type"] == "address_object" and c["entity"]["name"] == "APP01"
    ]
    assert addr_changes
    refs = addr_changes[0]["references"]["direct"]
    assert any(r["source_type"] == "nat_rule" for r in refs)
