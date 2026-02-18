# Фаза 1.2: Data Validation Profile (block/warn policy)

## 1) Мета
Стандартизувати, коли pipeline:
1. блокується (`BLOCK`),
2. запускається з попередженням (`WARN`),
3. проходить без зауважень (`PASS`).

## 2) Режими якості
1. `STRICT` - для production training/release.
2. `BALANCED` - для regular R&D.
3. `RESEARCH_FAST` - для швидких гіпотез (не для релізу).

## 3) Матриця правил

| Check | Метрика | STRICT | BALANCED | RESEARCH_FAST | Рішення |
|---|---|---|---|---|---|
| Required columns missing | count | `>0` | `>0` | `>0` | `BLOCK` |
| OHLC invariants fail | % rows | `>0.00%` | `>0.01%` | `>0.05%` | `BLOCK` |
| Negative volume | % rows | `>0.00%` | `>0.00%` | `>0.01%` | `BLOCK` |
| Duplicate key rows | % rows | `>0.10%` | `>0.50%` | `>1.00%` | `BLOCK` |
| Non-monotonic ts | count segments | `>0` | `>0` | `>1` | `BLOCK` |
| Missing bars (gaps) | % expected bars | `>1.00%` | `>3.00%` | `>7.00%` | `WARN/BLOCK` |
| Outlier candle range | % rows | `>0.50%` | `>1.00%` | `>3.00%` | `WARN` |
| Zero volume bars | % rows | `>5.00%` | `>10.00%` | `>20.00%` | `WARN` |
| Synthetic filled rows | % rows | `>0.00%` | `>10.00%` | `>50.00%` | `BLOCK/WARN` |

Примітка:
`WARN/BLOCK` означає `BLOCK` у `STRICT`, `WARN` у інших режимах.

## 4) Алгоритм рішення
1. Якщо спрацювало будь-яке правило `BLOCK` -> статус `BLOCK`.
2. Якщо `BLOCK` немає, але є `WARN` -> статус `WARN`.
3. Якщо немає ні `BLOCK`, ні `WARN` -> статус `PASS`.

## 5) Обов'язкові checks перед train
1. Schema check (`OHLCV_BASE_V1`).
2. Key uniqueness (`symbol,timeframe,source,ts`).
3. Monotonic timestamp.
4. OHLC invariants.
5. Gap analysis відносно timeframe.

## 6) Формат звіту валідації
```md
Validation Run ID:
Dataset:
Mode: STRICT|BALANCED|RESEARCH_FAST
Status: PASS|WARN|BLOCK
Checks:
- name:
  metric:
  threshold:
  result:
Actions:
- ...
```

## 7) Політика дій після статусу
1. `PASS` -> training дозволено.
2. `WARN` -> training дозволено тільки в R&D або з явним `override`.
3. `BLOCK` -> training заборонено до виправлення даних.

## 8) Override policy
1. Override дозволений лише для `R&D` режиму.
2. Override обов'язково фіксується в логах.
3. Override заборонений для `STRICT`.

## 9) Definition of Done для Фази 1.2
1. Є єдина таблиця порогів (`this file`).
2. Кожен training run має validation status.
3. Будь-який `BLOCK` автоматично зупиняє pipeline.
