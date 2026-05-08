# PAN-OS Change Documentation

## Summary

Compared two PAN-OS XML configurations for standalone firewall scope `vsys1`.

| Input | File | SHA256 |
|---|---|---|
| Before | `tests/fixtures/before_basic.xml` | `79e75ad906139d629fa0e1857e33a57baedc88fdfaeb17fd2962dd243914088d` |
| After | `tests/fixtures/after_basic.xml` | `f9db5cecc758f8a5803620959648be94aa1a17210374077ef91dbc44ecb88334` |

Generated at: `2026-05-08T00:00:00+00:00`

## Change Counts

| Category | Count |
|---|---:|
| Total changes | 4 |
| CRITICAL | 3 |
| HIGH | 1 |
| LOW | 0 |

### Modified: `RuleA` (security_rule)

**Significance:** CRITICAL  
**Rulebase:** security  

Fields changed: `destination`

### Removed: `APP01-OLD` (address_object)

**Significance:** CRITICAL  
**Rulebase:** None  

### Modified: `APP01` (address_object)

**Significance:** CRITICAL  
**Rulebase:** None  

Fields changed: `value`

### Reordered: `RuleB` (security_rule)

**Significance:** HIGH  
**Rulebase:** security  

Fields changed: `order`

## Parser Warnings

No parser warnings.

## Unsupported Sections

Unsupported sections encountered.
