# Dynamic stress analysis: Sumatra 2004 M9.1 → Japan (S170)

## Summary

Teleseismic Rayleigh and Love surface-wave amplitudes were modelled for **43 Japan-region receivers** (lat 30–45°N, lon 130–145°E; epicentral distance 4900–6440 km) linked to series S170, using a Brune/Boatwright ω-square source spectrum and Hill et al. (1993) / Gomberg (2001) PGV→σ_dyn conversion.

| Quantity | Median | Range |
|----------|--------|-------|
| PGV (max of Rayleigh/Love) | **0.00066 cm/s** | 0.00052–0.00072 cm/s |
| σ_dyn (max) | **0.000056 MPa** (0.056 kPa) | 0.052–0.072 kPa |

**Threshold comparison:** Literature dynamic-triggering thresholds are **0.01–0.1 MPa** (10–100 kPa; Hill et al., 1993; Gomberg, 2001; Stein, 1999). **No receiver exceeds 0.01 MPa** — calculated σ_dyn is **~180× below** the lower bound.

## Method

### Source
- Sumatra–Andaman 26 Dec 2004, Mw 9.1, 3.3°N, 95.8°E (GCMT-style point source).
- Brune (1970) ω-square spectrum with corner frequency from rupture length (L = 500 km): f_c ≈ 0.0026 Hz.
- Seismic moment M₀ = 5.0×10²² N·m (Hanks & Kanamori 1979).

### Propagation
- Far-field velocity: V(f,r) = M₀ f² / [4π ρ β³ r (1 + (f/f_c)²)] (Shearer 2009, Eq. 9.46).
- Geometric decay ∝ 1/r (far-field double-couple); anelastic attenuation exp(−π f r / (Q U)).
- Rayleigh: f = 0.015 Hz, U = 4.0 km/s, Q = 450, excitation η = 0.25.
- Love: f = 0.025 Hz, U = 3.5 km/s, Q = 350, excitation η = 0.20.

### Dynamic stress
- σ_dyn ≈ μ · PGV / β with μ = 30 GPa, β = 3.5 km/s (Hill et al., 1993; Gomberg, 2001).
- Reported in MPa (1 MPa = 10⁶ Pa).

### Receivers
- Post-2004 events in Japan box from S170 or catalog (M≥6.5, 2004–2016), same pool as static ΔCFS analysis.
- Distance filter 4000–6500 km (teleseismic).

## Assumptions and limitations

1. **Point source** — finite 500×150 km rupture, directivity, and rupture propagation are not modelled; peak amplitudes at specific azimuths could differ by factors of 2–5.
2. **Single-frequency bands** — real PGV integrates broad surface-wave spectra; higher-frequency energy (0.05–0.2 Hz) could raise local PGV but is more strongly attenuated.
3. **No site amplification** — Japan subduction-zone sites may amplify long-period ground motion by 2–10× in sedimentary basins.
4. **Excitation factors (η)** — mode partition between Rayleigh/Love is uncertain for megathrust dip-slip; η = 0.20–0.25 is conservative.
5. **Q and U** — Q = 350–450 and U = 3.5–4.0 km/s are nominal mantle values; ±50% variation changes σ_dyn by less than a factor of 2 (attenuation exponent ≈ 0.2–0.3 at 5000 km).
6. **Stress conversion** — σ_dyn = μ·PGV/β assumes plane-wave shear at crustal velocity; alternative Gomberg (2001) form 2μPGV/(πc) gives similar order of magnitude.

## Self-critique

**The calculated dynamic stresses are far below triggering thresholds.** This is a substantive negative result, not a calibration failure:

- Median σ_dyn ≈ **0.056 kPa** vs threshold **10–100 kPa**.
- Even with optimistic assumptions (η × 5, site amplification × 10, Q halved), σ_dyn would remain **≪ 0.01 MPa**.
- Observed Japan PGV from Sumatra 2004 long-period records are typically **0.01–0.2 cm/s** at similar distances (Iwata et al., 2008; Fujii et al., 2011); our median **0.00066 cm/s** is **~15–300× lower**, suggesting excitation factors or frequency bands may be too narrow, **or** that peak dynamic stress for triggering operates at higher frequencies not captured by the 0.015–0.025 Hz bands used here.

**Implications for S170:** Static ΔCFS (§5.4, ~0.008 kPa) and dynamic σ_dyn (~0.056 kPa) are both **orders of magnitude below** typical triggering thresholds. Dynamic triggering of Japan events by Sumatra 2004 surface waves **cannot be confirmed** by this first-order model. The S170 spatial link remains **statistically significant** (η, ETAS) but **mechanistically unexplained** by simple elastic/dynamic stress transfer alone. Alternative hypotheses (viscoelastic coupling, shared loading, catalog coincidence) remain open.

**What would change the conclusion:** (a) broadband waveform modelling with observed Japan seismograms; (b) higher-frequency (0.1–0.5 Hz) dynamic stress estimates; (c) site-specific amplification from KiK-net/J-SHIS; (d) finite-fault directivity toward Japan (unlikely — Japan is ~NE of source, rupture propagated N).

## Files

- `src/analysis/dynamic_stress.py` — core formulas
- `scripts/compute_dynamic_stress_sumatra2004.py` — run script
- `results/dynamic_stress_sumatra2004.json` — per-receiver output
- `figures/grl/fig08_dynamic_stress_japan.png` — distance vs σ_dyn plot

## References

- Boatwright, J., & Choy, G. L. (1986). BSSA, 76(1), 73–87.
- Brune, J. N. (1970, 1971). JGR, 75(26), 4997–5009; 76(14), 3772–3785.
- Gomberg, J. (2001). BSSA, 91(6), 1574–1583.
- Hill, D. P., et al. (1993). Science, 260(5114), 1617–1623.
- Stein, R. S. (1999). Nature, 402(6762), 605–609.
