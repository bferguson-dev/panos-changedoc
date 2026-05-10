from pathlib import Path
import tomllib

from panos_changedoc import __version__


def test_package_version_matches_project_metadata() -> None:
    root = Path(__file__).resolve().parents[2]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text())
    version_file = (root / "VERSION").read_text(encoding="utf-8").strip()

    assert __version__ == "0.1.1"
    assert pyproject["project"]["version"] == __version__
    assert version_file == __version__
