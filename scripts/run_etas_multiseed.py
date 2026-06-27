"""Multi-seed ETAS false-positive robustness check.

Runs ETAS null-model validation across multiple RNG seeds with
catalog-calibrated parameters to assess stability of mean false series,
FPR, and p_ETAS.

Usage:
    python scripts/run_etas_multiseed.py --run --seeds 42,43,...,51 --n-catalogs 1000

Output:
    results/etas_multiseed.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

N_OBSERVED = 27  # modern window detector count (1973–2026)


def _build_summary(per_seed: list[dict], seeds: list[int], n_catalogs: int) -> dict:
    means = [s["mean_false_series"] for s in per_seed]
    stds = [s.get("std_false_series", 0.0) for s in per_seed]
    pvals = [s.get("p_value_empirical") for s in per_seed]
    fprs = [s.get("false_positive_rate", 1.0) for s in per_seed]

    import statistics

    return {
        "n_observed": N_OBSERVED,
        "n_catalogs_per_seed": n_catalogs,
        "seeds": seeds,
        "mean_false_series_by_seed": {
            str(s["seed"]): s["mean_false_series"] for s in per_seed
        },
        "std_false_series_by_seed": {
            str(s["seed"]): s.get("std_false_series") for s in per_seed
        },
        "p_etas_by_seed": {
            str(s["seed"]): s.get("p_value_empirical") for s in per_seed
        },
        "fpr_by_seed": {
            str(s["seed"]): s.get("false_positive_rate") for s in per_seed
        },
        "overall_mean_false_series": statistics.mean(means) if means else None,
        "overall_std_false_series": statistics.stdev(means) if len(means) > 1 else 0.0,
        "overall_mean_p_etas": statistics.mean(
            [p for p in pvals if p is not None and p == p]
        )
        if any(p is not None and p == p for p in pvals)
        else None,
        "note": (
            "Calibrated ETAS params (use_calibrated_defaults=True); "
            f"n={n_catalogs} catalogs/seed; n_observed={N_OBSERVED}."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-seed ETAS FPR sweep")
    parser.add_argument(
        "--seeds",
        default="42,43,44,45,46,47,48,49,50,51",
        help="Comma-separated RNG seeds (default: 10 seeds 42–51)",
    )
    parser.add_argument(
        "--n-catalogs",
        type=int,
        default=1000,
        help="Synthetic catalogs per seed (default: 1000)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute validation (slow); default is dry-run stub only",
    )
    args = parser.parse_args()
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]

    out: dict = {
        "status": "stub",
        "message": (
            "Multi-seed ETAS sweep not run. Use --run to execute "
            f"(recommended: {args.n_catalogs} catalogs per seed)."
        ),
        "planned_seeds": seeds,
        "n_catalogs_per_seed": args.n_catalogs,
        "n_observed": N_OBSERVED,
        "reference_single_seed": "results/etas_validation.json",
    }

    if args.run:
        import pandas as pd
        from src.analysis.clustering import SeismicClusterAnalyzer
        from src.analysis.etas_params import load_calibrated_etas_params
        from src.analysis.etas_validation import ETASCatalogGenerator

        catalog_path = Path("data/processed/unified_catalog_full.csv")
        if not catalog_path.exists():
            logger.error("Catalog not found: %s", catalog_path)
            sys.exit(1)

        df = pd.read_csv(catalog_path)
        df = df[df["year"] >= 1973].copy()
        df = df[df["magnitude"] >= 6.5].copy()
        etas_params = load_calibrated_etas_params()
        t_span_years = float(df["year"].max() - df["year"].min()) if len(df) else 53.0
        n_background = int(round(etas_params["mu"] * t_span_years * 365.25))
        n_background = max(n_background, 40)
        logger.info(
            "Calibrated ETAS: mu=%.6f n_bg=%d t_span=%.1f yr",
            etas_params["mu"],
            n_background,
            t_span_years,
        )

        analyzer = SeismicClusterAnalyzer()
        generator = ETASCatalogGenerator(
            mu=etas_params["mu"],
            K=etas_params["K"],
            alpha=etas_params["alpha"],
            c=etas_params["c"],
            p=etas_params["p"],
            max_trigger_distance_km=etas_params.get("max_trigger_distance_km", 500.0),
            use_calibrated_defaults=False,
        )

        per_seed = []
        for seed in seeds:
            logger.info("ETAS validation seed=%d, n=%d", seed, args.n_catalogs)
            res = generator.run_false_positive_analysis(
                cluster_analyzer=analyzer,
                n_catalogs=args.n_catalogs,
                min_events=4,
                time_window_years=2.0,
                n_observed=N_OBSERVED,
                n_background=n_background,
                t_span_years=t_span_years,
                seed=seed,
            )
            per_seed.append({"seed": seed, **res})

        summary = _build_summary(per_seed, seeds, args.n_catalogs)
        out = {
            "status": "completed",
            "n_observed": N_OBSERVED,
            "per_seed": per_seed,
            "summary": summary,
        }

    out_path = Path("results/etas_multiseed.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Wrote %s", out_path)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
