---
doc_id: "lds-waivers"
title: "LDS Waiver Log"
version: "1.1.0"
status: "stable"
last_updated: "2026-02-18"
owner: "docs-architecture"
---

# LDS Waiver Log

Structured source of truth:
`contracts/governance/lds-waivers.yaml`

## Active Waivers

None.

## Waiver Template

```yaml
waiver_id: "WVR-YYYY-MM-DD-01"
waiver_type: "tier0_hash_override" # must_rule_exception | tier0_hash_override | temporary_gate_reduction
rule_id: "LDS-MUST-XXX" # optional for non-rule waivers
scope_path: "relative/path/to/file"
reason: "why waiver is required"
owner: "responsible owner"
created_on: "YYYY-MM-DD"
expires_on: "YYYY-MM-DD"
mitigation: "risk control and rollback"
status: "active" # active | closed
```

## Governance Rules

1. Every waiver must have an explicit expiration date.
2. Expired active waivers block release.
3. Tier-0 hash mismatches are allowed only with active `tier0_hash_override` waivers.
