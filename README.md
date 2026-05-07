# PAN-OS ChangeDoc

PAN-OS ChangeDoc is an offline PAN-OS XML semantic diff tool for change documentation.

## v1 scope

- Standalone PAN-OS firewall XML only
- `vsys1` only
- Offline files only
- JSON and Markdown outputs

## Quickstart

```bash
python -m pip install -e '.[dev]'
panos-changedoc diff \
  --before sample_configs/before.xml \
  --after sample_configs/after.xml \
  --json reports/change-summary.json
```
