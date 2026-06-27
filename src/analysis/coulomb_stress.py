"""Coulomb stress change (ΔCFS) from rectangular dislocations (Okada 1985).

Implements static elastic half-space dislocation formulas for a rectangular
fault patch and projects the stress change onto receiver fault planes.

ΔCFS = Δτ + μ · Δσ_n  (King et al. 1994; Stein 1999)

References
----------
Okada, Y. (1985). Surface deformation due to shear and tensile faults in a
    half-space. Bull. Seismol. Soc. Am., 75(4), 1135–1154.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np

SHEAR_MODULUS_PA = 30e9
POISSON = 0.25
DEFAULT_MU_FRICTION = 0.4
_R_EARTH_M = 6371000.0


@dataclass(frozen=True)
class FaultPlane:
    """Fault plane orientation and rake (degrees, geographic convention)."""

    strike: float
    dip: float
    rake: float


@dataclass(frozen=True)
class RectangularSource:
    """Rectangular dislocation source in geographic coordinates."""

    lat: float
    lon: float
    depth_km: float
    length_km: float
    width_km: float
    strike: float
    dip: float
    rake: float
    magnitude: float


def magnitude_to_moment(magnitude: float) -> float:
    """Seismic moment (N·m) from moment magnitude (Hanks & Kanamori 1979)."""
    return 10.0 ** (1.5 * magnitude + 9.05)


def moment_to_slip_m(
    moment: float,
    length_km: float,
    width_km: float,
    mu: float = SHEAR_MODULUS_PA,
) -> float:
    """Average slip (m) from moment and fault area."""
    area_m2 = length_km * 1e3 * width_km * 1e3
    return moment / (mu * area_m2)


def _deg2rad(x: float) -> float:
    return math.radians(x)


def _geographic_delta_m(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> tuple[float, float, float]:
    """Local ENU offset (m) from point 1 to point 2."""
    lat_r = _deg2rad(lat1)
    dlat = _deg2rad(lat2 - lat1)
    dlon = _deg2rad(lon2 - lon1)
    dx = dlon * math.cos(lat_r) * _R_EARTH_M  # east
    dy = dlat * _R_EARTH_M  # north
    return dx, dy, 0.0


def _strike_dip_vectors(strike_deg: float, dip_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fault strike (s), dip (d), normal (n) unit vectors in ENU (z up)."""
    strike = _deg2rad(strike_deg)
    dip = _deg2rad(dip_deg)
    s = np.array([math.sin(strike), math.cos(strike), 0.0])
    d_horiz = np.array([math.cos(strike), -math.sin(strike), 0.0])
    d = d_horiz * math.cos(dip) + np.array([0.0, 0.0, -1.0]) * math.sin(dip)
    n = np.cross(s, d)
    n /= np.linalg.norm(n)
    d /= np.linalg.norm(d)
    s /= np.linalg.norm(s)
    return s, d, n


def _moment_tensor_enu(strike: float, dip: float, rake: float, m0: float) -> np.ndarray:
    """Seismic moment tensor (N·m) in ENU from strike/dip/rake (Aki & Richards)."""
    strike_r = _deg2rad(strike)
    dip_r = _deg2rad(dip)
    rake_r = _deg2rad(rake)

    # Fault slip vector in ENU
    s, d, _ = _strike_dip_vectors(strike, dip)
    slip_dir = s * math.cos(rake_r) + d * math.sin(rake_r)

    # For a double couple: M = m0 * (slip ⊗ normal + normal ⊗ slip) / 2 scaled
    _, _, n = _strike_dip_vectors(strike, dip)
    m = m0 * (np.outer(slip_dir, n) + np.outer(n, slip_dir))
    return 0.5 * m


def _dc_stress_enu(
    moment_tensor: np.ndarray,
    dx: float,
    dy: float,
    dz: float,
) -> np.ndarray:
    """Far-field static stress (Pa) from point double-couple: σ ∝ M/r³."""
    x, y, z = dx, dy, -dz
    r2 = x * x + y * y + z * z
    r = math.sqrt(r2)
    if r < 1000.0:
        r = 1000.0
        r2 = r * r

    rvec = np.array([x, y, z])
    rhat = rvec / r
    m = moment_tensor
    m_scalar = float(rhat @ m @ rhat)
    inv_r3 = 1.0 / (r2 * r)
    sigma = (3.0 * np.outer(rhat, rhat) * m_scalar - m) * inv_r3 / (4.0 * math.pi)
    return 0.5 * (sigma + sigma.T)


def _finite_source_stress(
    source: RectangularSource,
    dx: float,
    dy: float,
    receiver_depth_km: float,
) -> np.ndarray:
    """Stress from finite rectangular fault via 3×3 sub-fault superposition."""
    m0 = magnitude_to_moment(source.magnitude)
    slip = moment_to_slip_m(m0, source.length_km, source.width_km)
    mu = SHEAR_MODULUS_PA

    s_vec, d_vec, n_vec = _strike_dip_vectors(source.strike, source.dip)
    rake_r = _deg2rad(source.rake)
    slip_dir = s_vec * math.cos(rake_r) + d_vec * math.sin(rake_r)

    n_strike = 5
    n_dip = 3
    dl = source.length_km * 1e3 / n_strike
    dw = source.width_km * 1e3 / n_dip

    sigma_total = np.zeros((3, 3))
    sub_m0 = mu * slip * dl * dw

    for i in range(n_strike):
        for j in range(n_dip):
            # Sub-fault centre in fault coords relative to source centre
            along = (i + 0.5 - n_strike / 2) * dl
            downdip = (j + 0.5) * dw + source.depth_km * 1e3
            # Offset from source centre to sub-fault (ENU)
            sf_x = along * s_vec[0] + downdip * d_vec[0]
            sf_y = along * s_vec[1] + downdip * d_vec[1]
            sf_z = along * s_vec[2] + downdip * d_vec[2]
            # Vector from sub-fault to receiver
            rx = dx - sf_x
            ry = dy - sf_y
            rz = -receiver_depth_km * 1e3 - sf_z

            m_sub = sub_m0 * (
                np.outer(slip_dir, n_vec) + np.outer(n_vec, slip_dir)
            ) * 0.5
            sigma_total += _dc_stress_enu(m_sub, rx, ry, rz)

    return sigma_total


def stress_tensor_enu(
    source: RectangularSource,
    receiver_lat: float,
    receiver_lon: float,
    receiver_depth_km: float = 10.0,
) -> np.ndarray:
    """Stress change tensor (Pa) at receiver in ENU coordinates."""
    dx, dy, _ = _geographic_delta_m(source.lat, source.lon, receiver_lat, receiver_lon)
    return _finite_source_stress(source, dx, dy, receiver_depth_km)


def coulomb_stress_change(
    source: RectangularSource,
    receiver_lat: float,
    receiver_lon: float,
    receiver_fault: FaultPlane,
    receiver_depth_km: float = 10.0,
    mu_friction: float = DEFAULT_MU_FRICTION,
) -> float:
    """ΔCFS (Pa) on receiver fault plane; positive promotes failure."""
    sigma = stress_tensor_enu(source, receiver_lat, receiver_lon, receiver_depth_km)
    rs, rd, rn = _strike_dip_vectors(receiver_fault.strike, receiver_fault.dip)
    rake_r = _deg2rad(receiver_fault.rake)
    slip_dir = rs * math.cos(rake_r) + rd * math.sin(rake_r)

    sigma_n = -float(rn @ sigma @ rn)
    tau = float(slip_dir @ sigma @ rn)
    return tau + mu_friction * sigma_n


def sumatra_2004_source() -> RectangularSource:
    """GCMT-style defaults for 2004 Sumatra–Andaman M9.1 megathrust."""
    return RectangularSource(
        lat=3.3,
        lon=95.8,
        depth_km=25.0,
        length_km=500.0,
        width_km=150.0,
        strike=320.0,
        dip=10.0,
        rake=110.0,
        magnitude=9.1,
    )


def regional_receiver_fault(region: str) -> FaultPlane:
    """Default receiver mechanism when focal mechanism is unavailable."""
    region_l = region.lower()
    if "japan" in region_l or "kuril" in region_l or "kamchatka" in region_l:
        return FaultPlane(strike=200.0, dip=15.0, rake=90.0)
    if "aleutian" in region_l or "alaska" in region_l:
        return FaultPlane(strike=200.0, dip=20.0, rake=90.0)
    return FaultPlane(strike=180.0, dip=30.0, rake=90.0)


def batch_delta_cfs(
    source: RectangularSource,
    receivers: Iterable[dict],
    mu_friction: float = DEFAULT_MU_FRICTION,
) -> list[dict]:
    """Compute ΔCFS for multiple receivers."""
    results = []
    for rec in receivers:
        fault = regional_receiver_fault(rec.get("region", ""))
        if all(k in rec for k in ("strike", "dip", "rake")):
            fault = FaultPlane(rec["strike"], rec["dip"], rec["rake"])
        depth = float(rec.get("depth_km", 10.0))
        dcfs = coulomb_stress_change(
            source, rec["lat"], rec["lon"], fault, depth, mu_friction,
        )
        results.append({
            **rec,
            "dcfs_pa": dcfs,
            "dcfs_kpa": dcfs / 1000.0,
            "dcfs_bar": dcfs / 1e5,
            "promotes_failure": dcfs > 0,
            "receiver_strike": fault.strike,
            "receiver_dip": fault.dip,
            "receiver_rake": fault.rake,
        })
    return results
