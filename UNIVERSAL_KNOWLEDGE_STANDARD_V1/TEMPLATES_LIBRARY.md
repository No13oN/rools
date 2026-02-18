---
id: UKS-TEMPLATES-LIB
type: templates
status: active
owner: system
created_at: 2026-02-17T00:00:00Z
updated_at: 2026-02-17T00:00:00Z
version: 1.0.0
depends_on:
  - UKS-START
hash_policy: canonical-md-v1
---
# Templates Library

## Template: Generic Knowledge Note
```md
---
id: NOTE-XXXX
type: knowledge_note
status: active
owner: {owner}
created_at: {ISO-8601}
updated_at: {ISO-8601}
version: 1.0.0
depends_on: []
hash_policy: canonical-md-v1
---
# {Title}

## Context
...

## Content
...

## References
...
```

## Template: Decision Record
```md
---
id: DEC-XXXX
type: decision
status: accepted
owner: {owner}
created_at: {ISO-8601}
updated_at: {ISO-8601}
version: 1.0.0
depends_on: []
hash_policy: canonical-md-v1
---
# Decision: {Title}

## Problem
...

## Options
1. ...
2. ...

## Decision
...

## Consequences
...
```

## Template: Handoff Note
```md
---
id: HOFF-XXXX
type: handoff_note
status: active
owner: {from_model}
created_at: {ISO-8601}
updated_at: {ISO-8601}
version: 1.0.0
depends_on:
  - UKS-TASK-STATE
hash_policy: canonical-md-v1
---
# Handoff {from_model} -> {to_model}

## Summary
...

## Completed
1. ...

## Next Actions
1. ...

## Risks
1. ...
```
