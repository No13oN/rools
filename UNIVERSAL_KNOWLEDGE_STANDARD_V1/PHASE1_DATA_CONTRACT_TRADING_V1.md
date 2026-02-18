# Фаза 1: Data Contract Trading v1 (виконуваний стандарт)

## 1) Мета
Уніфікувати всі ринкові дані в один канонічний формат, щоб:
1. `engine/training` споживав лише один тип даних.
2. `research` і `production` працювали на однаковій схемі.
3. Новий агент/LLM міг безпомилково підключитися до даних.

## 2) Сфера дії
Покриває джерела:
1. `/Users/sergej13/Xzone/data`
2. `/Users/sergej13/Xzone/Argent_13/data/raw`
3. `/Users/sergej13/Xzone/Agent_13_TA_101/data`

Поточні виявлені формати:
1. `datetime,timestamp,open,high,low,close,volume,...`
2. `datetime,timestamp,binance_Open,binance_High,binance_Low,binance_Close,binance_Volume`
3. `timestamp,open,high,low,close,volume` (OKX)
4. `close` (симуляційний спрощений формат)
5. multi-timeframe wide (`open_5m`, `open_15m`, `open_1h`, ...)

## 3) Канонічна схема (OHLCV_BASE_V1)

Обов'язкові поля:
1. `ts` (`int64`) - Unix epoch в мілісекундах, UTC.
2. `symbol` (`string`) - формат `BASE/QUOTE`, приклад: `BTC/USDT`.
3. `timeframe` (`string`) - один з: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`.
4. `source` (`string`) - один з: `binance`, `okx`, `synthetic`, `other`.
5. `open` (`float64`)
6. `high` (`float64`)
7. `low` (`float64`)
8. `close` (`float64`)
9. `volume` (`float64`)

Опційні поля:
1. `ts_iso` (`string`) - ISO8601 UTC (для читабельності).
2. `ingest_run_id` (`string`) - ідентифікатор імпорту.
3. `quality_flag` (`string`) - `ok`, `filled`, `suspicious`.

## 4) Інваріанти якості (обов'язково)
1. `high >= max(open, close)`
2. `low <= min(open, close)`
3. `high >= low`
4. `volume >= 0`
5. `ts` строго зростає в межах групи (`symbol`, `timeframe`, `source`)
6. Унікальний ключ: (`symbol`, `timeframe`, `source`, `ts`)
7. Час завжди UTC, без локальних TZ-зсувів

## 5) Правила мапінгу з legacy-форматів

## Випадок A
Вхід:
`datetime,timestamp,open,high,low,close,volume,...`

Мапінг:
1. `ts <- timestamp`
2. `open/high/low/close/volume <- однойменні`
3. `symbol <- з імені файлу або pipeline config`
4. `timeframe <- з імені файлу або pipeline config`
5. `source <- з pipeline config`

## Випадок B
Вхід:
`datetime,timestamp,binance_Open,binance_High,binance_Low,binance_Close,binance_Volume`

Мапінг:
1. `ts <- timestamp`
2. `open <- binance_Open`
3. `high <- binance_High`
4. `low <- binance_Low`
5. `close <- binance_Close`
6. `volume <- binance_Volume`
7. `source <- binance`

## Випадок C (OKX)
Вхід:
`timestamp,open,high,low,close,volume`

Мапінг:
1. Якщо `timestamp` рядок дати -> конвертувати в epoch ms UTC.
2. `open/high/low/close/volume <- однойменні`
3. `source <- okx`

## Випадок D (synthetic close-only)
Вхід:
`close`

Мапінг:
1. Використовувати лише в research-mode.
2. Конвертувати у повний OHLCV через policy:
   - `open=close`, `high=close`, `low=close`, `volume=0`
3. `source <- synthetic`
4. `quality_flag <- filled`

## Випадок E (multi-timeframe wide)
Вхід:
колонки виду `open_5m`, `open_15m`, `open_1h`, ...

Мапінг:
1. Денормалізований wide конвертується в long-формат.
2. На кожен timeframe генерується окремий рядок.
3. У вихідній таблиці лишається лише канонічний набір полів.

## 6) Нормалізація імен файлів
Канон:
`{source}_{symbol_norm}_{timeframe}_{from}_{to}.csv`

Правила:
1. `symbol_norm`: `btc_usdt` (нижній регістр, `_` між base/quote)
2. `source`: `binance|okx|synthetic|other`
3. Дати інтервалу в UTC.

Приклад:
`binance_btc_usdt_1m_20240206_20260217.csv`

## 7) Правила зберігання (v1)
1. Транзитний формат: `csv` (для сумісності з поточним кодом).
2. Канонічний формат (ціль): `parquet` + metadata sidecar.
3. У `training` допускається лише канонічно нормалізований набір.

## 8) Мінімальний контракт API для data loader
Вхід:
1. `symbol`
2. `timeframe`
3. `source` (optional, default any)
4. `ts_from`, `ts_to`

Вихід:
1. `DataFrame` строго в `OHLCV_BASE_V1`
2. Сортування по `ts` ASC
3. Без дублікатів по ключу (`symbol`,`timeframe`,`source`,`ts`)

## 9) Quality Gate перед тренуванням
Pipeline блокується, якщо:
1. Є пропущені обов'язкові поля.
2. Порушені OHLC-інваріанти.
3. `ts` не монотонний.
4. Частка дублікатів > `0.1%`.
5. Частка аномальних свічок > порогу policy.

## 10) Definition of Done для Фази 1
Фаза 1 закрита, якщо:
1. Усі активні датасети конвертуються в `OHLCV_BASE_V1`.
2. `Argent_13` training читає тільки канонічний формат.
3. `Agent_13_TA_101` research читає той самий формат.
4. Є один документ-джерело істини для схеми (цей файл).
5. Валідація даних проходить автоматично перед стартом тренування.

## 11) Політика версіонування контракту
1. Поточна версія: `OHLCV_BASE_V1`.
2. Зміна обов'язкових полів -> нова major-версія (`V2`).
3. Додавання опційних полів -> minor-оновлення (`V1.1`).
4. Будь-яка зміна контракту фіксується через ADR.

## 12) Пов'язані документи Фази 1
1. `PHASE1_1_DATASET_MAPPING_TABLES.md`
2. `PHASE1_2_DATA_VALIDATION_PROFILE.md`
3. `PHASE1_3_ROLLOUT_CHECKLIST.md`
4. `PHASE1_4_EXECUTION_BACKLOG.md`
