from pathlib import Path

from panos_changedoc.cli import (
    EXIT_FATAL_PARSE,
    EXIT_INPUT,
    EXIT_MANIFEST,
    EXIT_OUTPUT,
    EXIT_SCHEMA,
    EXIT_SCOPE,
    EXIT_UNEXPECTED,
    EXIT_USAGE,
    EXIT_XML,
    main,
)
from panos_changedoc.schema import SchemaValidationError


def test_usage_error_exit_2() -> None:
    assert main(["diff"]) == EXIT_USAGE


def test_help_exits_zero() -> None:
    assert main(["--help"]) == 0
    assert main(["diff", "--help"]) == 0


def test_input_error_exit_3(tmp_path: Path) -> None:
    out = tmp_path / "x.json"
    assert (
        main(
            [
                "diff",
                "--before",
                "missing.xml",
                "--after",
                "missing2.xml",
                "--json",
                str(out),
            ]
        )
        == EXIT_INPUT
    )


def test_xml_error_exit_4(tmp_path: Path) -> None:
    b = tmp_path / "b.xml"
    a = tmp_path / "a.xml"
    b.write_text("<config>", encoding="utf-8")
    a.write_text("<config></config>", encoding="utf-8")
    assert (
        main(["diff", "--before", str(b), "--after", str(a), "--json", str(tmp_path / "o.json")])
        == EXIT_XML
    )


def test_scope_error_exit_5(tmp_path: Path) -> None:
    xml = "<config><devices><entry name='d'/><entry name='e'/></devices></config>"
    b = tmp_path / "b.xml"
    a = tmp_path / "a.xml"
    b.write_text(xml, encoding="utf-8")
    a.write_text(xml, encoding="utf-8")
    assert (
        main(["diff", "--before", str(b), "--after", str(a), "--json", str(tmp_path / "o.json")])
        == EXIT_SCOPE
    )


def test_fatal_parse_error_exit_6(tmp_path: Path) -> None:
    bad = """
<config><devices><entry name='d'><vsys><entry name='vsys1'><rulebase><security><rules>
<entry><destination><member>x</member></destination></entry>
</rules></security></rulebase></entry></vsys></entry></devices></config>
""".strip()
    b = tmp_path / "b.xml"
    a = tmp_path / "a.xml"
    b.write_text(bad, encoding="utf-8")
    a.write_text(bad, encoding="utf-8")
    rc = main(["diff", "--before", str(b), "--after", str(a), "--json", str(tmp_path / "o.json")])
    assert rc == EXIT_FATAL_PARSE


def test_output_error_exit_7(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    out_dir = tmp_path / "reports"
    out_dir.mkdir()
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(out_dir),
        ]
    )
    assert rc == EXIT_OUTPUT


def test_schema_error_exit_8(monkeypatch, tmp_path: Path) -> None:
    def _raise_schema(*args, **kwargs):
        raise SchemaValidationError("forced")

    monkeypatch.setattr("panos_changedoc.cli.build_report", _raise_schema)
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(tmp_path / "o.json"),
        ]
    )
    assert rc == EXIT_SCHEMA


def test_manifest_exit_9(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    m = tmp_path / "manifest.json"
    m.write_text('{"expected":{"total_changes":999}}', encoding="utf-8")
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(tmp_path / "o.json"),
            "--manifest",
            str(m),
        ]
    )
    assert rc == EXIT_MANIFEST


def test_manifest_missing_file_exit_9(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(tmp_path / "o.json"),
            "--manifest",
            str(tmp_path / "missing.json"),
        ]
    )
    assert rc == EXIT_MANIFEST


def test_manifest_invalid_json_exit_9(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    manifest = tmp_path / "bad.json"
    manifest.write_text("{", encoding="utf-8")
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(tmp_path / "o.json"),
            "--manifest",
            str(manifest),
        ]
    )
    assert rc == EXIT_MANIFEST


def test_unexpected_error_exit_99(monkeypatch, tmp_path: Path) -> None:
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("panos_changedoc.cli.diff_configs", _boom)
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(tmp_path / "o.json"),
        ]
    )
    assert rc == EXIT_UNEXPECTED
