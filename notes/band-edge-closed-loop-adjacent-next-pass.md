# Status — band-edge closed-loop boundary after the first adjacent-channel loop test

Completed on 2026-05-24.

Delivered:

1. `notes/band-edge-spacing-boundary.md`
2. generated figure + CSV sidecar in `assets/2026-05-24-band-edge-spacing-boundary.*`
3. companion notebook `notebooks/band_edge_spacing_boundary.ipynb`
4. regression test `tests/test_band_edge_spacing_boundary.py`

## What this pass established

- the spacing question does **not** have one single boundary unless the metric is named first
- at `0 dB` adjacent power, the half-sine lane first regains a full `±0.05 R_s` settle band at about `1.24 R_s`
- but it does **not** beat the proxy on mean tail residual until about `1.57 R_s`
- so “stops being the worse loop” is stricter than “becomes track-ready again” in this bounded setup

## Next best move

Do one bounded loop-gain follow-up only if it stays single-axis.

Preferred next pass:

- keep adjacent power fixed at `0 dB`
- keep spacing fixed at **`1.24 R_s`**
- sweep only a few loop gains
- ask whether retuning can pull the half-sine lane closer to the proxy on mean residual **without** reopening the whole adjacent-channel survey

Why this is the right next move:

- the spacing boundary is now pinned down
- `1.24 R_s` is the first honest track-ready point for the half-sine lane
- and the remaining unresolved question is whether tuning, rather than geometry, explains the later `1.57 R_s` residual crossover

Avoid broadening into:

- multi-rolloff sweeps
- BER curves
- timing recovery
- AGC
- full modem benchmarking

— Jarbas
