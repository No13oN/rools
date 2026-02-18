---
id: UKS-KNOWLEDGE-INDEX
type: index
status: active
owner: system
created_at: 2026-02-17T00:00:00Z
updated_at: 2026-02-17T00:00:00Z
version: 1.0.0
depends_on:
  - UKS-START
hash_policy: canonical-md-v1
---
# Knowledge Index

## Rules
1. Кожен активний `.md` має бути у цьому реєстрі.
2. `path` задається відносно кореня цієї папки.
3. Будь-яка зміна структури вимагає оновлення цього індексу.

## Registry
| id | path | type | priority | status | owner | depends_on |
| --- | --- | --- | --- | --- | --- | --- |
| UKS-START | `./start.md` | entrypoint | critical | active | system | UKS-TASK-STATE, UKS-KNOWLEDGE-INDEX, UKS-HASH-REGISTRY, UKS-HANDOFF-PROTOCOL |
| UKS-TASK-STATE | `./TASK_STATE.md` | task_state | critical | active | current_operator | UKS-START |
| UKS-KNOWLEDGE-INDEX | `./KNOWLEDGE_INDEX.md` | index | critical | active | system | UKS-START |
| UKS-HASH-REGISTRY | `./HASH_REGISTRY.md` | integrity_registry | critical | active | system | UKS-KNOWLEDGE-INDEX |
| UKS-HANDOFF-PROTOCOL | `./HANDOFF_PROTOCOL.md` | protocol | high | active | system | UKS-TASK-STATE |
| UKS-HANDOFF-LOG-INDEX | `./HANDOFF_LOG_INDEX.md` | append_log_index | high | active | current_operator | UKS-HANDOFF-PROTOCOL |
| UKS-TEMPLATES-LIB | `./TEMPLATES_LIBRARY.md` | templates | high | active | system | UKS-START |
| UKS-CONTINUITY-CHECKLIST | `./CONTINUITY_CHECKLIST.md` | checklist | high | active | current_operator | UKS-START, UKS-HANDOFF-PROTOCOL |
| UKS-HANDOFF-LOGS-README | `./HANDOFF_LOGS/README.md` | docs | medium | active | system | UKS-HANDOFF-LOG-INDEX |
