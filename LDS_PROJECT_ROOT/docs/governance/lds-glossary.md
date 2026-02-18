---
doc_id: "lds-glossary"
title: "LDS Glossary"
version: "1.1.0"
status: "stable"
last_updated: "2026-02-18"
owner: "docs-architecture"
---

# LDS Glossary

| Canonical Term | Definition | Allowed Aliases | Policy |
|---|---|---|---|
| API key | Primary authentication credential for API requests | access token (legacy), auth credential (legacy) | Use `API key` in active docs |
| Semantic gate | Model-based release quality check | semantic QA gate | Use `semantic gate` |
| Waiver | Time-bounded exception for MUST-rule violation | exception | Use `waiver` |
| Tier-0 | Canonical immutable control surface for LDS | canonical core | Drift requires waiver and hash refresh |
| Protected manifest | Contract of Tier-0 paths and expected SHA256 values | integrity manifest | Mandatory source for anti-drift checks |
| Episodic memory | Time-scoped operational memory entries tied to tasks | session memory | Must have TTL and merge policy |
| Faithfulness | Degree to which generated answer is grounded in retrieved sources | grounding score | Must meet evaluation threshold |
