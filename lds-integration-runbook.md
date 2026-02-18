# ARHITECRO: LDS deployment and integration guide

Status: Protected
Protection: Do not modify without explicit owner approval.

Last updated: 2026-02-18
Canonical base: `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/`

---

## 0) Mandatory rule before any release

You MUST install dependencies and run strict validation:

```bash
cd /Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT
pip install jsonschema pyyaml tiktoken
python3 scripts/validate_lds.py --strict
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Release is blocked if `validate_lds.py --strict` fails.

---

## 1) New project bootstrap (greenfield)

### Goal
Apply LDS as-is into a new project with full canonical infrastructure:
`docs + contracts + policy + governance + tests + CI`.

### Steps
1. Create new project root.
2. Copy whole LDS base from:
   `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/`
3. Keep structure unchanged on first pass.
4. Update ownership and metadata:
   - `docs/governance/lds-ownership.yaml`
   - frontmatter `owner`, `doc_id`, `last_updated`
5. Run strict validation and tests.
6. Start writing project-specific docs only inside canonical structure.

### Do not do
- Do not rename canonical files in first iteration.
- Do not mix legacy docs into `docs/standards` directly.

### Done criteria
- `validate_lds.py --strict` is PASS.
- All tests are PASS.
- CI workflow is enabled in repository root.

---

## 2) Integration of one existing project (brownfield)

### Goal
Safely migrate one existing project into LDS without losing historical context.

### Required migration model
1. Existing root is renamed to `<project_name>_archive`.
2. Create fresh empty root `<project_name>`.
3. Copy LDS base into fresh root.
4. Analyze `<project_name>_archive`.
5. Reintegrate content into LDS structure by rules.

### Migration flow
1. Freeze old project changes.
2. Rename old root to archive.
3. Create new clean root.
4. Copy LDS base (`LDS_PROJECT_ROOT` content).
5. Inventory old archive:
   - docs
   - contracts/configs
   - runbooks/scripts
   - tests
6. Map each artifact:
   - operational docs -> `docs/`
   - strict contracts -> `contracts/`
   - waivers/governance -> `docs/governance` + `contracts/governance`
   - obsolete content -> `legacy/` or project archive
7. Normalize terminology and frontmatter.
8. Run strict validation and tests.
9. Open migration report and close deltas.

### Hard rule
No direct copy from archive to production docs without normalization and validation.

### Done criteria
- No orphaned critical docs outside LDS structure.
- All migrated docs pass gate.
- Archive remains immutable as historical evidence.

---

## 3) Integration of multiple projects into one

### Goal
Merge several legacy projects into one canonical LDS-based root.

### Required migration model
1. Rename old roots to archives:
   - `<target>_archive1`
   - `<target>_archive2`
   - ...
2. Create clean new root `<target>`.
3. Copy LDS base.
4. Run multi-source analysis.
5. Build and execute integration plan.

### Multi-project integration flow
1. Define target system boundaries and naming policy.
2. For each archive:
   - inventory all docs/contracts/policies/tests
   - detect duplicates and conflicts
3. Build canonical mapping table:
   - source file -> target path
   - merge strategy (`keep`, `merge`, `deprecate`, `archive`)
4. Resolve conflicts by priority:
   1) security and compliance
   2) data contracts
   3) operational runbooks
   4) reference docs
5. Migrate in batches with validation after each batch.
6. Keep deprecation notes for replaced artifacts.
7. Run full strict validation and test suite.

### Hard rule
Do not perform “big bang” merge without staged validation checkpoints.

### Done criteria
- Single canonical root with LDS structure.
- Explicit conflict resolution log exists.
- All gates PASS.

---

## 4) Canonical target structure (must stay stable)

```text
<project_root>/
├── docs/
│   ├── standards/
│   └── governance/
├── contracts/
│   ├── schemas/
│   ├── rules/
│   ├── policy/
│   └── governance/
├── scripts/
├── tests/
├── legacy/
└── .github/workflows/
```

---

## 5) Mandatory quality gates

### Static gate
- frontmatter valid
- required metadata present
- heading hierarchy valid
- code fence language tags present
- link integrity valid

### Semantic gate
- weighted score >= 90
- factual/procedural/error >= 90
- comparison/edge-case >= 80
- no critical hallucinations in critical classes

### Governance gate
- waivers documented
- waivers not expired
- freshness valid

---

## 6) Practical command sequence for any scenario

```bash
cd <target_root>/LDS_PROJECT_ROOT
python3 scripts/validate_lds.py --strict
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

If any command fails, integration is not complete.
