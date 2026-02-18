# LDS v3.1 Ultra-Compact Execution Card

> DEPRECATED NAME: canonical execution card moved to `docs/standards/lds-execution-card.md`.
> Keep this file only for backward links.

Status: Operational  
Last updated: 2026-02-17  
Parent spec: `docs/standards/lds-spec.md`

## Top-15 MUST Rules

1. Every operational doc MUST be Markdown (`.md`).
2. Every operational doc MUST start with YAML frontmatter.
3. Frontmatter MUST include: `doc_id`, `title`, `version`, `status`, `last_updated`, `owner`.
4. Each file MUST have one primary topic.
5. Heading levels MUST be contiguous (`H1 -> H2 -> H3`); skips are forbidden.
6. File size MUST be <= 10,000 tokens.
7. Critical steps MUST be inline (not link-only).
8. One concept MUST use one canonical term.
9. Time-sensitive claims MUST include date context.
10. Numeric claims MUST include source reference or verification date.
11. Code blocks MUST be fenced and language-tagged.
12. Secrets MUST NOT appear in examples.
13. Every image MUST include meaningful alt text.
14. Every architecture diagram MUST include a text equivalent.
15. Release MUST pass the semantic gate thresholds.

## Publish Gate (PASS/FAIL)

A release is `PASS` only if all conditions below are true.

### A) Static Gate (all required)
- Frontmatter schema: pass
- Required metadata fields: pass
- Heading hierarchy: pass
- Token limit: pass
- Code-fence language tags: pass
- Broken links: pass
- Alt text check: pass

### B) Semantic Gate (all required)
- Weighted score >= 90/100
- Factual score >= 90
- Procedural score >= 90
- Error-interpretation score >= 90
- Comparison score >= 80
- Edge-case score >= 80
- No critical hallucinations in factual/procedural/error classes

### C) Governance Gate (all required)
- Any MUST-rule exception has a waiver
- All waivers are unexpired
- Freshness coverage is current (`last_updated` valid)

## Release Decision

- `PASS`: all A + B + C are true.
- `FAIL`: any condition in A, B, or C fails.

## Required Release Artifacts

1. Static gate report.
2. Semantic scorecard.
3. Waiver list (or explicit `none`).
4. Freshness report.

## Fast Operator Checklist

```text
[ ] 15/15 MUST rules satisfied
[ ] Static gate PASS
[ ] Semantic gate PASS
[ ] Governance gate PASS
[ ] Artifacts attached
=> Decision: PASS / FAIL
```
