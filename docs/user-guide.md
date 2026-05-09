# PAN-OS ChangeDoc User Guide

This guide is written for firewall engineers reviewing PAN-OS configuration
changes.

PAN-OS ChangeDoc compares two exported XML configuration files:

- `before.xml`: the configuration before the change
- `after.xml`: the configuration after the change

The output is a change document, not an approval decision.

## Basic Workflow

1. Export or collect the before and after PAN-OS XML files.
2. Run `panos-changedoc diff`.
3. Attach the Markdown report to the change ticket.
4. Use the JSON report for repeatable testing or automation.

```bash
panos-changedoc diff \
  --before before.xml \
  --after after.xml \
  --json change-summary.json \
  --markdown change-summary.md
```

## What To Look For In The Markdown Report

The Markdown report is organized for review:

- Summary of input files and hashes
- Counts by significance and entity type
- Security rule changes
- NAT rule changes
- Object, service, and zone changes
- Reference impact
- Parser warnings
- Unsupported sections

`CRITICAL`, `HIGH`, and `LOW` describe how prominently a change should appear
in documentation. They are not risk scores and they do not make CI fail.

## What The JSON Report Is For

The JSON report is stable and schema-validated. Use it for:

- Golden-file tests
- CI artifact review
- Automation that needs machine-readable change records
- Verifying deterministic change IDs

The JSON report includes file hashes, detected firewall scope, summary counts,
changes, warnings, unsupported sections, and errors.

## Change IDs

Each change record has a deterministic ID such as:

```text
chg_sec_modified_9f31a8c7d0e2b441
```

The ID is based on the semantic change, not on the report timestamp or output
path. Repeating the same comparison should produce the same change IDs.

## Exit Codes

Common exit codes:

- `0`: report generated successfully
- `2`: CLI usage error
- `3`: input file missing or unreadable
- `4`: malformed XML
- `5`: unsupported or missing required scope
- `7`: output write error
- `8`: JSON schema validation failure
- `9`: generator manifest validation failure

Warnings do not change the exit code.

## Scope Expectations

The XML must be a standalone firewall export with exactly one:

```text
/config/devices/entry
```

The supported virtual system is:

```text
vsys1
```

Zones are parsed from the device network tree because PAN-OS stores zones there,
even though security and NAT policy reference them by name.

## Practical Review Notes

- A renamed rule or object appears as removed plus added.
- A disabled-state-only rule change appears as `enabled` or `disabled`.
- If the same rule also changes another field, it appears once as `modified`.
- Rule insertions and removals should not cause every shifted rule to appear as
  reordered.
- Unsupported sections should be reviewed manually because v1 did not normalize
  them.
