---
id: UKS-START
type: entrypoint
status: active
owner: system
created_at: 2026-02-17T00:00:00Z
updated_at: 2026-02-17T00:00:00Z
version: 1.0.0
depends_on:
  - UKS-TASK-STATE
  - UKS-KNOWLEDGE-INDEX
  - UKS-HASH-REGISTRY
  - UKS-HANDOFF-PROTOCOL
hash_policy: canonical-md-v1
---
# Universal Knowledge Start

Це єдина точка входу для будь-якої LLM (Codex, Claude, Gemini, локальна модель).

## MANDATORY_READ_ORDER
1. `./TASK_STATE.md`
2. `./KNOWLEDGE_INDEX.md`
3. `./HANDOFF_PROTOCOL.md`
4. `./CONTINUITY_CHECKLIST.md`
5. За потреби: `./TEMPLATES_LIBRARY.md`

## WRITE_POLICY
- `single_source_of_truth`: дозволено змінювати лише `./TASK_STATE.md` для статусу задачі.
- `append_only`: `./HANDOFF_LOG_INDEX.md` оновлюється лише додаванням нового запису.
- `registry_update_required`: якщо додано/видалено `.md`, обов'язково оновити `./KNOWLEDGE_INDEX.md` і `./HASH_REGISTRY.md`.
- `forbidden`: не використовувати `start.md` як спільний робочий чернетник.

## STATE_SOURCE
- Єдине джерело стану задачі: `./TASK_STATE.md`.

## KNOWLEDGE_POINTERS
- Реєстр документів: `./KNOWLEDGE_INDEX.md`.
- Шаблони: `./TEMPLATES_LIBRARY.md`.

## INTEGRITY_POINTERS
- Реєстр хешів: `./HASH_REGISTRY.md`.

## HANDOFF_ENTRY
- Протокол передачі: `./HANDOFF_PROTOCOL.md`.
- Журнал передач: `./HANDOFF_LOG_INDEX.md`.
- Довідка по логах: `./HANDOFF_LOGS/README.md`.

## TEMPLATE_POLICY
- Нові документи створюються лише за шаблонами з `./TEMPLATES_LIBRARY.md`.
- Для кожного нового документа обов'язковий YAML frontmatter.

## COPY_MODE (перенесення в інший проєкт)
1. Скопіювати папку стандарту як є.
2. Оновити шляхи в `./KNOWLEDGE_INDEX.md` (якщо використовуються абсолютні).
3. Перерахувати `./HASH_REGISTRY.md` після будь-яких змін.
