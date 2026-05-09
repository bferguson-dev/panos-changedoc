from dataclasses import dataclass


@dataclass(frozen=True)
class MemberSet:
    type: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class SecurityRule:
    name: str
    from_zone: MemberSet
    to_zone: MemberSet
    source: MemberSet
    destination: MemberSet
    application: MemberSet
    service: MemberSet
    action: str
    disabled: bool
    log_end: bool
    description: str | None
    tags: tuple[str, ...]
    xpath: str
    collection_xpath: str
    rulebase: str = "security"
