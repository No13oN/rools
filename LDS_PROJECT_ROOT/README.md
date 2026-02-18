# LDS Project Root (Conditional Root)

Status: Protected

This folder is the vendor-neutral LDS core: contracts-first governance, deterministic tokenizer runtime, policy gates, and release evidence.

## Structure

```text
LDS_PROJECT_ROOT/
├── contracts/
│   ├── schemas/
│   ├── rules/
│   ├── policy/
│   ├── governance/
│   ├── memory/
│   ├── retrieval/
│   ├── token/
│   └── evaluation/
├── docs/
│   ├── standards/
│   └── governance/
├── policies/
│   └── opa/
├── vendor/
│   └── tokenizers/
│       └── tiktoken-cache/
├── scripts/
├── reports/
│   ├── release/
│   └── handoff/
├── tests/
└── legacy/
```

CI workflow (repository root):
`../.github/workflows/lds-validate.yml`

## Canonical Entry Points

1. `contracts/governance/lds-contract-manifest.json`
2. `contracts/policy/lds-policy.json`
3. `contracts/rules/lds-publish-gate.json`
4. `contracts/token/lds-tokenizer-mirror.json`
5. `contracts/memory/lds-memory-api.json`
6. `contracts/evaluation/lds-handoff-acceptance.json`

## Validation

From `LDS_PROJECT_ROOT`:

```bash
pip install jsonschema pyyaml tiktoken
python3 scripts/validate_tokenizer_offline.py --strict
python3 scripts/validate_lds.py --strict
python3 scripts/build_policy_input.py
python3 scripts/eval_policy_gate.py --strict
python3 scripts/eval_semantic_gate.py --strict --scorecard reports/release/semantic_scorecard.json
python3 scripts/eval_handoff_acceptance.py --strict
python3 scripts/validate_integrity_gate.py --strict
python3 scripts/validate_release_artifacts.py --strict --artifacts-dir reports/release
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Operational Extensions

```bash
# Branch protection hardening
python3 scripts/apply_branch_protection.py --repo <owner/repo> --branch main --dry-run
python3 scripts/check_branch_protection.py --repo <owner/repo> --branch main --strict

# Memory backend adapter v2 (production SQLite backend)
python3 scripts/memory_backend_adapter_v2.py append \
  --memory-class short_term \
  --record '{"content":"example memory","evidence_score":0.8}' \
  --provenance '{"source":"manual"}'
python3 scripts/memory_backend_adapter_v2.py query --query "example" --top-k 5

# Memory backend adapter v1 (reference file backend)
python3 scripts/memory_backend_adapter_v1.py query --query "example" --top-k 5

# Release baseline and optional tag
python3 scripts/release_v1_baseline.py
python3 scripts/release_v1_baseline.py --create-tag --tag lds-v1.0.0
```

## Rules

1. `contracts/` is the source of truth; `docs/` is a projection.
2. Strict mode must pass without network dependency for tokenizer assets.
3. Policy gate must be enforced by OPA/Rego in CI.
4. Release is blocked if any stage fails: schema/static, policy, semantic, handoff, integrity, release artifacts.
