from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from defusedxml.ElementTree import ParseError, parse
from xml.etree.ElementTree import Element


@dataclass(frozen=True)
class LoadedXml:
    path: Path
    filename: str
    sha256_hex: str
    size_bytes: int
    root: Element


class InputFileError(Exception):
    pass


class XmlParseError(Exception):
    pass


def load_xml_file(path_str: str) -> LoadedXml:
    path = Path(path_str)
    if not path.exists() or not path.is_file():
        raise InputFileError(f"Input file not found: {path_str}")

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputFileError(f"Input file unreadable: {path_str}") from exc

    try:
        root = parse(path).getroot()
    except ParseError as exc:
        raise XmlParseError(f"Malformed XML: {path_str}") from exc
    if root is None:
        raise XmlParseError(f"Malformed XML: {path_str}")

    return LoadedXml(
        path=path,
        filename=path.name,
        sha256_hex=sha256(raw).hexdigest(),
        size_bytes=len(raw),
        root=root,
    )
