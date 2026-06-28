# Take-home message

## RU

**Первичная ETAS-null** для теста гипотезы о глобальных сериях — литература H&S 2003 (μ=0,008, K=0,08; **не связана** с детектором): mean≈15,4, p_ETAS≤0,001 — N_obs=27 превышает литературное ETAS-ожидание; отклонение от ETAS указывает на кластеризацию, которую модель не объясняет (циркум-тихоокеанский пояс, возможные региональные афтершоки), но не глобальные цепочки. Декластеризация GK vs ZBZ vs none: **N=27** при фиксированных воротах (`results/sensitivity_declustering.json`). Тектоническая метрика **удалена из первичного конвейера** (только GC). **Гипотеза о физически значимых глобальных сериях не подтверждается** (§5.4–5.7). Три различных теста: (1) перестановка — пуассоновские времена; (2) лит. ETAS — кластеризация вне модели; (3) гипотеза глобальных серий — не подтверждена.

## EN

**Primary ETAS null** for the global-series hypothesis test is literature H&S 2003 (μ = 0.008, K = 0.08; **decoupled** from detector output): mean ≈ 15.4, p_ETAS ≤ 0.001 — N_obs = 27 exceeds literature ETAS expectation; deviation from ETAS indicates clustering the model does not fully explain (circum-Pacific belt, possible regional aftershocks), but not global chains beyond model scope. Declustering GK vs ZBZ vs none: **N = 27** under fixed gates (`results/sensitivity_declustering.json`). Tectonic heuristic **removed from primary pipeline** (great-circle only). The global-series hypothesis is **not supported** (§5.4–5.7). Three distinct tests: (1) permutation — Poisson times; (2) literature ETAS — clustering beyond model; (3) global-series hypothesis — not confirmed.

**Do not claim:** “47 global series discovered”; tectonic metric as innovation/novelty; permutation “confirms structure” while ETAS shows clustering beyond model only; FDR 45/47 as physical discovery; literature p_ETAS≤0.001 as proof of teleseismic global series.

**Future work only:** ΔCFS, dynamic stress, full spatial ETAS MLE (`docs/future_work_etas_mle.md`), η₀ sensitivity at catalog b=0.911, search-space tightening.
