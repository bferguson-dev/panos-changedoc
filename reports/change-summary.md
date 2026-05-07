# PAN-OS Change Documentation

## Summary

Compared two PAN-OS XML configurations for standalone firewall scope `vsys1`.

| Input | File | SHA256 |
|---|---|---|
| Before | `sample_configs/before.xml` | `c4269ee5e1986f147d7a9d0efeb12cdde8b4c98bc79fe1d66b92d57ffd80e659` |
| After | `sample_configs/after.xml` | `f5efa36bfd73f813c6e975865878ee289ee2758c497bf4c593305970842410d0` |

Generated at: `2026-05-07T21:17:55+00:00`

## Change Counts

| Category | Count |
|---|---:|
| Total changes | 2 |
| CRITICAL | 2 |
| HIGH | 0 |
| LOW | 0 |

### Modified: `Allow-App01-HTTPS` (security_rule)

**Significance:** CRITICAL  
**Rulebase:** security  

Fields changed: `destination`

### Removed: `APP01-OLD` (address_object)

**Significance:** CRITICAL  
**Rulebase:** None  

## Parser Warnings

No parser warnings.

## Unsupported Sections

No unsupported sections were encountered in supported v1 scope.
