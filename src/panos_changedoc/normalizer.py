def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def normalize_bool_text(value: str | None) -> bool:
    normalized = normalize_text(value).lower()
    return normalized in {"yes", "true", "1"}


def normalize_member_list(members: list[str]) -> tuple[str, ...]:
    cleaned = [m.strip() for m in members if m and m.strip()]
    if any(m.lower() == "any" for m in cleaned):
        return ("any",)
    return tuple(sorted(cleaned))


def as_memberset(members: tuple[str, ...]) -> dict:
    if members == ("any",):
        return {"type": "any", "members": ["any"]}
    return {"type": "members", "members": list(members)}
