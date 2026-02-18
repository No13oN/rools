---
doc_id: "lds-canonical-tier0"
title: "LDS Canonical Tier-0"
version: "1.2.0"
status: "stable"
last_updated: "2026-02-18"
owner: "docs-architecture"
---

# LDS Canonical Tier-0

## Purpose

This document freezes the canonical files that define LDS behavior.
Any unmanaged drift in Tier-0 is a release blocker.

## Tier Model

1. Tier-0: Canonical law, contracts, strict validators, and CI gate logic.
2. Tier-1: Operational governance and release evidence.
3. Tier-2: Test fixtures, legacy references, and experimental notes.

## Tier-0 Paths

1. `docs/standards/lds-spec.md`
2. `docs/standards/lds-execution-card.md`
3. `docs/standards/lds-standards-profile.md`
4. `docs/governance/lds-glossary.md`
5. `docs/governance/lds-changelog.md`
6. `docs/governance/lds-waivers.md`
7. `docs/governance/lds-ownership.yaml`
8. `docs/governance/lds-canonical-tier0.md`
9. `docs/governance/lds-governance-raci.md`
10. `docs/governance/lds-readiness-audit.md`
11. `contracts/schemas/lds-frontmatter.schema.json`
12. `contracts/rules/lds-ruleset.json`
13. `contracts/rules/lds-ruleset.schema.json`
14. `contracts/rules/lds-publish-gate.json`
15. `contracts/rules/lds-publish-gate.schema.json`
16. `contracts/rules/lds-publish-gate.yaml`
17. `contracts/policy/lds-policy.json`
18. `contracts/policy/lds-policy.schema.json`
19. `contracts/governance/lds-waivers.yaml`
20. `contracts/governance/lds-waivers.schema.json`
21. `contracts/governance/lds-contract-manifest.json`
22. `contracts/governance/lds-contract-manifest.schema.json`
23. `contracts/governance/lds-protected-manifest.json`
24. `contracts/governance/lds-protected-manifest.schema.json`
25. `contracts/memory/lds-memory-policy.json`
26. `contracts/memory/lds-memory-policy.schema.json`
27. `contracts/memory/lds-memory-api.json`
28. `contracts/memory/lds-memory-api.schema.json`
29. `contracts/retrieval/lds-retrieval-policy.json`
30. `contracts/retrieval/lds-retrieval-policy.schema.json`
31. `contracts/token/lds-token-budget.json`
32. `contracts/token/lds-token-budget.schema.json`
33. `contracts/token/lds-tokenizer-mirror.json`
34. `contracts/token/lds-tokenizer-mirror.schema.json`
35. `contracts/evaluation/lds-eval-thresholds.json`
36. `contracts/evaluation/lds-eval-thresholds.schema.json`
37. `contracts/evaluation/lds-handoff-acceptance.json`
38. `contracts/evaluation/lds-handoff-acceptance.schema.json`
39. `policies/opa/lds_gate.rego`
40. `scripts/validate_lds.py`
41. `scripts/validate_tokenizer_offline.py`
42. `scripts/build_policy_input.py`
43. `scripts/eval_policy_gate.py`
44. `scripts/eval_semantic_gate.py`
45. `scripts/eval_handoff_acceptance.py`
46. `scripts/validate_integrity_gate.py`
47. `scripts/validate_release_artifacts.py`
48. `../.github/workflows/lds-validate.yml`

## Tier-0 Change Protocol

1. Open waiver in `contracts/governance/lds-waivers.yaml` with `waiver_type: tier0_hash_override` when required.
2. Apply controlled change.
3. Recompute checksums in `contracts/governance/lds-contract-manifest.json`.
4. Recompute hashes in `contracts/governance/lds-protected-manifest.json`.
5. Run all strict gates in canonical order.
6. Merge only after all gates pass.
