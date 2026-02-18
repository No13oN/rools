---
id: UKS-HANDOFF-PROTOCOL
type: protocol
status: active
owner: system
created_at: 2026-02-17T00:00:00Z
updated_at: 2026-02-17T00:00:00Z
version: 1.0.0
depends_on:
  - UKS-TASK-STATE
  - UKS-HANDOFF-LOG-INDEX
hash_policy: canonical-md-v1
---
# Model Handoff Protocol

## Purpose
Уніфікувати передачу контексту між моделями без втрати стану, рішень і наступних дій.

## Preconditions
1. `TASK_STATE.md` оновлений до актуального стану.
2. Зміни синхронізовані в `KNOWLEDGE_INDEX.md` (якщо додавалися файли).
3. Хеші оновлені в `HASH_REGISTRY.md`.

## Handoff Steps
1. `State Lock`: зафіксувати поточний статус у `TASK_STATE.md`.
2. `Summary`: сформувати коротке резюме прогресу (що зроблено/що залишилось).
3. `Risks`: зафіксувати ризики і блокери.
4. `Next`: записати 1-3 наступні кроки.
5. `Log`: додати новий рядок у `HANDOFF_LOG_INDEX.md`.

## Handoff Record Minimum
Кожен handoff повинен мати:
1. `handoff_id`
2. `timestamp`
3. `from_model`
4. `to_model`
5. `task_state_ref`
6. `summary`
7. `next_actions`
8. `open_risks`

## Failure Rules
- Якщо не виконано `Preconditions`, handoff вважається невалідним.
- Якщо `TASK_STATE.md` і `HANDOFF_LOG_INDEX.md` суперечать одне одному, джерелом істини є `TASK_STATE.md`.
