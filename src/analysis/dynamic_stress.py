"""Dynamic stress from teleseismic surface waves (Rayleigh & Love).

Estimates peak ground velocity (PGV) from a point-source Brune/Boatwright-style
spectrum with geometric spreading and anelastic attenuation, then converts PGV
to peak dynamic shear stress following Hill et al. (1993) and Gomberg (2001).

References
----------
Boatwright, J., & Choy, G. L. (1986). Teleseismic spectral estimates of
    seismic source parameters. Bull. Seismol. Soc. Am., 76(1), 73–87.
Brune, J. N. (1970, 1971). Tectonic stress and spectra of seismic shear waves.
    J. Geophys. Res., 75(26), 4997–5009; 76(14), 3772–3785.
Gomberg, J. (2001). Triggered earthquakes and the 1992 Landers, California,
    earthquake. Bull. Seismol. Soc. Am., 91(6), 1574–1583.
Hill, D. P., et al. (1993). Seismicity remotely triggered by the magnitude
    7.3 Landers, California, earthquake. Science, 260(5114), 1617–1623.
Stein, R. S. (1999). The role of stress transfer in earthquake occurrence.
    Nature, 402(6762), 605–609.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from src.analysis.coulomb_stress import magnitude_to_moment
from src.analysis.tectonic_distance import haversine

# Material and wave defaults (crustal receiver)
SHEAR_MODULUS_PA = 30e9  # 30 GPa
SHEAR_VELOCITY_M_S = 3500.0  # β, m/s
CRUSTAL_DENSITY_KG_M3 = 3300.0

# Dynamic triggering thresholds (literature range)
THRESHOLD_SIGMA_LOW_MPA = 0.01  # 10 kPa — lower bound (Hill et al. 1993; Gomberg 2001)
THRESHOLD_SIGMA_HIGH_MPA = 0.1  # 100 kPa — upper bound (Stein 1999; Parsons & Velasco 2011)

# Sumatra 2004 source (GCMT-style)
SUMATRA_2004_LAT = 3.3
SUMATRA_2004_LON = 95.8
SUMATRA_2004_MW = 9.1


@dataclass(frozen=True)
class SurfaceWaveBand:
    """Surface-wave band parameters for amplitude and attenuation."""

    name: str  # "Rayleigh" or "Love"
    frequency_hz: float
    group_velocity_km_s: float
    quality_factor: float
    excitation_factor: float = 1.0  # radiation / mode partition


@dataclass(frozen=True)
class DynamicStressResult:
    """Per-receiver dynamic stress estimate."""

    event_id: str
    lat: float
    lon: float
    distance_km: float
    pgv_rayleigh_m_s: float
    pgv_love_m_s: float
    pgv_max_m_s: float
    sigma_dyn_rayleigh_mpa: float
    sigma_dyn_love_mpa: float
    sigma_dyn_max_mpa: float
    exceeds_0_01_mpa: bool
    exceeds_0_1_mpa: bool


def brune_corner_frequency_hz(
    magnitude: float,
    *,
    delta_sigma_bars: float = 20.0,
    shear_velocity_m_s: float = SHEAR_VELOCITY_M_S,
    fault_length_km: float | None = None,
) -> float:
    """Corner frequency (Hz) from Brune (1970, 1971) ω-square model.

    For large megathrusts (Mw ≥ 8.5) the stress-drop form with Δσ = 20 bar
    overestimates *f_c*; we prefer the fault-length scaling (Brune 1970):

        f_c ≈ 2.34 β / (2π L)

    with β in km/s and L the rupture length in km.  For smaller events we fall
    back to the empirical relation f_c = 10^(2.24 − 0.5 Mw) (Hz).
    """
    if fault_length_km is not None and magnitude >= 8.5:
        beta_km_s = shear_velocity_m_s / 1000.0
        return max(2.34 * beta_km_s / (2.0 * math.pi * fault_length_km), 1e-4)
    return max(10.0 ** (2.24 - 0.5 * magnitude), 1e-4)


def brune_displacement_spectrum(m0: float, frequency_hz: float, fc_hz: float) -> float:
    """Brune (1970) far-field displacement spectrum Ω(f) in m·s (single-sided)."""
    return m0 / (1.0 + (frequency_hz / fc_hz) ** 2)


def brune_far_field_velocity(
    magnitude: float,
    frequency_hz: float,
    distance_km: float,
    *,
    fault_length_km: float = 500.0,
    delta_sigma_bars: float = 20.0,
) -> float:
    """Far-field velocity amplitude (m/s) at frequency *f* and distance *r*.

    Shearer (2009, Eq. 9.46) / Brune (1970) ω-square scaling:

        V(f, r) = R · M0 · f² / [4π ρ β³ r (1 + (f/f_c)²)]

    with *r* in metres.  Boatwright & Choy (1986) use the same spectral shape
    for teleseismic *P*-wave spectra; here we apply it to long-period surface-
    wave bands with mode-specific excitation factors (see ``SurfaceWaveBand``).
    """
    m0 = magnitude_to_moment(magnitude)
    fc = brune_corner_frequency_hz(
        magnitude,
        delta_sigma_bars=delta_sigma_bars,
        fault_length_km=fault_length_km,
    )
    r_m = max(distance_km, 1.0) * 1000.0
    denom = (
        4.0
        * math.pi
        * CRUSTAL_DENSITY_KG_M3
        * SHEAR_VELOCITY_M_S ** 3
        * r_m
        * (1.0 + (frequency_hz / fc) ** 2)
    )
    return m0 * frequency_hz ** 2 / denom


def surface_wave_amplitude(
    far_field_velocity_m_s: float,
    distance_km: float,
    frequency_hz: float,
    group_velocity_km_s: float,
    quality_factor: float,
) -> float:
    """Apply anelastic attenuation to far-field velocity amplitude.

    The input ``far_field_velocity_m_s`` already includes Brune far-field
    geometric decay ∝ 1/*r* (Shearer 2009).  At teleseismic distances this
    dominates over the cylindrical 1/√r envelope factor; we apply only
    anelastic attenuation (Hill et al. 1993; Lay & Wallace 1995):

        A(r) = V_far · exp(−π f r / (Q U))

    with *r* in km, *U* in km/s, *f* in Hz.
    """
    r_km = max(distance_km, 1.0)
    atten = math.exp(
        -math.pi * frequency_hz * r_km / (quality_factor * group_velocity_km_s)
    )
    return far_field_velocity_m_s * atten


def pgv_from_surface_waves(
    magnitude: float,
    distance_km: float,
    band: SurfaceWaveBand,
    *,
    fault_length_km: float = 500.0,
    delta_sigma_bars: float = 20.0,
) -> float:
    """Peak ground velocity (m/s) for one surface-wave mode."""
    v_far = brune_far_field_velocity(
        magnitude,
        band.frequency_hz,
        distance_km,
        fault_length_km=fault_length_km,
        delta_sigma_bars=delta_sigma_bars,
    )
    amp = surface_wave_amplitude(
        v_far * band.excitation_factor,
        distance_km,
        band.frequency_hz,
        band.group_velocity_km_s,
        band.quality_factor,
    )
    return amp


def dynamic_stress_from_pgv(
    pgv_m_s: float,
    *,
    shear_modulus_pa: float = SHEAR_MODULUS_PA,
    shear_velocity_m_s: float = SHEAR_VELOCITY_M_S,
    method: str = "hill",
) -> float:
    """Peak dynamic shear stress (Pa) from peak ground velocity.

    Hill et al. (1993); Gomberg (2001):
        σ_dyn ≈ μ · PGV / β

    Alternative (phase velocity *c* form, Gomberg 2001 appendix):
        σ_dyn ≈ 2 · μ · PGV / (π · c)

    Returns stress in Pascals; divide by 1e6 for MPa.
    """
    if method == "gomberg":
        c = shear_velocity_m_s  # approximate phase velocity with β
        return 2.0 * shear_modulus_pa * pgv_m_s / (math.pi * c)
    return shear_modulus_pa * pgv_m_s / shear_velocity_m_s


def default_rayleigh_band() -> SurfaceWaveBand:
    """Default Rayleigh band for teleseismic M9 surface waves."""
    return SurfaceWaveBand(
        name="Rayleigh",
        frequency_hz=0.015,
        group_velocity_km_s=4.0,
        quality_factor=450.0,
        excitation_factor=0.25,
    )


def default_love_band() -> SurfaceWaveBand:
    """Default Love band for teleseismic M9 surface waves."""
    return SurfaceWaveBand(
        name="Love",
        frequency_hz=0.025,
        group_velocity_km_s=3.5,
        quality_factor=350.0,
        excitation_factor=0.20,
    )


def compute_dynamic_stress(
    receiver_lat: float,
    receiver_lon: float,
    *,
    source_lat: float = SUMATRA_2004_LAT,
    source_lon: float = SUMATRA_2004_LON,
    magnitude: float = SUMATRA_2004_MW,
    event_id: str = "",
    rayleigh_band: SurfaceWaveBand | None = None,
    love_band: SurfaceWaveBand | None = None,
    stress_method: str = "hill",
) -> DynamicStressResult:
    """Full dynamic stress estimate for one receiver."""
    rayleigh_band = rayleigh_band or default_rayleigh_band()
    love_band = love_band or default_love_band()

    dist_km = haversine(source_lat, source_lon, receiver_lat, receiver_lon)

    pgv_r = pgv_from_surface_waves(magnitude, dist_km, rayleigh_band)
    pgv_l = pgv_from_surface_waves(magnitude, dist_km, love_band)
    pgv_max = max(pgv_r, pgv_l)

    sig_r = dynamic_stress_from_pgv(pgv_r, method=stress_method) / 1e6
    sig_l = dynamic_stress_from_pgv(pgv_l, method=stress_method) / 1e6
    sig_max = max(sig_r, sig_l)

    return DynamicStressResult(
        event_id=event_id,
        lat=receiver_lat,
        lon=receiver_lon,
        distance_km=dist_km,
        pgv_rayleigh_m_s=pgv_r,
        pgv_love_m_s=pgv_l,
        pgv_max_m_s=pgv_max,
        sigma_dyn_rayleigh_mpa=sig_r,
        sigma_dyn_love_mpa=sig_l,
        sigma_dyn_max_mpa=sig_max,
        exceeds_0_01_mpa=sig_max >= THRESHOLD_SIGMA_LOW_MPA,
        exceeds_0_1_mpa=sig_max >= THRESHOLD_SIGMA_HIGH_MPA,
    )


def batch_dynamic_stress(
    receivers: Iterable[dict],
    *,
    source_lat: float = SUMATRA_2004_LAT,
    source_lon: float = SUMATRA_2004_LON,
    magnitude: float = SUMATRA_2004_MW,
    stress_method: str = "hill",
) -> list[dict]:
    """Compute dynamic stress for multiple receivers; returns serialisable dicts."""
    results = []
    for rec in receivers:
        out = compute_dynamic_stress(
            rec["lat"],
            rec["lon"],
            source_lat=source_lat,
            source_lon=source_lon,
            magnitude=magnitude,
            event_id=str(rec.get("event_id", "")),
            stress_method=stress_method,
        )
        results.append({
            **rec,
            "distance_km": out.distance_km,
            "pgv_rayleigh_m_s": out.pgv_rayleigh_m_s,
            "pgv_love_m_s": out.pgv_love_m_s,
            "pgv_max_m_s": out.pgv_max_m_s,
            "pgv_rayleigh_cm_s": out.pgv_rayleigh_m_s * 100.0,
            "pgv_love_cm_s": out.pgv_love_m_s * 100.0,
            "pgv_max_cm_s": out.pgv_max_m_s * 100.0,
            "sigma_dyn_rayleigh_mpa": out.sigma_dyn_rayleigh_mpa,
            "sigma_dyn_love_mpa": out.sigma_dyn_love_mpa,
            "sigma_dyn_max_mpa": out.sigma_dyn_max_mpa,
            "exceeds_0_01_mpa": out.exceeds_0_01_mpa,
            "exceeds_0_1_mpa": out.exceeds_0_1_mpa,
        })
    return results
