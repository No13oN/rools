# LLM Documentation Standard (LDS) v3.0

> DEPRECATED NAME: canonical spec moved to `docs/standards/lds-spec.md`.
> Keep this file only for backward links.

Status: Canonical Law/Spec  
Last updated: 2026-02-17  
Language: English

## 1. Purpose

This standard defines how to write documentation for Large Language Models (LLMs) so that retrieval, reasoning, and task execution are reliable under limited context windows.

Primary objective:
- Maximize factual accuracy per token.

Non-objectives:
- Marketing copy.
- Human-only storytelling without operational value.

## 2. Normative Keywords

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as described in RFC 2119.

## 3. Model Assumptions

Documentation MUST be designed for these constraints:
1. Context is finite and expensive.
2. Position matters; middle sections are easier to miss in long files.
3. Retrieval is chunk-based, not page-based.
4. Link-following is not guaranteed.
5. Some models are text-only; image understanding is not guaranteed.

## 4. File Format and Structure

### 4.1 Default Format
- Operational docs MUST be authored in Markdown (`.md`).
- JSON/YAML MAY be used for machine-readable schemas and configs.
- If HTML is the delivery layer, a Markdown-equivalent source SHOULD exist.

### 4.2 Document Size
- Recommended target: <= 2,000 tokens for operational how-to docs.
- Recommended target: <= 5,000 tokens for API references.
- Hard ceiling: <= 10,000 tokens per file.
- If the file exceeds 10,000 tokens, it MUST be split by topic.

### 4.3 Heading Hierarchy
- Heading levels MUST be contiguous (`H1 -> H2 -> H3`).
- Heading skips (for example `H1 -> H3`) MUST NOT be used.
- Section order SHOULD be stable across documents of the same type.

### 4.4 One Topic per File
- Each file MUST have one primary intent (for example: authentication, rate limits, errors, one endpoint group).
- Mixed-intent files SHOULD be decomposed.

## 5. Required Frontmatter

Each operational Markdown file MUST start with YAML frontmatter:

```yaml
---
doc_id: "api-rate-limiting-v1"
title: "Rate Limiting"
version: "1.0.0"
status: "stable" # stable | beta | deprecated
last_updated: "2026-02-17"
owner: "platform-team"
audience: "developers"
scope: "public-api"
tags: ["api", "limits", "reliability"]
related: ["authentication-v2", "error-codes-v3"]
---
```

Minimum required fields:
- `doc_id`
- `title`
- `version`
- `status`
- `last_updated`
- `owner`

## 6. Terminology Control

- One concept MUST map to one canonical term.
- Synonyms for the same concept SHOULD NOT be used in technical instructions.
- A project glossary file MUST exist and be treated as source of truth.
- If legacy aliases exist, they MUST be listed in an explicit alias map.

Example:

```yaml
canonical: "API key"
aliases: ["access token", "auth credential"]
policy: "Use canonical term in all active docs"
```

## 7. Writing Rules

### 7.1 Important First
- The first 2-3 sentences of each section MUST contain the key fact, constraint, or decision.

### 7.2 Precision over Style
- Sentences MUST be information-dense and unambiguous.
- Filler text SHOULD be removed.
- Pronouns SHOULD be minimized in procedural instructions.

### 7.3 Claims and Freshness
- Numeric claims MUST include a source reference or verification date.
- Time-sensitive statements MUST include date context.
- Units and time zones MUST be explicit.

## 8. Code and Command Examples

- Code blocks MUST be fenced and language-tagged.
- Every example SHOULD be runnable without hidden context.
- Required environment variables MUST be listed before the example.
- Expected output SHOULD be shown for critical flows.
- Secrets MUST NOT appear in plaintext examples.

Example:

```bash
export API_KEY="***"
curl -H "Authorization: Bearer ${API_KEY}" https://api.example.com/v1/users
```

## 9. API and Data Contract Sections

Any API/data contract page MUST include:
1. Field names.
2. Types.
3. Required/optional status.
4. Constraints.
5. Error behavior.
6. Version compatibility notes.

Recommended table:

| Field | Type | Required | Constraints | Notes |
|---|---|---|---|---|
| `user_id` | string | yes | UUID v4 | Stable identifier |

## 10. Links and Cross-References

- Critical instructions MUST be inline; links are support, not dependency.
- Related documents SHOULD be linked in a dedicated "Related" section.
- Broken or circular references MUST be treated as defects.

## 11. Images and Diagrams

- Every image MUST have meaningful alt text.
- Every architecture diagram MUST have a text equivalent.
- Text equivalent MUST describe components and data/control flow.

## 12. `llms.txt` Profile

`llms.txt` is a practical indexing convention. It is useful, but provider behavior can change. Treat it as operational guidance, not guaranteed protocol behavior.

Rules:
1. `llms.txt` SHOULD remain concise (target <= 10,000 tokens).
2. Links SHOULD point to Markdown or plaintext documents.
3. Each link SHOULD include a one-sentence, concrete description.
4. `llms-full.txt` MAY exist for RAG pipelines, but should be generated from canonical docs.

Minimal shape:

```markdown
# Product Name
> One-line product purpose.

## Docs
- [Authentication](https://docs.example.com/authentication.md): API key and OAuth setup.
- [Rate Limiting](https://docs.example.com/rate-limits.md): Limits, headers, retry strategy.
```

## 13. Compliance Matrix

| Rule ID | Requirement | Level | Auto-check | Fail Condition |
|---|---|---|---|---|
| LDS-001 | YAML frontmatter present | MUST | yes | Missing frontmatter |
| LDS-002 | Required metadata fields present | MUST | yes | Any required field missing |
| LDS-003 | No heading level skips | MUST | yes | `H1 -> H3` or similar |
| LDS-004 | File <= 10k tokens | MUST | yes | Token count exceeds limit |
| LDS-005 | Single canonical term per concept | MUST | partial | Alias drift in active docs |
| LDS-006 | Code fences include language | MUST | yes | Untagged code blocks |
| LDS-007 | Critical steps inline, not link-only | MUST | no | Required step only referenced |
| LDS-008 | Time-sensitive claims have date | MUST | partial | Undated time-sensitive claims |
| LDS-009 | Images include alt text | MUST | yes | Missing/empty alt text |
| LDS-010 | Diagram has text equivalent | MUST | partial | No textual flow description |
| LDS-011 | Semantic gate passes threshold | MUST | partial | Semantic score below release threshold |
| LDS-012 | Exception waivers valid and unexpired | MUST | yes | Missing/expired waiver for MUST violation |
| LDS-013 | Deprecated content explicitly marked | SHOULD | partial | Legacy endpoint not marked |
| LDS-014 | Q&A section for common failures | SHOULD | no | Missing FAQ in user-facing docs |

## 14. Validation Workflow

### 14.1 Static Gates
Run linters/checkers for:
- frontmatter schema
- heading structure
- code fence language tags
- token length
- broken links

### 14.2 Semantic Gates
Use model-based tests with five mandatory question classes:
1. factual
2. procedural
3. error interpretation
4. comparison
5. edge case

Scoring profile:

| Class | Weight | Minimum Class Score |
|---|---:|---:|
| factual | 25 | 90 |
| procedural | 25 | 90 |
| error interpretation | 20 | 90 |
| comparison | 15 | 80 |
| edge case | 15 | 80 |

Release thresholds:
1. Weighted total score MUST be >= 90/100.
2. Any class below its minimum score MUST block release.
3. Any critical hallucination in factual/procedural/error class MUST block release.

### 14.3 Evidence Package
Each release MUST include:
1. Static gate report.
2. Semantic QA scorecard.
3. Exception waiver list (if any).
4. Document freshness report (`last_updated` coverage).

## 15. Exception Policy

Any exception to a MUST rule requires a documented waiver:

```yaml
exception_id: "EX-2026-02-17-01"
rule_id: "LDS-004"
reason: "Regulatory appendix cannot be split"
scope: "compliance-manual.md"
owner: "docs-lead"
expires_on: "2026-06-30"
mitigation: "Add chunk-level index and summary pages"
```

Expired exceptions MUST be reviewed or removed.

## 16. Anti-Patterns (Do Not Ship)

1. Large unstructured text blocks without headings.
2. Link-only critical steps.
3. Multiple terms for one concept without alias policy.
4. Undated operational claims.
5. Incomplete code snippets that depend on hidden context.
6. Diagrams without textual equivalents.

## 17. Minimal Templates

### 17.1 Endpoint Template

````markdown
## [Endpoint Name]
`[METHOD] /path`

### Purpose
One sentence with business and technical intent.

### Preconditions
- auth requirement
- required headers

### Parameters
| Name | Type | Required | Constraints | Description |
|---|---|---|---|---|

### Response
```json
{}
```

### Errors
- `400` Validation error
- `401` Authentication error
- `429` Rate limit exceeded
````

### 17.2 Runbook Step Template

````markdown
## Step [N]: [Action]
### Why
One sentence.

### Command
```bash
# exact command
```

### Expected Result
Observable success signal.

### Failure Modes
- symptom
- probable cause
- corrective action
````

## 18. Definition of Done

A document set is compliant when:
1. All MUST rules pass.
2. SHOULD violations are tracked with owners.
3. Semantic QA passes defined numeric thresholds.
4. Metadata freshness is current as of release date.
5. Evidence package is attached to the release.
