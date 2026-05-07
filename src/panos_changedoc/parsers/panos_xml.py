from dataclasses import dataclass
from xml.etree.ElementTree import Element

from panos_changedoc.models.nat import NatRule
from panos_changedoc.models.objects import AddressGroup, AddressObject
from panos_changedoc.models.security import MemberSet, SecurityRule
from panos_changedoc.models.services import ServiceObject
from panos_changedoc.models.zones import Zone
from panos_changedoc.normalizer import normalize_bool_text, normalize_member_list, normalize_text


class UnsupportedScopeError(Exception):
    pass


class FatalModelParseError(Exception):
    pass


@dataclass(frozen=True)
class ParsedConfig:
    device_entry_name: str
    hostname: str | None
    config_version: str | None
    panos_version: str | None
    vsys: str
    base_xpath: str
    security_rules: tuple[SecurityRule, ...]
    nat_rules: tuple[NatRule, ...]
    address_objects: tuple[AddressObject, ...]
    address_groups: tuple[AddressGroup, ...]
    service_objects: tuple[ServiceObject, ...]
    zones: tuple[Zone, ...]
    unsupported: tuple[dict, ...]
    warnings: tuple[dict, ...]


def _ms(parent: Element | None) -> MemberSet:
    if parent is None:
        return MemberSet(type="any", members=("any",))
    members = normalize_member_list([normalize_text(m.text) for m in parent.findall("member")])
    if not members:
        members = ("any",)
    return MemberSet(type="any" if members == ("any",) else "members", members=members)


def _tags(entry: Element) -> tuple[str, ...]:
    return normalize_member_list([normalize_text(m.text) for m in entry.findall("tag/member")])


def _desc(entry: Element) -> str | None:
    value = normalize_text(entry.findtext("description"))
    return value or None


def _translation(entry: Element) -> dict:
    sat = entry.find("source-translation")
    dat = entry.find("destination-translation")
    return {
        "source_translation": sat is not None,
        "destination_translation": {
            "raw": normalize_text("".join(dat.itertext())) if dat is not None else "",
        },
    }


def _detect_unsupported(vsys1: Element, base_xpath: str) -> list[dict]:
    supported = {"rulebase", "address", "address-group", "service"}
    unsupported: list[dict] = []
    for child in list(vsys1):
        tag = child.tag
        if tag not in supported and tag not in {"import", "display-name"}:
            unsupported.append(
                {
                    "xpath": f"{base_xpath}/{tag}",
                    "reason": f"Unsupported section in v1: {tag}",
                }
            )
    rb = vsys1.find("rulebase")
    if rb is not None:
        for child in list(rb):
            if child.tag not in {"security", "nat"}:
                unsupported.append(
                    {
                        "xpath": f"{base_xpath}/rulebase/{child.tag}",
                        "reason": f"Unsupported rulebase section in v1: {child.tag}",
                    }
                )
    return unsupported


def parse_standalone_vsys1(root: Element) -> ParsedConfig:
    if root.tag != "config":
        raise UnsupportedScopeError("Root element must be <config>")

    device_entries = root.findall("./devices/entry")
    if len(device_entries) != 1:
        raise UnsupportedScopeError("Expected exactly one /config/devices/entry")

    device = device_entries[0]
    device_entry_name = device.attrib.get("name")
    if not device_entry_name:
        raise UnsupportedScopeError("Device entry missing name")

    vsys1 = device.find("./vsys/entry[@name='vsys1']")
    if vsys1 is None:
        raise UnsupportedScopeError("Required vsys1 not found")

    base_xpath = f"/config/devices/entry[@name='{device_entry_name}']/vsys/entry[@name='vsys1']"

    sec_col = f"{base_xpath}/rulebase/security/rules"
    nat_col = f"{base_xpath}/rulebase/nat/rules"
    addr_col = f"{base_xpath}/address"
    agrp_col = f"{base_xpath}/address-group"
    svc_col = f"{base_xpath}/service"
    zone_col = f"/config/devices/entry[@name='{device_entry_name}']/network/zone"

    security_rules: list[SecurityRule] = []
    for entry in vsys1.findall("./rulebase/security/rules/entry"):
        name = entry.attrib.get("name")
        if not name:
            raise FatalModelParseError("Security rule entry missing name")
        security_rules.append(
            SecurityRule(
                name=name,
                from_zone=_ms(entry.find("from")),
                to_zone=_ms(entry.find("to")),
                source=_ms(entry.find("source")),
                destination=_ms(entry.find("destination")),
                application=_ms(entry.find("application")),
                service=_ms(entry.find("service")),
                action=normalize_text(entry.findtext("action")) or "allow",
                disabled=normalize_bool_text(entry.findtext("disabled")),
                log_end=normalize_bool_text(entry.findtext("log-end")),
                description=_desc(entry),
                tags=_tags(entry),
                xpath=f"{sec_col}/entry[@name='{name}']",
                collection_xpath=sec_col,
            )
        )

    nat_rules: list[NatRule] = []
    for entry in vsys1.findall("./rulebase/nat/rules/entry"):
        name = entry.attrib.get("name")
        if not name:
            raise FatalModelParseError("NAT rule entry missing name")
        nat_rules.append(
            NatRule(
                name=name,
                from_zone=_ms(entry.find("from")),
                to_zone=_ms(entry.find("to")),
                source=_ms(entry.find("source")),
                destination=_ms(entry.find("destination")),
                service=_ms(entry.find("service")),
                disabled=normalize_bool_text(entry.findtext("disabled")),
                translation=_translation(entry),
                xpath=f"{nat_col}/entry[@name='{name}']",
                collection_xpath=nat_col,
            )
        )

    address_objects: list[AddressObject] = []
    for entry in vsys1.findall("./address/entry"):
        name = entry.attrib.get("name")
        if not name:
            raise FatalModelParseError("Address object entry missing name")
        value_type = "ip-netmask"
        value = normalize_text(entry.findtext("ip-netmask"))
        if not value:
            value_type = "fqdn"
            value = normalize_text(entry.findtext("fqdn"))
        address_objects.append(
            AddressObject(
                name=name,
                value_type=value_type,
                value=value,
                description=_desc(entry),
                tags=_tags(entry),
                xpath=f"{addr_col}/entry[@name='{name}']",
                collection_xpath=addr_col,
            )
        )

    address_groups: list[AddressGroup] = []
    for entry in vsys1.findall("./address-group/entry"):
        name = entry.attrib.get("name")
        if not name:
            raise FatalModelParseError("Address group entry missing name")
        static_members = normalize_member_list([normalize_text(m.text) for m in entry.findall("./static/member")])
        dynamic_filter = normalize_text(entry.findtext("./dynamic/filter")) or None
        group_type = "dynamic" if dynamic_filter else "static"
        address_groups.append(
            AddressGroup(
                name=name,
                group_type=group_type,
                static_members=static_members,
                dynamic_filter=dynamic_filter,
                description=_desc(entry),
                tags=_tags(entry),
                xpath=f"{agrp_col}/entry[@name='{name}']",
                collection_xpath=agrp_col,
            )
        )

    service_objects: list[ServiceObject] = []
    for entry in vsys1.findall("./service/entry"):
        name = entry.attrib.get("name")
        if not name:
            raise FatalModelParseError("Service object entry missing name")
        protocol = "tcp"
        dport = normalize_text(entry.findtext("./protocol/tcp/port"))
        sport = normalize_text(entry.findtext("./protocol/tcp/source-port")) or None
        if not dport:
            protocol = "udp"
            dport = normalize_text(entry.findtext("./protocol/udp/port"))
            sport = normalize_text(entry.findtext("./protocol/udp/source-port")) or None
        service_objects.append(
            ServiceObject(
                name=name,
                protocol=protocol,
                destination_port=dport,
                source_port=sport,
                description=_desc(entry),
                tags=_tags(entry),
                xpath=f"{svc_col}/entry[@name='{name}']",
                collection_xpath=svc_col,
            )
        )

    zones: list[Zone] = []
    for entry in device.findall("./network/zone/entry"):
        name = entry.attrib.get("name")
        if not name:
            raise FatalModelParseError("Zone entry missing name")
        interfaces = normalize_member_list([normalize_text(m.text) for m in entry.findall("./network/layer3/member")])
        zones.append(Zone(name=name, interfaces=interfaces, xpath=f"{zone_col}/entry[@name='{name}']", collection_xpath=zone_col))

    hostname = normalize_text(device.findtext("./deviceconfig/system/hostname")) or None
    config_version = normalize_text(root.attrib.get("version")) or None
    panos_version = normalize_text(root.attrib.get("platform-version")) or None

    return ParsedConfig(
        device_entry_name=device_entry_name,
        hostname=hostname,
        config_version=config_version,
        panos_version=panos_version,
        vsys="vsys1",
        base_xpath=base_xpath,
        security_rules=tuple(security_rules),
        nat_rules=tuple(nat_rules),
        address_objects=tuple(address_objects),
        address_groups=tuple(address_groups),
        service_objects=tuple(service_objects),
        zones=tuple(zones),
        unsupported=tuple(_detect_unsupported(vsys1, base_xpath)),
        warnings=tuple(),
    )
