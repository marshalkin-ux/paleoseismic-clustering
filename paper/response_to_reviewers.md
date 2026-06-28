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

---

## ROUND 2: In-sample ETAS, train/test, FDR, contribution reframe

**Замечание:** p_ETAS=1.0 tautological (in-sample calibration + same detector); contribution reads as disproof; FDR on windows unclear; need hold-out split.

**Исправлено:**

1. **Contribution reframe (RU/EN/main.tex):** явный абзац — reproducible pipeline, falsification framing, bounds of inference; value = methodology + honest null bounds, **not** discovery; **not** «we disproved global series».

2. **In-sample disclaimer (Methods §2.5–2.6, Results, Discussion):** p_ETAS=1.0 = **in-sample** calibration 1973–2026 + same detector; формулировка «consistent with in-sample temporal null»; ETAS triggering vs GK-declustered mainshocks — model mismatch.

3. **Hold-out ETAS:** `scripts/calibrate_etas_holdout.py` → `results/etas_holdout_validation.json` (train 1973–2000, validate 2001–2026: N_obs=13, mean=13.0, p=1.0, n=1000 synthetics).

4. **FDR windows:** `scripts/compute_fdr_windows.py` → `results/fdr_windows.json` — 142→47→27 pipeline; BH post-hoc on 47 merged (45/47); window-level BH **not** discovery procedure (correlated tests).

5. **Trim defensive repetition:** единый блок §5.6 Limitations; detector-liberal subsection сокращён.

6. **Mean GC gate:** одно предложение — mean pairwise слабее all-pairs constraint.

7. **Bird:** только «excluded; no synthetic benchmark in this work».

8. **Future work:** spatial Ogata MLE + synthetic benchmark → `docs/future_work_etas_mle.md`.

| Пункт | Статус |
|-------|--------|
| In-sample disclaimer | **Done** |
| Hold-out split | **Done** — p=1.0, N=13 |
| FDR windows doc | **Done** — fdr_windows.json |
| Contribution reframe | **Done** |
| Spatial ETAS / Bird benchmark | **Future work** — documented |

---

## STRUCTURE §1: Сократить Introduction, убрать Bird/WLS из основного текста

**Замечание:** избыточное введение с превью методологии; Bird и WLS повторяются в Methods/Results/Discussion.

**Исправлено:**
- **Introduction (RU+EN):** problem statement + Michael (2011) + Shearer & Stark (2012); убрано превью ETAS/BP/Hill.
- **Bird:** одна строка в Methods; детали → `paper/supplementary.md` §S1.
- **WLS:** одна строка в Methods; детали → `paper/supplementary.md` §S2 / Appendix B.
- Сноски вместо цепочек «см. Приложение A/B».

---

## STRUCTURE §2: Консолидировать Results (§4)

**Замечание:** числа размазаны по Methods/Results/Discussion.

**Исправлено — единый блок §4.1 (modern window):**
- Каталог: 4418 CSV → 4267 M≥6.5; ~151 M<6.5; 2041 modern.
- N_series=27; permutation p=0.0001 (cross-ref Methods only).
- Primary ETAS MLE: N_obs=27, mean=27.0, p_ETAS=1.0 — **полностью один раз**.
- GK/ZBZ/none sensitivity + объяснение (`sensitivity_declustering.json`).
- Table 1: «raw detector candidates, NOT validated series; illustrative only».

---

## STRUCTURE §3: Объединить Discussion + Conclusions

**Исправлено:** §5 «Discussion and conclusions» — 4 лаконичных пункта; §6 удалён; дубли p_ETAS/N=27 убраны из Discussion.

---

## STRUCTURE §4: Permutation vs ETAS nuance

**Исправлено:** один явный блок в Results (§4.1), **не в abstract**; разные гипотезы (Poisson times vs calibrated temporal null).

---

## STRUCTURE §5: GK/ZBZ/none все N=27

**Исправлено:** честное объяснение — `global_series()` gates доминируют; декластеризация влияет на upstream labels; liberal-detector red flag; cite `results/sensitivity_declustering.json`.
