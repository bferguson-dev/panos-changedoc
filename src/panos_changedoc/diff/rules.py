from dataclasses import asdict

from panos_changedoc.models.changes import Change, FieldChange
from panos_changedoc.models.nat import NatRule
from panos_changedoc.models.security import SecurityRule
from panos_changedoc.normalizer import as_memberset


def _lcs(a: list[str], b: list[str]) -> list[str]:
    """Return rule names that kept their relative order across both configs."""
    m = len(a)
    n = len(b)
    lengths: list[list[int]] = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                lengths[i][j] = lengths[i - 1][j - 1] + 1
            else:
                lengths[i][j] = (
                    lengths[i - 1][j]
                    if lengths[i - 1][j] >= lengths[i][j - 1]
                    else lengths[i][j - 1]
                )

    out: list[str] = []
    i = m
    j = n
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif lengths[i - 1][j] >= lengths[i][j - 1]:
            i -= 1
        else:
            j -= 1
    out.reverse()
    return out


def _rule_field_changes(before: SecurityRule, after: SecurityRule) -> list[FieldChange]:
    fields = []
    mapping = {
        "from": (
            as_memberset(before.from_zone.members),
            as_memberset(after.from_zone.members),
        ),
        "to": (
            as_memberset(before.to_zone.members),
            as_memberset(after.to_zone.members),
        ),
        "source": (
            as_memberset(before.source.members),
            as_memberset(after.source.members),
        ),
        "destination": (
            as_memberset(before.destination.members),
            as_memberset(after.destination.members),
        ),
        "application": (
            as_memberset(before.application.members),
            as_memberset(after.application.members),
        ),
        "service": (
            as_memberset(before.service.members),
            as_memberset(after.service.members),
        ),
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


def diff_security_rules(
    before: tuple[SecurityRule, ...], after: tuple[SecurityRule, ...]
) -> list[Change]:
    """Compare security policy rules by name, fields, and rulebase position."""
    changes: list[Change] = []
    before_by_name = {r.name: r for r in before}
    after_by_name = {r.name: r for r in after}

    for name in sorted(set(before_by_name) - set(after_by_name)):
        old = before_by_name[name]
        changes.append(
            Change(
                "removed",
                "security_rule",
                name,
                "local",
                "vsys1",
                "security",
                old.xpath,
                old.collection_xpath,
                "CRITICAL",
                f"Security rule `{name}` removed",
                tuple(),
                tuple(),
                snapshot=asdict(old),
            )
        )

    for name in sorted(set(after_by_name) - set(before_by_name)):
        new = after_by_name[name]
        changes.append(
            Change(
                "added",
                "security_rule",
                name,
                "local",
                "vsys1",
                "security",
                new.xpath,
                new.collection_xpath,
                "CRITICAL",
                f"Security rule `{name}` added",
                tuple(),
                tuple(),
                snapshot=asdict(new),
            )
        )

    for name in sorted(set(before_by_name) & set(after_by_name)):
        b = before_by_name[name]
        a = after_by_name[name]
        field_changes = _rule_field_changes(b, a)
        if not field_changes:
            continue
        fields_changed = tuple(fc.path for fc in field_changes)
        # A pure disabled-state toggle gets a readable enabled/disabled change.
        # If any other field changed too, keep one modified record with all
        # changed fields so the report does not double-count the same rule.
        if fields_changed == ("disabled",):
            change_type = "enabled" if b.disabled and not a.disabled else "disabled"
        else:
            change_type = "modified"
        changes.append(
            Change(
                change_type,
                "security_rule",
                name,
                "local",
                "vsys1",
                "security",
                a.xpath,
                a.collection_xpath,
                "CRITICAL",
                f"Security rule `{name}` {change_type}",
                fields_changed,
                tuple(field_changes),
            )
        )

    # PAN-OS policy order matters. LCS prevents insertions/removals from
    # making every shifted rule look reordered.
    common = [n for n in [r.name for r in before] if n in after_by_name]
    after_common = [n for n in [r.name for r in after] if n in before_by_name]
    stable = set(_lcs(common, after_common))
    for name in [n for n in common if n not in stable]:
        r = after_by_name[name]
        changes.append(
            Change(
                "reordered",
                "security_rule",
                name,
                "local",
                "vsys1",
                "security",
                r.xpath,
                r.collection_xpath,
                "HIGH",
                f"Security rule `{name}` reordered",
                ("order",),
                tuple(),
            )
        )

    return changes


def _nat_field_changes(before: NatRule, after: NatRule) -> list[FieldChange]:
    out = []
    mapping = {
        "from": (
            as_memberset(before.from_zone.members),
            as_memberset(after.from_zone.members),
        ),
        "to": (
            as_memberset(before.to_zone.members),
            as_memberset(after.to_zone.members),
        ),
        "source": (
            as_memberset(before.source.members),
            as_memberset(after.source.members),
        ),
        "destination": (
            as_memberset(before.destination.members),
            as_memberset(after.destination.members),
        ),
        "service": (
            as_memberset(before.service.members),
            as_memberset(after.service.members),
        ),
        "disabled": (before.disabled, after.disabled),
        "translation": (before.translation, after.translation),
    }
    for key, pair in mapping.items():
        if pair[0] != pair[1]:
            out.append(FieldChange(path=key, before=pair[0], after=pair[1]))
    return out


def diff_nat_rules(
    before: tuple[NatRule, ...], after: tuple[NatRule, ...]
) -> list[Change]:
    """Compare NAT rules with the same ordering rules used for security."""
    changes: list[Change] = []
    before_by_name = {r.name: r for r in before}
    after_by_name = {r.name: r for r in after}

    for name in sorted(set(before_by_name) - set(after_by_name)):
        old = before_by_name[name]
        changes.append(
            Change(
                "removed",
                "nat_rule",
                name,
                "local",
                "vsys1",
                "nat",
                old.xpath,
                old.collection_xpath,
                "CRITICAL",
                f"NAT rule `{name}` removed",
                tuple(),
                tuple(),
                snapshot=asdict(old),
            )
        )

    for name in sorted(set(after_by_name) - set(before_by_name)):
        new = after_by_name[name]
        changes.append(
            Change(
                "added",
                "nat_rule",
                name,
                "local",
                "vsys1",
                "nat",
                new.xpath,
                new.collection_xpath,
                "CRITICAL",
                f"NAT rule `{name}` added",
                tuple(),
                tuple(),
                snapshot=asdict(new),
            )
        )

    for name in sorted(set(before_by_name) & set(after_by_name)):
        b = before_by_name[name]
        a = after_by_name[name]
        fcs = _nat_field_changes(b, a)
        if not fcs:
            continue
        fields = tuple(fc.path for fc in fcs)
        # Keep enabled/disabled as its own change type only for pure toggles.
        if fields == ("disabled",):
            change_type = "enabled" if b.disabled and not a.disabled else "disabled"
        else:
            change_type = "modified"
        changes.append(
            Change(
                change_type,
                "nat_rule",
                name,
                "local",
                "vsys1",
                "nat",
                a.xpath,
                a.collection_xpath,
                "CRITICAL",
                f"NAT rule `{name}` {change_type}",
                fields,
                tuple(fcs),
            )
        )

    # NAT rule order is evaluated with LCS for the same reason as security
    # policy: added or removed rules should not create a reorder cascade.
    common = [n for n in [r.name for r in before] if n in after_by_name]
    after_common = [n for n in [r.name for r in after] if n in before_by_name]
    stable = set(_lcs(common, after_common))
    for name in [n for n in common if n not in stable]:
        r = after_by_name[name]
        changes.append(
            Change(
                "reordered",
                "nat_rule",
                name,
                "local",
                "vsys1",
                "nat",
                r.xpath,
                r.collection_xpath,
                "HIGH",
                f"NAT rule `{name}` reordered",
                ("order",),
                tuple(),
            )
        )

    return changes
