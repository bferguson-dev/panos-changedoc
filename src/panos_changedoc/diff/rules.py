from dataclasses import asdict

from panos_changedoc.models.changes import Change, FieldChange
from panos_changedoc.models.nat import NatRule
from panos_changedoc.models.security import SecurityRule
from panos_changedoc.normalizer import as_memberset


def _lcs(a: list[str], b: list[str]) -> list[str]:
    dp: list[list[list[str]]] = [
        [[] for _ in range(len(b) + 1)] for _ in range(len(a) + 1)
    ]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + [a[i - 1]]
            else:
                dp[i][j] = dp[i - 1][j] if len(dp[i - 1][j]) >= len(dp[i][j - 1]) else dp[i][j - 1]
    return dp[-1][-1]


def _rule_field_changes(before: SecurityRule, after: SecurityRule) -> list[FieldChange]:
    fields = []
    mapping = {
        "from": (as_memberset(before.from_zone.members), as_memberset(after.from_zone.members)),
        "to": (as_memberset(before.to_zone.members), as_memberset(after.to_zone.members)),
        "source": (as_memberset(before.source.members), as_memberset(after.source.members)),
        "destination": (as_memberset(before.destination.members), as_memberset(after.destination.members)),
        "application": (as_memberset(before.application.members), as_memberset(after.application.members)),
        "service": (as_memberset(before.service.members), as_memberset(after.service.members)),
        "action": (before.action, after.action),
        "disabled": (before.disabled, after.disabled),
        "log_end": (before.log_end, after.log_end),
        "description": (before.description, after.description),
        "tags": (list(before.tags), list(after.tags)),
    }
    for key, pair in mapping.items():
        if pair[0] != pair[1]:
            fields.append(FieldChange(path=key, before=pair[0], after=pair[1]))
    return fields


def diff_security_rules(before: tuple[SecurityRule, ...], after: tuple[SecurityRule, ...]) -> list[Change]:
    changes: list[Change] = []
    before_by_name = {r.name: r for r in before}
    after_by_name = {r.name: r for r in after}

    for name in sorted(set(before_by_name) - set(after_by_name)):
        old = before_by_name[name]
        changes.append(Change("removed", "security_rule", name, "local", "vsys1", "security", old.xpath, old.collection_xpath, "CRITICAL", f"Security rule `{name}` removed", tuple(), tuple(), snapshot=asdict(old)))

    for name in sorted(set(after_by_name) - set(before_by_name)):
        new = after_by_name[name]
        changes.append(Change("added", "security_rule", name, "local", "vsys1", "security", new.xpath, new.collection_xpath, "CRITICAL", f"Security rule `{name}` added", tuple(), tuple(), snapshot=asdict(new)))

    for name in sorted(set(before_by_name) & set(after_by_name)):
        b = before_by_name[name]
        a = after_by_name[name]
        field_changes = _rule_field_changes(b, a)
        if not field_changes:
            continue
        fields_changed = tuple(fc.path for fc in field_changes)
        if fields_changed == ("disabled",):
            change_type = "enabled" if b.disabled and not a.disabled else "disabled"
        else:
            change_type = "modified"
        changes.append(Change(change_type, "security_rule", name, "local", "vsys1", "security", a.xpath, a.collection_xpath, "CRITICAL", f"Security rule `{name}` {change_type}", fields_changed, tuple(field_changes)))

    common = [n for n in [r.name for r in before] if n in after_by_name]
    after_common = [n for n in [r.name for r in after] if n in before_by_name]
    stable = set(_lcs(common, after_common))
    for name in [n for n in common if n not in stable]:
        r = after_by_name[name]
        changes.append(Change("reordered", "security_rule", name, "local", "vsys1", "security", r.xpath, r.collection_xpath, "HIGH", f"Security rule `{name}` reordered", ("order",), tuple()))

    return changes


def _nat_field_changes(before: NatRule, after: NatRule) -> list[FieldChange]:
    out = []
    mapping = {
        "from": (as_memberset(before.from_zone.members), as_memberset(after.from_zone.members)),
        "to": (as_memberset(before.to_zone.members), as_memberset(after.to_zone.members)),
        "source": (as_memberset(before.source.members), as_memberset(after.source.members)),
        "destination": (as_memberset(before.destination.members), as_memberset(after.destination.members)),
        "service": (as_memberset(before.service.members), as_memberset(after.service.members)),
        "disabled": (before.disabled, after.disabled),
        "translation": (before.translation, after.translation),
    }
    for key, pair in mapping.items():
        if pair[0] != pair[1]:
            out.append(FieldChange(path=key, before=pair[0], after=pair[1]))
    return out


def diff_nat_rules(before: tuple[NatRule, ...], after: tuple[NatRule, ...]) -> list[Change]:
    changes: list[Change] = []
    before_by_name = {r.name: r for r in before}
    after_by_name = {r.name: r for r in after}

    for name in sorted(set(before_by_name) - set(after_by_name)):
        old = before_by_name[name]
        changes.append(Change("removed", "nat_rule", name, "local", "vsys1", "nat", old.xpath, old.collection_xpath, "CRITICAL", f"NAT rule `{name}` removed", tuple(), tuple(), snapshot=asdict(old)))

    for name in sorted(set(after_by_name) - set(before_by_name)):
        new = after_by_name[name]
        changes.append(Change("added", "nat_rule", name, "local", "vsys1", "nat", new.xpath, new.collection_xpath, "CRITICAL", f"NAT rule `{name}` added", tuple(), tuple(), snapshot=asdict(new)))

    for name in sorted(set(before_by_name) & set(after_by_name)):
        b = before_by_name[name]
        a = after_by_name[name]
        fcs = _nat_field_changes(b, a)
        if not fcs:
            continue
        fields = tuple(fc.path for fc in fcs)
        if fields == ("disabled",):
            change_type = "enabled" if b.disabled and not a.disabled else "disabled"
        else:
            change_type = "modified"
        changes.append(Change(change_type, "nat_rule", name, "local", "vsys1", "nat", a.xpath, a.collection_xpath, "CRITICAL", f"NAT rule `{name}` {change_type}", fields, tuple(fcs)))

    common = [n for n in [r.name for r in before] if n in after_by_name]
    after_common = [n for n in [r.name for r in after] if n in before_by_name]
    stable = set(_lcs(common, after_common))
    for name in [n for n in common if n not in stable]:
        r = after_by_name[name]
        changes.append(Change("reordered", "nat_rule", name, "local", "vsys1", "nat", r.xpath, r.collection_xpath, "HIGH", f"NAT rule `{name}` reordered", ("order",), tuple()))

    return changes
