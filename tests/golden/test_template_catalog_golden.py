from pathlib import Path

from panos_changedoc.cli import main


def test_template_catalog_json_golden(capsys) -> None:
    rc = main(["generate", "--list-templates", "--format", "json"])
    assert rc == 0
    out = capsys.readouterr().out
    expected = (
        Path(__file__).resolve().parent / "expected_template_catalog.json"
    ).read_text(encoding="utf-8")
    assert out == expected


def test_template_catalog_yaml_golden(capsys) -> None:
    rc = main(["generate", "--list-templates", "--format", "yaml"])
    assert rc == 0
    out = capsys.readouterr().out
    expected = (
        Path(__file__).resolve().parent / "expected_template_catalog.yaml"
    ).read_text(encoding="utf-8")
    assert out == expected
