# Інтеграційна карта: Trading / Quant R&D -> One Project

## 1) Рішення (коротко)
Інтеграція в один проєкт **доцільна** за модульною схемою:
- `Argent_13` -> production core (training + env + risk/runtime baseline)
- `Agent_13_TA_101` -> quant research lab (гіпотези, AL_v01/AL_v02, експерименти)
- `Argent_13C` -> inference/UI layer (лише корисні компоненти)
- `data` -> єдине джерело сирих/нормалізованих рядів
- `docs` -> єдиний source-of-truth для методології

Ціль: не "злити все в одну папку", а зібрати **єдину систему** з чіткими контрактами.

## 2) Поточний стан і оцінка інтегровності

### 2.1 Сильні сторони
- Є готовий PPO-контур у `Argent_13` (env/models/training/tests).
- Є сильний R&D-контур у `Agent_13_TA_101` (AL_v01/AL_v02, тести, дослідження).
- Є docs-база і вже сформований knowledge-каркас у `KNOWLEDGE_Architecture`.

### 2.2 Блокери
- Різні CSV-схеми (schema drift): `open/high/low/close/volume` vs `binance_Open/...`.
- Велика кількість дубльованих docs у кількох папках.
- Нерівна зрілість контурів (`Argent_13` зріліший за `Argent_13C`).
- Об'єм архівів/копій ускладнює підтримку.

### 2.3 Підсумкова оцінка
- Технічна інтегровність: **висока**
- Операційна складність: **середньо-висока**
- Ризик без data contract: **високий**
- Ризик з data contract + поетапним планом: **помірний**

## 3) Цільова архітектура єдиного проєкту

```text
quant_platform/
├── apps/
│   ├── trainer/                 # запуск навчання
│   ├── research_runner/         # експерименти AL_v01/AL_v02
│   └── inference_ui/            # API/UI/dashboard
├── engine/
│   ├── data_contract/           # схеми, валідація, адаптери
│   ├── env/                     # trading env
│   ├── models/                  # actor/critic, policy
│   ├── training/                # PPO loop, callbacks, checkpoints
│   ├── execution/               # paper/sim execution
│   └── risk/                    # risk limits, kill-switch
├── research/
│   ├── hypotheses/
│   ├── experiments/
│   └── notebooks/
├── tests/
├── docs/
├── scripts/
└── archive/
```

Принцип: `research` ніколи не ламає `engine`, а зміни потрапляють у `engine` тільки через інтеграційний gate.

## 4) Що лишити / що об'єднати / що архівувати

### 4.1 Лишити як основу
1. Модулі `src/environment`, `src/models`, `src/training` з `Argent_13`.
2. AL-експериментальні контури з `Agent_13_TA_101` як research-пакети.
3. Валідні тести з обох контурів у спільний `tests/`.

### 4.2 Об'єднати
1. Data ingestion у єдиний `engine/data_contract`.
2. Конфіги запуску в один формат (`yaml` або `toml`, один стандарт).
3. Документацію в один каталог `docs/` без дзеркальних копій.

### 4.3 Архівувати
1. Дублікати docs та версії з однаковим змістом.
2. Старі артефакти експериментів без відтворюваності.
3. Важкі CSV-копії, якщо вони дублюють канонічний датасет.

## 5) План інтеграції по фазах

## Фаза 0: Freeze і рамки
Ціль: стабілізувати вхідний стан.
1. Визначити "активні" гілки/папки.
2. Заборонити хаотичне копіювання між репо.
3. Зафіксувати критерії приймання інтеграції.

Exit criteria:
- Є перелік owner-ів модулів.
- Є зафіксована структура цільового монорепо.

## Фаза 1: Data Contract (критичний пріоритет)
Ціль: уніфікувати формат ринкових даних.
1. Затвердити канонічний schema:
   - `ts`, `symbol`, `open`, `high`, `low`, `close`, `volume`, `source`, `timeframe`.
2. Створити адаптери для legacy-схем (`binance_Open/...`, `okx_*`).
3. Додати валідатор + quality checks (missing, monotonic ts, duplicates).

Exit criteria:
- Будь-який датасет проходить конвертацію в канонічний формат.
- Training pipeline споживає лише канонічний формат.

## Фаза 2: Core Engine Consolidation
Ціль: сформувати єдине production-ядро.
1. Перенести ядро `Argent_13` у `engine/`.
2. Винести загальні інтерфейси env/model/trainer.
3. Підключити unit + smoke tests у CI-процес.

Exit criteria:
- PPO тренування запускається end-to-end на канонічних даних.
- Базові тести стабільно проходять.

## Фаза 3: Research Integration
Ціль: інтегрувати R&D без деградації production.
1. Оформити `AL_v01/AL_v02` як research plugins.
2. Стандартизувати протокол експерименту:
   - config
   - seed
   - dataset snapshot
   - metrics
3. Додати "promotion gate" R&D -> core (лише через benchmark).

Exit criteria:
- Експерименти відтворювані.
- Є формалізований процес переносу ідей у production.

## Фаза 4: Inference/UI Layer
Ціль: прикрутити `Argent_13C` як сервісний шар.
1. Взяти тільки потрібні компоненти інференсу/dashboard.
2. Уніфікувати API контракт (`predict`, `health`, `model_info`).
3. Забезпечити сумісність з артефактами з `engine/training`.

Exit criteria:
- Модель після тренування доступна через стандартний inference endpoint.

## Фаза 5: Docs & Governance
Ціль: прибрати knowledge-хаос.
1. Один канонічний docs-контур (без дзеркал).
2. ADR для всіх критичних рішень (data schema, risk policy, experiment gate).
3. Runbooks: training, rollback, release, incident.

Exit criteria:
- Немає конкуруючих версій інструкцій.
- Новий агент стартує по одному entrypoint-файлу.

## Фаза 6: Hardening і реліз
Ціль: стабільна експлуатація.
1. Ризик-обмеження і kill-switch.
2. Моніторинг метрик (PnL, drawdown, slippage, policy drift).
3. Release process: versioned models + rollback.

Exit criteria:
- Є повторюваний цикл train -> validate -> release -> rollback.

## 6) Мінімальні стандарти якості (must-have)
1. Reproducibility: фіксовані seed + snapshot даних.
2. Observability: логи тренування, метрики ризику, версія моделі.
3. Safety: ліміти позицій, max drawdown stop, аварійне відключення.
4. Governance: ADR + changelog на критичні зміни.

## 7) Порядок пріоритетів (щоб не втратити темп)
1. Data contract
2. Core engine стабільність
3. Research plugin-модель
4. Inference/UI
5. Документаційна чистка

## 8) Що НЕ робити
1. Не змішувати експериментальний код у production без benchmark gate.
2. Не тримати паралельні "майже однакові" docs в різних папках.
3. Не запускати тренування на різних схемах даних без адаптера.
4. Не робити інтеграцію "великим вибухом" за один крок.

## 9) Рекомендований результат цього етапу
Після виконання roadmap має з'явитися один керований контур:
- єдине ядро навчання/інференсу,
- відокремлений і дисциплінований R&D,
- єдиний контракт даних,
- один канонічний knowledge-контур для будь-якої LLM.

## 10) Артефакт Фази 1
Офіційний набір артефактів:
1. `PHASE1_DATA_CONTRACT_TRADING_V1.md` - канонічний контракт схеми.
2. `PHASE1_1_DATASET_MAPPING_TABLES.md` - мапінг конкретних наборів.
3. `PHASE1_2_DATA_VALIDATION_PROFILE.md` - policy порогів `PASS/WARN/BLOCK`.
4. `PHASE1_3_ROLLOUT_CHECKLIST.md` - поетапний rollout у контури.
5. `PHASE1_4_EXECUTION_BACKLOG.md` - черга задач для практичного виконання.
