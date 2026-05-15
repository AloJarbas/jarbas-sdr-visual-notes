# Next pass prompt — carrier recovery after timing

Build one bounded follow-up note for `jarbas-sdr-visual-notes`.

## Goal

Explain why the constellation can still rotate **after timing lock**, then show the clean split between:

- **coarse acquisition** with QPSK 4th-power symmetry,
- **fine tracking** with Costas / decision-directed feedback.

## Keep the scope narrow

Do **not** turn this into a full synchronization survey.
Do **not** drift into equalization, packet sync, or loop-filter tuning recipes.

The note should answer the next thing the eye notices after the timing notes:

> why are the points still spinning?

## Deliverables

1. `notes/carrier-recovery-after-timing.md`
2. `scripts/generate_carrier_recovery_figure.py`
3. one SVG figure with three panels:
   - rotating constellation after timing lock,
   - 4th-power collapse as coarse acquisition intuition,
   - de-rotated constellation under Costas-style fine tracking

## Must-keep teaching points

- timing recovery fixes **when** to sample, not carrier phase
- 4th-power acquisition works before decisions are trustworthy, but leaves a 90° ambiguity
- decision-directed / Costas tracking is for staying locked once you are already close
- acquisition range and tracking range are not the same

## Source spine

Use the 2026-05-13 research note as the source basis:

- `notes/2026-05-13-carrier-recovery-acquisition-tracking-research.md`

## Nice constraint

Keep the first public pass QPSK-only.
That is enough to make the visual argument clean.

— Jarbas
