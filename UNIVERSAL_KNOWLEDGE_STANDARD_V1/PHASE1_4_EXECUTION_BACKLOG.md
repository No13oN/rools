# Фаза 1.4: Execution Backlog (з документів у задачі)

## 1) Призначення
Цей backlog перетворює Фазу 1 на набір конкретних задач для виконання.

Вхідні документи:
1. `PHASE1_DATA_CONTRACT_TRADING_V1.md`
2. `PHASE1_1_DATASET_MAPPING_TABLES.md`
3. `PHASE1_2_DATA_VALIDATION_PROFILE.md`
4. `PHASE1_3_ROLLOUT_CHECKLIST.md`

## 2) Черга задач (пріоритет P0 -> P2)

| ID | Пріоритет | Задача | Власник контуру | Артефакт результату | Критерій приймання |
|---|---|---|---|---|---|
| DC-001 | P0 | Реалізувати schema classifier (`A/B/C/D/E`) | `Argent_13` | classifier report | 100% активних CSV класифіковано |
| DC-002 | P0 | Реалізувати transformer у `OHLCV_BASE_V1` | `Argent_13` | normalized datasets | усі активні набори мають канонічні поля |
| DC-003 | P0 | Реалізувати timestamp normalizer в epoch ms UTC | `Argent_13` + `Agent_13_TA_101` | ts-normalization log | відсутні локальні TZ, `ts` уніфікований |
| DC-004 | P0 | Реалізувати validation gate (`PASS/WARN/BLOCK`) | `Argent_13` | validation reports | `BLOCK` реально зупиняє pipeline |
| DC-005 | P0 | Перемкнути train loader на канонічну схему | `Argent_13` | training run evidence | train не читає legacy напряму |
| DC-006 | P1 | Перемкнути research loader на канонічну схему | `Agent_13_TA_101` | research run evidence | research працює на `OHLCV_BASE_V1` |
| DC-007 | P1 | Дедуп між `data` і `Argent_13/data` | shared | dedup registry | для кожного датасету один canonical path |
| DC-008 | P1 | Додати override policy log | shared | override audit log | кожен override має trace |
| DC-009 | P2 | Підготовка міграції CSV -> Parquet | shared | conversion plan | визначені критерії cutover |

## 3) Рекомендований порядок виконання
1. `DC-001`
2. `DC-002`
3. `DC-003`
4. `DC-004`
5. `DC-005`
6. `DC-006`
7. `DC-007`
8. `DC-008`
9. `DC-009`

## 4) Мінімальні докази виконання (evidence pack)
1. Список оброблених датасетів з schema-type.
2. Звіти валідації до/після нормалізації.
3. Лог одного успішного train run на канонічних даних.
4. Лог одного успішного research run на канонічних даних.
5. Реєстр дедуп-рішень по файлах.

## 5) Stop conditions
1. Будь-який `BLOCK` у `STRICT` без виправлення.
2. Виявлений новий dataset без mapping-entry.
3. Виявлений train path, що читає legacy CSV напряму.

## 6) Definition of Done для Фази 1.4
1. P0 задачі закриті.
2. Є evidence pack.
3. Фаза 1 готова до переходу у Фазу 2 (`Core Engine Consolidation`).
