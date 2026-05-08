import pytest

from panos_changedoc.generate import (
    GenerateValidationError,
    build_from_spec,
    default_spec,
    load_spec,
)


def test_default_spec_builds() -> None:
    before_xml, after_xml, manifest = build_from_spec(default_spec())
    assert before_xml.startswith("<config>")
    assert after_xml.startswith("<config>")
    assert manifest["expected"]["total_changes"] >= 1


def test_unknown_yaml_key_is_hard_error(tmp_path) -> None:
    path = tmp_path / "spec.yaml"
    path.write_text(
        """
version: 1
panos_version: '12.1'
profile: standalone_vsys1
unknown_root_key: true
settings:
  - key: security_dest_app01
    before: true
    after: true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(GenerateValidationError):
        load_spec(str(path))


def test_setting_unknown_key_is_hard_error(tmp_path) -> None:
    path = tmp_path / "spec.yaml"
    path.write_text(
        """
version: 1
panos_version: '12.1'
profile: standalone_vsys1
settings:
  - key: security_dest_app01
    before: true
    after: true
    wrong: 1
""".strip()
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(GenerateValidationError):
        load_spec(str(path))
