# Response to reviewers (brief)

## RU

- **b=0.911 vs 1.0:** `sensitivity_b_eta0.json` — N_series=27 при обоих b; upstream η₀/кластеры не пересчитаны (честное ограничение).
- **η₀:** влияет на GK/ZBZ `identify_clusters()`, не на N_obs=`global_series()`; ±20% — not_applied, future work.
- **ETAS:** первичная null — только лит. H&S 2003; WLS — **негативный контроль**, не для выводов; temporal MLE + bootstrap CI в `etas_mle_calibration.json`; spatial Ogata MLE — future work.
- **p_ETAS≤0,001:** статистически значимый избыток **локальной** кластеризации (N_obs=27 > mean≈15,4), не доказательство телесейсмики; учтены либеральность детектора (142 окна) и правила ворот.
- **Чувствительность:** сводная табл. §4.4 / Table sensitivity — окна, GC, b, декластеризация, strict N≥8.

## EN

- **b=0.911 vs 1.0:** `sensitivity_b_eta0.json` — N_series=27 for both; upstream η₀/cluster membership not re-run (honest limitation).
- **η₀:** affects GK/ZBZ `identify_clusters()`, not N_obs=`global_series()`; ±20% not_applied — future work.
- **ETAS:** primary null — literature H&S 2003 only; WLS — **negative control**, never for inference; temporal MLE + bootstrap CIs in `etas_mle_calibration.json`; spatial Ogata MLE — future work.
- **p_ETAS≤0.001:** statistically real **local** clustering excess (N_obs=27 > mean≈15.4), not teleseismic proof; paired with detector liberalness (142 windows) and gate rules.
- **Sensitivity:** consolidated table §4.4 — windows, GC, b, declustering, strict N≥8.

**Remaining blocker:** publication-grade spatial Ogata (1998) ETAS MLE with CIs (`docs/future_work_etas_mle.md`).
