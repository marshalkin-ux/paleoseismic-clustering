#!/usr/bin/env python
"""
Step 3 — Generate all publication-quality figures.

Reads outputs from run_analysis.py (cluster_summary.csv, clusters.json,
null_scores.npy, events_with_nn.csv) and the unified catalogue, then
produces eight static figures plus an interactive HTML map.

Outputs (in figures/)
---------------------
fig01_global_catalogue.png   — All events coloured by magnitude
fig02_cluster_map.png        — Events coloured by global series ID
fig03_event_density.png      — KDE density over time with cluster bands
fig04_series_timelines.png   — One timeline per top-10 global series
fig05_iei_distribution.png   — Inter-event interval histograms
fig06_null_distribution.png  — Monte Carlo null vs. observed statistic
fig07_completeness_surface.png — Mc over time / region heatmap
fig08_gr_curve.png           — Gutenberg–Richter frequency-magnitude plot
cluster_map_interactive.html — Folium interactive map (for web / digest)

Usage
-----
    python scripts/generate_figures.py [--config CONFIG] [--results DIR]
                                       [--output DIR] [--format png|pdf]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib
matplotlib.use("Agg")  # non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_catalogue(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _savefig(fig: plt.Figure, out_dir: Path, name: str, fmt: str) -> None:
    path = out_dir / f"{name}.{fmt}"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", path)


def _apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.dpi": 150,
    })


SERIES_COLORS = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#a65628", "#f781bf", "#999999",
    "#1b9e77", "#d95f02",
]


# ── Figure functions ───────────────────────────────────────────────────────────

def fig_global_catalogue(cat: pd.DataFrame, out_dir: Path, fmt: str) -> None:
    """Fig 01 — global scatter coloured by magnitude."""
    fig, ax = plt.subplots(figsize=(14, 7))
    lat = cat["lat"] if "lat" in cat.columns else cat["latitude"]
    lon = cat["lon"] if "lon" in cat.columns else cat["longitude"]
    mag = cat["magnitude"].fillna(6.5)

    sc = ax.scatter(lon, lat, c=mag, cmap="hot_r", vmin=6.5, vmax=9.5,
                    s=(mag - 6.0) ** 2.5, alpha=0.4, linewidths=0, rasterized=True)
    plt.colorbar(sc, ax=ax, label="Magnitude (Mw)")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title(f"Global M ≥ 6.5 Earthquake Catalogue "
                 f"({int(cat['year'].min())}–{int(cat['year'].max())})\n"
                 f"n = {len(cat):,} events")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.axhline(0, color="k", lw=0.3, ls="--")
    _savefig(fig, out_dir, "fig01_global_catalogue", fmt)


def fig_cluster_map(cat: pd.DataFrame, global_series: list[dict],
                    out_dir: Path, fmt: str) -> None:
    """Fig 02 — events coloured by global series membership."""
    if not global_series:
        logger.warning("No global series for fig02")
        return

    fig, ax = plt.subplots(figsize=(14, 7))
    lat = cat["lat"] if "lat" in cat.columns else cat["latitude"]
    lon = cat["lon"] if "lon" in cat.columns else cat["longitude"]

    # Background: all events in light grey
    ax.scatter(lon, lat, c="#cccccc", s=4, alpha=0.3, linewidths=0, rasterized=True)

    # Overlay top-10 global series
    for idx, series in enumerate(global_series[:10]):
        ids = set(series.get("event_ids", []))
        sub = cat[cat["event_id"].isin(ids)] if "event_id" in cat.columns else cat.iloc[:0]
        if sub.empty:
            continue
        slat = sub["lat"] if "lat" in sub.columns else sub["latitude"]
        slon = sub["lon"] if "lon" in sub.columns else sub["longitude"]
        smag = sub["magnitude"].fillna(6.5)
        color = SERIES_COLORS[idx % len(SERIES_COLORS)]
        ax.scatter(slon, slat, c=color,
                   s=(smag - 5.5) ** 2.5, alpha=0.75, linewidths=0.3,
                   edgecolors="white", label=series.get("series_id", f"S{idx}"),
                   zorder=3)

    ax.legend(loc="lower left", fontsize=7, ncol=2, framealpha=0.8)
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title("Top-10 Global Earthquake Series (M ≥ 6.5)")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    _savefig(fig, out_dir, "fig02_cluster_map", fmt)


def fig_event_density(cat: pd.DataFrame, global_series: list[dict],
                      out_dir: Path, fmt: str) -> None:
    """Fig 03 — KDE event density over time with series bands."""
    from scipy.stats import gaussian_kde

    fig, ax = plt.subplots(figsize=(12, 4))
    years = cat["year"].dropna().astype(float).values
    years = years[np.isfinite(years)]

    if len(years) < 2:
        logger.warning("Not enough data for density plot")
        return

    x = np.linspace(years.min(), years.max(), 1000)
    kde = gaussian_kde(years, bw_method=0.05)
    density = kde(x)

    ax.fill_between(x, density, alpha=0.3, color="#377eb8")
    ax.plot(x, density, color="#377eb8", lw=1.5, label="Event density (KDE)")

    # Mark top-5 series as coloured bands
    for idx, series in enumerate(global_series[:5]):
        s = series.get("start_year")
        e = series.get("end_year")
        if s is not None and e is not None:
            ax.axvspan(s, max(e, s + 1), alpha=0.2,
                       color=SERIES_COLORS[idx % len(SERIES_COLORS)],
                       label=series.get("series_id", f"S{idx}"))

    ax.set_xlabel("Year")
    ax.set_ylabel("Event density (KDE)")
    ax.set_title("Global M ≥ 6.5 Seismicity Rate and Identified Series")
    ax.legend(fontsize=8, loc="upper left")
    _savefig(fig, out_dir, "fig03_event_density", fmt)


def fig_series_timelines(cat: pd.DataFrame, global_series: list[dict],
                         out_dir: Path, fmt: str) -> None:
    """Fig 04 — horizontal timelines for top-10 series."""
    top = global_series[:10]
    if not top:
        return

    n = len(top)
    fig, axes = plt.subplots(n, 1, figsize=(12, max(n * 0.9, 4)), sharex=False)
    if n == 1:
        axes = [axes]

    for i, (series, ax) in enumerate(zip(top, axes)):
        ids = set(series.get("event_ids", []))
        sub = cat[cat["event_id"].isin(ids)] if "event_id" in cat.columns else cat.iloc[:0]
        if sub.empty:
            ax.set_yticks([])
            ax.set_title(series.get("series_id", f"S{i}"), fontsize=8)
            continue

        yr = (sub["year"].fillna(0).astype(float) +
              (sub["month"].fillna(6).astype(float) - 1) / 12.0 +
              (sub["day"].fillna(15).astype(float) - 1) / 365.25)
        mag = sub["magnitude"].fillna(6.5)
        color = SERIES_COLORS[i % len(SERIES_COLORS)]

        ax.scatter(yr, np.ones(len(yr)), s=(mag - 5.5) ** 2.5,
                   c=color, alpha=0.8, edgecolors="white", linewidths=0.4, zorder=3)
        ax.set_ylim(0.5, 1.5)
        ax.set_yticks([])
        label = (f"{series.get('series_id','?')} | "
                 f"n={series.get('n_events','?')} | "
                 f"Mmax={series.get('max_magnitude','?'):.1f} | "
                 f"regions={series.get('n_regions','?')}")
        ax.set_title(label, fontsize=8, loc="left")
        ax.tick_params(axis="x", labelsize=7)

    fig.suptitle("Top-10 Global Earthquake Series — Event Timelines", y=1.01)
    fig.tight_layout()
    _savefig(fig, out_dir, "fig04_series_timelines", fmt)


def fig_iei_distribution(cat: pd.DataFrame, global_series: list[dict],
                          out_dir: Path, fmt: str) -> None:
    """Fig 05 — inter-event interval (IEI) histograms for top-5 series."""
    top = [s for s in global_series[:5] if s.get("n_events", 0) >= 3]
    if not top:
        return

    fig, axes = plt.subplots(1, len(top), figsize=(3.5 * len(top), 4), sharey=False)
    if len(top) == 1:
        axes = [axes]

    for ax, series in zip(axes, top):
        ids = set(series.get("event_ids", []))
        sub = cat[cat["event_id"].isin(ids)] if "event_id" in cat.columns else cat.iloc[:0]
        if sub.empty or len(sub) < 2:
            continue

        yr = (sub["year"].fillna(0).astype(float) +
              (sub["month"].fillna(6).astype(float) - 1) / 12.0)
        yr_sorted = np.sort(yr.values)
        ieis = np.diff(yr_sorted) * 365.25  # convert to days
        ieis = ieis[ieis > 0]

        ax.hist(ieis, bins=min(10, len(ieis)), color="#4daf4a", edgecolor="white",
                alpha=0.8)
        ax.axvline(np.median(ieis), color="red", ls="--", lw=1.2,
                   label=f"Median={np.median(ieis):.0f}d")
        ax.set_xlabel("Inter-event interval (days)")
        ax.set_ylabel("Count")
        ax.set_title(series.get("series_id", "?"), fontsize=9)
        ax.legend(fontsize=7)

    fig.suptitle("Inter-Event Interval Distributions")
    fig.tight_layout()
    _savefig(fig, out_dir, "fig05_iei_distribution", fmt)


def fig_null_distribution(mc: dict, out_dir: Path, fmt: str) -> None:
    """Fig 06 — Monte Carlo null distribution vs. observed statistic."""
    sim = np.array(mc.get("simulated", []))
    obs = mc.get("observed")
    p = mc.get("pvalue")
    z = mc.get("zscore")

    if len(sim) == 0 or obs is None:
        logger.warning("No MC data for fig06")
        return

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(sim, bins=30, color="#999999", edgecolor="white", alpha=0.7,
            label=f"Null distribution (n={len(sim):,})")
    ax.axvline(obs, color="#e41a1c", lw=2,
               label=f"Observed = {obs:.3f}")
    ax.set_xlabel("Mean log₁₀(η) nearest-neighbour statistic")
    ax.set_ylabel("Count")
    title = "Monte Carlo Permutation Test"
    if p is not None and not np.isnan(p):
        title += f"\np = {p:.3f}, z = {z:.2f}"
    ax.set_title(title)
    ax.legend()
    _savefig(fig, out_dir, "fig06_null_distribution", fmt)


def fig_completeness_surface(completeness_path: Path, out_dir: Path, fmt: str) -> None:
    """Fig 07 — Mc heatmap over decades × regions."""
    if not completeness_path.exists():
        logger.warning("completeness_surface.csv not found; skipping fig07")
        return

    df = pd.read_csv(completeness_path, index_col=0)
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(df.values.T, aspect="auto", cmap="RdYlGn_r",
                   vmin=5.5, vmax=8.5,
                   extent=[df.index.min(), df.index.max(), 0, df.shape[1]])
    plt.colorbar(im, ax=ax, label="Magnitude of Completeness (Mc)")
    ax.set_xlabel("Decade")
    ax.set_ylabel("FE Region index")
    ax.set_title("Magnitude of Completeness Surface (Mc) by Region and Decade")
    _savefig(fig, out_dir, "fig07_completeness_surface", fmt)


def fig_gr_curve(cat: pd.DataFrame, out_dir: Path, fmt: str) -> None:
    """Fig 08 — Gutenberg–Richter frequency–magnitude distribution."""
    mag = cat["magnitude"].dropna().values
    mag = mag[mag >= 5.0]

    if len(mag) < 10:
        return

    bins = np.arange(5.0, 10.0, 0.1)
    n_cum = np.array([np.sum(mag >= m) for m in bins])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.semilogy(bins, n_cum, "k.", ms=5, label="Observed N(≥M)")

    # G-R fit for M >= 6.5 (completeness range)
    fit_mask = bins >= 6.5
    if fit_mask.sum() >= 3:
        log_n = np.log10(n_cum[fit_mask] + 1e-6)
        coeffs = np.polyfit(bins[fit_mask], log_n, 1)
        b = -coeffs[0]
        fit_line = 10 ** np.polyval(coeffs, bins[fit_mask])
        ax.semilogy(bins[fit_mask], fit_line, "r-", lw=1.5,
                    label=f"G-R fit b = {b:.2f}")

    ax.axvline(6.5, color="grey", ls="--", lw=0.8, label="M₀ = 6.5 (completeness)")
    ax.set_xlabel("Magnitude (Mw)")
    ax.set_ylabel("Cumulative frequency N(≥M)")
    ax.set_title("Gutenberg–Richter Frequency–Magnitude Distribution")
    ax.legend()
    _savefig(fig, out_dir, "fig08_gr_curve", fmt)


def save_interactive_map(cat: pd.DataFrame, global_series: list[dict],
                          out_path: Path) -> None:
    """Generate Folium interactive HTML map."""
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        logger.warning("folium not installed; skipping interactive map")
        return

    lat = cat["lat"] if "lat" in cat.columns else cat.get("latitude", pd.Series())
    lon = cat["lon"] if "lon" in cat.columns else cat.get("longitude", pd.Series())

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    # Build event_id → series map
    id_to_series: dict[str, dict] = {}
    for s in global_series[:20]:
        for eid in s.get("event_ids", []):
            id_to_series[eid] = s

    mc = MarkerCluster().add_to(m)

    for _, row in cat.iterrows():
        eid = row.get("event_id", "")
        series = id_to_series.get(eid)
        color = "red" if series else "gray"
        tooltip = (f"M{row.get('magnitude','?'):.1f} | "
                   f"{int(row['year'])} | {row.get('region','')}")
        if series:
            tooltip += f" | {series.get('series_id','')}"
        folium.CircleMarker(
            location=[lat[row.name], lon[row.name]],
            radius=max(3, (row.get("magnitude", 6.5) - 5) * 1.5),
            color=color, fill=True, fill_opacity=0.5,
            tooltip=tooltip,
        ).add_to(mc)

    m.save(str(out_path))
    logger.info("Interactive map saved: %s", out_path)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate publication figures")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--results", default="data/processed")
    parser.add_argument("--output", default="figures")
    parser.add_argument("--format", default="png", choices=["png", "pdf"])
    args = parser.parse_args()

    with open(args.config) as fh:
        config = yaml.safe_load(fh)

    results_dir = Path(args.results)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = args.format

    _apply_style()

    # ── Load data ──────────────────────────────────────────────────────────────
    cat_path = results_dir / "unified_catalogue.csv"
    if not cat_path.exists():
        logger.error("unified_catalogue.csv not found — run download_data.py first")
        sys.exit(1)

    cat = _load_catalogue(cat_path)
    logger.info("Catalogue: %d events", len(cat))

    json_data = _load_json(results_dir / "clusters.json")
    global_series = json_data.get("global_series", [])
    mc_data = json_data.get("monte_carlo", {})
    logger.info("Global series: %d", len(global_series))

    null_path = results_dir / "null_scores.npy"
    null_scores = np.load(null_path) if null_path.exists() else np.array([])

    completeness_path = results_dir / "completeness_surface.csv"

    # If mc_data has simulated array from the json, use that
    if mc_data and "simulated" not in mc_data and len(null_scores) > 0:
        mc_data["simulated"] = null_scores.tolist()

    # Also load from clusters.json if the simulated array is in there
    if not mc_data.get("simulated"):
        sim_from_json = json_data.get("monte_carlo", {}).get("simulated", [])
        if sim_from_json:
            mc_data["simulated"] = sim_from_json

    # ── Generate figures ───────────────────────────────────────────────────────
    logger.info("Generating fig01 — global catalogue map …")
    fig_global_catalogue(cat, out_dir, fmt)

    logger.info("Generating fig02 — cluster map …")
    fig_cluster_map(cat, global_series, out_dir, fmt)

    logger.info("Generating fig03 — event density …")
    fig_event_density(cat, global_series, out_dir, fmt)

    logger.info("Generating fig04 — series timelines …")
    fig_series_timelines(cat, global_series, out_dir, fmt)

    logger.info("Generating fig05 — IEI distributions …")
    fig_iei_distribution(cat, global_series, out_dir, fmt)

    logger.info("Generating fig06 — null distribution …")
    fig_null_distribution(mc_data, out_dir, fmt)

    logger.info("Generating fig07 — completeness surface …")
    fig_completeness_surface(completeness_path, out_dir, fmt)

    logger.info("Generating fig08 — G-R curve …")
    fig_gr_curve(cat, out_dir, fmt)

    logger.info("Generating interactive HTML map …")
    save_interactive_map(cat, global_series, out_dir / "cluster_map_interactive.html")

    # Copy to paper/figures for LaTeX integration
    import shutil
    paper_fig_dir = Path("paper/figures")
    paper_fig_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob(f"fig0*.{fmt}"):
        shutil.copy2(f, paper_fig_dir / f.name)

    logger.info("\n=== All figures saved to %s ===", out_dir)


if __name__ == "__main__":
    main()
