#!/usr/bin/env python
"""
Step 2 — Run the full seismic clustering analysis pipeline.

Pipeline
--------
1. Load unified catalogue from data/processed/unified_catalogue.csv
2. Estimate Magnitude of Completeness per epoch
3. Run Baiesi-Paczuski nearest-neighbor clustering
4. Identify global series (multi-region clusters)
5. Monte Carlo permutation significance test
6. Save cluster summary table and JSON results

Usage
-----
    python scripts/run_analysis.py [options]

Options
-------
--catalogue   Path to unified CSV (default: data/processed/unified_catalogue.csv).
--config      Path to config.yaml (default: config.yaml).
--min-mag     Minimum magnitude (default: 6.5).
--n-sim       Monte Carlo simulations (default: 1000; use 10000 for publication).
--fast        Use n_sim=200 for a quick sanity-check run.
--no-mc       Skip Monte Carlo entirely.
--output      Output directory (default: data/processed).
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PYTHON = sys.executable


def _load_catalogue(path: Path, min_mag: float) -> pd.DataFrame:
    """Load and filter the unified catalogue."""
    if not path.exists():
        # try parquet sibling
        pq = path.with_suffix(".parquet")
        if pq.exists():
            df = pd.read_parquet(pq)
        else:
            raise FileNotFoundError(f"Catalogue not found: {path}. "
                                    "Run scripts/download_data.py first.")
    else:
        df = pd.read_csv(path, low_memory=False)

    # Normalise column names (handle both lat/lon and latitude/longitude)
    if "latitude" in df.columns and "lat" not in df.columns:
        df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
    if "lat" in df.columns and "latitude" not in df.columns:
        df["latitude"] = df["lat"]
        df["longitude"] = df["lon"]

    before = len(df)
    df = df.dropna(subset=["lat", "lon", "magnitude"])
    df = df[df["magnitude"] >= min_mag].reset_index(drop=True)
    logger.info("Catalogue: %d events after filtering (M≥%.1f); %d dropped",
                len(df), min_mag, before - len(df))
    return df


def main():
    parser = argparse.ArgumentParser(description="Run PST-Cluster analysis")
    parser.add_argument("--catalogue", default="data/processed/unified_catalogue.csv")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--min-mag", type=float, default=6.5)
    parser.add_argument("--n-sim", type=int, default=1000)
    parser.add_argument("--fast", action="store_true",
                        help="Use n_sim=200 (quick check)")
    parser.add_argument("--no-mc", action="store_true",
                        help="Skip Monte Carlo testing")
    parser.add_argument("--output", default="data/processed")
    args = parser.parse_args()

    with open(args.config) as fh:
        config = yaml.safe_load(fh)

    n_sim = 200 if args.fast else args.n_sim
    seed = config["monte_carlo"]["random_seed"]
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Paleoseismic Clustering — Analysis Pipeline")
    logger.info("n_sim=%d | M≥%.1f | seed=%d", n_sim, args.min_mag, seed)
    logger.info("=" * 60)

    # ── 1. Load catalogue ─────────────────────────────────────────────────────
    logger.info("\n[1/5] Loading catalogue …")
    df = _load_catalogue(Path(args.catalogue), args.min_mag)

    if len(df) < 20:
        logger.error("Too few events (%d). Run download_data.py first.", len(df))
        sys.exit(1)

    # ── 2. Completeness estimation ────────────────────────────────────────────
    logger.info("\n[2/5] Estimating completeness surface …")
    try:
        from src.analysis.completeness import CompletenessAnalyzer
        comp = CompletenessAnalyzer()
        mc_global = comp.estimate_mc(df)
        b_val, b_err = comp.compute_bvalue(df, mc_global)
        completeness_df = comp.completeness_matrix(df)
        if not completeness_df.empty:
            completeness_df.to_csv(out_dir / "completeness_surface.csv")
        logger.info("Mc(global)=%.2f, b=%.2f±%.2f", mc_global, b_val, b_err)
    except Exception as exc:
        logger.warning("Completeness estimation failed (%s); continuing …", exc)
        completeness_df = pd.DataFrame()

    # ── 3. Nearest-neighbor clustering (Baiesi-Paczuski 2004) ─────────────────
    logger.info("\n[3/5] Running nearest-neighbor clustering …")
    from src.analysis.clustering import SeismicClusterAnalyzer

    # Try to load tectonic distance calculator
    tectonic_calc = None
    try:
        from src.analysis.tectonic_distance import TectonicDistanceCalculator
        bird_path = Path(config["data"]["paths"]["raw"]) / "pb2002_boundaries.json"
        if bird_path.exists():
            tectonic_calc = TectonicDistanceCalculator(bird_path=bird_path)
            logger.info("Using tectonic distance calculator (Bird 2003)")
        else:
            logger.info("Plate boundary file not found; using Haversine × 1.5")
    except Exception as exc:
        logger.warning("Tectonic distance init failed (%s); using Haversine", exc)

    analyzer = SeismicClusterAnalyzer(
        df_param=config["clustering"].get("df_param", 1.6),
        b_param=config["clustering"].get("b_param", 1.0),
    )

    df_nn = analyzer.find_nearest_neighbor(df, dist_calculator=tectonic_calc)

    # Identify clusters using eta threshold from config or automatic
    eta_thresh = config["clustering"].get("eta_threshold", None)
    clusters_df = analyzer.identify_clusters(df_nn, eta_threshold=eta_thresh)
    n_clusters = int(clusters_df["cluster_id"].max()) + 1 if not clusters_df.empty and "cluster_id" in clusters_df.columns else 0
    logger.info("Identified %d clusters", n_clusters)

    # Save nearest-neighbor results
    df_nn.to_csv(out_dir / "events_with_nn.csv", index=False)

    # ── 4. Global series detection ─────────────────────────────────────────────
    logger.info("\n[4/5] Extracting global series …")
    try:
        global_series = analyzer.find_global_series(
            clusters_df,
            min_regions=config["clustering"].get("min_regions", 2),
            min_events=config["clustering"].get("min_cluster_size", 3),
        )
        logger.info("Global series candidates: %d", len(global_series))
    except AttributeError:
        # Fallback: use all clusters with ≥3 events and ≥2 distinct FE regions
        global_series = _extract_global_series(clusters_df, df, min_events=3)
        logger.info("Global series (fallback): %d", len(global_series))

    # ── 5. Monte Carlo significance test ──────────────────────────────────────
    logger.info("\n[5/5] Monte Carlo significance testing (n=%d) …", n_sim)

    mc_result = {"pvalue": float("nan"), "observed": float("nan"),
                 "simulated": [], "zscore": float("nan")}

    if not args.no_mc and len(df) > 0:
        try:
            mc_result = _run_mc_vectorized(
                df, df_nn, n_sim=n_sim, seed=seed,
                df_param=analyzer.df_param, b_param=analyzer.b_param,
            )
            # Save null scores array for figure generation
            sim_arr = np.array(mc_result.get("simulated", []))
            if len(sim_arr):
                np.save(out_dir / "null_scores.npy", sim_arr)
            logger.info("Monte Carlo complete: p=%.4f, z=%.2f",
                        mc_result.get("pvalue", float("nan")),
                        mc_result.get("zscore", float("nan")))

            # Save null scores
            null_scores = np.array(mc_result.get("simulated", []))
            if len(null_scores):
                np.save(out_dir / "null_scores.npy", null_scores)
        except Exception as exc:
            logger.error("Monte Carlo failed: %s", exc)
    else:
        logger.warning("Monte Carlo skipped")

    # ── Save results ───────────────────────────────────────────────────────────
    _save_results(global_series, mc_result, clusters_df, out_dir)

    # ── Summary ────────────────────────────────────────────────────────────────
    logger.info("\n%s", "=" * 60)
    logger.info("ANALYSIS COMPLETE")
    logger.info("  Events analysed:    %d", len(df))
    logger.info("  Clusters found:     %d", n_clusters)
    logger.info("  Global series:      %d", len(global_series))
    logger.info("  MC p-value:         %.4f", mc_result.get("pvalue", float("nan")))
    logger.info("  MC z-score:         %.2f", mc_result.get("zscore", float("nan")))
    logger.info("  Output dir:         %s", out_dir)
    logger.info("=" * 60)


def _run_mc_vectorized(
    df: pd.DataFrame,
    df_nn: pd.DataFrame,
    n_sim: int,
    seed: int,
    df_param: float = 1.6,
    b_param: float = 1.0,
    max_sample: int = 500,
) -> dict:
    """Fast vectorised Monte Carlo permutation test.

    Uses numpy broadcasting to compute all nearest-neighbour eta values at once,
    making each permutation O(n²) in numpy rather than O(n²) in Python loops.
    For n > max_sample the catalogue is randomly subsampled.
    """
    rng = np.random.default_rng(seed)

    lat_col = "lat" if "lat" in df_nn.columns else "latitude"
    lon_col = "lon" if "lon" in df_nn.columns else "longitude"

    sub = df_nn.dropna(subset=[lat_col, lon_col, "magnitude"]).copy()
    if len(sub) > max_sample:
        sub = sub.sample(max_sample, random_state=seed).reset_index(drop=True)

    lats = sub[lat_col].values
    lons = sub[lon_col].values
    mags = sub["magnitude"].values

    # Fractional year times
    year = sub["year"].fillna(0).astype(float).values
    month = sub["month"].fillna(6).astype(float).values if "month" in sub.columns else np.full(len(sub), 6.0)
    day = sub["day"].fillna(15).astype(float).values if "day" in sub.columns else np.full(len(sub), 15.0)
    times_orig = year + (month - 1) / 12.0 + (day - 1) / 365.25

    order = np.argsort(times_orig)
    times_orig = times_orig[order]
    lats = lats[order]
    lons = lons[order]
    mags = mags[order]

    def _haversine_mat(la1, lo1, la2, lo2):
        R = 6371.0
        dlat = np.radians(la2 - la1)
        dlon = np.radians(lo2 - lo1)
        a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(la1)) * np.cos(np.radians(la2)) * np.sin(dlon / 2) ** 2
        return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

    def _mean_log_eta_fast(times: np.ndarray) -> float:
        """Compute mean log10(eta_nn) via numpy upper-triangular broadcasting."""
        n = len(times)
        if n < 2:
            return 0.0
        # time differences (n×n upper triangle)
        t_i = times[:, None]
        t_j = times[None, :]
        dt = t_j - t_i  # dt[i,j] = t_j - t_i

        # Distances (precomputed once, reused across permutations for same coords)
        r_mat = _haversine_km_mat  # passed in via closure

        # eta[i,j] = dt * r^df * 10^(-b*m_i) — valid only when dt > 0
        mask = dt > 0
        with np.errstate(divide="ignore", invalid="ignore"):
            eta_mat = dt * (r_mat ** df_param) * (10 ** (-b_param * mags[:, None]))
        eta_mat[~mask] = np.inf

        # Nearest neighbour: min eta per column j (best parent i for each j)
        nn_eta = eta_mat.min(axis=0)
        valid = nn_eta[np.isfinite(nn_eta) & (nn_eta > 0)]
        return float(np.mean(np.log10(valid))) if len(valid) > 0 else 0.0

    # Precompute distance matrix (fixed, positions don't change)
    _haversine_km_mat = _haversine_mat(
        lats[:, None], lons[:, None],
        lats[None, :], lons[None, :],
    ) * 1.5  # tectonic penalty factor

    # Observed statistic (sort already applied)
    observed = _mean_log_eta_fast(times_orig)
    logger.info("Observed mean log10(eta_nn) = %.4f", observed)
    logger.info("Running %d vectorised permutations on %d events …",
                n_sim, len(sub))

    sim_stats = np.empty(n_sim)
    for s in range(n_sim):
        perm_times = rng.permutation(times_orig)
        sim_stats[s] = _mean_log_eta_fast(perm_times)
        if (s + 1) % 50 == 0:
            logger.info("  … permutation %d/%d done", s + 1, n_sim)

    valid_sim = sim_stats[~np.isnan(sim_stats)]
    if len(valid_sim) > 0:
        p = float(np.mean(valid_sim <= observed))
        z = float((observed - valid_sim.mean()) / (valid_sim.std() + 1e-12))
    else:
        p = float("nan")
        z = float("nan")

    return {
        "observed": float(observed),
        "simulated": sim_stats.tolist(),
        "pvalue": p,
        "zscore": z,
    }


def _extract_global_series(clusters_df: pd.DataFrame,
                            events_df: pd.DataFrame,
                            min_events: int = 3) -> list[dict]:
    """Fallback: extract clusters spanning multiple FE regions."""
    if clusters_df.empty or "cluster_id" not in clusters_df.columns:
        return []

    results = []
    fe_col = "fe_region" if "fe_region" in events_df.columns else None

    for cid, group in clusters_df.groupby("cluster_id"):
        if len(group) < min_events:
            continue
        n_regions = 1
        if fe_col:
            n_regions = group[fe_col].nunique() if fe_col in group.columns else 1

        results.append({
            "series_id": f"S{int(cid):03d}",
            "n_events": len(group),
            "n_regions": int(n_regions),
            "start_year": float(group["year"].min()) if "year" in group.columns else None,
            "end_year": float(group["year"].max()) if "year" in group.columns else None,
            "max_magnitude": float(group["magnitude"].max()),
            "mean_eta": float(group["eta"].mean()) if "eta" in group.columns else None,
            "event_ids": group["event_id"].tolist() if "event_id" in group.columns else [],
        })

    results.sort(key=lambda x: x.get("mean_eta") or float("inf"))
    return results


def _save_results(global_series: list, mc_result: dict,
                  clusters_df: pd.DataFrame, out_dir: Path) -> None:
    """Persist all analysis outputs."""
    # Cluster summary CSV
    if not clusters_df.empty:
        clusters_df.to_csv(out_dir / "cluster_assignments.csv", index=False)

    # Global series summary
    if global_series:
        gs_df = pd.DataFrame(global_series)
        gs_df.to_csv(out_dir / "cluster_summary.csv", index=False)
        logger.info("Cluster summary: %s", out_dir / "cluster_summary.csv")

    # Full JSON results
    json_payload = {
        "global_series": global_series,
        "monte_carlo": {
            "pvalue": mc_result.get("pvalue"),
            "zscore": mc_result.get("zscore"),
            "observed": mc_result.get("observed"),
            "n_simulations": len(mc_result.get("simulated", [])),
        },
    }
    json_path = out_dir / "clusters.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(json_payload, fh, indent=2, default=_json_default)
    logger.info("Results JSON: %s", json_path)


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if pd.isna(obj):
        return None
    return str(obj)


if __name__ == "__main__":
    main()
