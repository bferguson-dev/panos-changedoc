# Generator Guide

The generator creates deterministic PAN-OS XML pairs for testing ChangeDoc.

It is useful when you do not have a firewall available but still need realistic
XML examples for security policy, NAT, objects, services, and zones.

## Generate Default Files

```bash
panos-changedoc generate --write-default-spec sample_configs/spec.yaml
panos-changedoc generate \
  --spec sample_configs/spec.yaml \
  --before-out sample_configs/before.xml \
  --after-out sample_configs/after.xml \
  --manifest-out sample_configs/manifest.json
```

Or run the helper script:

```bash
python3 tools/generate_config.py
```

## YAML Spec Shape

```yaml
version: 1
panos_version: '12.1'
profile: standalone_vsys1
settings:
  - key: security_dest_app01
    before: true
    after: true
```

Each `settings` item selects one generator template.

- `before: true` means the template appears in `before.xml`.
- `after: true` means the template appears in `after.xml`.
- `before: true` and `after: true` can create a modification if the template
  has different before and after payloads.
- `before: true` and `after: false` creates a removal.
- `before: false` and `after: true` creates an addition.

## List Available Templates

```bash
panos-changedoc generate --list-templates --format yaml
```

Template categories currently include:

- `security_rules`
- `security_reorder`
- `nat_rules`
- `nat_reorder`
- `address_objects`
- `address_groups`
- `service_objects`
- `zones`

## Logical Validation

The generator checks that the resulting XML is logically usable for the
supported v1 sections.

Examples of hard errors:

- A security or NAT rule references a missing zone.
- A rule references a missing address object, address group, or service object.
- Duplicate names exist in the same object type and side.
- YAML contains unknown keys.
- YAML uses an unsupported template key.

The error message includes a fix suggestion.

## Manifest File

The generator writes `manifest.json` next to the XML files. The manifest
describes the expected diff output for that generated pair.

Use the manifest to confirm that the diff tool saw the intended changes, not
only that it produced syntactically valid output.

## GUI Relationship

The Tkinter GUI `Test Generator` tab uses the same template catalog and
validation logic as the CLI. The GUI checkboxes are just a visual way to build
the same YAML settings model.

This keeps future additions simple: add a template to the catalog, and both CLI
and GUI workflows can expose it.
