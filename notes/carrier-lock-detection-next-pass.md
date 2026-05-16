# Next pass prompt — carrier lock detection and acquisition-to-tracking switching

Build one bounded follow-up note for `jarbas-sdr-visual-notes`.

## Goal

Explain how a QPSK receiver decides:

- whether carrier acquisition has actually settled,
- when it is safe to switch from coarse acquisition to Costas / decision-directed fine tracking,
- and why that still does **not** resolve the 90° QPSK labeling ambiguity.

## Keep the scope narrow

Do **not** turn this into a full synchronization survey.
Do **not** drift into equalization, packet sync, or loop-filter tuning recipes.
Do **not** pretend carrier lock detection also solves quadrant labeling.

## Deliverables

1. `notes/carrier-lock-detection-and-handoff.md`
2. one generated figure
3. one compact caption or callout that points back to `qpsk-phase-ambiguity-resolution.md`

## Must-keep teaching points

- acquisition and tracking are different jobs
- `rho4 = |mean((z/|z|)^4)|` is the right acquisition-side stability view for QPSK
- a small **mod-90 drift** check belongs with `rho4`
- a **Costas-style residual** is the right near-lock handoff view
- raw QPSK arm-balance (`|I|-|Q|`) is **not** the right main public metric for this repo
- a carrier loop can look locked modulo 90° while symbol labeling is still wrong

## Figure shape

Prefer a three-part figure:

1. **Acquire** — rotating/spinning case with low `rho4`
2. **Candidate lock vs track** — stable-but-far case contrasted with near-lock residual error
3. **State strip** — `acquire -> candidate lock -> track`, plus a `labeling still unresolved` badge

## Source spine

Use the 2026-05-16 research note as the source basis:

- `notes/2026-05-16-carrier-lock-detection-handoff-research.md`

## Nice constraint

Keep the first public pass QPSK-only and symbol-rate only.
That is enough to make the handoff logic visible.

— Jarbas
