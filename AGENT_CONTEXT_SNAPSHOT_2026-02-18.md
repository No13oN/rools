# Agent Context Snapshot

- Date: 2026-02-18
- Purpose: full operational context for cross-LLM handoff without loss.

## Strategic Goal
Build a universal, vendor-neutral knowledge architecture so any LLM can continue work safely and consistently.

## Canonical Workspace
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT`

## Key Decisions
1. Vendor-neutral core.
2. Contracts-first (`JSON` + `JSON Schema`) as machine source of truth.
3. Markdown as human layer, not sole enforcement layer.
4. Strict gates: static/schema, policy (OPA), semantic, handoff, integrity, release artifacts.
5. Offline tokenizer mirror + hash pinning.
6. Production memory backend selected: SQLite adapter v2 (transactional, persistent, local-first).

## Implemented Blocks
1. Branch protection hardening (bound to real repo, strict validation PASS):
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/.github/branch-protection.json`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/apply_branch_protection.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/check_branch_protection.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_branch_protection_tools.py`

2. Black-swan failure tests:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_black_swan_failures.py`

3. Memory backend adapters:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/memory_backend_adapter_v1.py` (reference file backend)
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_memory_backend_adapter_v1.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/memory_backend_adapter_v2.py` (production SQLite backend)
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_memory_backend_adapter_v2.py`

4. Release baseline/tag logic:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/release_v1_baseline.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_release_v1_baseline.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/reports/release/freeze_report.json`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/reports/release/release_tag_report.json`
- Git tag: `lds-v1.0.0` (annotated, provenance hashes in tag message)

5. Mandatory CI critical suite gate:
- `/Users/sergej13/Xzone/rools/.github/workflows/lds-validate.yml` (explicit Stage 1c for black-swan + memory v1/v2 tests)
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/contracts/governance/lds-protected-manifest.json` (hash pin updated for workflow change)

## Latest Validation State
From `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT`:
- `python3 -m unittest discover -s tests -p "test_*.py" -v` -> PASS (`33 tests`)
- `python3 -m unittest -v tests.test_black_swan_failures tests.test_memory_backend_adapter_v1 tests.test_memory_backend_adapter_v2` -> PASS (`10 tests`)
- `python3 scripts/validate_tokenizer_offline.py --strict` -> PASS
- `python3 scripts/validate_lds.py --strict` -> PASS
- `python3 scripts/build_policy_input.py` -> PASS
- `python3 scripts/eval_policy_gate.py --strict` -> PASS
- `python3 scripts/eval_semantic_gate.py --strict --scorecard reports/release/semantic_scorecard.json` -> PASS
- `python3 scripts/eval_handoff_acceptance.py --strict` -> PASS
- `python3 scripts/validate_integrity_gate.py --strict` -> PASS
- `python3 scripts/validate_release_artifacts.py --strict --artifacts-dir reports/release` -> PASS
- `python3 scripts/check_branch_protection.py --repo No13oN/rools --branch main --strict` -> PASS
- `python3 scripts/release_v1_baseline.py --strict` -> PASS
- `python3 scripts/release_v1_baseline.py --strict --create-tag --tag lds-v1.0.0` -> PASS

## Open Gaps
1. No blocking release gaps as of 2026-02-18.
2. Protected branch requires PR flow by design (operational constraint, not a blocker).

## Practical Next Steps
1. Verify post-merge baseline on `main` commit `fc5000b`.
2. Optional: add `.gitignore` cleanup for `__pycache__` and OS artifacts to reduce repository noise.
3. Optional: issue a follow-up tag that points to current `main` if release policy requires tag-on-main only.

## Handoff Note
This file is the bootstrap context for the next model session. Regenerate after major architecture changes.
