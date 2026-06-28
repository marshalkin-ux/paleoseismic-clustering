# Ответ рецензентам (кратко)

## Пакет правок: формальные гипотезы, спецификация алгоритмов, dedupe Results/Discussion

### 1. Исследовательский вопрос + H₀/H₁/Ha

- Добавлен §1.1 (RU/EN) и таблица `tab:hypotheses` в `main.tex`: RQ, permutation, ETAS H&S, гипотеза глобальных серий, негативный контроль WLS (строка d).
- Расширен `Hypothesis Separation` / §3.7–3.8 в markdown.
- Синхронизированы `take_home_message.md`.

### 2. Спецификация алгоритмов (§3.3.1)

- Новый подраздел с деталями из `declustering.py`, `clustering.py`, `pipeline_v2.py`, `run_clustering_gc1500.py`: GK WINDOWS, η NN, Union–Find, `global_series`, merge 142→47, stopping rule.

### 3. Dedupe Results vs Discussion

- §4 (Results): **только числа** — таблицы, p-values, пространственное описание; длинные ETAS-абзацы удалены; ссылка «Интерпретация — §5.1–5.4».
- §5 (Discussion): интерпретация сохранена; дублирующие ETAS-параграфы в Results убраны.

### 4. η₀ в Table 3

- Расширена ячейка: KDE-долина ≈7,1×10⁻⁶, слабая бимодальность, N=27 стабилен (`global_series` без η₀), влияние только на GK/ZBZ-метки.

### 5. Permutation — методологическое заявление

- Выделено в Methods (`main.tex` §Permutation test) и §3.7/3.8 markdown: p=0,0001 отвергает **только** пуассоновские времена (Ogata 1988).

### 6. Тектоническая метрика

- Явно: Bird 2003 **исключена из primary**; провал валидации — непригодность метрики, **не** доказательство против глобальных серий.

### 7. Appendix B в выводах

- Один абзац в Discussion §5.2 и Conclusions §6: WLS p=1,0, mean=27; supports negative conclusion; WLS invalid; лит. H&S primary; spatial MLE — future work.

### 8. MLE / Limitations

- Честно: catalog spatial Ogata MLE не реализован; литературная null до MLE; отмечено в Limitations и §1.1.

### PDF

- Перегенерированы `article_ru.pdf`, `article_en.pdf`.

## ETAS-null (ранее)

- **Первичная null:** литература H&S 2003; WLS — только Приложение B.
- **Spatial Ogata MLE:** future work (`docs/future_work_etas_mle.md`).

## Не исправлено → статус

| Замечание | Статус |
|-----------|--------|
| Spatial Ogata (1998) MLE с ДИ | Документировано; лит. null в основном тексте | **Полная реализация** — future work |
| η₀ / b upstream | Таблица + prose + overlap JSON | Перезапуск GK/ZBZ при b=0,911 |
| 142 окна → либеральность | Prose + §5.7 + algorithm spec | Ужесточение search space — future work |
