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

## Generate Test Configs from YAML

```bash
panos-changedoc generate --write-default-spec sample_configs/spec.yaml
panos-changedoc generate \
  --spec sample_configs/spec.yaml \
  --before-out sample_configs/before.xml \
  --after-out sample_configs/after.xml \
  --manifest-out sample_configs/manifest.json
```

List selectable generator templates:

```bash
panos-changedoc list-templates
```

## GUI Wrapper

Launch the Tkinter wrapper:

```bash
panos-changedoc gui
```

GUI features:
- Tabbed sections for generator and diff workflows
- Before/After checkboxes for each deterministic change template
- Test mode to generate before running diff
- Run Diff button for user-selected before/after files
