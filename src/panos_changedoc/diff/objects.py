from dataclasses import asdict
from typing import Any, Callable

from panos_changedoc.models.changes import Change, FieldChange


def _generic_diff(
    *,
    entity_type: str,
    title_prefix: str,
    before: tuple[Any, ...],
    after: tuple[Any, ...],
    rulebase: str | None,
    significance: str,
    fields_fn: Callable[[Any, Any], list[FieldChange]],
) -> list[Change]:
    changes: list[Change] = []
    before_by_name = {getattr(x, "name"): x for x in before}
    after_by_name = {getattr(x, "name"): x for x in after}

    for name in sorted(set(before_by_name) - set(after_by_name)):
        old = before_by_name[name]
        changes.append(
            Change(
                "removed",
                entity_type,
                name,
                "local",
                "vsys1",
                rulebase,
                getattr(old, "xpath"),
                getattr(old, "collection_xpath"),
                significance,
                f"{title_prefix} `{name}` removed",
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
                entity_type,
                name,
                "local",
                "vsys1",
                rulebase,
                getattr(new, "xpath"),
                getattr(new, "collection_xpath"),
                significance,
                f"{title_prefix} `{name}` added",
                tuple(),
                tuple(),
                snapshot=asdict(new),
            )
        )

    for name in sorted(set(before_by_name) & set(after_by_name)):
        b = before_by_name[name]
        a = after_by_name[name]
        fcs = fields_fn(b, a)
        if not fcs:
            continue
        changes.append(
            Change(
                "modified",
                entity_type,
                name,
                "local",
                "vsys1",
                rulebase,
                getattr(a, "xpath"),
                getattr(a, "collection_xpath"),
                significance,
                f"{title_prefix} `{name}` modified",
                tuple(fc.path for fc in fcs),
                tuple(fcs),
            )
        )

    return changes


def diff_address_objects(before, after) -> list[Change]:
    def fields(b, a):
        out = []
        for key in ("value_type", "value", "description", "tags"):
            bv, av = getattr(b, key), getattr(a, key)
            if bv != av:
                out.append(FieldChange(path=key, before=bv, after=av))
        return out

    return _generic_diff(
        entity_type="address_object",
        title_prefix="Address object",
        before=before,
        after=after,
        rulebase=None,
        significance="CRITICAL",
        fields_fn=fields,
    )


def diff_address_groups(before, after) -> list[Change]:
    def fields(b, a):
        out = []
        for key in (
            "group_type",
            "static_members",
            "dynamic_filter",
            "description",
            "tags",
        ):
            bv, av = getattr(b, key), getattr(a, key)
            if bv != av:
                out.append(FieldChange(path=key, before=bv, after=av))
        return out

    return _generic_diff(
        entity_type="address_group",
        title_prefix="Address group",
        before=before,
        after=after,
        rulebase=None,
        significance="HIGH",
        fields_fn=fields,
    )


def diff_service_objects(before, after) -> list[Change]:
    def fields(b, a):
        out = []
        for key in (
            "protocol",
            "destination_port",
            "source_port",
            "description",
            "tags",
        ):
            bv, av = getattr(b, key), getattr(a, key)
            if bv != av:
                out.append(FieldChange(path=key, before=bv, after=av))
        return out

    return _generic_diff(
        entity_type="service_object",
        title_prefix="Service object",
        before=before,
        after=after,
        rulebase=None,
        significance="HIGH",
        fields_fn=fields,
    )


def diff_zones(before, after) -> list[Change]:
    def fields(b, a):
        if b.interfaces != a.interfaces:
            return [
                FieldChange(
                    path="interfaces",
                    before=list(b.interfaces),
                    after=list(a.interfaces),
                )
            ]
        return []

    return _generic_diff(
        entity_type="zone",
        title_prefix="Zone",
        before=before,
        after=after,
        rulebase=None,
        significance="LOW",
        fields_fn=fields,
    )
