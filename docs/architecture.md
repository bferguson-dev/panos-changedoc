# PAN-OS ChangeDoc v1 Architecture

## Goals

Offline PAN-OS XML semantic diff for change documentation. Outputs Markdown (humans) and JSON (automation/tests).

## Non-goals

No risk linting, policy enforcement, approval workflows, deployment, live firewall access, Panorama/device groups/templates/shared resolution, multi-vsys, rename detection.

## Package layout

- `loader.py`: file IO, hash/size metadata, safe XML parse wrapper
- `parsers/panos_xml.py`: standalone device discovery, `vsys1` scope validation, entity extraction
- `normalizer.py`: canonicalization helpers for model fields
- `models/*`: typed model primitives
- `diff/*`: entity diff logic, LCS reorder logic, stable ordering
- `ids.py`: deterministic change IDs from canonical JSON input
- `schema.py`: JSON schema and validation
- `reports/json_report.py`: JSON assembly and emission
- `reports/markdown.py`: Markdown emission (Epic 8)
- `cli.py`: command line contract and exit code orchestration
- `generate.py`: deterministic before/after XML generator
- `gui.py`: Tkinter wrapper around generator and diff workflows
- `tools/generate_config.py`: direct helper for generating sample XML

## Pipeline

1. CLI validates arguments and paths.
2. Load before/after XML with safe parser.
3. Discover single `/config/devices/entry`, validate `vsys1`.
4. Parse supported entities.
5. Normalize models.
6. Diff models.
7. Attach deterministic IDs.
8. Sort stable output order.
9. Build JSON document.
10. Validate JSON schema.
11. Write outputs.

## Error model and exit codes

- `2`: CLI usage
- `3`: input file read
- `4`: malformed XML parse
- `5`: unsupported/missing required scope (root/device entry/vsys1)
- `6`: fatal parse/model error inside supported section
- `7`: output write
- `8`: JSON schema validation
- `9`: manifest validation
- `99`: unexpected internal error

Warnings never change exit code.

## Determinism

Determinism controls:

- canonical model normalization
- canonical JSON for ID hashing
- stable change ordering
- no runtime-specific fields in ID input
- no randomness in generators/tests
