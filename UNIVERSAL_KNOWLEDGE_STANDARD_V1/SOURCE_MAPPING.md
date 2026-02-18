# Source Mapping (Джерело -> Канон)

## Призначення
Цей файл показує, як початкові матеріали були зведені у канонічний набір Markdown-документів.

## Мапінг
| Початковий файл | Статус | Куди увійшло | Нотатка |
|---|---|---|---|
| `Architecture_Plan_Sofia13.md.docx` | Злито | `ARCHITECTURE.md`, `MIGRATION_RUNBOOK.md` | Базова структура, KPI, міграційні фази |
| `Architecture_Plan_Sofia13.md (1).docx` | Дубль/перевірка | `ARCHITECTURE.md` (непрямо) | Семантичний дубль базового плану |
| `Architecture_Plan_Sofia13.md (2).docx` | Варіант форматування | `ARCHITECTURE.md` (непрямо) | Той самий зміст з інакшим форматуванням |
| `Architecture_Critique_and_V2.md.docx` | Злито | `ARCHITECTURE.md`, `MIGRATION_RUNBOOK.md`, `AGENT_RULES.md` | Критика V1, підхід V2, inbox/Git-Ops акценти |
| `Architecture_Critique_and_V2.md (1).docx` | Варіант форматування | `ARCHITECTURE.md` (непрямо) | Близький вміст, відмінності у верстці |
| `Migration_Checklist_and_Rules.md.docx` | Злито | `MIGRATION_RUNBOOK.md`, `AGENT_RULES.md` | Чекліст міграції та директиви для агентів |
| `Migration_Checklist_and_Rules.md (1).docx` | Дубль | `MIGRATION_RUNBOOK.md`, `AGENT_RULES.md` (непрямо) | Дубль основного checklist-файлу |
| `setup_sofia_arch.py` | Проаналізовано | `MIGRATION_RUNBOOK.md` (концептуально) | Notebook-JSON з міграційною логікою, не канонічний runtime |
| `universal_agent_arch.py` | Проаналізовано | `ARCHITECTURE.md`, `AGENT_RULES.md` (концептуально) | Notebook-JSON з bootstrap-шаблонами і правилами |

## Канонічний набір після синтезу
1. `ARCHITECTURE.md`
2. `MIGRATION_RUNBOOK.md`
3. `AGENT_RULES.md`
4. `SYNTHESIS_DOCS_CONSOLIDATION.md`
5. `SOURCE_MAPPING.md`

## Політика щодо сирих джерел
- Початкові `.docx` і notebook-JSON `.py` не входять у активний контур після синтезу.
- Для аудиту достатньо канонічних файлів + цього mapping-файлу.
