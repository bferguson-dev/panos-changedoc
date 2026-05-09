from dataclasses import dataclass


@dataclass(frozen=True)
class ParserWarning:
    code: str
    message: str


@dataclass(frozen=True)
class UnsupportedSection:
    xpath: str
    reason: str
