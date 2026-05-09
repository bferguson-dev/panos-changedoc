# Versioning

PAN-OS ChangeDoc tracks two different versions:

- Package version: the Python tool release, currently `0.1.0`
- JSON schema version: the report contract, currently `1.0`

These versions move independently.

## Package Version

The package version follows semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Use:

- `PATCH` for bug fixes that do not change documented behavior.
- `MINOR` for new supported sections, new CLI options, or additive report data.
- `MAJOR` for incompatible CLI, schema, or meaning changes.

The package version is recorded in:

- `pyproject.toml`
- `src/panos_changedoc/__init__.py`
- `VERSION`
- `CHANGELOG.md`

The JSON report includes the package version under:

```json
"tool": {
  "name": "panos-changedoc",
  "version": "0.1.0"
}
```

## JSON Schema Version

The JSON schema version describes the report shape.

Current schema:

```json
"schema_version": "1.0"
```

Changing the Python package version does not automatically change the JSON
schema version.

## Release Checklist

Before a release:

1. Update `CHANGELOG.md`.
2. Update `VERSION`.
3. Update `pyproject.toml`.
4. Update `src/panos_changedoc/__init__.py`.
5. Regenerate golden outputs if report content intentionally changed.
6. Run the full test suite.

Required checks:

```bash
ruff check .
ruff format --check .
ruff check --select E501 .
mypy src
pytest
```

## Current Release History

- `0.1.0`: initial MVP release with offline diff, Markdown and JSON reports,
  deterministic generator, GUI wrapper, and test coverage.
