# Status — large-CFO front-end boundary after the symbol-rate packet

Updated on 2026-05-19.

Delivered:

1. `notes/when-symbol-rate-carrier-recovery-stops-being-enough.md`
2. `assets/2026-05-19-large-cfo-front-end-boundary.png`
3. `assets/2026-05-19-large-cfo-front-end-boundary.csv`
4. `notebooks/large_cfo_front_end_boundary.ipynb`
5. `scripts/generate_large_cfo_front_end_figure.py`

## What this pass established

- the earlier `\pi/4` alias note is now pinned down as a **1-sample/symbol QPSK symbol-rate** statement, not a generic carrier-recovery law
- the honest 4th-power coarse-frequency window scales with the observation rate: `|\Delta f| < F_s/8 = L R_s / 8`
- a simple local oversampled toy check is enough to make the rate-scaling point visible without bloating the repo into a full modem lab
- the same physical CFO can alias at `1 sps` while staying honest at `4 sps`, so the next receiver move is often an earlier front end rather than a stronger claim about the late-stage estimator
- the two follow-on branches worth naming are:
  - oversampled waveform-domain coarse recovery, including band-edge FLL style logic
  - pilot or correlation-based coarse estimation for receivers that can spend known structure

## Best next move

If this lane gets one more pass, keep it narrow.
The strongest next artifact is probably **one bounded waveform-domain sidecar**:

- compare an oversampled 4th-power front end against a band-edge style FLL view
- keep it focused on **when each front end is the cleaner object**, not on implementing a full receiver chain
- only do it if the pulse-shape and oversampling details teach something the current rate-scaling note does not already cover

## Avoid next time

- do not reopen the symbol-rate alias note as if it were still unfinished
- do not let this branch sprawl into AGC, equalization, or packet framing
- do not pretend the hold-model sweep is a full waveform receiver study; its job is only to make the sample-rate boundary obvious
