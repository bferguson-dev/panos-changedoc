from pathlib import Path

from panos_changedoc.loader import load_xml_file
from panos_changedoc.parsers.panos_xml import parse_standalone_vsys1


def test_parse_all_supported_entities() -> None:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "before_basic.xml"
    loaded = load_xml_file(str(root))
    parsed = parse_standalone_vsys1(loaded.root)
    assert len(parsed.security_rules) == 2
    assert len(parsed.nat_rules) == 1
    assert len(parsed.address_objects) == 2
    assert len(parsed.address_groups) == 1
    assert len(parsed.service_objects) == 1
    assert len(parsed.zones) == 3
