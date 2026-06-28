# Ответ рецензентам (кратко)

## ETAS-null

- **Первичная null для выводов:** литература H&S 2003 (μ=0,008, K=0,08), p_ETAS≤0,001, mean≈15,4 — отклонение от литературной ETAS указывает на кластеризацию, которую эта null не полностью описывает; пространственный анализ остатков ETAS **не проводился**; отклонение **не интерпретируется** как доказательство глобальных серий; циркум-Тихоокеан; возможные региональные афтершоки/неполнота/либеральность (142 окна); не глобальные цепочки.
- **WLS/MLE каталог-калибровка:** перенесена в **Приложение B** как негативный контроль воспроизводимости; **удалена** из аннотации, Results, Discussion, Conclusions, hero/KPI (`index.html`, `project_showcase.html`), PDF-генераторов.
- **Spatial Ogata MLE:** не реализован — **обоснованный выбор** временной лит. null H&S 2003 на глобальном масштабе (24 задержки, нет spatial kernel); полная spatial MLE — **future work** (`docs/future_work_etas_mle.md`).

## Ограничения

- Таблица «ограничение → шаг → влияние на вывод» (`tab:limitations_impact` / §5.6 в markdown).
- **Добавлен prose-анализ** (2–3 абзаца RU+EN): η₀ → GK-метки, N=27 стабилен; b=0,911 → N=27, Jaccard наборов серий=1,0, upstream ~9,8% смена меток (`sensitivity_b0911_series_overlap.json`); нет spatial MLE → лит. null как reasoned choice; 142 окна → либеральность; p≤0,001 → кластеризация вне ETAS, **не** доказательство глобальных серий.
- b=1.0 vs 0.911: `sensitivity_b_eta0.json` → N=27/27; совпадение N **не доказывает** идентичность кандидатов; разделение scope η₀ (declustering vs `global_series`).

## Метрика

- Первичный конвейер: **только great-circle**; тектоника Bird — одно предложение + deprecated diagnostic (приложение); длинное описание pipeline удалено из Methods.

## PDF

- Исправлена регистрация шрифтов DejaVu (Cyrillic-safe); `safe_text` больше не ломает кириллицу; таблицы с переносом в ячейках; Table 1 lat/lon formatting.

## Не исправлено → статус

| Замечание рецензента | Сделано | Остаётся |
|----------------------|---------|----------|
| Spatial Ogata (1998) MLE с ДИ | Документировано как reasoned limitation; лит. null в основном тексте | **Полная реализация** — future work |
| Publication-grade catalog ETAS fit | WLS/MLE только Appendix B | Spatial MLE |
| η₀ / b upstream sensitivity | Таблица + prose + `sensitivity_b0911_series_overlap.json` | Перезапуск полного GK/ZBZ-пайплайна при b=0,911 |
| Тектоническая метрика как innovation | Удалена из primary pipeline | Diagnostic figures в приложении |
| p_ETAS=1,0 как главная фальсификация | Убрано из narrative; Appendix B only | — |
| 142 окна → либеральность | Prose + §5.7 | Ужесточение search space — future work |
