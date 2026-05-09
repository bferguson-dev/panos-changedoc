from pathlib import Path

from panos_changedoc.cli import EXIT_INPUT, EXIT_SCOPE, EXIT_XML, main


def test_missing_input_file_returns_exit_3(tmp_path: Path) -> None:
    missing = tmp_path / "missing.xml"
    out = tmp_path / "out.json"
    rc = main(
        ["diff", "--before", str(missing), "--after", str(missing), "--json", str(out)]
    )
    assert rc == EXIT_INPUT


def test_malformed_xml_returns_exit_4(tmp_path: Path) -> None:
    before = tmp_path / "before.xml"
    after = tmp_path / "after.xml"
    out = tmp_path / "out.json"
    before.write_text("<config>", encoding="utf-8")
    after.write_text("<config></config>", encoding="utf-8")
    rc = main(
        ["diff", "--before", str(before), "--after", str(after), "--json", str(out)]
    )
    assert rc == EXIT_XML


def test_missing_vsys1_returns_exit_5(tmp_path: Path) -> None:
    before = tmp_path / "before.xml"
    after = tmp_path / "after.xml"
    out = tmp_path / "out.json"
    xml = "<config><devices><entry name='d'></entry></devices></config>"
    before.write_text(xml, encoding="utf-8")
    after.write_text(xml, encoding="utf-8")
    rc = main(
        ["diff", "--before", str(before), "--after", str(after), "--json", str(out)]
    )
    assert rc == EXIT_SCOPE
