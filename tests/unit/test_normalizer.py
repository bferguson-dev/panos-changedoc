from panos_changedoc.normalizer import normalize_member_list


def test_normalize_member_list_sorts_members() -> None:
    assert normalize_member_list([" APP02", "APP01 "]) == ("APP01", "APP02")


def test_normalize_member_list_any_is_explicit() -> None:
    assert normalize_member_list(["any"]) == ("any",)
