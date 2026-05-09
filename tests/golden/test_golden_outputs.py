from pathlib import Path

from panos_changedoc.cli import main


def test_golden_json_and_markdown_exact_match(tmp_path: Path, monkeypatch) -> None:
    root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(root)
    monkeypatch.setenv("PANOS_CHANGEDOC_GENERATED_AT", "2026-05-08T00:00:00+00:00")

    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"

    rc = main(
        [
            "diff",
            "--before",
            "tests/fixtures/before_basic.xml",
            "--after",
            "tests/fixtures/after_basic.xml",
            "--json",
            str(out_json),
            "--markdown",
            str(out_md),
        ]
    )
    assert rc == 0

    expected_json = (root / "tests" / "golden" / "expected_report.json").read_text(
        encoding="utf-8"
    )
    expected_md = (root / "tests" / "golden" / "expected_report.md").read_text(
        encoding="utf-8"
    )

    assert out_json.read_text(encoding="utf-8") == expected_json
    assert out_md.read_text(encoding="utf-8") == expected_md

    monkeypatch.delenv("PANOS_CHANGEDOC_GENERATED_AT", raising=False)
