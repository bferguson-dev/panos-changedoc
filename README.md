# PAN-OS ChangeDoc

PAN-OS ChangeDoc is an offline change-documentation tool for PAN-OS XML
configuration files.

It compares a `before.xml` file and an `after.xml` file, then writes:

- Markdown for change tickets and firewall review notes
- JSON for CI checks, automation, and repeatable tests

The tool does not connect to a firewall. It does not push config, approve
changes, score risk, or replace firewall review. It only documents what changed
inside the supported PAN-OS XML scope.

Current release: `0.1.1`

## Screenshots

UI screenshots will be added here later.

This section is reserved for:

- Main GUI layout
- Test Generator tab
- Diff tab
- Evidence bundle workflow

## Supported Scope

Version `0.1.1` supports standalone firewall exports with one device entry and
`vsys1`.

Supported sections:

- Security policy rules
- NAT policy rules
- Address objects
- Address groups
- Service objects
- Zones

Not supported in v1:

- Panorama, templates, device groups, or shared object resolution
- Multi-vsys comparison
- Live firewall or API access
- Routing analysis, rule hit counts, or dynamic address group runtime members
- Rename detection

Renames are documented as one removed item and one added item.

## Install

Use Python `3.12`.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Compare Two XML Files

```bash
panos-changedoc diff \
  --before sample_configs/before.xml \
  --after sample_configs/after.xml \
  --json reports/change-summary.json \
  --markdown reports/change-summary.md
```

Exit code `0` means the report was written. Warnings and `CRITICAL` changes do
not make the command fail.

## Create An Evidence Bundle

Use evidence bundle mode when you want one zip file to attach to a change ticket:

```bash
panos-changedoc diff \
  --before sample_configs/before.xml \
  --after sample_configs/after.xml \
  --evidence-bundle evidence/change-001.zip
```

The zip contains copied inputs, JSON and Markdown reports, an evidence
manifest, and `SHA256SUMS`.

## Generate Test XML

The generator creates deterministic before/after XML pairs for testing the diff
tool. It does not use randomness.

```bash
panos-changedoc generate --write-default-spec sample_configs/spec.yaml
panos-changedoc generate \
  --spec sample_configs/spec.yaml \
  --before-out sample_configs/before.xml \
  --after-out sample_configs/after.xml \
  --manifest-out sample_configs/manifest.json
```

You can also run the direct helper script from the project checkout:

```bash
python3 tools/generate_config.py
```

## List Generator Templates

```bash
panos-changedoc list-templates
panos-changedoc generate --list-templates --format yaml
```

Each template is a realistic firewall change building block. The YAML spec
chooses whether that block appears in `before`, `after`, or both.

## GUI Wrapper

```bash
panos-changedoc gui
```

The Tkinter GUI has:

- A Test Generator tab with before/after checkboxes for each template
- A diff tab with a Run Diff button
- Verbose on-screen diff results with field-level before/after values
- Two progress bars while the diff runs: current task and overall progress
- A completed-work trail in the results window while the job runs
- A View Results button after the report is ready
- Test mode that generates XML before running the diff
- Validation messages written for firewall operators

If the host does not have Tkinter installed, the CLI prints a readable error and
exits with code `2`.

## Important Output Rules

- `significance` means documentation prominence, not risk scoring.
- Change IDs are deterministic across repeated runs of the same inputs.
- Added and removed items include a normalized snapshot.
- Rule order changes use longest common subsequence detection so inserted or
  deleted rules do not make every shifted rule look reordered.
- Unsupported sections are surfaced in the report instead of silently ignored.

## Documentation

- [User guide](docs/user-guide.md)
- [Evidence bundle mode](docs/evidence-bundle.md)
- [Generator guide](docs/generator-guide.md)
- [Validation and limits](docs/validation-and-limits.md)
- [Versioning](docs/versioning.md)
- [Changelog](CHANGELOG.md)
- [XPath map](docs/xpath-map.md)
- [Normalization contract](docs/normalization-contract.md)
- [JSON schema contract](docs/json-schema.md)

## Development Checks

Run these before committing:

```bash
ruff check .
ruff format --check .
ruff check --select E501 .
mypy src
pytest
```

The configured line length is `88` characters.
