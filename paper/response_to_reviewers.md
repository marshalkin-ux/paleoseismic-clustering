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

Literature H&S (p≤0,001, mean≈15,4) — **invalid primary null**, только сравнение.

---

## ERROR 3: Неполная спецификация GK / детектора

**Замечание:** в Methods не указаны точные окна GK, Δt, параметры η.

**Исправлено — §3.3 / `subsubsec:algo-spec` + Table `tab:gk_windows`:**
- **GK:** таблица T(M), R(M) из `GardnerKnopoffDeclustering.WINDOWS`; линейная интерполяция; порядок по убыванию M; aftershock [0,T], foreshock [-T/2,0); haversine km.
- **Series detection:** Δt = 1, 2, 5 лет (шаг 1 год); modern primary Δt=2 г.; min_events=4, min_magnitude=6,5, mean GC>1500 км; greedy `used[]`.
- **η:** η_ij = t_ij · r_ij^1,6 · 10^(−b·m_i); b=1,0; r_ij = GC km.
- **Merge:** 142 окна → 47 merged (`clustering_gc1500.json`: n_series_total_three_epochs=47, modern n=27).

---

## Статус по пунктам

| Замечание | Статус |
|-----------|--------|
| Catalog-calibrated ETAS primary | **Done** — temporal MLE |
| Spatial Ogata (1998) MLE | **Future work** — documented |
| p-value schizophrenia | **Fixed** — three-layer logic |
| GK reproducibility tables | **Added** — code-accurate |
| PDF regeneration | `generate_article_pdf.py`, `generate_article_en_pdf.py` |
