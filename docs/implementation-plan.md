# PAN-OS ChangeDoc v1 Implementation Plan

## Current status

The `0.1.0` MVP implements the v1 epics listed below. Future work should keep
this file as the implementation history and use `CHANGELOG.md` for release
notes.

## Locked scope

- Standalone firewall XML only
- `vsys1` only
- Security/NAT/address/address-group/service/zone entities
- JSON + Markdown outputs
- Deterministic IDs
- Reference graph max depth `3` with cycle detection

## Epic sequencing

1. Epic 0: docs - complete in `0.1.0`
2. Epic 1: scaffold + walking skeleton - complete in `0.1.0`
3. Epic 2: core model + schema validation - complete in `0.1.0`
4. Epic 3: full security parser/diff + LCS reorder - complete in `0.1.0`
5. Epic 4: address object/group parser/diff - complete in `0.1.0`
6. Epic 5: NAT parser/diff - complete in `0.1.0`
7. Epic 6: service + zone parser/diff - complete in `0.1.0`
8. Epic 7: reference graph - complete in `0.1.0`
9. Epic 8: markdown generator - complete in `0.1.0`
10. Epic 9: deterministic generator + manifest - complete in `0.1.0`
11. Epic 10: golden tests - complete in `0.1.0`
12. Epic 11: CLI hardening + exit code coverage - complete in `0.1.0`
13. Epic 12: CI workflow - complete in `0.1.0`

## Epic 1 walking skeleton definition

Must include:

- `panos-changedoc diff --before --after --json`
- safe XML parsing
- exactly one standalone device entry detection
- `vsys1` presence check
- parse security rule name and destination members
- normalize destination members
- detect one destination modification
- deterministic ID
- schema-valid JSON output

## Key v1 rules to enforce from day one

- `rulebase` required on all entities (`security`, `nat`, `null`)
- `config_version` and `panos_version` nullable
- change type `enabled`/`disabled` only when `disabled` field changed alone
- `added`/`removed` include `snapshot`
- IDs format `chg_<abbrev>_<change_type>_<hash16>`
- significance taxonomy only (`CRITICAL|HIGH|LOW`)
