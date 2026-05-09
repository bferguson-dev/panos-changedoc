import json
from pathlib import Path

from panos_changedoc.cli import main


def test_end_to_end_json_and_markdown(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--json",
            str(out_json),
            "--markdown",
            str(out_md),
        ]
    )
    assert rc == 0
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1.0"
    assert out_md.exists()


def test_noop_formatting_produces_zero_changes(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    source = (fixtures / "before_basic.xml").read_text(encoding="utf-8")
    noisy = source.replace("<member>APP01</member>", "\n    <member>APP01</member>   ")
    b = tmp_path / "b.xml"
    a = tmp_path / "a.xml"
    out = tmp_path / "out.json"
    b.write_text(source, encoding="utf-8")
    a.write_text(noisy, encoding="utf-8")
    rc = main(["diff", "--before", str(b), "--after", str(a), "--json", str(out)])
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["total_changes"] == 0
