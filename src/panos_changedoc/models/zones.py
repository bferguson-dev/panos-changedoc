from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    name: str
    interfaces: tuple[str, ...]
    xpath: str
    collection_xpath: str
