from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceObject:
    name: str
    protocol: str
    destination_port: str
    source_port: str | None
    description: str | None
    tags: tuple[str, ...]
    xpath: str
    collection_xpath: str
