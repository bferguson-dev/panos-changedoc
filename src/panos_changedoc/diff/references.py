def _walk_group_refs(groups: dict[str, object], group_name: str, visited: set[str], depth: int, max_depth: int, warnings: list[dict]) -> set[str]:
    if depth > max_depth:
        return set()
    if group_name in visited:
        warnings.append({"code": "REF_CYCLE", "message": f"Address group cycle detected at {group_name}"})
        return set()
    visited = set(visited)
    visited.add(group_name)
    group = groups.get(group_name)
    if group is None:
        return set()
    refs = set(getattr(group, "static_members"))
    out = set(refs)
    for item in refs:
        if item in groups:
            out |= _walk_group_refs(groups, item, visited, depth + 1, max_depth, warnings)
    return out


def attach_references(changes: list[dict], before_parsed, after_parsed) -> tuple[list[dict], list[dict]]:
    warnings: list[dict] = []
    groups = {g.name: g for g in after_parsed.address_groups}

    sec_refs = []
    for r in after_parsed.security_rules:
        for field, members in {
            "source": r.source.members,
            "destination": r.destination.members,
            "service": r.service.members,
            "from": r.from_zone.members,
            "to": r.to_zone.members,
        }.items():
            for m in members:
                sec_refs.append((m, "security_rule", r.name, field))

    nat_refs = []
    for r in after_parsed.nat_rules:
        for field, members in {
            "source": r.source.members,
            "destination": r.destination.members,
            "from": r.from_zone.members,
            "to": r.to_zone.members,
            "service": r.service.members,
        }.items():
            for m in members:
                nat_refs.append((m, "nat_rule", r.name, field))

    indexed = {}
    for m, src_t, src_n, field in sec_refs + nat_refs:
        indexed.setdefault(m, []).append({"source_type": src_t, "source_name": src_n, "field": field})

    out = []
    for change in changes:
        entity_name = change["entity"]["name"]
        entity_type = change["entity"]["type"]
        direct = indexed.get(entity_name, [])
        transitive = []
        truncated = False

        if entity_type == "address_object":
            for group_name, group in groups.items():
                expanded = _walk_group_refs(groups, group_name, set(), 0, 3, warnings)
                if entity_name in expanded:
                    transitive.append({"source_type": "address_group", "source_name": group_name, "field": "static"})

        if len(transitive) > 100:
            transitive = transitive[:100]
            truncated = True

        clone = dict(change)
        clone["references"] = {"direct": direct, "transitive": transitive, "truncated": truncated, "max_depth": 3}
        out.append(clone)

    return out, warnings
