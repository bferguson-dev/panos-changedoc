from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from panos_changedoc.diff.engine import diff_configs
from panos_changedoc.parsers.panos_xml import parse_standalone_vsys1
import yaml


@dataclass(frozen=True)
class ValidationIssue:
    message: str
    solution: str


class GenerateValidationError(Exception):
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        details = "\n".join(
            f"- {issue.message} | Fix: {issue.solution}" for issue in issues
        )
        super().__init__(f"Generation validation failed:\n{details}")


@dataclass(frozen=True)
class ChangeTemplate:
    key: str
    category: str
    description: str
    before_payload: dict[str, Any] | None
    after_payload: dict[str, Any] | None


ALLOWED_ROOT_KEYS = {"version", "panos_version", "profile", "settings"}
ALLOWED_SETTING_KEYS = {"key", "before", "after"}


def _security_rule(
    *,
    name: str,
    from_zones: list[str],
    to_zones: list[str],
    source: list[str],
    destination: list[str],
    application: list[str],
    service: list[str],
    action: str,
    disabled: bool,
    log_end: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "from": from_zones,
        "to": to_zones,
        "source": source,
        "destination": destination,
        "application": application,
        "service": service,
        "action": action,
        "disabled": disabled,
        "log_end": log_end,
    }


def _nat_rule(
    *,
    name: str,
    from_zones: list[str],
    to_zones: list[str],
    source: list[str],
    destination: list[str],
    service: list[str],
    disabled: bool,
    destination_translation: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "from": from_zones,
        "to": to_zones,
        "source": source,
        "destination": destination,
        "service": service,
        "disabled": disabled,
        "destination_translation": destination_translation,
    }


CHANGE_TEMPLATES: dict[str, ChangeTemplate] = {
    "security_dest_app01": ChangeTemplate(
        key="security_dest_app01",
        category="security_rules",
        description="Security rule destination changes APP01-OLD -> APP01.",
        before_payload=_security_rule(
            name="Allow-App01-HTTPS",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP01-OLD"],
            application=["ssl", "web-browsing"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=True,
        ),
        after_payload=_security_rule(
            name="Allow-App01-HTTPS",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP01"],
            application=["ssl", "web-browsing"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=True,
        ),
    ),
    "security_disable_app02": ChangeTemplate(
        key="security_disable_app02",
        category="security_rules",
        description="Security rule disable toggle for Allow-App02-HTTPS.",
        before_payload=_security_rule(
            name="Allow-App02-HTTPS",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP02"],
            application=["ssl"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=True,
        ),
        after_payload=_security_rule(
            name="Allow-App02-HTTPS",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP02"],
            application=["ssl"],
            service=["application-default"],
            action="allow",
            disabled=True,
            log_end=True,
        ),
    ),
    "security_reorder_pair": ChangeTemplate(
        key="security_reorder_pair",
        category="security_reorder",
        description="Security rule order changes between App01 and App02.",
        before_payload={"order": ["Allow-App01-HTTPS", "Allow-App02-HTTPS"]},
        after_payload={"order": ["Allow-App02-HTTPS", "Allow-App01-HTTPS"]},
    ),
    "nat_translation_app01": ChangeTemplate(
        key="nat_translation_app01",
        category="nat_rules",
        description="NAT destination translation changes APP01 -> APP01-NEW.",
        before_payload=_nat_rule(
            name="DNAT-App01",
            from_zones=["untrust"],
            to_zones=["untrust"],
            source=["any"],
            destination=["APP01"],
            service=["any"],
            disabled=False,
            destination_translation="APP01",
        ),
        after_payload=_nat_rule(
            name="DNAT-App01",
            from_zones=["untrust"],
            to_zones=["untrust"],
            source=["any"],
            destination=["APP01"],
            service=["any"],
            disabled=False,
            destination_translation="APP01-NEW",
        ),
    ),
    "nat_snat_app02": ChangeTemplate(
        key="nat_snat_app02",
        category="nat_rules",
        description="SNAT-App02 baseline NAT rule used for reorder scenarios.",
        before_payload=_nat_rule(
            name="SNAT-App02",
            from_zones=["trust"],
            to_zones=["untrust"],
            source=["APP02"],
            destination=["any"],
            service=["any"],
            disabled=False,
            destination_translation="APP02",
        ),
        after_payload=_nat_rule(
            name="SNAT-App02",
            from_zones=["trust"],
            to_zones=["untrust"],
            source=["APP02"],
            destination=["any"],
            service=["any"],
            disabled=False,
            destination_translation="APP02",
        ),
    ),
    "nat_reorder_pair": ChangeTemplate(
        key="nat_reorder_pair",
        category="nat_reorder",
        description="NAT rule order swaps DNAT-App01 and SNAT-App02.",
        before_payload={"order": ["DNAT-App01", "SNAT-App02"]},
        after_payload={"order": ["SNAT-App02", "DNAT-App01"]},
    ),
    "addr_app01_value": ChangeTemplate(
        key="addr_app01_value",
        category="address_objects",
        description="Address APP01 value changes 10.10.10.20/32 -> 10.10.10.25/32.",
        before_payload={"name": "APP01", "type": "ip-netmask", "value": "10.10.10.20/32"},
        after_payload={"name": "APP01", "type": "ip-netmask", "value": "10.10.10.25/32"},
    ),
    "addr_app01_old": ChangeTemplate(
        key="addr_app01_old",
        category="address_objects",
        description="Address APP01-OLD used for remove tests.",
        before_payload={"name": "APP01-OLD", "type": "ip-netmask", "value": "10.10.10.20/32"},
        after_payload={"name": "APP01-OLD", "type": "ip-netmask", "value": "10.10.10.20/32"},
    ),
    "addr_app02": ChangeTemplate(
        key="addr_app02",
        category="address_objects",
        description="Address APP02 baseline object.",
        before_payload={"name": "APP02", "type": "ip-netmask", "value": "10.10.10.30/32"},
        after_payload={"name": "APP02", "type": "ip-netmask", "value": "10.10.10.30/32"},
    ),
    "addr_app03": ChangeTemplate(
        key="addr_app03",
        category="address_objects",
        description="Address APP03 used for add tests.",
        before_payload={"name": "APP03", "type": "ip-netmask", "value": "10.10.10.40/32"},
        after_payload={"name": "APP03", "type": "ip-netmask", "value": "10.10.10.40/32"},
    ),
    "addr_app01_new": ChangeTemplate(
        key="addr_app01_new",
        category="address_objects",
        description="Address APP01-NEW used as NAT translation target.",
        before_payload={
            "name": "APP01-NEW",
            "type": "ip-netmask",
            "value": "10.10.10.26/32",
        },
        after_payload={
            "name": "APP01-NEW",
            "type": "ip-netmask",
            "value": "10.10.10.26/32",
        },
    ),
    "agrp_app_servers": ChangeTemplate(
        key="agrp_app_servers",
        category="address_groups",
        description="Address-group APP-SERVERS member set changes.",
        before_payload={"name": "APP-SERVERS", "static": ["APP01", "APP02"]},
        after_payload={"name": "APP-SERVERS", "static": ["APP01", "APP03"]},
    ),
    "svc_https": ChangeTemplate(
        key="svc_https",
        category="service_objects",
        description="Service SVC-HTTPS port changes 443 -> 8443.",
        before_payload={"name": "SVC-HTTPS", "protocol": "tcp", "port": "443"},
        after_payload={"name": "SVC-HTTPS", "protocol": "tcp", "port": "8443"},
    ),
    "zone_dmz": ChangeTemplate(
        key="zone_dmz",
        category="zones",
        description="Zone dmz layer3 interfaces add ethernet1/4.",
        before_payload={"name": "dmz", "interfaces": ["ethernet1/3"]},
        after_payload={"name": "dmz", "interfaces": ["ethernet1/3", "ethernet1/4"]},
    ),
    "zone_trust": ChangeTemplate(
        key="zone_trust",
        category="zones",
        description="Zone trust baseline.",
        before_payload={"name": "trust", "interfaces": ["ethernet1/2"]},
        after_payload={"name": "trust", "interfaces": ["ethernet1/2"]},
    ),
    "zone_untrust": ChangeTemplate(
        key="zone_untrust",
        category="zones",
        description="Zone untrust baseline.",
        before_payload={"name": "untrust", "interfaces": ["ethernet1/1"]},
        after_payload={"name": "untrust", "interfaces": ["ethernet1/1"]},
    ),
    "security_add_admin_portal": ChangeTemplate(
        key="security_add_admin_portal",
        category="security_rules",
        description="Add security rule for Admin-Portal traffic in after.",
        before_payload=_security_rule(
            name="Allow-Admin-Portal",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP02"],
            application=["ssl"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=True,
        ),
        after_payload=_security_rule(
            name="Allow-Admin-Portal",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP02"],
            application=["ssl"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=True,
        ),
    ),
    "security_remove_legacy_temp": ChangeTemplate(
        key="security_remove_legacy_temp",
        category="security_rules",
        description="Remove legacy temporary rule in after.",
        before_payload=_security_rule(
            name="Allow-Legacy-Temp",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP02"],
            application=["web-browsing"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=False,
        ),
        after_payload=_security_rule(
            name="Allow-Legacy-Temp",
            from_zones=["trust"],
            to_zones=["dmz"],
            source=["Corp-Users"],
            destination=["APP02"],
            application=["web-browsing"],
            service=["application-default"],
            action="allow",
            disabled=False,
            log_end=False,
        ),
    ),
    "nat_disable_temp": ChangeTemplate(
        key="nat_disable_temp",
        category="nat_rules",
        description="Disable NAT temp rule in after.",
        before_payload=_nat_rule(
            name="SNAT-Temp",
            from_zones=["trust"],
            to_zones=["untrust"],
            source=["APP02"],
            destination=["any"],
            service=["any"],
            disabled=False,
            destination_translation="APP02",
        ),
        after_payload=_nat_rule(
            name="SNAT-Temp",
            from_zones=["trust"],
            to_zones=["untrust"],
            source=["APP02"],
            destination=["any"],
            service=["any"],
            disabled=True,
            destination_translation="APP02",
        ),
    ),
    "service_add_dns": ChangeTemplate(
        key="service_add_dns",
        category="service_objects",
        description="Add UDP DNS service object in after.",
        before_payload={"name": "SVC-DNS", "protocol": "udp", "port": "53"},
        after_payload={"name": "SVC-DNS", "protocol": "udp", "port": "53"},
    ),
    "zone_add_guest": ChangeTemplate(
        key="zone_add_guest",
        category="zones",
        description="Add guest zone in after.",
        before_payload={"name": "guest", "interfaces": ["ethernet1/5"]},
        after_payload={"name": "guest", "interfaces": ["ethernet1/5"]},
    ),
}


def default_spec() -> dict[str, Any]:
    return {
        "version": 1,
        "panos_version": "12.1",
        "profile": "standalone_vsys1",
        "settings": [
            {"key": "security_dest_app01", "before": True, "after": True},
            {"key": "security_disable_app02", "before": True, "after": True},
            {"key": "security_reorder_pair", "before": True, "after": True},
            {"key": "nat_translation_app01", "before": True, "after": True},
            {"key": "nat_snat_app02", "before": True, "after": True},
            {"key": "nat_reorder_pair", "before": True, "after": True},
            {"key": "addr_app01_value", "before": True, "after": True},
            {"key": "addr_app01_old", "before": True, "after": False},
            {"key": "addr_app02", "before": True, "after": True},
            {"key": "addr_app03", "before": False, "after": True},
            {"key": "addr_app01_new", "before": False, "after": True},
            {"key": "agrp_app_servers", "before": True, "after": True},
            {"key": "svc_https", "before": True, "after": True},
            {"key": "zone_dmz", "before": True, "after": True},
            {"key": "zone_trust", "before": True, "after": True},
            {"key": "zone_untrust", "before": True, "after": True},
        ],
    }


def load_spec(path: str) -> dict[str, Any]:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise GenerateValidationError(
            [
                ValidationIssue(
                    message="YAML root must be a mapping/object.",
                    solution="Set top-level keys: version, panos_version, "
                    "profile, settings.",
                )
            ]
        )
    _validate_unknown_keys(data)
    _validate_spec_shape(data)
    return data


def _validate_unknown_keys(spec: dict[str, Any]) -> None:
    issues: list[ValidationIssue] = []
    unknown_root = sorted(set(spec.keys()) - ALLOWED_ROOT_KEYS)
    if unknown_root:
        issues.append(
            ValidationIssue(
                message=f"Unknown top-level YAML keys: {', '.join(unknown_root)}.",
                solution="Remove unknown keys or rename them to valid keys.",
            )
        )

    settings = spec.get("settings")
    if isinstance(settings, list):
        for idx, setting in enumerate(settings):
            if not isinstance(setting, dict):
                continue
            unknown = sorted(set(setting.keys()) - ALLOWED_SETTING_KEYS)
            if unknown:
                issues.append(
                    ValidationIssue(
                        message=(
                            f"Unknown setting keys at settings[{idx}]: "
                            f"{', '.join(unknown)}."
                        ),
                        solution=(
                            "Allowed keys are: key, before, after. "
                            "Remove unknown keys."
                        ),
                    )
                )
    if issues:
        raise GenerateValidationError(issues)


def _validate_spec_shape(spec: dict[str, Any]) -> None:
    issues: list[ValidationIssue] = []
    if spec.get("version") != 1:
        issues.append(
            ValidationIssue(
                message="version must be 1.",
                solution="Set version: 1 in the YAML.",
            )
        )
    if spec.get("panos_version") != "12.1":
        issues.append(
            ValidationIssue(
                message="panos_version must be 12.1 for this generator.",
                solution="Set panos_version: '12.1'.",
            )
        )
    if spec.get("profile") != "standalone_vsys1":
        issues.append(
            ValidationIssue(
                message="profile must be standalone_vsys1.",
                solution="Set profile: standalone_vsys1.",
            )
        )

    settings = spec.get("settings")
    if not isinstance(settings, list) or not settings:
        issues.append(
            ValidationIssue(
                message="settings must be a non-empty list.",
                solution="Add at least one settings item with key/before/after.",
            )
        )
    else:
        for idx, setting in enumerate(settings):
            if not isinstance(setting, dict):
                issues.append(
                    ValidationIssue(
                        message=f"settings[{idx}] must be an object.",
                        solution="Use mapping keys: key, before, after.",
                    )
                )
                continue
            key = setting.get("key")
            if key not in CHANGE_TEMPLATES:
                issues.append(
                    ValidationIssue(
                        message=f"settings[{idx}].key '{key}' is not supported.",
                        solution=(
                            "Use a key from the generator catalog returned by "
                            "list_change_templates()."
                        ),
                    )
                )
            for side in ("before", "after"):
                if not isinstance(setting.get(side), bool):
                    issues.append(
                        ValidationIssue(
                            message=(
                                f"settings[{idx}].{side} must be true or false."
                            ),
                            solution=(
                                f"Set settings[{idx}].{side}: true or false."
                            ),
                        )
                    )
    if issues:
        raise GenerateValidationError(issues)


def list_change_templates() -> list[dict[str, str]]:
    return sorted(
        [
            {
                "key": t.key,
                "category": t.category,
                "description": t.description,
            }
            for t in CHANGE_TEMPLATES.values()
        ],
        key=lambda x: (x["category"], x["key"]),
    )


def _base_model() -> dict[str, Any]:
    return {
        "device_entry_name": "localhost.localdomain",
        "hostname": "pa-fw01",
        "security_rules": [],
        "nat_rules": [],
        "address_objects": [],
        "address_groups": [],
        "service_objects": [],
        "zones": [],
    }


def _upsert(items: list[dict[str, Any]], payload: dict[str, Any]) -> None:
    name = payload["name"]
    for idx, item in enumerate(items):
        if item["name"] == name:
            items[idx] = deepcopy(payload)
            return
    items.append(deepcopy(payload))


def _apply_setting(model: dict[str, Any], key: str, payload: dict[str, Any]) -> None:
    category = CHANGE_TEMPLATES[key].category
    if category == "security_rules":
        _upsert(model["security_rules"], payload)
    elif category == "nat_rules":
        _upsert(model["nat_rules"], payload)
    elif category == "address_objects":
        _upsert(model["address_objects"], payload)
    elif category == "address_groups":
        _upsert(model["address_groups"], payload)
    elif category == "service_objects":
        _upsert(model["service_objects"], payload)
    elif category == "zones":
        _upsert(model["zones"], payload)


def _order_rules(
    model: dict[str, Any], category: str, ordering: list[str]
) -> None:
    source = model[category]
    by_name = {item["name"]: item for item in source}
    ordered: list[dict[str, Any]] = []
    for name in ordering:
        item = by_name.get(name)
        if item is not None:
            ordered.append(item)
    for item in source:
        if item["name"] not in ordering:
            ordered.append(item)
    model[category] = ordered


def _build_models_from_spec(
    spec: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    before = _base_model()
    after = _base_model()

    sec_before_order: list[str] | None = None
    sec_after_order: list[str] | None = None
    nat_before_order: list[str] | None = None
    nat_after_order: list[str] | None = None

    for item in spec["settings"]:
        key = item["key"]
        template = CHANGE_TEMPLATES[key]
        if template.category == "security_reorder":
            assert template.before_payload is not None
            assert template.after_payload is not None
            if item["before"]:
                sec_before_order = list(template.before_payload["order"])
            if item["after"]:
                sec_after_order = list(template.after_payload["order"])
            continue
        if template.category == "nat_reorder":
            assert template.before_payload is not None
            assert template.after_payload is not None
            if item["before"]:
                nat_before_order = list(template.before_payload["order"])
            if item["after"]:
                nat_after_order = list(template.after_payload["order"])
            continue

        if item["before"] and template.before_payload is not None:
            _apply_setting(before, key, template.before_payload)
        if item["after"] and template.after_payload is not None:
            _apply_setting(after, key, template.after_payload)

    if sec_before_order:
        _order_rules(before, "security_rules", sec_before_order)
    if sec_after_order:
        _order_rules(after, "security_rules", sec_after_order)
    if nat_before_order:
        _order_rules(before, "nat_rules", nat_before_order)
    if nat_after_order:
        _order_rules(after, "nat_rules", nat_after_order)

    return before, after


def _validate_model_logic(
    before: dict[str, Any], after: dict[str, Any]
) -> None:
    issues: list[ValidationIssue] = []

    def check_unique(model: dict[str, Any], collection: str, label: str) -> None:
        names = [item["name"] for item in model[collection]]
        dupes = sorted({name for name in names if names.count(name) > 1})
        if dupes:
            issues.append(
                ValidationIssue(
                    message=f"Duplicate {label} names detected: {', '.join(dupes)}.",
                    solution=(
                        f"Ensure each {label} has a unique name per configuration "
                        "side."
                    ),
                )
            )

    for side, model in (("before", before), ("after", after)):
        check_unique(model, "security_rules", f"security rule ({side})")
        check_unique(model, "nat_rules", f"NAT rule ({side})")
        check_unique(model, "address_objects", f"address object ({side})")
        check_unique(model, "address_groups", f"address group ({side})")
        check_unique(model, "service_objects", f"service object ({side})")
        check_unique(model, "zones", f"zone ({side})")

        obj_names = {x["name"] for x in model["address_objects"]}
        grp_names = {x["name"] for x in model["address_groups"]}
        svc_names = {x["name"] for x in model["service_objects"]}
        zone_names = {x["name"] for x in model["zones"]}

        for rule in model["security_rules"]:
            for zone in rule["from"] + rule["to"]:
                if zone not in zone_names:
                    issues.append(
                        ValidationIssue(
                            message=(
                                f"Security rule '{rule['name']}' in {side} "
                                f"references missing zone '{zone}'."
                            ),
                            solution=(
                                f"Add zone '{zone}' to {side} zones or update the "
                                "rule zone references."
                            ),
                        )
                    )
            for member in rule["destination"]:
                if member != "any" and member not in obj_names and member not in grp_names:
                    issues.append(
                        ValidationIssue(
                            message=(
                                f"Security rule '{rule['name']}' in {side} "
                                f"references missing destination '{member}'."
                            ),
                            solution=(
                                f"Add address/address-group '{member}' to {side} "
                                "or set destination to any."
                            ),
                        )
                    )
            for svc in rule["service"]:
                if svc not in {"any", "application-default"} and svc not in svc_names:
                    issues.append(
                        ValidationIssue(
                            message=(
                                f"Security rule '{rule['name']}' in {side} "
                                f"references missing service '{svc}'."
                            ),
                            solution=(
                                f"Add service object '{svc}' to {side} or use any/"
                                "application-default."
                            ),
                        )
                    )

        for rule in model["nat_rules"]:
            for zone in rule["from"] + rule["to"]:
                if zone not in zone_names:
                    issues.append(
                        ValidationIssue(
                            message=(
                                f"NAT rule '{rule['name']}' in {side} references "
                                f"missing zone '{zone}'."
                            ),
                            solution=(
                                f"Add zone '{zone}' to {side} zones or update the "
                                "NAT rule zones."
                            ),
                        )
                    )
            target = rule.get("destination_translation")
            if target and target not in obj_names:
                issues.append(
                    ValidationIssue(
                        message=(
                            f"NAT rule '{rule['name']}' in {side} translates to "
                            f"missing address '{target}'."
                        ),
                        solution=(
                            f"Add address object '{target}' to {side} or update "
                            "destination_translation."
                        ),
                    )
                )

    if not before["security_rules"] and not after["security_rules"]:
        issues.append(
            ValidationIssue(
                message="No security rules were selected in before or after.",
                solution=(
                    "Select at least one security rule template so generated "
                    "configs are meaningful for diff testing."
                ),
            )
        )

    if issues:
        raise GenerateValidationError(issues)


def _add_members(parent: Element, tag: str, members: list[str]) -> None:
    node = SubElement(parent, tag)
    for member in members:
        SubElement(node, "member").text = member


def _build_security_rule(parent: Element, rule: dict[str, Any]) -> None:
    entry = SubElement(parent, "entry", {"name": rule["name"]})
    _add_members(entry, "from", rule["from"])
    _add_members(entry, "to", rule["to"])
    _add_members(entry, "source", rule["source"])
    _add_members(entry, "destination", rule["destination"])
    _add_members(entry, "application", rule["application"])
    _add_members(entry, "service", rule["service"])
    SubElement(entry, "action").text = rule["action"]
    SubElement(entry, "disabled").text = "yes" if rule["disabled"] else "no"
    SubElement(entry, "log-end").text = "yes" if rule["log_end"] else "no"


def _build_nat_rule(parent: Element, rule: dict[str, Any]) -> None:
    entry = SubElement(parent, "entry", {"name": rule["name"]})
    _add_members(entry, "from", rule["from"])
    _add_members(entry, "to", rule["to"])
    _add_members(entry, "source", rule["source"])
    _add_members(entry, "destination", rule["destination"])
    _add_members(entry, "service", rule["service"])
    SubElement(entry, "disabled").text = "yes" if rule["disabled"] else "no"
    dt = SubElement(entry, "destination-translation")
    SubElement(dt, "translated-address").text = rule["destination_translation"]


def _build_config(model: dict[str, Any]) -> str:
    config = Element("config")
    devices = SubElement(config, "devices")
    dev = SubElement(devices, "entry", {"name": model["device_entry_name"]})

    dc = SubElement(dev, "deviceconfig")
    system = SubElement(dc, "system")
    SubElement(system, "hostname").text = model["hostname"]

    vsys = SubElement(dev, "vsys")
    vsys1 = SubElement(vsys, "entry", {"name": "vsys1"})

    rulebase = SubElement(vsys1, "rulebase")
    sec = SubElement(rulebase, "security")
    sec_rules = SubElement(sec, "rules")
    for rule in model["security_rules"]:
        _build_security_rule(sec_rules, rule)

    nat = SubElement(rulebase, "nat")
    nat_rules = SubElement(nat, "rules")
    for rule in model["nat_rules"]:
        _build_nat_rule(nat_rules, rule)

    address = SubElement(vsys1, "address")
    for obj in model["address_objects"]:
        entry = SubElement(address, "entry", {"name": obj["name"]})
        SubElement(entry, obj["type"]).text = obj["value"]

    address_group = SubElement(vsys1, "address-group")
    for group in model["address_groups"]:
        entry = SubElement(address_group, "entry", {"name": group["name"]})
        _add_members(entry, "static", group.get("static", []))

    service = SubElement(vsys1, "service")
    for svc in model["service_objects"]:
        entry = SubElement(service, "entry", {"name": svc["name"]})
        proto = SubElement(entry, "protocol")
        pnode = SubElement(proto, svc["protocol"])
        SubElement(pnode, "port").text = svc["port"]

    network = SubElement(dev, "network")
    zone = SubElement(network, "zone")
    for z in model["zones"]:
        entry = SubElement(zone, "entry", {"name": z["name"]})
        nnode = SubElement(entry, "network")
        layer3 = SubElement(nnode, "layer3")
        for iface in z["interfaces"]:
            SubElement(layer3, "member").text = iface

    return tostring(config, encoding="unicode") + "\n"


def build_from_spec(spec: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    before_model, after_model = _build_models_from_spec(spec)
    _validate_model_logic(before_model, after_model)

    before_xml = _build_config(before_model)
    after_xml = _build_config(after_model)
    before_parsed = parse_standalone_vsys1(fromstring(before_xml))
    after_parsed = parse_standalone_vsys1(fromstring(after_xml))
    expected_total = len(diff_configs(before_parsed, after_parsed))

    manifest = {
        "scenario": "yaml_driven_generation",
        "expected": {
            "total_changes": expected_total,
            "notes": "Deterministic expected change count from selected toggles.",
        },
    }
    return before_xml, after_xml, manifest


def write_outputs(
    before_xml: str,
    after_xml: str,
    manifest: dict[str, Any],
    before_out: str,
    after_out: str,
    manifest_out: str | None,
) -> None:
    before_path = Path(before_out)
    after_path = Path(after_out)
    before_path.parent.mkdir(parents=True, exist_ok=True)
    after_path.parent.mkdir(parents=True, exist_ok=True)
    before_path.write_text(before_xml, encoding="utf-8")
    after_path.write_text(after_xml, encoding="utf-8")

    if manifest_out:
        mp = Path(manifest_out)
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_default_spec(path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(default_spec(), sort_keys=False), encoding="utf-8")
