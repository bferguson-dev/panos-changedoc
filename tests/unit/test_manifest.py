from panos_changedoc.schema import ManifestValidationError, validate_manifest


def test_manifest_validation_failure() -> None:
    manifest = {"expected": {"total_changes": 999}}
    report = {"summary": {"total_changes": 1}}
    try:
        validate_manifest(manifest, report)
        assert False
    except ManifestValidationError:
        assert True
