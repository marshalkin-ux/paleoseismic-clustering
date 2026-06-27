# Ответ рецензентам (кратко)

## ETAS-null

- **Первичная null для выводов:** литература H&S 2003 (μ=0,008, K=0,08), p_ETAS≤0,001, mean≈15,4 — статистически реальный избыток локальной афтершоковой кластеризации, **не** телесейсмика.
- **WLS/MLE каталог-калибровка:** перенесена в **Приложение B** как негативный контроль воспроизводимости; **удалена** из аннотации, Results, Discussion, Conclusions, hero/KPI (`index.html`, `project_showcase.html`), PDF-генераторов.
- **Spatial Ogata MLE:** не реализован — **остаётся future work** (`docs/future_work_etas_mle.md`).

## Ограничения

- Таблица «ограничение → шаг → влияние на вывод» (`tab:limitations_impact` / §5.6 в markdown).
- **Добавлен prose-анализ** (2–3 абзаца RU+EN): η₀ → GK-метки, N=27 стабилен; b=0,911 → N=27, upstream не пересчитан; нет spatial MLE → только лит. null; 142 окна → либеральность; p≤0,001 → локальный избыток, не опровержение гипотезы глобальных серий.
- b=1.0 vs 0.911: `sensitivity_b_eta0.json` → N=27/27; разделение scope η₀ (declustering vs `global_series`).

## Метрика

- Первичный конвейер: **только great-circle**; тектоника Bird — одно предложение + deprecated diagnostic (приложение); длинное описание pipeline удалено из Methods.

## PDF

- Исправлена регистрация шрифтов DejaVu (Cyrillic-safe); `safe_text` больше не ломает кириллицу; таблицы с переносом в ячейках.

## Не исправлено → статус

| Замечание рецензента | Сделано | Остаётся |
|----------------------|---------|----------|
| Spatial Ogata (1998) MLE с ДИ | Документировано как limitation; лит. null в основном тексте | **Полная реализация** — future work |
| Publication-grade catalog ETAS fit | WLS/MLE только Appendix B | Spatial MLE |
| η₀ / b upstream sensitivity | Таблица + prose; N=27 стабилен на `global_series` | Перезапуск `identify_clusters()` при b=0,911 |
| Тектоническая метрика как innovation | Удалена из primary pipeline | Diagnostic figures в приложении |
| p_ETAS=1,0 как главная фальсификация | Убрано из narrative; Appendix B only | — |
| 142 окна → либеральность | Prose + §5.7 | Ужесточение search space — future work |
