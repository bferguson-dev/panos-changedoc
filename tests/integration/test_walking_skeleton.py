import json
from pathlib import Path

from panos_changedoc.cli import main


def test_walking_skeleton_detects_security_destination_change(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    before = root / "sample_configs" / "before.xml"
    after = root / "sample_configs" / "after.xml"
    out = tmp_path / "report.json"

    rc = main(["diff", "--before", str(before), "--after", str(after), "--json", str(out)])
    assert rc == 0

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1.0"
    assert len(report["changes"]) >= 1
    security = [
        c
        for c in report["changes"]
        if c["entity"]["type"] == "security_rule" and c["entity"]["name"] == "Allow-App01-HTTPS"
    ][0]
    assert security["change_type"] == "modified"
    assert security["fields_changed"] == ["destination"]


def test_walking_skeleton_id_is_stable_across_runs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    before = root / "sample_configs" / "before.xml"
    after = root / "sample_configs" / "after.xml"
    out1 = tmp_path / "r1.json"
    out2 = tmp_path / "r2.json"

    rc1 = main(["diff", "--before", str(before), "--after", str(after), "--json", str(out1)])
    rc2 = main(["diff", "--before", str(before), "--after", str(after), "--json", str(out2)])
    assert rc1 == 0
    assert rc2 == 0

    id1 = json.loads(out1.read_text(encoding="utf-8"))["changes"][0]["id"]
    id2 = json.loads(out2.read_text(encoding="utf-8"))["changes"][0]["id"]
    assert id1 == id2
