# Фаза 1.1: Dataset Mapping Tables (конкретні набори)

## 1) Мета
Цей файл деталізує застосування контракту `OHLCV_BASE_V1` до конкретних датасетів.

Базовий контракт:
`/Users/sergej13/Xzone/KNOWLEDGE_Architecture/PHASE1_DATA_CONTRACT_TRADING_V1.md`

## 2) Канонічний пріоритет джерел
1. `Tier A` (канон): `/Users/sergej13/Xzone/data`
2. `Tier B` (дзеркало/кандидат на дедуп): `/Users/sergej13/Xzone/Argent_13/data`
3. `Tier C` (R&D-джерела): `/Users/sergej13/Xzone/Agent_13_TA_101/data`

Правило:
`Tier B` використовується лише якщо відповідного файлу немає в `Tier A`.

## 3) Таблиця мапінгу: набори з `data` і `Argent_13/data`

| Dataset pattern | Вхідна схема | Мапінг у `OHLCV_BASE_V1` | `source` | `symbol` | `timeframe` | Примітка |
|---|---|---|---|---|---|---|
| `binance_btc_usdt_1m_2y.csv` | `datetime,timestamp,binance_Open,binance_High,binance_Low,binance_Close,binance_Volume` | `ts=timestamp`, `open=binance_Open`, `high=binance_High`, `low=binance_Low`, `close=binance_Close`, `volume=binance_Volume` | `binance` | `BTC/USDT` | `1m` | Основний історичний ряд |
| `raw/binance_btc_usdt_1m.csv` | `datetime,timestamp,binance_Open,binance_High,binance_Low,binance_Close,binance_Volume` | same as above | `binance` | `BTC/USDT` | `1m` | Raw-джерело |
| `raw/binance_btc_usdt_1h.csv` | `datetime,timestamp,binance_Open,binance_High,binance_Low,binance_Close,binance_Volume` | same as above | `binance` | `BTC/USDT` | `1h` | Raw-джерело |
| `binance_btc_usdt_5m.csv` | `datetime,timestamp,open,high,low,close,volume,...` | `ts=timestamp`, `open=open`, `high=high`, `low=low`, `close=close`, `volume=volume` | `binance` | `BTC/USDT` | `5m` | Індикатори (`rsi/sma/...`) не входять у base-контракт |
| `binance_btc_usdt_15m.csv` | очікується `open/high/low/close/volume` або `binance_*` | мапінг за виявленим header | `binance` | `BTC/USDT` | `15m` | Потрібна автоматична класифікація schema-type |
| `binance_btc_usdt_1h.csv` | очікується `open/high/low/close/volume` або `binance_*` | мапінг за виявленим header | `binance` | `BTC/USDT` | `1h` | Потрібна автоматична класифікація schema-type |
| `binance_btc_usdt_1h_from_1m.csv` | очікується OHLCV + `timestamp` | стандартний мапінг до `ts/open/high/low/close/volume` | `binance` | `BTC/USDT` | `1h` | Resampled-набір |
| `multi_tf_5m_base.csv` | wide multi-timeframe (`open_5m`, `open_15m`, `open_1h`, ...) | конвертація wide -> long; генерація рядків по кожному timeframe | `binance` | `BTC/USDT` | `5m/15m/1h` | Окремий обов'язковий transformer |

## 4) Таблиця мапінгу: набори з `Agent_13_TA_101/data`

| Dataset | Вхідна схема | Мапінг у `OHLCV_BASE_V1` | `source` | `symbol` | `timeframe` | Примітка |
|---|---|---|---|---|---|---|
| `okx_BTC_USDT_1m.csv` | `timestamp,open,high,low,close,volume` | `ts=parse(timestamp->epoch_ms_utc)`, `open/high/low/close/volume` one-to-one | `okx` | `BTC/USDT` | `1m` | `timestamp` має бути нормалізований до UTC epoch ms |
| `okx_BTC_USDT_5m.csv` | `timestamp,open,high,low,close,volume` | same as above | `okx` | `BTC/USDT` | `5m` | same |
| `okx_BTC_USDT_1H.csv` | `timestamp,open,high,low,close,volume` | same as above | `okx` | `BTC/USDT` | `1h` | `1H` у назві нормалізується в `1h` |
| `binance_btc_usdt_1m_2y.csv` | `datetime,timestamp,binance_*` | стандартний Binance-мапінг | `binance` | `BTC/USDT` | `1m` | дубль з Tier A |
| `simulated_market_data.csv` | `close` | policy fill: `open=close`, `high=close`, `low=close`, `volume=0`, `quality_flag=filled` | `synthetic` | `BTC/USDT` (або з config) | з config | тільки для research |

## 5) Обов'язкова нормалізація метаданих
1. `symbol` не витягувати з колонок, якщо їх немає; брати з `filename parser` або `pipeline config`.
2. `timeframe` парсити з назви файлу (`1m`, `5m`, `15m`, `1h`, ...).
3. `source` парсити з префікса файлу (`binance_`, `okx_`, ...).

## 6) Рішення по дублях між `data` і `Argent_13/data`
1. Якщо `sha256` однаковий -> лишається лише Tier A-посилання.
2. Якщо дані різні, але назва однакова -> додати суфікс діапазону дат у канонічній назві.
3. Для тренування за замовчуванням використовувати тільки Tier A.

## 7) Шаблон запису про мапінг (для нових датасетів)
```md
Dataset:
Path:
Header:
Detected schema type:
Canonical mapping:
symbol/timeframe/source inference:
Quality issues found:
Decision:
```

## 8) Definition of Done для Фази 1.1
1. Кожен активний CSV набір має рядок у mapping-таблиці.
2. Для кожного набору визначені `source/symbol/timeframe`.
3. Позначені дублікати та встановлений пріоритет джерела.
