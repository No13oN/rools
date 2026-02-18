---
doc_id: "lds-execution-card"
title: "LDS Execution Card"
version: "1.1.0"
status: "stable"
last_updated: "2026-02-17"
owner: "docs-architecture"
---

# LDS Execution Card

Status: Operational  
Last updated: 2026-02-17  
Parent: `docs/standards/lds-spec.md`

## Top-15 MUST Checklist

1. `LDS-MUST-001`: File is Markdown (`.md`) for operational docs.
2. `LDS-MUST-002`: YAML frontmatter exists.
3. `LDS-MUST-003`: Frontmatter includes `doc_id,title,version,status,last_updated,owner`.
4. `LDS-MUST-004`: Single primary topic per file.
5. `LDS-MUST-005`: Contiguous heading levels only (`H1->H2->H3`).
6. `LDS-MUST-006`: File size <= 10,000 tokens.
7. `LDS-MUST-007`: Critical steps are inline, not link-only.
8. `LDS-MUST-008`: Canonical terminology is used consistently.
9. `LDS-MUST-009`: Time-sensitive statements include explicit date context.
10. `LDS-MUST-010`: Numeric claims have source or verification date.
11. `LDS-MUST-011`: Code fences are language-tagged.
12. `LDS-MUST-012`: No secrets in examples.
13. `LDS-MUST-013`: All images have meaningful alt text.
14. `LDS-MUST-014`: All architecture diagrams have text equivalents.
15. `LDS-MUST-015`: Semantic gate passes release thresholds.

## Publish Gate

`PASS` only if all sections pass.

### A) Static
- frontmatter schema
- required metadata fields
- heading hierarchy
- token limit
- code-fence language tags
- link integrity

### B) Semantic
- weighted score >= 90/100
- factual >= 90
- procedural >= 90
- error interpretation >= 90
- comparison >= 80
- edge case >= 80
- no critical hallucinations in factual/procedural/error classes

### C) Governance
- waivers exist for every MUST exception
- waivers are not expired
- freshness (`last_updated`) is valid for release scope

## Release Artifacts

1. Static report
2. Semantic scorecard
3. Waiver list (`none` if no waivers)
4. Freshness report
