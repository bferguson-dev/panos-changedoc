# Evidence Bundle Mode

Evidence bundle mode writes a self-contained zip file for change-ticket or audit
attachment.

It is designed to make the comparison reproducible and easier to verify later.
It does not replace normal firewall approval, commit validation, or operational
review.

## Basic Usage

```bash
panos-changedoc diff \
  --before before.xml \
  --after after.xml \
  --evidence-bundle evidence/change-2026-05-09.zip
```

You can also write normal output files at the same time:

```bash
panos-changedoc diff \
  --before before.xml \
  --after after.xml \
  --json reports/change-summary.json \
  --markdown reports/change-summary.md \
  --evidence-bundle evidence/change-2026-05-09.zip
```

## Bundle Contents

```text
evidence/change-2026-05-09.zip
├── before.xml
├── after.xml
├── change-summary.json
├── change-summary.md
├── evidence-manifest.json
└── SHA256SUMS
```

## Evidence Manifest

`evidence-manifest.json` records:

- evidence manifest version
- tool name and version
- JSON schema version
- generated timestamp
- diff command arguments
- Python version and platform
- Git commit, when available
- whether the working tree was dirty, when available
- file names, source paths, sizes, and SHA256 hashes

`SHA256SUMS` provides a simple hash list for the copied inputs, reports, and
manifest.

## GUI Use

In the GUI Diff tab:

1. Select before and after XML files.
2. Check `Create evidence bundle`.
3. Choose the bundle zip path.
4. Click `Run Diff`.

The Diff Results panel shows that it is creating the evidence bundle and zipping
it while the run is in progress. It also shows the evidence bundle zip path
after the run completes.
