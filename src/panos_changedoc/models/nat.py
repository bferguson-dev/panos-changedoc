from dataclasses import dataclass

from panos_changedoc.models.security import MemberSet


@dataclass(frozen=True)
class NatRule:
    name: str
    from_zone: MemberSet
    to_zone: MemberSet
    source: MemberSet
    destination: MemberSet
    service: MemberSet
    disabled: bool
    translation: dict
    xpath: str
    collection_xpath: str
    rulebase: str = "nat"
