---
doc_id: "lds-spec"
title: "LDS Canonical Spec"
version: "1.1.0"
status: "stable"
last_updated: "2026-02-17"
owner: "docs-architecture"
---

# LDS Canonical Spec

Status: Canonical  
Last updated: 2026-02-17  
Owner: docs-architecture

## 1. Scope

This document defines the canonical documentation standard for LLM-oriented projects.
It replaces versioned filename variants as the source of truth.

## 2. Core Principle

There is no single "best format for machines" for all content types.  
Machine reliability is achieved through a layered standard stack:
1. Correct format per artifact type.
2. Stable schema.
3. Deterministic validation gates.

## 3. Canonical Standards Stack

The project standardizes on these formal references:

1. Markdown syntax baseline: CommonMark
2. Structured data interchange: JSON (RFC 8259)
3. Data schema validation: JSON Schema Draft 2020-12
4. HTTP API contracts: OpenAPI Specification 3.2
5. Event API contracts: AsyncAPI 3.1
6. Optional linked data semantics: JSON-LD 1.1
7. Optional JSON stream framing: RFC 7464 (`application/json-seq`)
8. Agent runtime interoperability (optional): MCP, A2A

## 4. Format Selection Matrix

| Artifact Type | Canonical Format | Why |
|---|---|---|
| Policy / runbook / knowledge docs | CommonMark `.md` + YAML frontmatter | Human + LLM readable, diff-friendly |
| Machine config / contracts | JSON + JSON Schema | Deterministic parsing and validation |
| REST API definition | OpenAPI 3.2 (YAML or JSON source) | Broad tooling, contract-first workflows |
| Event-driven API definition | AsyncAPI 3.1 | Native event semantics |
| Line-by-line machine logs | JSON Lines (`.jsonl`) or JSON Text Sequences | Stream-safe ingestion |
| Semantic web interoperability | JSON-LD 1.1 (optional) | Graph-aware interoperability |

Decision rule:
1. If humans must read/edit often -> Markdown first.
2. If machines must validate strictly -> JSON + schema first.
3. If both are required -> dual artifact (`.md` explainer + schema contract).

## 5. Canonical File Naming (No Version in Filename)

Required filenames:
1. `docs/standards/lds-spec.md` (this law/spec)
2. `docs/standards/lds-execution-card.md` (operator card)
3. `docs/standards/lds-standards-profile.md` (standards map and rationale)
4. `docs/governance/lds-glossary.md` (canonical terms)
5. `docs/governance/lds-changelog.md` (version history in-content)
6. `docs/governance/lds-waivers.md` (human-readable exceptions)
7. `contracts/schemas/lds-frontmatter.schema.json` (metadata schema contract)
8. `contracts/rules/lds-ruleset.json` (machine-readable ruleset)
9. `contracts/rules/lds-publish-gate.json` (machine publish-gate contract)
10. `contracts/rules/lds-publish-gate.schema.json` (publish-gate schema)
11. `contracts/rules/lds-publish-gate.yaml` (human-readable mirror)
12. `contracts/governance/lds-waivers.yaml` (structured waiver registry)
13. `contracts/policy/lds-policy.schema.json` (policy schema)
14. `contracts/policy/lds-policy.json` (machine policy instance)
15. `docs/governance/lds-ownership.yaml` (owner map / RACI)

Rules:
1. Version MUST be stored in frontmatter or changelog, not in filename.
2. Canonical files MUST NOT be duplicated with suffixes like `_v3`, `_final`, `_new`.
3. Deprecated files MUST point to canonical file in the first lines.
4. Machine-checkable rules MUST live in schema/ruleset artifacts, not only prose.

## 6. Required Frontmatter (Markdown)

Every operational Markdown file MUST begin with:

```yaml
---
doc_id: "unique-id"
title: "Document Title"
version: "x.y.z"
status: "stable" # stable | beta | deprecated
last_updated: "YYYY-MM-DD"
owner: "team-or-person"
---
```

Validation source:
`contracts/schemas/lds-frontmatter.schema.json`

## 7. Non-Negotiable MUST Rules

1. `LDS-MUST-001`: Operational documentation MUST be Markdown.
2. `LDS-MUST-002`: YAML frontmatter MUST exist in operational Markdown files.
3. `LDS-MUST-003`: Required frontmatter fields MUST be present.
4. `LDS-MUST-004`: Each file MUST have one primary topic.
5. `LDS-MUST-005`: Heading hierarchy MUST be contiguous (`H1 -> H2 -> H3`).
6. `LDS-MUST-006`: File length MUST be <= 10,000 tokens.
7. `LDS-MUST-007`: Critical steps MUST be inline (not link-only).
8. `LDS-MUST-008`: One concept MUST use one canonical term.
9. `LDS-MUST-009`: Time-sensitive claims MUST include explicit date context.
10. `LDS-MUST-010`: Numeric claims MUST include source reference or verification date.
11. `LDS-MUST-011`: Code blocks MUST be fenced and language-tagged.
12. `LDS-MUST-012`: Secrets MUST NOT appear in examples.
13. `LDS-MUST-013`: Every image MUST include meaningful alt text.
14. `LDS-MUST-014`: Every architecture diagram MUST include text equivalent.
15. `LDS-MUST-015`: Release MUST pass semantic gate thresholds.

## 8. Publish Gate

Release is `PASS` only if all are true:

### 8.1 Static Gate
1. Frontmatter schema valid.
2. Required metadata fields present.
3. No heading level skips.
4. Token limit respected.
5. Code-fence language tags present.
6. No broken links.

### 8.2 Semantic Gate
1. Weighted semantic score >= 90/100.
2. Factual score >= 90.
3. Procedural score >= 90.
4. Error-interpretation score >= 90.
5. Comparison score >= 80.
6. Edge-case score >= 80.
7. No critical hallucinations in factual/procedural/error classes.

### 8.3 Governance Gate
1. All MUST-rule exceptions are documented.
2. Waivers are unexpired.
3. Freshness (`last_updated`) is current for release scope.

## 9. Exception Policy

Any deviation from a MUST rule requires a waiver entry in `docs/governance/lds-waivers.md`:

```yaml
exception_id: "EX-YYYY-MM-DD-01"
rule_id: "LDS-MUST-XX"
scope: "file-or-module"
reason: "why exception is needed"
owner: "responsible owner"
expires_on: "YYYY-MM-DD"
mitigation: "risk control"
```

Machine registry source:
`contracts/governance/lds-waivers.yaml`

## 10. Definition of Done

Documentation is compliant when:
1. All MUST rules pass.
2. Semantic gate passes.
3. Governance gate passes.
4. Required release artifacts are attached.

## 11. Anti-Drift Control

Normative anti-drift checks:
1. `contracts/rules/lds-ruleset.json` and `contracts/policy/lds-policy.json` MUST have the same MUST-rule ID set.
2. MUST-rule IDs declared in this spec MUST match the same set.
3. Publish gate thresholds in `contracts/rules/lds-publish-gate.json` and policy gate thresholds MUST be identical.
4. Any mismatch MUST block release.

Enforcement:
`scripts/validate_lds.py`

## 12. Standards References

1. CommonMark: https://commonmark.org/
2. JSON RFC 8259: https://www.rfc-editor.org/info/rfc8259
3. JSON Schema 2020-12: https://json-schema.org/specification
4. OpenAPI latest: https://spec.openapis.org/oas/latest
5. AsyncAPI latest: https://www.asyncapi.com/docs/reference/specification/latest
6. JSON-LD 1.1: https://www.w3.org/news/2020/json-ld-1-1-specifications-are-w3c-recommendations/
7. JSON Text Sequences RFC 7464: https://www.rfc-editor.org/info/rfc7464
8. MCP: https://docs.anthropic.com/en/docs/mcp
9. A2A: https://github.com/google-a2a/A2A
