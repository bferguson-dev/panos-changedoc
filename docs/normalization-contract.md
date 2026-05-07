# PAN-OS ChangeDoc v1 Normalization Contract

## Core rule

Do not raw-diff XML. Parse supported XML into normalized internal models, then diff normalized models.

## Normalize these

- XML whitespace
- XML comments
- leading/trailing text whitespace
- known missing defaults
- unordered member lists
- boolean values
- canonical subtrees where required

## Never normalize away these differences

- security rule order
- NAT rule order
- rule names
- object names
- `any` vs named values
- source vs destination context
- action
- source/destination zones
- source/destination members
- application members
- service members
- NAT translation subtrees
- address object values
- address group membership/filter
- service protocol/port
- zone interface membership
- disabled/enabled state
- log fields
- descriptions
- tags

## Member list representation

`any` is explicit and never represented as an empty list:

```json
{
  "type": "any",
  "members": ["any"]
}
```

Named members:

```json
{
  "type": "members",
  "members": ["APP01", "APP02"]
}
```

Sort unordered member lists lexicographically after trimming each member.

Do not sort security or NAT rule entries.

## Enabled/disabled change typing

If `disabled` is the only changed field on a rule:

- `true -> false` emits `change_type: "enabled"`
- `false -> true` emits `change_type: "disabled"`

If `disabled` changes with any other field:

- emit one `change_type: "modified"`
- include `disabled` in `fields_changed`

Do not emit both `modified` and `enabled`/`disabled` for the same entity in one comparison.

## Rule reorder detection

Use longest common subsequence (LCS) on rule names within the same rulebase.

- Rules in LCS are not reordered.
- Existing rules outside LCS are reordered.
- Insertions/removals must not trigger reorder cascade on every shifted rule.
