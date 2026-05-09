# Validation And Limits

PAN-OS ChangeDoc validates the XML enough to compare supported v1 sections
safely. It does not perform a PAN-OS commit validation.

## What Is Validated

For input XML:

- Root element is `<config>`.
- Exactly one `/config/devices/entry` exists.
- `vsys1` exists.
- Supported entries have required names.
- XML is parsed with a safe XML parser.

For generated XML:

- The selected profile is supported.
- The PAN-OS version in the spec matches the profile.
- Generator keys are known.
- Rule references point to generated objects, groups, services, and zones.
- Duplicate names are rejected per side and entity type.

For JSON output:

- The final report validates against the project JSON schema.
- All required top-level sections are present.
- Change records include required entity and reference fields.

## What Is Not Validated

The tool does not validate:

- Whether PAN-OS would commit the full candidate configuration.
- Whether a rule is safe or risky.
- Whether an address is routable.
- Whether NAT and security policy are operationally correct together.
- Whether a dynamic address group has runtime members.
- Whether application dependencies are complete.

## Unsupported Sections

Unsupported sections are reported in the JSON and Markdown output.

This is intentional. If a config contains supported and unsupported content,
the report should make the unsupported content visible to the reviewer instead
of hiding it.

## Current PAN-OS Profile

The generator profile is:

```text
standalone_vsys1
```

The configured PAN-OS version label is:

```text
12.1
```

This is used for generated fixture metadata and syntax shape. It is not a live
firewall compatibility guarantee.

## Recommended Operator Use

Use the generated report as change-documentation input:

- Attach the Markdown report to the ticket.
- Use the JSON report when a pipeline needs stable structured output.
- Review unsupported sections manually.
- Run normal firewall validation and peer review outside this tool.
