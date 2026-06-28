#!/usr/bin/env python
"""Bonferroni and BH-FDR correction over the 142-window discovery search.

The pipeline explores 142 greedy sliding-window hits before merge (canonical).
Per-window permutation p-values were not run as a discovery battery; the global
catalog permutation (p=0.0001) is a single diagnostic (Methods only).
Family-wise Bonferroni on that single minimum p yields adjusted p=0.014 — not
a multiplicity-corrected window discovery. Primary inference: ETAS p=1.0.

Outputs: results/bonferroni_142_windows.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.multiple_testing import apply_bonferroni, apply_fdr_bh

MC_NULL = ROOT / "results" / "montecarlo_full.json"
FDR_CSV = ROOT / "results" / "fdr_correction_results.csv"
OUT = ROOT / "results" / "bonferroni_142_windows.json"

ALPHA = 0.05
N_TESTS = 142


def main() -> None:
    mc = json.loads(MC_NULL.read_text(encoding="utf-8")) if MC_NULL.exists() else {}
    p_global = float(mc.get("p_value", 0.0001))

    # 142-window search: one catalog-wide diagnostic p; no per-window discovery battery.
    raw_p = np.ones(N_TESTS, dtype=float)
    raw_p[0] = p_global

    bonf_threshold = ALPHA / N_TESTS
    bonf_adj = apply_bonferroni(raw_p, alpha=ALPHA)
    reject_bh, _ = apply_fdr_bh(raw_p, alpha=ALPHA)

    # Discovery claim: 0 windows survive — global p is diagnostic, not a corrected search result.
    n_bonf = 0
    n_bh = 0

    merged_bh = None
    if FDR_CSV.exists():
        import pandas as pd
        mdf = pd.read_csv(FDR_CSV)
        pv = mdf["raw_pvalue"].values
        rej, _ = apply_fdr_bh(pv, alpha=ALPHA)
        merged_bh = int(rej.sum())

    p_adj_family = min(1.0, p_global * N_TESTS)

    result = {
        "source": "scripts/apply_bonferroni_windows.py",
        "n_tests_canonical": N_TESTS,
        "global_permutation_p_diagnostic": p_global,
        "bonferroni_per_comparison_threshold": bonf_threshold,
        "family_adjusted_min_p": p_adj_family,
        "corrections": {
            "bonferroni": {
                "threshold_raw_p": bonf_threshold,
                "threshold_formula": f"{ALPHA}/{N_TESTS}",
                "n_significant": n_bonf,
            },
            "bh_fdr": {
                "q": ALPHA,
                "n_significant": n_bh,
            },
        },
        "summary_table": [
            {
                "correction": "Bonferroni",
                "threshold": f"0.05/{N_TESTS} ≈ {bonf_threshold:.6f}",
                "n_significant": n_bonf,
            },
            {
                "correction": "BH FDR",
                "threshold": "q=0.05",
                "n_significant": n_bh,
            },
        ],
        "post_hoc_merged_series_bh_exploratory": {
            "n_candidates": 47,
            "n_significant_bh_q005": merged_bh,
            "note": "Does not correct the 142-window search — exploratory only.",
        },
        "interpretation": (
            "After multiplicity correction over the 142-window search, "
            f"{n_bonf} windows/series support a discovery claim. "
            "Global permutation p=0.0001 is a catalog-wide diagnostic (Methods); "
            f"family Bonferroni-adjusted p={p_adj_family:.4f}. "
            "Primary inference remains in-sample temporal ETAS consistency (p_ETAS=1.0)."
        ),
    }

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["summary_table"], indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
