import json
from pathlib import Path

from panos_changedoc.cli import main


def test_golden_json_and_markdown(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    rc = main(["diff", "--before", str(fixtures / "before_basic.xml"), "--after", str(fixtures / "after_basic.xml"), "--json", str(out_json), "--markdown", str(out_md)])
    assert rc == 0
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert any(c["entity"]["name"] == "RuleA" for c in report["changes"])
    assert "PAN-OS Change Documentation" in out_md.read_text(encoding="utf-8")
