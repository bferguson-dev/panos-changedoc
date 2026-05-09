# PAN-OS ChangeDoc v1 JSON Contract

## Top-level shape

```json
{
  "schema_version": "1.0",
  "tool": {},
  "run": {},
  "inputs": {},
  "summary": {},
  "changes": [],
  "warnings": [],
  "unsupported": [],
  "errors": []
}
```

All top-level keys above are required.

## Inputs contract

`inputs.before` and `inputs.after` are required and each include:

- `role` (`"before"` or `"after"`)
- `path`
- `filename`
- `sha256`
- `size_bytes`
- `detected`

`detected` fields:

- `config_type`: `"standalone_firewall"`
- `device_entry_name`
- `hostname`
- `config_version`: nullable
- `panos_version`: nullable
- `vsys`: `"vsys1"`
- `base_xpath`

## Change record contract

Every change requires:

- `id` format: `chg_<entity_type_abbrev>_<change_type>_<hash16>`
- `change_type`: one of `added`, `removed`, `modified`, `reordered`, `enabled`, `disabled`
- `entity`
- `significance`: one of `CRITICAL`, `HIGH`, `LOW`
- `title`
- `fields_changed` (list, may be empty)
- `field_changes` (list of before/after details, may be empty)
- `references` object
- `notes` (list)

`field_changes` entries include:

- `path`: normalized changed field path
- `before`: normalized before value
- `after`: normalized after value

For `added` and `removed` records, use `snapshot` for the full normalized
entity state.

`entity` requires:

- `type`: `security_rule|nat_rule|address_object|address_group|service_object|zone`
- `name`
- `scope`: `"local"`
- `vsys`: `"vsys1"`
- `rulebase`: required; `"security"|"nat"|null` per entity type
- `xpath`
- `collection_xpath`

`references` requires:

- `direct` list
- `transitive` list
- `truncated` bool
- `max_depth` (must be `3` in v1)

`snapshot` requirements:

- `added` records include `snapshot` = normalized after-state.
- `removed` records include `snapshot` = normalized before-state.

## Change ordering (stable)

Sort by:

1. significance (`CRITICAL`, `HIGH`, `LOW`)
2. entity type (`security_rule`, `nat_rule`, `address_object`, `address_group`, `service_object`, `zone`)
3. change type (`added`, `removed`, `modified`, `enabled`, `disabled`, `reordered`)
4. entity name
5. change ID

## Significance semantics

`significance` is documentation prominence only, not risk scoring. CI must not fail due to change significance value.
