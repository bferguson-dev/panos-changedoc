import json
from pathlib import Path

from panos_changedoc.cli import main


def test_unsupported_entries_are_deduplicated(tmp_path: Path) -> None:
    xml = (
        "<config><devices><entry name='d'><vsys><entry name='vsys1'>"
        "<rulebase><security><rules><entry name='r'>"
        "<destination><member>a</member></destination></entry></rules></security>"
        "</rulebase><weird><x/></weird></entry></vsys><network><zone/>"
        "</network></entry></devices></config>"
    )
    before = tmp_path / "before.xml"
    after = tmp_path / "after.xml"
    out = tmp_path / "out.json"
    before.write_text(xml, encoding="utf-8")
    after.write_text(xml, encoding="utf-8")

    rc = main(
        [
            "diff",
            "--before",
            str(before),
            "--after",
            str(after),
            "--json",
            str(out),
        ]
    )
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert len(report["unsupported"]) == 1
