# ARHITECRO Checklist-Only (EN/UA)

Status: Protected
Protection: Do not modify without explicit owner approval.

Last updated: 2026-02-18  
Canonical base: `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/`

---

## A) Global Release Gate (mandatory)

- [ ] EN: Install dependencies: `pip install jsonschema pyyaml tiktoken`  
  UA: Встановити залежності: `pip install jsonschema pyyaml tiktoken`
- [ ] EN: Run strict validator: `python3 scripts/validate_lds.py --strict`  
  UA: Запустити строгий валідатор: `python3 scripts/validate_lds.py --strict`
- [ ] EN: Run tests: `python3 -m unittest discover -s tests -p 'test_*.py' -v`  
  UA: Запустити тести: `python3 -m unittest discover -s tests -p 'test_*.py' -v`
- [ ] EN: Block release if any command fails  
  UA: Блокувати реліз, якщо будь-яка команда завершилась помилкою

---

## B) Scenario 1 — New Project (Greenfield)

- [ ] EN: Create new project root  
  UA: Створити новий корінь проєкту
- [ ] EN: Copy full LDS base from `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/`  
  UA: Скопіювати повну LDS-базу з `/Users/sergej13/Xzone/rools/LDS_PROJECT_ROOT/`
- [ ] EN: Keep canonical structure unchanged on first pass  
  UA: Не змінювати канонічну структуру на першому проході
- [ ] EN: Update metadata (`owner`, `doc_id`, `last_updated`) and ownership file  
  UA: Оновити метадані (`owner`, `doc_id`, `last_updated`) і ownership-файл
- [ ] EN: Run strict gate + tests and record result  
  UA: Запустити strict gate + тести і зафіксувати результат
- [ ] EN: Enable CI in repository root  
  UA: Увімкнути CI у корені репозиторію

Done criteria:
- [ ] EN: Validation PASS  
  UA: Валідація PASS
- [ ] EN: Tests PASS  
  UA: Тести PASS

---

## C) Scenario 2 — Integration of One Existing Project (Brownfield)

- [ ] EN: Freeze old project changes  
  UA: Заморозити зміни старого проєкту
- [ ] EN: Rename old root to `<project_name>_archive`  
  UA: Перейменувати старий корінь у `<project_name>_archive`
- [ ] EN: Create clean new root `<project_name>`  
  UA: Створити чистий новий корінь `<project_name>`
- [ ] EN: Copy LDS base to new root  
  UA: Скопіювати LDS-базу в новий корінь
- [ ] EN: Inventory archive artifacts (docs/contracts/scripts/tests)  
  UA: Провести інвентаризацію архіву (docs/contracts/scripts/tests)
- [ ] EN: Map artifacts to canonical targets (`docs`, `contracts`, `governance`, `legacy`)  
  UA: Замапити артефакти в канонічні цілі (`docs`, `contracts`, `governance`, `legacy`)
- [ ] EN: Normalize terminology and frontmatter before import  
  UA: Нормалізувати термінологію і frontmatter перед імпортом
- [ ] EN: Run strict gate + tests after migration batch  
  UA: Запускати strict gate + тести після кожного батчу міграції
- [ ] EN: Keep archive immutable  
  UA: Тримати архів незмінним

Done criteria:
- [ ] EN: No critical orphan artifacts outside canonical structure  
  UA: Немає критичних сирітських артефактів поза канонічною структурою
- [ ] EN: Validation PASS and Tests PASS  
  UA: Validation PASS і Tests PASS

---

## D) Scenario 3 — Integration of Multiple Projects

- [ ] EN: Freeze all source projects  
  UA: Заморозити всі вихідні проєкти
- [ ] EN: Rename roots to archives (`_archive1`, `_archive2`, ...)  
  UA: Перейменувати корені в архіви (`_archive1`, `_archive2`, ...)
- [ ] EN: Create one clean target root  
  UA: Створити один чистий цільовий корінь
- [ ] EN: Copy LDS base to target root  
  UA: Скопіювати LDS-базу в цільовий корінь
- [ ] EN: Build global inventory and duplicate/conflict map  
  UA: Побудувати глобальну інвентаризацію і мапу дублікатів/конфліктів
- [ ] EN: Create integration plan by priority (security -> data contracts -> runbooks -> reference docs)  
  UA: Побудувати план інтеграції за пріоритетом (security -> data contracts -> runbooks -> reference docs)
- [ ] EN: Migrate in batches with validation checkpoint after each batch  
  UA: Мігрувати батчами з checkpoint-валідацією після кожного батчу
- [ ] EN: Record conflict resolution decisions  
  UA: Фіксувати рішення щодо конфліктів
- [ ] EN: Run full strict gate + tests at final stage  
  UA: На фіналі запустити повний strict gate + тести

Done criteria:
- [ ] EN: Single canonical LDS root exists  
  UA: Існує єдиний канонічний LDS-корінь
- [ ] EN: Conflict resolution log exists  
  UA: Існує журнал вирішення конфліктів
- [ ] EN: Validation PASS and Tests PASS  
  UA: Validation PASS і Tests PASS

---

## E) Hard Prohibitions

- [ ] EN: No direct copy from archive to production docs without normalization  
  UA: Заборонено пряме копіювання з архіву в production docs без нормалізації
- [ ] EN: No “big bang” migration without staged checkpoints  
  UA: Заборонена “big bang” міграція без поетапних checkpoint
- [ ] EN: No release if strict validation fails  
  UA: Заборонений реліз, якщо strict validation не пройдено
