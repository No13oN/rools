---
doc_id: "lds-changelog"
title: "LDS Changelog"
version: "1.3.0"
status: "stable"
last_updated: "2026-02-18"
owner: "docs-architecture"
---

# LDS Changelog

## 2026-02-18

### Added
1. `contracts/token/lds-tokenizer-mirror.schema.json` and `contracts/token/lds-tokenizer-mirror.json` for deterministic offline tokenizer mirror.
2. `vendor/tokenizers/tiktoken-cache/*` with pinned tokenizer asset hash.
3. `scripts/validate_tokenizer_offline.py` for strict no-network tokenizer validation.
4. `policies/opa/lds_gate.rego` for policy-as-code gate.
5. `scripts/build_policy_input.py` and `scripts/eval_policy_gate.py` for OPA policy stage.
6. `scripts/validate_integrity_gate.py` for dedicated integrity stage.
7. `contracts/memory/lds-memory-api.schema.json` and `contracts/memory/lds-memory-api.json` for vendor-neutral memory operations (`append/query/compact/evict`).
8. `contracts/evaluation/lds-handoff-acceptance.schema.json` and `contracts/evaluation/lds-handoff-acceptance.json` for multi-agent consistency thresholds.
9. `scripts/eval_handoff_acceptance.py` and `reports/handoff/{codex,claude,gemini}.json` fixtures.

### Changed
1. `scripts/validate_lds.py` now validates tokenizer mirror runtime and supports `--skip-integrity` for staged CI order.
2. `contracts/rules/lds-publish-gate.json` and `.yaml` now include offline tokenizer check, policy gate, and handoff gate.
3. `contracts/policy/lds-policy.json` synced with new checks and required artifacts.
4. `.github/workflows/lds-validate.yml` converted to staged pipeline: offline -> schema/static -> policy -> semantic -> handoff -> integrity -> release.
5. `contracts/governance/lds-contract-manifest.json` regenerated with new contracts.
6. `README.md`, `lds-canonical-tier0.md`, and `lds-ownership.yaml` aligned to the new architecture scope.

## 2026-02-17

### Added
1. `docs/standards/lds-spec.md` as canonical law/spec.
2. `docs/standards/lds-execution-card.md` as operational release card.
3. `docs/standards/lds-standards-profile.md` as machine-standards map.
4. `contracts/schemas/lds-frontmatter.schema.json` for strict metadata validation.
5. `contracts/rules/lds-ruleset.json` for machine-readable MUST rules.
6. `contracts/rules/lds-publish-gate.yaml` for release gate thresholds.
7. `contracts/governance/lds-waivers.yaml` for structured waiver registry.
8. `docs/governance/lds-glossary.md` for canonical terminology control.
9. `docs/governance/lds-waivers.md` for human-readable waiver log.
10. `contracts/rules/lds-publish-gate.json` and `contracts/rules/lds-publish-gate.schema.json` for strict gate validation.
11. `contracts/policy/lds-policy.json` and `contracts/policy/lds-policy.schema.json` for machine policy control.
12. `docs/governance/lds-ownership.yaml` for ownership/RACI mapping.
13. `scripts/validate_lds.py` for static + anti-drift enforcement.
14. `.github/workflows/lds-validate.yml` for CI execution.
15. `tests/fixtures/*` and `tests/test_lds_validator.py` for regression safety.
