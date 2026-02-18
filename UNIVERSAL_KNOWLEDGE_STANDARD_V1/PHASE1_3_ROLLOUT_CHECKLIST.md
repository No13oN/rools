# Фаза 1.3: Rollout Checklist (впровадження Data Contract)

## 1) Мета
Перевести активні контури на `OHLCV_BASE_V1` поетапно і контрольовано.

Базові документи:
1. `/Users/sergej13/Xzone/KNOWLEDGE_Architecture/PHASE1_DATA_CONTRACT_TRADING_V1.md`
2. `/Users/sergej13/Xzone/KNOWLEDGE_Architecture/PHASE1_1_DATASET_MAPPING_TABLES.md`
3. `/Users/sergej13/Xzone/KNOWLEDGE_Architecture/PHASE1_2_DATA_VALIDATION_PROFILE.md`

## 2) Кроки впровадження

## Step 1: Freeze scope
1. Зафіксувати список датасетів, що реально використовуються у train/research.
2. Зафіксувати цільовий режим валідації (`STRICT` або `BALANCED`).

Gate:
Список датасетів затверджений і не змінюється до завершення rollout.

## Step 2: Schema classifier
1. Кожен датасет отримує schema-type (`A/B/C/D/E` з контракту).
2. Для невідомої схеми запуск блокується.

Gate:
100% датасетів класифіковані.

## Step 3: Canonical transform
1. Конвертувати всі активні датасети у `OHLCV_BASE_V1`.
2. Призначити `source/symbol/timeframe` для кожного набору.
3. Нормалізувати `ts` до epoch ms UTC.

Gate:
Вихідні набори мають лише канонічні поля.

## Step 4: Validation run
1. Запустити validation профіль для кожного канонічного набору.
2. Згенерувати статус `PASS/WARN/BLOCK`.
3. Заблокувати набори зі статусом `BLOCK`.

Gate:
Усі training-набори мають статус не нижче `WARN` (або `PASS` для `STRICT`).

## Step 5: Training switch
1. Перемкнути `Argent_13` train pipeline на канонічні набори.
2. Перемкнути `Agent_13_TA_101` research pipeline на ті самі канонічні набори.
3. Заборонити пряме читання legacy CSV в train path.

Gate:
End-to-end тренування відпрацьовує на новому форматі.

## Step 6: Dedup policy
1. Визначити дублікати між `/Users/sergej13/Xzone/data` і `/Users/sergej13/Xzone/Argent_13/data`.
2. Позначити `Tier B` копії як deprecated (через docs-політику).
3. Залишити один канонічний шлях для кожного датасету.

Gate:
Для кожного активного датасету є один canonical path.

## Step 7: Governance lock
1. Додати правило: новий датасет без мапінгу не допускається.
2. Додати правило: новий датасет без validation status не допускається.
3. Будь-яка зміна контракту через ADR.

Gate:
Є формально зафіксовані правила прийому нових даних.

## 3) Ризики і запобіжники
1. Ризик: silent schema drift.
   Запобіжник: classifier + required columns check.
2. Ризик: змішування timezone.
   Запобіжник: примус UTC epoch ms.
3. Ризик: непомітні дублікати.
   Запобіжник: unique key + duplicate threshold.
4. Ризик: просадка якості через synthetic rows.
   Запобіжник: quality flag + threshold profile.

## 4) Щоденний операційний чек
1. Чи є нові CSV без mapping-entry.
2. Чи є нові CSV без validation report.
3. Чи є `BLOCK` статуси в останньому запуску.
4. Чи є datasets, що читаються з `Tier B` замість `Tier A`.

## 5) Definition of Done для Фази 1.3
1. Обидва контури (`Argent_13`, `Agent_13_TA_101`) працюють з `OHLCV_BASE_V1`.
2. Legacy-схеми використовуються тільки через трансформер.
3. Всі активні датасети мають mapping + validation.
4. Дедуп політика застосована, canonical paths зафіксовані.
