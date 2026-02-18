---
doc_id: "lds-standards-profile"
title: "LDS Standards Profile"
version: "1.1.0"
status: "stable"
last_updated: "2026-02-17"
owner: "docs-architecture"
---

# LDS Standards Profile (Machine Readability)

Status: Canonical Companion  
Last updated: 2026-02-17  
Parent: `docs/standards/lds-spec.md`

## Direct Answer

There is no universal single format that is "best for machines" in all cases.
The best machine outcome is a layered profile:
1. Markdown (CommonMark) for human+LLM operational knowledge.
2. JSON + JSON Schema for strict machine contracts.
3. OpenAPI/AsyncAPI for API ecosystems.

## Recommended Profile by Use Case

| Use Case | Best Standard | Confidence | Notes |
|---|---|---:|---|
| Prose documentation for LLM reading | CommonMark Markdown | High | Best readability and version-control ergonomics |
| Strict machine contract validation | JSON + JSON Schema | Very High | Deterministic validation |
| REST API contract and tooling | OpenAPI 3.2 | Very High | Mature ecosystem |
| Event API contract | AsyncAPI 3.1 | High | Native event model |
| Line-stream machine logs | JSON Lines / RFC 7464 | High | Streaming-friendly |
| Knowledge graph semantics | JSON-LD 1.1 | Medium | Use only when graph interoperability is required |

## Practical Architecture Rule

For robust LLM systems, use dual artifacts:
1. Human/LLM explanation in `.md`.
2. Machine-enforceable schema in JSON/contract form.

## Interoperability Layer (Optional)

1. MCP can standardize tool/context exchange between assistants.
2. A2A can standardize agent-to-agent handoff in multi-agent topologies.

These are runtime protocol layers, not replacements for documentation standards.

## Source Links

1. CommonMark: https://commonmark.org/
2. JSON RFC 8259: https://www.rfc-editor.org/info/rfc8259
3. JSON Schema 2020-12: https://json-schema.org/specification
4. OpenAPI latest: https://spec.openapis.org/oas/latest
5. AsyncAPI latest: https://www.asyncapi.com/docs/reference/specification/latest
6. JSON-LD 1.1: https://www.w3.org/news/2020/json-ld-1-1-specifications-are-w3c-recommendations/
7. RFC 7464: https://www.rfc-editor.org/info/rfc7464
8. MCP docs: https://docs.anthropic.com/en/docs/mcp
9. A2A repo: https://github.com/google-a2a/A2A
10. llms.txt proposal: https://llmstxt.org/index.html
