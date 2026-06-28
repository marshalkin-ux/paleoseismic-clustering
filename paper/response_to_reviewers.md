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

---

## ROUND 4: Linear IMRAD, hold-out Methods, b=0.911 full pipeline, N=27 stability

**Исправлено:**
- Линейная структура RU+EN+`main.tex`: §3.1 GK → §3.2 η → §3.3 детектор → §3.4 ETAS MLE → §3.5 hold-out; все числа в §4.1; Discussion без stats; Conclusions §6 без чисел.
- Appendix A (pre-1900) + B (WLS) удалены из основного текста; сноски на `paper/supplementary.md` §S2/S3.
- §3.5 hold-out: train 1024 GK mainshocks (1973–2000), hold-out 1010 events / 25 yr, detector Δt=2, n=1000 seed=42, max_total_events=5000.
- `scripts/run_sensitivity_b0911_full.py` → `results/sensitivity_b0911_full_pipeline.json`: N_series=27 при b=1.0 и 0.911; Jaccard=1.0; 8.2% upstream label mismatch.
- `scripts/compute_series_stability.py` → `results/series_stability_venn.json`: матрица Δt×decluster×b; N=27 стабилен при Δt=2 (4/12 configs); доминирует ширина окна.
- `index.html`, `take_home_message.md`: указатели на структуру; stats → §4.1.


**Замечание 2.1 (title / scope honesty):** заголовок «spatiotemporal» читается как полная пространственно-временная валидация; фактически — детекция с пространственными воротами + **только temporal** ETAS hold-out.

**Исправлено:**
- Подзаголовок EN: *Temporal ETAS null and hold-out validation*; RU: *Временная ETAS-null и hold-out валидация*.
- Аннотации (RU+EN): явное предложение — заголовок = **detection**; **validation** = temporal-only.
- §1 Introduction (RU+EN): анализируем **кандидатов детектора** с GC>1500 км; валидируем **только временной избыток**; spatial linkage **не тестируется**.
- `main.tex`: `\title{...\\{\large Temporal ETAS null and hold-out validation}}`; abstract + scope paragraph синхронизированы.

**Замечание 2.2 (Bird):** формулировка «validation failed proves unsuitability» без synthetic benchmark.

**Исправлено:**
- Основной текст: «excluded from primary pipeline; **no synthetic benchmark** in this work; comparison deferred to supplementary/future work».
- `paper/supplementary.md` §S1: убрана фраза про «metric unsuitability» как доказательство; audit 98% GC-fallback сохранён.
- `generate_article_en_pdf.py`: Bird paragraph синхронизирован.

**Замечание 2.3 (FDR / multiple testing):** 27 modern не скорректированы за поиск по 142 окнам.

**Исправлено:**
- §4.1 Results (RU+EN, `main.tex`): новый абзац — FDR на 142 **не** применялась к 27; Bonferroni 0,05/142≈0,00035 vs permutation p=0,0001; BH на 47 merged — exploratory, **не** discovery claim.
- `results/fdr_windows.json` — pipeline 142→47→27 задокументирован (`scripts/compute_fdr_windows.py`).

**Замечание 2.4 (b=0.911):** Jaccard=1.0 при фиксированных воротах не доказывает идентичность upstream-кластеров.

**Исправлено:**
- §3 / §4.4 (RU+EN): Jaccard=1.0 для **наборов событий серий** ≠ доказательство upstream identity; полный конвейер при b=0,911 **не перезапускался** (~9,8% label mismatch).
- Убраны формулировки, подразумевающие полный re-run.

**Typo (CRITICAL):** EN abstract «N_obs cornacovan c in-sample» → «N_obs **consistent with in-sample temporal null**»; grep по репозиторию — других вхождений «cornacovan» нет.

**Future work (не в этой сессии):** spatial Ogata (1998) MLE — journal requirement; synthetic Bird benchmark — `docs/future_work_etas_mle.md`.

| Пункт | Статус |
|-------|--------|
| Title/subtitle reframe | **Done** |
| Abstract detection vs validation | **Done** |
| EN typo cornacovan | **Done** (grep clean) |
| Bird unsuitability claim | **Removed** |
| FDR/Bonferroni paragraph | **Done** |
| b=0.911 Jaccard disclaimer | **Done** |
| Spatial Ogata MLE | **Future work** — documented |

---

## ROUND 4: Dedupe stats, appendices → supplementary, hold-out Methods/Results

**Замечание:** N=27/p_ETAS/p повторяются в abstract, intro, discussion; Appendices A/B в теле; hold-out без Methods; hero/index дублируют числа.

**Исправлено:**

1. **§4.1 canonical table (RU+EN+main.tex):** единственное полное сообщение p_ETAS/N_obs — таблица Split | N_obs | mean | p_ETAS (in-sample + hold-out); permutation p=0.0001 один раз там же.

2. **Abstract (RU+EN+PDF):** catalog, 27 candidates, p_ETAS=1.0 одной строкой; без hold-out чисел; без mean=27.

3. **Introduction hypothesis table:** Result → «см. §4.1»; WLS → Supplementary S2.

4. **Discussion/Conclusions:** интерпретация без повторения N=27/p; generalizing phrases only.

5. **Appendices A/B удалены** из article_ru/en.md, main.tex, PDF-генераторов; контент в `paper/supplementary.md` §S2 (WLS) + **§S3 (pre-1900)**; ссылки Supplementary S1/S2/S3; index materials link обновлён.

6. **Hold-out Methods §3.7/3.8 (RU) / §3.8 (EN) / main.tex §subsec:holdout-methods:** train GK 1973–2000, hold-out 2001–2026, Δt=2 yr, GC>1500, N≥4, n=1000 seed=42, `results/etas_holdout_validation.json`; partial out-of-time note.

7. **Trim:** hero/index — без hold-out в hero; PDF generators deduped.

| Пункт | Статус |
|-------|--------|
| Canonical §4.1 table | **Done** |
| Abstract minimal | **Done** |
| Appendices → supplementary | **Done** |
| Hold-out Methods + Results | **Done** |

---

## ROUND 5: «Супер-стабильность» N=27, b=0.911 full pipeline, hold-out spec, merge Methods

**Замечание 1 (N=27 super-stability):** стабильность N=27 при GK/ZBZ/none и b=1.0/0.911 не доказывает физическое «ядро 27»; доминирует ширина окна Δt (53→27→11).

**Исправлено:**
- Матрица чувствительности `scripts/compute_series_stability.py` → `results/series_stability_venn.json`: при Δt=1/2/5 г. N_series = 53/**27**/11; при Δt=2 г. все 4 конфигурации (GK/ZBZ/none × b=1.0/0.911) дают N=27, но Jaccard **состава серий** vs baseline GK = **0,32** для ZBZ/none (Jaccard **наборов событий** = 1,0).
- `results/sensitivity_declustering.json`: GK/ZBZ/none → N=27 при фиксированных воротах; merge **142→47→27**.
- Полный upstream re-run `scripts/run_sensitivity_b0911_full.py` → `results/sensitivity_b0911_full_pipeline.json`: N=27, Jaccard=1,0, **8,2%** upstream label mismatch (165/2017) — ворота `global_series()` доминируют.
- §4.1 Results (RU+EN+`main.tex`): абзац **после Таблицы 2** (декластеризация); §4.4 — полная таблица стабильности + интерпретация «detector-artifact, not core 27».

**Замечание 2 (b=1.0 vs 0.911):** требовался полный пересчёт upstream, не только Jaccard при фиксированных воротах.

**Исправлено:**
- `run_sensitivity_b0911_full.py` задокументирован в §3.2/§4.4 (RU+EN), `main.tex` (η subsection, limitations table), PDF-генераторах.
- Удалены формулировки «upstream не пересчитан» / «not re-run» — заменены на: full pipeline re-run, Jaccard=1,0, 8,2% label mismatch; equal N ≠ unchanged upstream structure.

**Замечание 3 (merge §2.3.1 + §2.4):** дублирование спецификации алгоритма и критериев.

**Исправлено:**
- RU+EN markdown: единый §3.3 «Детектор (`global_series`, окна, merge, ворота)»; критерии — §2.3 канонический список.
- PDF RU: §2.3.1 + §2.4 → **§2.3 Алгоритм детектирования**; PDF EN: algorithm spec + criteria → единый блок Detection algorithm.
- `main.tex`: Declustering + Series Detection с `subsubsec:algo-spec` (без дублирующего §2.4 в markdown-структуре).

**Замечание 4 (hold-out reproducibility):** Methods должны явно указывать train-only MLE без дообучения на hold-out.

**Исправлено — §3.5 Methods (RU+EN+`main.tex` `subsec:holdout-methods`):**
- ETAS temporal MLE калибруется **только** на train GK mainshocks **1973–2000** (n=**1024**).
- Параметры **фиксируются** и применяются к hold-out **2001–2026** (n=**1010** событий) **без повторной калибровки**.
- Детектор: Δt=2 г., mean GC>1500 км, N≥4; n=1000 synthetics, seed=42.
- `scripts/calibrate_etas_holdout.py` → `results/etas_holdout_validation.json`: N_obs=**13**, mean=13,0, p_ETAS=1,0.

**Замечание 5 (после Таблицы 2):** краткий абзац о стабильности N=27.

**Исправлено:** абзац после таблицы декластеризации в §4.1 (RU+EN+`main.tex` после `tab:gk_zbz`) + после Table 2 в PDF-генераторах.

| Пункт | Статус |
|-------|--------|
| N=27 stability data + interpretation | **Done** |
| b=0.911 full pipeline documented | **Done** |
| Merge algorithm sections | **Done** |
| Hold-out train-only spec | **Done** |
| Post-Table 2 paragraph | **Done** |
| Discussion dedupe | **Done** |

---

## ROUND 5: Table 2 «upstream 8,2%» clarification

**Замечание:** строка «b overlap (full pipeline)» (Jaccard=1,0; upstream 8,2%) не объяснена — кажется противоречивой.

**Исправлено:**
- §4.4 (RU+EN), `main.tex` Table~\ref{tab:sensitivity}, PDF-генераторы: сноска ‡/† и 2–3 предложения сразу после Таблицы 2 — **Jaccard=1,0** = идентичные **наборы событий** в 27 сериях (`global_series()` не использует b); **8,2%** = 165/2017 GK mainshocks с изменившейся **меткой кластера** `identify_clusters()` при b=1,0→0,911 (полный конвейер; `sensitivity_b0911_full_pipeline.json`).
- §3.2 η-метрика (RU+EN): одна строка — b влияет на upstream-метки, не на ворота `global_series()`.
- Исправлены устаревшие формулировки «конвейер не перезапускался» / «~9,8%» в EN PDF и ROUND 3.

| Пункт | Статус |
|-------|--------|
| Table 2 footnote + post-table text | **Done** |
| §3.2 b sensitivity scope | **Done** |
| PDF generators synced | **Done** |

---

## ROUND 6: Scope honesty — detection vs validation, demote permutation, FDR limit

**Замечание 2.1 (title/intro mismatch):** заголовок обещает spatiotemporal clustering; валидация — temporal-only.

**Исправлено (Option A — subtitle retained):**
- **Abstract (RU+EN+main.tex):** «Title refers to detection geometry; inferential tests are temporal-only» / RU-эквивалент.
- **Introduction (RU+EN+main.tex+PDF):** двухфазный дизайн — (1) detection: η + GC>1500 km; (2) validation: temporal ETAS + hold-out, **не** spatial linkage. Bird — только «explored early, excluded — Supplementary S1», не цель.
- **Hypothesis table row (c):** «Not tested (spatial ETAS open)».
- **index.html hero:** detection → validation tone; permutation убран из hero/results chip.

**Замечание 2.2 (Bird):** «validation failed proves unsuitability» без benchmark.

**Исправлено:**
- Все claims «validation failed» / «unsuitable metric proved» удалены (grep clean).
- **Introduction:** zero Bird-as-objective; **supplementary.md S1:** «preliminary idea, not validated»; excluded + no synthetic benchmark.
- **generate_article_pdf.py:** удалён абзац «Провал валидации показывает непригодность».

**Замечание 2.3 (Bonferroni / FDR):**

**Исправлено:**
- **§4.1 (RU+EN+main.tex):** explicit box — 142 windows → N=27 **NOT** multiplicity-corrected; Bonferroni α/142≈0.00035 vs p=0.0001; conclusion = **consistency with in-sample temporal ETAS**, not corrected significance; FDR 47 merged exploratory only.
- **Conclusions (RU+EN):** no language implying corrected significance.

**Замечание 2.4 (permutation in Table 3.1 / ETAS table):**

**Исправлено:**
- Permutation **removed** from §4.1 primary counts table (RU+EN+main.tex); ETAS table = **in-sample MLE + hold-out only**.
- Hypothesis row (a) relabelled «Diagnostic (Methods)»; permutation one sentence in Methods §3.3 / main.tex `subsec:stat-tests`.
- **tab:epochs** p-column → «Perm. p† (diagnostic)» footnote.

| Пункт | Статус |
|-------|--------|
| Two-phase intro + abstract scope sentence | **Done** |
| Bird failure claims removed | **Done** |
| Multiplicity box §4.1 | **Done** |
| Permutation demoted from Results table | **Done** |
| index.html hero/results trim | **Done** |
| take_home_message.md | **Done** |
| PDF generators + verify_ru_pdf_cyrillic | **Done** |
