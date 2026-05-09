import json

from panos_changedoc.cli import main


def test_unsupported_address_subtype_is_reported(tmp_path) -> None:
    xml = (
        "<config><devices><entry name='d'><vsys><entry name='vsys1'>"
        "<rulebase><security><rules><entry name='r'><destination><member>a</member>"
        "</destination></entry></rules></security></rulebase>"
        "<address><entry name='RANGE'><ip-range>1.1.1.1-1.1.1.2</ip-range></entry>"
        "</address><address-group></address-group><service></service>"
        "</entry></vsys><network><zone/></network></entry></devices></config>"
    )
    before = tmp_path / "before.xml"
    after = tmp_path / "after.xml"
    out = tmp_path / "out.json"
    before.write_text(xml, encoding="utf-8")
    after.write_text(xml, encoding="utf-8")

    rc = main(
        ["diff", "--before", str(before), "--after", str(after), "--json", str(out)]
    )
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert any(
        "Unsupported address object type" in x["reason"] for x in report["unsupported"]
    )


def test_unsupported_service_subtype_is_reported(tmp_path) -> None:
    xml = (
        "<config><devices><entry name='d'><vsys><entry name='vsys1'>"
        "<rulebase><security><rules><entry name='r'><destination><member>a</member>"
        "</destination></entry></rules></security></rulebase>"
        "<address></address><address-group></address-group>"
        "<service><entry name='SCTP'><protocol><sctp><port>80</port></sctp></protocol>"
        "</entry></service></entry></vsys><network><zone/></network></entry></devices></config>"
    )
    before = tmp_path / "before.xml"
    after = tmp_path / "after.xml"
    out = tmp_path / "out.json"
    before.write_text(xml, encoding="utf-8")
    after.write_text(xml, encoding="utf-8")

    rc = main(
        ["diff", "--before", str(before), "--after", str(after), "--json", str(out)]
    )
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert any(
        "Unsupported service protocol/port" in x["reason"]
        for x in report["unsupported"]
    )
