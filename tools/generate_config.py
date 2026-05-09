from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def _reexec_with_project_venv() -> None:
    # Direct script execution is common during testing. Prefer the project
    # virtualenv when it exists so generator dependencies match the package.
    venv_root = ROOT / ".venv"
    venv_python = ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return
    if Path(sys.prefix) == venv_root or Path(sys.executable) == venv_python:
        return
    os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


def _add_src_to_path() -> None:
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def main(argv: list[str] | None = None) -> int:
    _reexec_with_project_venv()
    _add_src_to_path()
    from panos_changedoc.cli import main as cli_main
    from panos_changedoc.generate import build_from_spec, default_spec, write_outputs

    args = sys.argv[1:] if argv is None else argv
    if args:
        return cli_main(["generate", *args])

    sample = ROOT / "sample_configs"
    sample.mkdir(parents=True, exist_ok=True)

    spec = default_spec()
    before_xml, after_xml, manifest = build_from_spec(spec)
    write_outputs(
        before_xml=before_xml,
        after_xml=after_xml,
        manifest=manifest,
        before_out=str(sample / "before.xml"),
        after_out=str(sample / "after.xml"),
        manifest_out=str(sample / "manifest.json"),
    )
    print(
        "Generated files:\n"
        f"- before: {sample / 'before.xml'}\n"
        f"- after: {sample / 'after.xml'}\n"
        f"- manifest: {sample / 'manifest.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
