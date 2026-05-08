from __future__ import annotations

from pathlib import Path

from panos_changedoc.generate import build_from_spec, default_spec, write_outputs


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sample = root / "sample_configs"
    sample.mkdir(parents=True, exist_ok=True)

    spec = default_spec()
    before_xml, after_xml, manifest = build_from_spec(spec)
    write_outputs(
        before_xml=before_xml,
        after_xml=after_xml,
        manifest=manifest,
        before_out=str(sample / "before.xml"),
        after_out=str(sample / "after.xml"),
        manifest_out=str(sample / "manifest.json"),
    )


if __name__ == "__main__":
    main()
