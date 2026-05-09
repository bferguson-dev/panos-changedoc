import json

from panos_changedoc.cli import main


def test_address_object_transitive_reference_to_security_rule_via_group(
    tmp_path,
) -> None:
    before = (
        "<config><devices><entry name='d'><vsys><entry name='vsys1'>"
        "<rulebase><security><rules><entry name='Allow-App'>"
        "<from><member>trust</member></from><to><member>dmz</member></to>"
        "<source><member>any</member></source>"
        "<destination><member>APP-GRP</member></destination>"
        "<application><member>ssl</member></application>"
        "<service><member>application-default</member></service>"
        "<action>allow</action></entry></rules></security></rulebase>"
        "<address><entry name='APP01'><ip-netmask>10.0.0.1/32</ip-netmask></entry>"
        "</address><address-group><entry name='APP-GRP'><static><member>APP01</member>"
        "</static></entry></address-group><service></service>"
        "</entry></vsys><network><zone><entry name='trust'/><entry name='dmz'/></zone>"
        "</network></entry></devices></config>"
    )
    after = before.replace("10.0.0.1/32", "10.0.0.2/32")

    b = tmp_path / "before.xml"
    a = tmp_path / "after.xml"
    o = tmp_path / "out.json"
    b.write_text(before, encoding="utf-8")
    a.write_text(after, encoding="utf-8")

    rc = main(["diff", "--before", str(b), "--after", str(a), "--json", str(o)])
    assert rc == 0

    report = json.loads(o.read_text(encoding="utf-8"))
    target = [
        c
        for c in report["changes"]
        if c["entity"]["type"] == "address_object" and c["entity"]["name"] == "APP01"
    ][0]
    transitive = target["references"]["transitive"]
    assert any(
        r.get("source_type") == "security_rule"
        and r.get("source_name") == "Allow-App"
        and r.get("via") == "APP-GRP"
        for r in transitive
    )
