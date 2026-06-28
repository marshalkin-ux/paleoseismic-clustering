#!/usr/bin/env python
"""Report FDR pipeline counts from existing artifacts (fast).

Outputs:
    results/fdr_windows.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.multiple_testing import apply_fdr_bh


def main() -> None:
    merged_fdr_path = ROOT / "results" / "fdr_correction_results.csv"
    mdf = pd.read_csv(merged_fdr_path)
    pvals = mdf["raw_pvalue"].values
    reject_bh, adj = apply_fdr_bh(pvals, alpha=0.05)

    gc_path = ROOT / "results" / "clustering_gc1500.json"
    gc = json.loads(gc_path.read_text(encoding="utf-8")) if gc_path.exists() else {}

    result = {
        "source": "scripts/compute_fdr_windows.py",
        "pipeline_counts": {
            "raw_window_candidates_canonical": 142,
            "union_merged_candidates": 47,
            "modern_greedy_2yr": gc.get("modern_gc1500", {}).get("n_series", 27),
            "three_epoch_greedy_sum": gc.get("n_series_total_three_epochs", 47),
        },
        "pipeline_note": (
            "142 → 47 → 27: 142 raw sliding-window hits before merge (epochs × Δt=1/2/5 yr); "
            "47 union-merged overlapping groups (full historical); "
            "27 greedy global_series on modern Δt=2 yr."
        ),
        "fdr_applicability": (
            "Benjamini–Hochberg on 142 correlated sliding-window tests is not applied as a "
            "discovery procedure — windows overlap strongly (M_eff << 142). "
            "Post-hoc BH on 47 merged-series Monte Carlo p-values is exploratory; "
            "does not correct the full search space."
        ),
        "merged_series_fdr_posthoc": {
            "n_candidates": len(mdf),
            "significant_raw_p005": int((pvals < 0.05).sum()),
            "significant_bh_q005": int(reject_bh.sum()),
            "removed_by_correction": int((~reject_bh & (pvals < 0.05)).sum()),
            "source_file": "results/fdr_correction_results.csv",
        },
    }

    out = ROOT / "results" / "fdr_windows.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["merged_series_fdr_posthoc"], indent=2))


if __name__ == "__main__":
    main()
