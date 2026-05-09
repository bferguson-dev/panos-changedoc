SIGNIFICANCE_ORDER = {"CRITICAL": 0, "HIGH": 1, "LOW": 2}
ENTITY_ORDER = {
    "security_rule": 0,
    "nat_rule": 1,
    "address_object": 2,
    "address_group": 3,
    "service_object": 4,
    "zone": 5,
}
CHANGE_TYPE_ORDER = {
    "added": 0,
    "removed": 1,
    "modified": 2,
    "enabled": 3,
    "disabled": 4,
    "reordered": 5,
}


def sort_changes(changes: list[dict]) -> list[dict]:
    return sorted(
        changes,
        key=lambda c: (
            SIGNIFICANCE_ORDER[c["significance"]],
            ENTITY_ORDER[c["entity"]["type"]],
            CHANGE_TYPE_ORDER[c["change_type"]],
            c["entity"]["name"],
            c["id"],
        ),
    )
