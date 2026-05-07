from dataclasses import dataclass


@dataclass(frozen=True)
class AddressObject:
    name: str
    value_type: str
    value: str
    description: str | None
    tags: tuple[str, ...]
    xpath: str
    collection_xpath: str


@dataclass(frozen=True)
class AddressGroup:
    name: str
    group_type: str
    static_members: tuple[str, ...]
    dynamic_filter: str | None
    description: str | None
    tags: tuple[str, ...]
    xpath: str
    collection_xpath: str
