# Take-home message

## RU

**Первичная ETAS-null** для теста гипотезы о глобальных сериях — литература H&S 2003 (μ=0,008, K=0,08; **не связана** с детектором): mean≈15,4, p_ETAS≤0,001 — N_obs=27 превышает **локальное афтершоковое** ожидание (кластеризация сверх пуассоновских времён), но **не доказывает** телесейсмические цепочки. **Негативный контроль (WLS):** mean=27,0=N_obs (p_ETAS=1,0) — **артефакт связки «детектор+калибровка»**; **не** независимое доказательство (K завышен WLS на 24 афтершоках). **Не цитировать** p_ETAS=1,0 как единственную фальсификацию. Декластеризация GK vs ZBZ vs none: **N=27** во всех случаях (`results/sensitivity_declustering.json`). Тектоническая метрика **удалена из первичного конвейера** (только GC). Гипотеза о физически значимых глобальных сериях **не подтверждается** (§5.4–5.6).

## EN

**Primary ETAS null** for the global-series hypothesis test is literature H&S 2003 (μ = 0.008, K = 0.08; **decoupled** from detector output): mean ≈ 15.4, p_ETAS ≤ 0.001 — N_obs = 27 exceeds **local aftershock-only** expectation (clustering beyond Poisson times), but **does not prove** teleseismic chains. **Negative control (WLS):** mean = 27.0 = N_obs (p_ETAS = 1.0) — **detector–calibration coupling artifact**; **not** independent evidence (K inflated by 24-event WLS). **Do not cite** p_ETAS = 1.0 alone as falsification. Declustering GK vs ZBZ vs none: **N = 27** in all cases (`results/sensitivity_declustering.json`). Tectonic heuristic **removed from primary pipeline** (great-circle only). The global-series hypothesis is **not supported** (§5.4–5.6). The permutation test rejects only a temporal Poisson null — trivial for earthquake catalogs.

**Do not claim:** “47 global series discovered”; tectonic metric as innovation/novelty; permutation “confirms structure” while ETAS is indistinguishable; FDR 45/47 as physical discovery (Methods/sensitivity only); prominent FPR=1000/1000 in abstract/hero (Methods §5.7 only); p_ETAS=1.0 alone as falsification of global structure; η at b=0.911 without re-run; literature p_ETAS≤0.001 as proof of teleseismic global series.

**Future work only:** ΔCFS, dynamic stress, full ETAS MLE (`docs/future_work_etas_mle.md`), η₀ sensitivity at catalog b=0.911, search-space tightening, plate-boundary graph with guaranteed path coverage.
