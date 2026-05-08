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


def test_generate_list_templates_yaml(capsys) -> None:
    rc = main(["generate", "--list-templates", "--format", "yaml"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "key: security_dest_app01" in out
    assert "category: security_rules" in out


def test_generate_missing_spec_returns_input_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    rc = main(["generate", "--spec", str(missing)])
    assert rc == 3


def test_generate_validation_message_dedupes_duplicate_issues(
    tmp_path: Path, capsys
) -> None:
    spec = tmp_path / "logicbad.yaml"
    spec.write_text(
        "\n".join(
            [
                "version: 1",
                "panos_version: '12.1'",
                "profile: standalone_vsys1",
                "settings:",
                "  - key: nat_translation_app01",
                "    before: false",
                "    after: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rc = main(["generate", "--spec", str(spec)])
    assert rc == 9
    err = capsys.readouterr().err
    assert err.count("missing zone 'untrust'") == 1


def test_gui_command_handles_missing_tkinter(monkeypatch, capsys) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "tkinter":
            raise ModuleNotFoundError("No module named 'tkinter'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    rc = main(["gui"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "GUI dependencies are unavailable" in err
