"""Multi-seed ETAS false-positive robustness check (planned).

Runs ETAS null-model validation across multiple RNG seeds to assess
whether FPR=0/100 at seed=42 is robust or seed-dependent.

Usage (future):
    python scripts/run_etas_multiseed.py --seeds 42,43,44,45,46 --n-catalogs 100

Output:
    results/etas_multiseed.json

Not yet executed in the publication pipeline — see paper §5.3 (Limitations).
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-seed ETAS FPR sweep (stub)")
    parser.add_argument(
        "--seeds",
        default="42,43,44,45,46",
        help="Comma-separated RNG seeds (default: 5 quick seeds)",
    )
    parser.add_argument(
        "--n-catalogs",
        type=int,
        default=100,
        help="Synthetic catalogs per seed (default: 100)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute validation (slow); default is dry-run stub only",
    )
    args = parser.parse_args()
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]

    out = {
        "status": "stub",
        "message": (
            "Multi-seed ETAS sweep not run by default. "
            "Use --run to execute (recommended: >=1000 catalogs per seed for publication)."
        ),
        "planned_seeds": seeds,
        "n_catalogs_per_seed": args.n_catalogs,
        "reference_single_seed": "results/etas_validation.json (seed=42, see n_catalogs_with_false_series)",
    }

    if args.run:
        import pandas as pd
        from src.analysis.clustering import SeismicClusterAnalyzer
        from src.analysis.etas_validation import ETASCatalogGenerator

        catalog_path = Path("data/processed/unified_catalog_full.csv")
        if not catalog_path.exists():
            logger.error("Catalog not found: %s", catalog_path)
            sys.exit(1)

        df = pd.read_csv(catalog_path)
        df = df[df["year"] >= 1973].copy()
        analyzer = SeismicClusterAnalyzer()
        generator = ETASCatalogGenerator(
            mu=0.008, K=0.08, alpha=1.0, c=0.005, p=1.1,
            max_trigger_distance_km=500,
        )

        per_seed = []
        for seed in seeds:
            logger.info("ETAS validation seed=%d, n=%d", seed, args.n_catalogs)
            res = generator.run_false_positive_analysis(
                cluster_analyzer=analyzer,
                n_catalogs=args.n_catalogs,
                min_events=4,
                time_window_years=2.0,
                seed=seed,
            )
            per_seed.append({"seed": seed, **res})
        out = {"status": "completed", "per_seed": per_seed}

    out_path = Path("results/etas_multiseed.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Wrote %s", out_path)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
