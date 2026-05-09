import json
import time
from pathlib import Path

from panos_changedoc.cli import main


def _build_config(rule_count: int, destination_suffix: str) -> str:
    rules = []
    for i in range(rule_count):
        name = f"Rule-{i:04d}"
        dest = f"APP{i:04d}{destination_suffix}"
        rules.append(
            "<entry name='{}'><from><member>trust</member></from>"
            "<to><member>dmz</member></to><source><member>Users</member></source>"
            "<destination><member>{}</member></destination>"
            "<application><member>ssl</member></application>"
            "<service><member>application-default</member></service>"
            "<action>allow</action><disabled>no</disabled><log-end>yes</log-end></entry>".format(
                name, dest
            )
        )
    rules_xml = "".join(rules)
    return (
        "<config><devices><entry name='localhost.localdomain'><deviceconfig><system>"
        "<hostname>pa-fw01</hostname></system></deviceconfig><vsys><entry name='vsys1'>"
        "<rulebase><security><rules>{}</rules></security></rulebase>"
        "<address></address><address-group></address-group><service></service>"
        "</entry></vsys><network><zone><entry name='trust'/><entry name='dmz'/>"
        "</zone></network></entry></devices></config>"
    ).format(rules_xml)


def test_large_config_is_deterministic_and_fast(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PANOS_CHANGEDOC_GENERATED_AT", "2026-05-08T00:00:00+00:00")
    before = tmp_path / "before.xml"
    after = tmp_path / "after.xml"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    before.write_text(_build_config(300, "-OLD"), encoding="utf-8")
    after.write_text(_build_config(300, ""), encoding="utf-8")

    t0 = time.perf_counter()
    rc1 = main(
        ["diff", "--before", str(before), "--after", str(after), "--json", str(out1)]
    )
    elapsed = time.perf_counter() - t0
    rc2 = main(
        ["diff", "--before", str(before), "--after", str(after), "--json", str(out2)]
    )

    assert rc1 == 0
    assert rc2 == 0
    assert elapsed < 5.0

    report1 = json.loads(out1.read_text(encoding="utf-8"))
    report2 = json.loads(out2.read_text(encoding="utf-8"))

    assert report1 == report2
    assert report1["summary"]["total_changes"] == 300
