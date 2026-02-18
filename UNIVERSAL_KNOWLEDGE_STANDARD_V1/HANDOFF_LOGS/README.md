---
id: UKS-HANDOFF-LOGS-README
type: docs
status: active
owner: system
created_at: 2026-02-17T00:00:00Z
updated_at: 2026-02-17T00:00:00Z
version: 1.0.0
depends_on:
  - UKS-HANDOFF-LOG-INDEX
hash_policy: canonical-md-v1
---
# Handoff Logs Directory

Ця директорія призначена для file-per-handoff документів.

## Naming
- `handoff_{YYYYMMDD_HHMMSS}_{from}_{to}.md`

## Minimal Sections
1. Summary
2. Completed Work
3. Next Actions
4. Risks
5. References

## Policy
- Не редагувати старі handoff-файли.
- Кожен новий handoff-файл має бути зареєстрований у `../HANDOFF_LOG_INDEX.md`.
