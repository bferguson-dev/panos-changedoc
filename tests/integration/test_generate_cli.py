import json
from pathlib import Path

from panos_changedoc.cli import main
from panos_changedoc.generate import default_spec
import yaml


def test_generate_cli_from_spec_and_diff_manifest(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        yaml.safe_dump(default_spec(), sort_keys=False), encoding="utf-8"
    )

    before_out = tmp_path / "before.xml"
    after_out = tmp_path / "after.xml"
    manifest_out = tmp_path / "manifest.json"

    rc_gen = main(
        [
            "generate",
            "--spec",
            str(spec_path),
            "--before-out",
            str(before_out),
            "--after-out",
            str(after_out),
            "--manifest-out",
            str(manifest_out),
        ]
    )
    assert rc_gen == 0

    report_out = tmp_path / "report.json"
    rc_diff = main(
        [
            "diff",
            "--before",
            str(before_out),
            "--after",
            str(after_out),
            "--json",
            str(report_out),
            "--manifest",
            str(manifest_out),
        ]
    )
    assert rc_diff == 0

    report = json.loads(report_out.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    assert report["summary"]["total_changes"] == manifest["expected"]["total_changes"]


def test_generate_write_default_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "default.yaml"
    rc = main(["generate", "--write-default-spec", str(spec_path)])
    assert rc == 0
    assert spec_path.exists()
