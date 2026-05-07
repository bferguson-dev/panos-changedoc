from pathlib import Path

from panos_changedoc.cli import (
    EXIT_INPUT,
    EXIT_MANIFEST,
    EXIT_SCOPE,
    EXIT_USAGE,
    EXIT_XML,
    main,
)


def test_usage_error_exit_2() -> None:
    assert main(["diff"]) == EXIT_USAGE


def test_input_error_exit_3(tmp_path: Path) -> None:
    out = tmp_path / "x.json"
    assert main(["diff", "--before", "missing.xml", "--after", "missing2.xml", "--json", str(out)]) == EXIT_INPUT


def test_xml_error_exit_4(tmp_path: Path) -> None:
    b = tmp_path / "b.xml"
    a = tmp_path / "a.xml"
    b.write_text("<config>", encoding="utf-8")
    a.write_text("<config></config>", encoding="utf-8")
    assert main(["diff", "--before", str(b), "--after", str(a), "--json", str(tmp_path / "o.json")]) == EXIT_XML


def test_scope_error_exit_5(tmp_path: Path) -> None:
    xml = "<config><devices><entry name='d'/><entry name='e'/></devices></config>"
    b = tmp_path / "b.xml"
    a = tmp_path / "a.xml"
    b.write_text(xml, encoding="utf-8")
    a.write_text(xml, encoding="utf-8")
    assert main(["diff", "--before", str(b), "--after", str(a), "--json", str(tmp_path / "o.json")]) == EXIT_SCOPE


def test_manifest_exit_9(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    m = tmp_path / "manifest.json"
    m.write_text('{"expected":{"total_changes":999}}', encoding="utf-8")
    rc = main(["diff", "--before", str(fixtures / "before_basic.xml"), "--after", str(fixtures / "after_basic.xml"), "--json", str(tmp_path / "o.json"), "--manifest", str(m)])
    assert rc == EXIT_MANIFEST
