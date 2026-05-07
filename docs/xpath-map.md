# PAN-OS ChangeDoc v1 XPath Map

## Scope

This map is locked for v1 and supports **standalone PAN-OS firewall XML** only, **vsys1** only.

## Device Discovery

Parser discovery root:

- `/config/devices/entry`

Behavior:

- If exactly one `/config/devices/entry` exists: use it.
- If zero exist: fail with exit code `5`.
- If more than one exists: fail with exit code `5`.

Variables:

- `DEVICE_ENTRY = /config/devices/entry[@name='<device_entry_name>']`
- `VSYS1 = DEVICE_ENTRY/vsys/entry[@name='vsys1']`

Required scope path:

- `/config/devices/entry[@name='<device_entry_name>']/vsys/entry[@name='vsys1']`

If `vsys1` is missing: fail with exit code `5`.

## Supported v1 Paths

### Security rules

- `VSYS1/rulebase/security/rules`
- `VSYS1/rulebase/security/rules/entry`

### NAT rules

- `VSYS1/rulebase/nat/rules`
- `VSYS1/rulebase/nat/rules/entry`

### Address objects

- `VSYS1/address`
- `VSYS1/address/entry`

### Address groups

- `VSYS1/address-group`
- `VSYS1/address-group/entry`

### Service objects

- `VSYS1/service`
- `VSYS1/service/entry`

### Zones

Zones are parsed from **device-level network scope**, not `vsys1` path:

- `/config/devices/entry[@name='<device_entry_name>']/network/zone`
- `/config/devices/entry[@name='<device_entry_name>']/network/zone/entry`

## Unsupported Detection

Everything outside supported v1 paths is unsupported in v1. Unsupported encountered sections are surfaced in `unsupported[]`; they are not silently ignored.

## Entity Scope Metadata

All entities include `rulebase`:

- Security rules: `"security"`
- NAT rules: `"nat"`
- Address objects: `null`
- Address groups: `null`
- Service objects: `null`
- Zones: `null`
