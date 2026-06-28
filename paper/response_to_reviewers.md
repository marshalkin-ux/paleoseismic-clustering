# Ответ рецензентам

## ERROR 1: Literature ETAS вместо catalog-calibrated ETAS

**Замечание:** основной тест с plug-in H&S 2003 (μ=0,008, K=0,08) недействителен — ETAS должна быть откалибрована к каталогу M≥6,5.

**Исправлено:**
- **Первичная null:** temporal Ogata (1988) MLE на **2017 GK mainshocks** (1973–2026), `scripts/calibrate_etas_mle.py` → `results/etas_mle_calibration.json`: μ≈0,097, K≈10⁻⁴, α≈0,25, c=0,001 сут., p≈1,91.
- **Валидация:** `scripts/run_etas_validation.py` → `results/etas_validation.json`: mean=**27,0**, **p_ETAS=1,0** (N_obs=27).
- **WLS** (`calibrate_etas.py`, Appendix B): negative control only — p=1,0, не primary.
- **Literature H&S:** `scripts/run_etas_validation_literature.py` → `results/etas_validation_literature.json` — comparison only; ранее ошибочно использовался как primary.
- **Ограничение:** spatial Ogata (1998) MLE не реализован; temporal MLE — лучший доступный catalog-calibrated null (`docs/future_work_etas_mle.md`).
- Обновлены: `main.tex`, `article_ru.md`, `article_en.md`, abstract, results, discussion, conclusions, `take_home_message.md`, HTML/showcase, PDF-генераторы, `etas_params.py`, `etas_validation.py`.

---

## ERROR 2: Противоречие p-values (abstract vs conclusions)

**Замечание:** abstract с p=0,0001 и p≤0,001 при выводе «гипотеза не подтверждена» читается как шизофрения.

**Исправлено — явная трёхслойная логика** (abstract, §1.1, results, discussion, conclusions):

| Тест | Что означает p | Связь с глобальными сериями |
|------|----------------|----------------------------|
| Permutation p=0,0001 | Отвергает H₀: пуассоновские/независимые времена | Временная кластеризация; **не** доказательство глобальных цепочек |
| ETAS p=1,0 (temporal MLE) | **Не** отвергает H₀: N_series ≤ синтетика calibrated ETAS | N_obs=27 = mean=27; детектор согласован с null; **не** подтверждает гипотезу |
| Глобальные серии | **Не подтверждена** | Первичное научное утверждение — отрицательный результат |

Выводы **начинаются** с: гипотеза о мультирегиональных глобальных сериях **не подтверждена**; permutation и ETAS — разные под-гипотезы.

Literature H&S (p≤0,001, mean≈15,4) — **invalid primary null**, только сравнение (историческая сноска в Introduction).

---

## ERROR 4: Annotation schizophrenia (RU/EN abstracts, §5.5, Appendix B)

**Замечание:** противоречивые RU/EN abstracts (H&S primary vs MLE p=1.0); устаревшее правило Appendix B «не цитировать p_ETAS=1.0».

**Исправлено:**
- **Abstracts (RU+EN):** minimal structure — catalog N=4267/2041 modern, detector 27 candidates, ETAS mean=27.0 p_ETAS=1.0; без permutation p и без Bird; ограничение §5.6.
- **H&S 2003:** удалён из Methods, Results, Conclusions, §5.5, hypothesis table; оставлен только в Introduction как историческая сноска.
- **Appendix B:** удалено правило «do not cite p_ETAS=1.0»; WLS = coupling illustration, не primary.
- **§5.5–5.6:** MLE primary; **bold** temporal-only limitation.
- Синхронизированы: `main.tex`, `article_ru.md`, `article_en.md`, `take_home_message.md`, `index.html`, `project_showcase.html`; PDF перегенерированы.

---

## ERROR 3: Неполная спецификация GK / детектора

**Замечание:** в Methods не указаны точные окна GK, Δt, параметры η.

**Исправлено — §3.3 / `subsubsec:algo-spec` + Table `tab:gk_windows`:**
- **GK:** таблица T(M), R(M) из `GardnerKnopoffDeclustering.WINDOWS`; линейная интерполяция; порядок по убыванию M; aftershock [0,T], foreshock [-T/2,0); haversine km.
- **Series detection:** Δt = 1, 2, 5 лет (шаг 1 год); modern primary Δt=2 г.; min_events=4, min_magnitude=6,5, mean GC>1500 км; greedy `used[]`.
- **η:** η_ij = t_ij · r_ij^1,6 · 10^(−b·m_i); b=1,0; r_ij = GC km.
- **Merge:** 142 окна → 47 merged (`clustering_gc1500.json`: n_series_total_three_epochs=47, modern n=27).

---

## ERROR 5: Overstatement — temporal ETAS vs spatial linkage

**Замечание:** §5.6 честно указывает temporal-only ETAS, но заголовок/введение заявляют «spatiotemporal clustering», а выводы — «global series hypothesis NOT supported». Temporal ETAS (p=1.0) тестирует лишь временную кластеризацию в 2-летних окнах, **не** физическую связанность географически разнесённых событий (>1500 км GC). Без spatial kernel r^{-d} тест не отвечает на вопрос пространственной связи.

**Исправлено — скромные канонические выводы (RU+EN):**

- RU: «Мы не обнаружили аномалий временной кластеризации сверх калиброванной ETAS. Пространственная компонента не моделировалась, поэтому вопрос о физической связанности удалённых событий остаётся открытым для будущих исследований.»
- EN: «We found no anomalous temporal clustering beyond catalog-calibrated ETAS. The spatial component was not modeled; the question of physical linkage among geographically remote events remains open for future work.»

**Изменения:**
- Abstracts (RU/EN): modest conclusion + MLE p=1.0; без permutation p; MLE primary, WLS App. B only.
- §6 Conclusions / Discussion: различие established (N=27 temporal ETAS) vs not tested (spatial linkage).
- §1.1 Introduction: scope paragraph — primary ETAS = temporal excess; spatial linkage = future work.
- Hypothesis table row (c): «Not tested by temporal-only ETAS; detector candidates lack validated physical mechanism; spatial null open».
- §5.6: bold temporal limitation + explicit sentence that «global series rejected» would require spatial ETAS.
- Синхронизированы: `take_home_message.md`, `index.html`, `project_showcase.html`, PDF-генераторы.

---

## Статус по пунктам

| Замечание | Статус |
|-----------|--------|
| Catalog-calibrated ETAS primary | **Done** — temporal MLE |
| Spatial Ogata (1998) MLE | **Future work** — documented |
| p-value schizophrenia | **Fixed** — three-layer logic |
| GK reproducibility tables | **Added** — code-accurate |
| Temporal vs spatial scope | **Fixed** — modest conclusions |
