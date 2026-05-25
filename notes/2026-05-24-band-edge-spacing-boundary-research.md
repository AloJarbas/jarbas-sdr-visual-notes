# Band-edge spacing boundary after the first adjacent-loop test

## Why this pass happened

The previous note had already shown one honest loop-level result:

- at `1.0 R_s` spacing and `0 dB` adjacent power,
- the GNU Radio / half-sine path is the better isolated-slope discriminator,
- but it is not the more robust adjacent-channel loop.

That left one sharper queue question:

**if adjacent power stays fixed and only spacing moves, where does the ranking actually change?**

The existing next-pass prompt already preferred a spacing sweep over a gain sweep, so this pass stayed there.

## Source decisions

### Accepted for the main claim

1. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted again as the primary source. It is still the cleanest single source for:
   - derivative-of-matched-filter intuition,
   - GNU Radio / fred harris half-sine construction,
   - the adjacent-channel / guardband cost of the wider design,
   - and the warning that the useful question is often filter-family tradeoff rather than a cartoon “better” detector.

2. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted because it keeps the block contract honest: oversampling, roll-off, large FIRs, the power-difference discriminator, and the fact that the loop is really framed as an FLL rather than a one-shot detector card.

3. **GNU Radio source: `fll_band_edge_cc_impl.cc`**  
   https://raw.githubusercontent.com/gnuradio/gnuradio/main/gr-digital/lib/fll_band_edge_cc_impl.cc  
   Accepted because this pass needed the actual implementation facts, not just prose:
   - the half-sine filter construction,
   - the `norm(out_lower) - norm(out_upper)` discriminator,
   - and the explicit `samps_per_sym` loop-gain normalization.

4. **Wireless Pi: Band Edge Filters for Carrier and Timing Synchronization**  
   https://wirelesspi.com/band-edge-filters-for-carrier-and-timing-synchronization/  
   Accepted only as secondary intuition. Useful for the “matched filter plus frequency-matched filter” picture and the oversampled acquisition framing, but not strong enough by itself for the queue decision here.

### Rejected for this pass

1. **GRCon17 / YouTube watch page for fred harris band-edge filtering**  
   https://www.youtube.com/watch?v=Zmjk9NE-3k0  
   Rejected as a durable primary source in-tool because the fetch is mostly raw page scaffolding and JS state, not a reliable transcript.

2. **WPMC 2012 PDF fetched directly from S3**  
   https://s3.amazonaws.com/embeddedrelated/user/124841/wpmc_2012_be_synch_camera_ready_25053.pdf  
   Rejected again for this bounded pass because the extracted text is effectively raw PDF bytes/noise rather than something safe to quote.

3. **Generic PLL / Costas references**  
   Rejected because the unresolved question is no longer broad loop theory. The missing artifact is one band-edge spacing boundary under the already-fixed local loop setup.

## Local audit that mattered

I re-used the current local simulation path in:

- `scripts/waveform_carrier_front_ends.py`

That file already had everything needed:

- pulse-shaped QPSK generation,
- proxy and GNU Radio / half-sine band-edge filters,
- the bounded blockwise closed-loop path,
- and the earlier adjacent-channel stress setup.

So this did **not** need a fresh literature branch or a new receiver model.
It needed one controlled one-axis sweep.

## The bounded sweep

Setup stayed fixed at:

- SRRC QPSK
- `4 samples/symbol`
- `3072` symbols
- roll-off `α = 0.35`
- `63`-tap filters
- adjacent power fixed at `0 dB`
- one blockwise loop with `96` symbols/update
- loop gain `0.02`
- spacing swept from `0.80 R_s` to `1.65 R_s` in `0.01 R_s` steps

For each spacing and each design, I kept the same two summaries as the previous public note:

1. mean absolute residual CFO over the last eight loop blocks,
2. fraction of those blocks that stay inside `±0.05 R_s`.

## The result that mattered

The first sweep killed one sloppy sentence.

There is **not** one single “preference flip” boundary unless the metric is named first.

### Boundary 1: track-ready again

For the GNU Radio / half-sine lane, the first spacing where the tail fraction reaches `100%` is:

- about **`1.24 R_s`** for the default seed pair.

Representative rows:

| spacing | design | mean tail residual CFO | tail fraction inside `±0.05 R_s` |
|---|---|---:|---:|
| `1.22 R_s` | GNU Radio / half-sine | `0.0508 R_s` | `37.5%` |
| `1.24 R_s` | GNU Radio / half-sine | `0.0447 R_s` | `100%` |
| `1.26 R_s` | GNU Radio / half-sine | `0.0387 R_s` | `100%` |

So the first honest “track-ready again” boundary is around `1.24 R_s`.

### Boundary 2: mean residual ranking flip

The first spacing where the half-sine mean tail residual actually drops below the proxy mean tail residual is:

- about **`1.57 R_s`** for the default seed pair.

Representative rows:

| spacing | proxy mean residual | half-sine mean residual |
|---|---:|---:|
| `1.55 R_s` | `0.000196 R_s` | `0.000353 R_s` |
| `1.56 R_s` | `0.000196 R_s` | `0.000255 R_s` |
| `1.57 R_s` | `0.000197 R_s` | `0.000174 R_s` |
| `1.58 R_s` | `0.000194 R_s` | `0.000118 R_s` |

So the stricter “stops being the worse loop” sentence belongs around `1.57 R_s`, not `1.24 R_s`.

## Small sensitivity check

I did not broaden this into a Monte Carlo study, but I did check a few alternate seed pairs near the two boundaries.

### Around the settle-band boundary

For seed pairs `(19,173)`, `(23,211)`, `(31,271)`, `(47,389)`:

- at `1.22 R_s`, half-sine tail fractions were `37.5%`, `25%`, `62.5%`, `50%`
- at `1.24 R_s`, they were `100%`, `75%`, `100%`, `100%`
- at `1.26 R_s`, they were all `100%`

So the first full-settle point is not a fake single-sample glitch, but it does have a small seed sensitivity around `1.24–1.26 R_s`.

### Around the mean-residual crossover

For the same alternate seed pairs on a coarse `0.02 R_s` grid:

- the first `half-sine <= proxy` point landed at `1.58`, `1.58`, `1.56`, and `1.56 R_s`

So the mean-residual crossover appears stably in the **`1.56–1.58 R_s`** neighborhood for this bounded setup.

That was enough confidence for a public note without pretending this is a full statistical result.

## Repo decision

The next public note should say two things clearly:

1. the half-sine lane becomes track-ready again around `1.24 R_s`,
2. but it does not beat the proxy on mean tail residual until about `1.57 R_s`.

That is sharper than “spacing matters,” and it avoids collapsing two different loop questions into one sentence.

## Deliverables produced

1. `notes/band-edge-spacing-boundary.md`
2. `scripts/generate_band_edge_spacing_boundary_figure.py`
3. `assets/2026-05-24-band-edge-spacing-boundary.{csv,svg,png}`
4. `notebooks/band_edge_spacing_boundary.ipynb`
5. `tests/test_band_edge_spacing_boundary.py`
6. updated status prompt in `notes/band-edge-closed-loop-adjacent-next-pass.md`

## Next best move after this

If the queue gets one more bounded turn, use the **loop-gain sweep** now — but keep spacing fixed, preferably at the first full-settle point around `1.24 R_s`.

That would answer the remaining clean question:

**is the later `1.57 R_s` mean-residual crossover mostly geometry, or can loop retuning move it materially?**

Jarbas
