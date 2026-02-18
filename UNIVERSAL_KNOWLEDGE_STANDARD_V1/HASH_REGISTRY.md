---
id: UKS-HASH-REGISTRY
type: integrity_registry
status: active
owner: system
created_at: 2026-02-17T00:00:00Z
updated_at: 2026-02-17T00:00:00Z
version: 1.0.0
depends_on:
  - UKS-KNOWLEDGE-INDEX
hash_policy: canonical-md-v1
---
# Hash Registry

## Hash Policy: `canonical-md-v1`
1. Файл зберігається в UTF-8.
2. Рядки мають закінчення LF (`\n`).
3. Без trailing spaces.
4. Один фінальний перенос рядка наприкінці файлу.
5. Алгоритм хешування: `SHA-256`.

## Notes
- `HASH_REGISTRY.md` не хешується сам на себе, щоб уникнути циклічної залежності.
- Після будь-яких змін у `.md` оновити записи нижче.

## Registry
| id | path | sha256 | checked_at | checker |
| --- | --- | --- | --- | --- |
| UKS-START | `./start.md` | `18c6c2f737f7277838c4b61604d931213ecfcaa05c828719146ac8e4cbdd39a8` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-TASK-STATE | `./TASK_STATE.md` | `74a83a10b335fe0f8053df03a24eeb17004e62ed4a7def3acfaa8ebca01d95c4` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-KNOWLEDGE-INDEX | `./KNOWLEDGE_INDEX.md` | `3e7a7ee37ebdea36b03ef0e31427a7318e668f33560b62f87d33178d5200f5d6` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-HANDOFF-PROTOCOL | `./HANDOFF_PROTOCOL.md` | `33b85665e0cfb41cb1c130cb33758ae43fc15d0f7c577e261408bcac7d589ccf` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-HANDOFF-LOG-INDEX | `./HANDOFF_LOG_INDEX.md` | `378e3826e751da30e142ffd035249798b6cadfb4d30e55a4191100734cfcc179` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-TEMPLATES-LIB | `./TEMPLATES_LIBRARY.md` | `39bea334213ce4d466ad1821db15c8bdc37613a9606cc67a1e20f34959584d35` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-CONTINUITY-CHECKLIST | `./CONTINUITY_CHECKLIST.md` | `fd7a8da566838d96e45fa1d4b3f0f262ee992ef362596d98dcc9775534827950` | `2026-02-17T00:00:00Z` | `sha256sum` |
| UKS-HANDOFF-LOGS-README | `./HANDOFF_LOGS/README.md` | `e821a4d45e9bc1cb481e08b605b918b0cccb17a97bd47e6956f90b011ab08f13` | `2026-02-17T00:00:00Z` | `sha256sum` |
