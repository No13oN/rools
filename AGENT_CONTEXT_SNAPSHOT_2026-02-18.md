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

## Implemented Blocks
1. Branch protection hardening:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/.github/branch-protection.json`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/apply_branch_protection.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/check_branch_protection.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_branch_protection_tools.py`

2. Black-swan failure tests:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_black_swan_failures.py`

3. Memory backend adapter v1:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/memory_backend_adapter_v1.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_memory_backend_adapter_v1.py`

4. Release baseline/tag logic:
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/scripts/release_v1_baseline.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/tests/test_release_v1_baseline.py`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/reports/release/freeze_report.json`
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/reports/release/release_tag_report.json`

5. Mandatory CI critical suite gate:
- `/Users/sergej13/Xzone/rools/.github/workflows/lds-validate.yml` (explicit Stage 1c for black-swan + memory tests)
- `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/contracts/governance/lds-protected-manifest.json` (hash pin updated for workflow change)

## Latest Validation State
From `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT`:
- `python3 -m unittest discover -s tests -p "test_*.py" -v` -> PASS (`30 tests`)
- `python3 -m unittest -v tests.test_black_swan_failures tests.test_memory_backend_adapter_v1` -> PASS (`7 tests`)
- `python3 scripts/validate_lds.py --strict` -> PASS
- `python3 scripts/build_policy_input.py` -> PASS
- `python3 scripts/eval_policy_gate.py --strict` -> PASS
- `python3 scripts/eval_handoff_acceptance.py --strict` -> PASS
- `python3 scripts/validate_integrity_gate.py --strict` -> PASS
- `python3 scripts/validate_release_artifacts.py --strict --artifacts-dir reports/release` -> PASS
- `python3 scripts/release_v1_baseline.py --strict` -> PASS

## Open Gaps
1. Branch protection report is `warn` until bound to real GitHub repo (`owner/repo`).
2. Tag creation is not final in non-git/no-remote context.
3. Memory adapter is reference file backend; production backend integration pending.

## Practical Next Steps
1. Bind repo remote and apply branch protection in strict mode.
2. Decide production memory backend (DB/vector/graph).
3. Create first clean release tag with provenance.

## Handoff Note
This file is the bootstrap context for the next model session. Regenerate after major architecture changes.
