from __future__ import annotations

from hashlib import sha256
import json
import platform
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from panos_changedoc.loader import LoadedXml
from panos_changedoc.reports.markdown import render_markdown


def _hash_file(path: Path) -> tuple[str, int]:
    raw = path.read_bytes()
    return sha256(raw).hexdigest(), len(raw)


def _copy_input(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        return
    shutil.copyfile(source, destination)


def _git_value(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _git_dirty() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def _file_record(role: str, path: Path, source_path: str | None = None) -> dict:
    digest, size = _hash_file(path)
    record: dict[str, Any] = {
        "role": role,
        "path": path.name,
        "sha256": digest,
        "size_bytes": size,
    }
    if source_path is not None:
        record["source_path"] = source_path
    return record


def _zip_path(bundle_path: str) -> Path:
    target = Path(bundle_path)
    if target.suffix.lower() != ".zip":
        target = target.with_suffix(".zip")
    return target


def write_evidence_bundle(
    *,
    bundle_dir: str,
    before_loaded: LoadedXml,
    after_loaded: LoadedXml,
    report: dict,
    command_args: dict,
) -> Path:
    """Write a zipped evidence bundle for change-ticket attachment."""
    zip_path = _zip_path(bundle_dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # Stage the evidence files in a temporary directory first so the final zip
    # is created atomically from a complete, known-good set of artifacts.
    with tempfile.TemporaryDirectory(prefix="panos-changedoc-evidence-") as tmp:
        bundle = Path(tmp)
        before_copy = bundle / "before.xml"
        after_copy = bundle / "after.xml"
        json_report = bundle / "change-summary.json"
        markdown_report = bundle / "change-summary.md"
        manifest_path = bundle / "evidence-manifest.json"
        sums_path = bundle / "SHA256SUMS"

        _copy_input(before_loaded.path, before_copy)
        _copy_input(after_loaded.path, after_copy)
        json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        markdown_report.write_text(render_markdown(report), encoding="utf-8")

        files = [
            _file_record("before_input", before_copy, str(before_loaded.path)),
            _file_record("after_input", after_copy, str(after_loaded.path)),
            _file_record("json_report", json_report),
            _file_record("markdown_report", markdown_report),
        ]
        manifest = {
            "evidence_manifest_version": "1.0",
            "tool": report["tool"],
            "json_schema_version": report["schema_version"],
            "run": report["run"],
            "command": command_args,
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "git_commit": _git_value(["rev-parse", "HEAD"]),
                "git_dirty": _git_dirty(),
            },
            "files": files,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

        sums_records = [*files, _file_record("evidence_manifest", manifest_path)]
        sums = "".join(f"{item['sha256']}  {item['path']}\n" for item in sums_records)
        sums_path.write_text(sums, encoding="utf-8")

        # The final deliverable is a zip file, not a loose directory.
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted(bundle.iterdir()):
                archive.write(path, arcname=path.name)

    return zip_path
