import json
from pathlib import Path
from zipfile import ZipFile

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


def test_evidence_bundle_can_be_only_output(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    bundle = tmp_path / "evidence.zip"

    rc = main(
        [
            "diff",
            "--before",
            str(fixtures / "before_basic.xml"),
            "--after",
            str(fixtures / "after_basic.xml"),
            "--evidence-bundle",
            str(bundle),
        ]
    )

    assert rc == 0
    expected_files = {
        "before.xml",
        "after.xml",
        "change-summary.json",
        "change-summary.md",
        "evidence-manifest.json",
        "SHA256SUMS",
    }
    assert bundle.exists()

    with ZipFile(bundle) as archive:
        assert set(archive.namelist()) == expected_files
        report = json.loads(archive.read("change-summary.json").decode("utf-8"))
        manifest = json.loads(archive.read("evidence-manifest.json").decode("utf-8"))
        sums = archive.read("SHA256SUMS").decode("utf-8")

    assert report["schema_version"] == "1.0"
    assert manifest["evidence_manifest_version"] == "1.0"
    assert manifest["command"]["evidence_bundle"] == str(bundle)
    assert "before.xml" in sums
    assert "evidence-manifest.json" in sums


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
