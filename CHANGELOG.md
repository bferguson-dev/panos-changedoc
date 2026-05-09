# Changelog

All notable project changes are recorded here.

PAN-OS ChangeDoc uses semantic versioning for the Python package and a separate
JSON schema version for report compatibility.

## [Unreleased]

### Added

- Firewall-engineer-facing user documentation.
- Versioning policy documentation.
- Generator and validation documentation.

### Changed

- Centralized report output to use the package version.
- Added operational comments around PAN-OS parsing, diff, generator, and ID
  logic.

## [0.1.0] - 2026-05-09

### Added

- Offline `panos-changedoc diff` command for before/after PAN-OS XML files.
- Markdown report output for change documentation.
- JSON report output for CI, automation, and golden tests.
- Safe XML loading with standalone firewall and `vsys1` scope validation.
- Security rule parsing and diffing.
- NAT rule parsing and diffing.
- Address object and address group parsing and diffing.
- Service object and zone parsing and diffing.
- Device-level zone parsing from `/config/devices/entry/network/zone`.
- Deterministic change IDs using canonical JSON and SHA-256.
- Longest common subsequence rule reorder detection.
- Enabled/disabled change type handling for pure disabled-state toggles.
- Reference graph with max depth `3`, transitive references, and cycle handling.
- Unsupported-section reporting for unsupported v1 XML content.
- Deterministic YAML-driven XML generator.
- `tools/generate_config.py` helper for direct sample config generation.
- Tkinter GUI wrapper for generator and diff workflows.
- Golden JSON, golden Markdown, unit, integration, and exit-code tests.
- GitHub Actions CI workflow.

### Fixed

- Direct generator script now works from a source checkout by using the project
  virtual environment when present.
- Generator missing-spec handling returns input error exit code `3`.
- Malformed YAML errors include operator-facing fix guidance.
- Duplicate generator validation issues are deduplicated.
- GUI command handles missing Tkinter with a clean message and exit code `2`.

### Known Limits

- Panorama, templates, device groups, shared objects, and multi-vsys exports are
  outside v1 scope.
- Rename detection is deferred; renamed items appear as removed plus added.
- Dynamic address group runtime membership is not evaluated.
- No live firewall validation or commit validation is performed.
