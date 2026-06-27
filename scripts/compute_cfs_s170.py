#!/usr/bin/env python
"""Compute ΔCFS for S170 receivers after the 2004 Sumatra M9.1 earthquake.

Assumptions (documented for reproducibility)
--------------------------------------------
* Source: GCMT-style Sumatra 2004 megathrust (lat 3.3°N, lon 95.8°E, M9.1;
  strike 320°, dip 10°, rake 110°; rupture 500×150 km, top depth 25 km).
* Static elastic half-space (Okada 1985 rectangular dislocation; ν=0.25, μ=30 GPa).
* Receivers: post-2004 events in Japan and Aleutians from S170 **or** catalog
  (M≥6.5, 2004–2016) when S170 has sparse coverage in those regions.
* Receiver fault planes: regional template mechanisms when MT unavailable
  (Japan/Kuril: strike 200°, dip 15°, rake 90°; Aleutians: strike 200°, dip 20°,
  rake 90°).
* ΔCFS = Δτ + 0.4·Δσ_n (King et al. 1994); positive ΔCFS → promoting failure.
* No viscoelastic relaxation, no poroelastic effects, no dynamic stresses.
* Focal mechanisms not fetched from GCMT/SCARDEC in this run (lightweight defaults).

Outputs
-------
    results/cfs_s170_analysis.json
    results/cfs_s170_events.csv
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.coulomb_stress import (
    batch_delta_cfs,
    sumatra_2004_source,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

JAPAN_KEYWORDS = ("japan", "kuril", "kamchatka", "ryukyu", "hokkaido", "honshu")
ALEUTIAN_KEYWORDS = ("aleutian", "alaska peninsula", "alaska", "rat islands", "andreanof")


def _region_label(fe_region: str, lat: float, lon: float) -> str:
    """Assign Japan vs Aleutians vs other from FE region string and coordinates."""
    fe = (fe_region or "").lower()
    if any(k in fe for k in JAPAN_KEYWORDS) or (24 <= lat <= 52 and 125 <= lon <= 155):
        return "Japan"
    if any(k in fe for k in ALEUTIAN_KEYWORDS) or (48 <= lat <= 62 and -180 <= lon <= -155):
        return "Aleutians"
    return "other"


def load_s170_event_ids() -> list[str]:
    """Load S170 event IDs from clusters.json or cluster_summary.csv."""
    clusters_path = ROOT / "results" / "clusters.json"
    if clusters_path.exists():
        with open(clusters_path, encoding="utf-8") as f:
            data = json.load(f)
        for series in data.get("series", data.get("global_series", data.get("clusters", []))):
            if series.get("series_id") == "S170":
                return list(series["event_ids"])
    summary = ROOT / "results" / "cluster_summary.csv"
    if summary.exists():
        row = pd.read_csv(summary)
        s170 = row[row["series_id"] == "S170"]
        if not s170.empty:
            import ast
            return ast.literal_eval(s170.iloc[0]["event_ids"])
    raise FileNotFoundError("S170 not found in results/clusters.json or cluster_summary.csv")


def load_catalog_receivers(catalog: pd.DataFrame, s170_ids: set[str]) -> pd.DataFrame:
    """Post-Sumatra receivers in Japan and Aleutians (S170 members or catalog)."""
    catalog = catalog.copy()
    catalog["region_group"] = catalog.apply(
        lambda r: _region_label(str(r.get("fe_region", r.get("region", ""))), r["lat"], r["lon"]),
        axis=1,
    )
    in_target = catalog["region_group"].isin(["Japan", "Aleutians"])
    post_sumatra = catalog["year"] >= 2004
    s170_mask = catalog["event_id"].isin(s170_ids) & in_target & post_sumatra
    catalog_mask = in_target & post_sumatra & (catalog["year"] <= 2016) & (catalog["magnitude"] >= 6.5)
    receivers = catalog[s170_mask | catalog_mask].drop_duplicates(subset=["event_id"])
    receivers["from_s170"] = receivers["event_id"].isin(s170_ids)
    return receivers


def main() -> None:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    if not catalog_path.exists():
        logger.error("Catalog not found: %s", catalog_path)
        sys.exit(1)

    event_ids = load_s170_event_ids()
    s170_id_set = set(event_ids)
    logger.info("S170: %d event IDs", len(event_ids))

    catalog = pd.read_csv(catalog_path)
    receivers_df = load_catalog_receivers(catalog, s170_id_set)
    logger.info(
        "Post-2004 Japan/Aleutians receivers: %d (S170 members: %d)",
        len(receivers_df),
        int(receivers_df["from_s170"].sum()),
    )

    source = sumatra_2004_source()
    receiver_dicts = [
        {
            "event_id": row["event_id"],
            "year": float(row["year"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "magnitude": float(row["magnitude"]),
            "depth_km": float(row["depth_km"]) if pd.notna(row.get("depth_km")) else 10.0,
            "region": row["region_group"],
            "fe_region": str(row.get("fe_region", "")),
            "from_s170": bool(row["from_s170"]),
        }
        for _, row in receivers_df.iterrows()
    ]

    results = batch_delta_cfs(source, receiver_dicts)

    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    df_out = pd.DataFrame(results)
    csv_path = out_dir / "cfs_s170_events.csv"
    df_out.to_csv(csv_path, index=False)
    logger.info("Saved %s", csv_path)

    def _summary(group: str) -> dict:
        sub = df_out[df_out["region"] == group]
        if sub.empty:
            return {"n": 0, "mean_dcfs_kpa": None, "median_dcfs_kpa": None, "pct_promoting": None}
        return {
            "n": int(len(sub)),
            "mean_dcfs_kpa": float(sub["dcfs_kpa"].mean()),
            "median_dcfs_kpa": float(sub["dcfs_kpa"].median()),
            "min_dcfs_kpa": float(sub["dcfs_kpa"].min()),
            "max_dcfs_kpa": float(sub["dcfs_kpa"].max()),
            "pct_promoting": float(100.0 * sub["promotes_failure"].mean()),
        }

    analysis = {
        "series_id": "S170",
        "source_event": "Sumatra 2004 M9.1",
        "source_parameters": {
            "lat": source.lat,
            "lon": source.lon,
            "depth_km": source.depth_km,
            "strike": source.strike,
            "dip": source.dip,
            "rake": source.rake,
            "magnitude": source.magnitude,
            "length_km": source.length_km,
            "width_km": source.width_km,
        },
        "method": "Okada (1985) rectangular dislocation, half-space",
        "mu_friction": 0.4,
        "receiver_window": "year >= 2004, <= 2016, Japan and Aleutians (S170 or catalog M>=6.5)",
        "n_receivers_total": len(results),
        "summary_by_region": {
            "Japan": _summary("Japan"),
            "Aleutians": _summary("Aleutians"),
        },
        "events": results,
    }

    json_path = out_dir / "cfs_s170_analysis.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", json_path)

    for region in ("Japan", "Aleutians"):
        s = analysis["summary_by_region"][region]
        logger.info(
            "%s: n=%s mean ΔCFS=%.4f kPa median=%.4f kPa pct promoting=%.1f%%",
            region,
            s["n"],
            s["mean_dcfs_kpa"] or 0,
            s["median_dcfs_kpa"] or 0,
            s["pct_promoting"] or 0,
        )


if __name__ == "__main__":
    main()
