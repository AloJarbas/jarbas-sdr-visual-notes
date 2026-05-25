# Band-edge loop-gain retuning: slower helps, but the ranking stays the same

The spacing-boundary note left one clean tuning question behind:

- once the half-sine lane becomes track-ready again at about `1.24 R_s`, can loop-gain retuning make it stop being the worse loop?

This note answers that with one bounded gain sweep.

![Band-edge loop-gain retuning at the first settle point](../assets/2026-05-24-band-edge-loop-gain-retuning.png)

## 1. What is being simulated here

Keep the setup fixed:

- SRRC QPSK
- `4 samples/symbol`
- `3072` symbols
- roll-off `α = 0.35`
- `63`-tap band-edge filters
- one adjacent QPSK interferer at `1.24 R_s` spacing
- adjacent power fixed at `0 dB`
- the desired channel still sits at the correct carrier (`Δf = 0`)
- one simple blockwise frequency loop with `96` symbols per update
- only **loop gain** moves, from `0.0005` to `0.0240`

So this is still not BER, not AGC, not timing recovery, and not a full modem benchmark.
It is one bounded retuning pass after the spacing boundary was pinned down.

## 2. The table that matters

| loop gain | design | mean tail residual CFO | tail fraction inside `±0.05 R_s` |
|---|---|---:|---:|
| `0.002` | current proxy | `0.00030 R_s` | `100%` |
| `0.002` | GNU Radio / half-sine | `0.00461 R_s` | `100%` |
| `0.020` | current proxy | `0.00283 R_s` | `100%` |
| `0.020` | GNU Radio / half-sine | `0.04475 R_s` | `100%` |
| `0.022` | current proxy | `0.00309 R_s` | `100%` |
| `0.022` | GNU Radio / half-sine | `0.04907 R_s` | `62.5%` |

Those rows are the whole point of this pass.

## 3. What the gain sweep actually shows

### A. Lower gain really does calm both loops

If the gain is reduced from `0.020` to `0.002`:

- proxy tail pull drops from about `0.00283 R_s` to `0.00030 R_s`,
- half-sine tail pull drops from about `0.04475 R_s` to `0.00461 R_s`.

So retuning is not fake.
A gentler loop really does reduce adjacent-channel pull in this bounded setup.

### B. But the ranking does **not** flip anywhere in the tested gain set

The important detail is what happens to the **ratio** between the two designs.

At gain `0.002`:

- half-sine is still about **`15.2×`** worse than proxy on mean tail residual.

At gain `0.020`:

- half-sine is still about **`15.8×`** worse than proxy.

So the gain sweep does not turn the spacing result into a one-parameter tuning problem.
It mostly rescales the same geometry penalty.

That is the sharper sentence this branch was missing:

**lower gain helps, but it does not make the half-sine lane competitive again at `1.24 R_s`; the detector geometry is still the main story.**

### C. Pushing gain upward hurts the half-sine lane first

The proxy lane stays fully inside the `±0.05 R_s` tail band for every tested gain.

The half-sine lane does not.
On the default seed pair, it first drops below a full `100%` tail fraction at about `0.022`.

So the gain sweep adds one more clean bounded fact:

**the half-sine lane is not only worse in residual pull at `1.24 R_s`; it also loses settle margin first as gain is increased.**

## 4. Small sensitivity check

This did not become a Monte Carlo branch, but I did check four seed pairs near the same gains.

Across seed pairs `(19,173)`, `(23,211)`, `(31,271)`, `(47,389)`:

- at gains `0.002`, `0.010`, and `0.020`, the half-sine / proxy residual ratio stayed between about `15×` and `28×`,
- at gains `0.016–0.019`, all four seed pairs still kept the half-sine tail fraction at `100%`,
- at gain `0.020`, one seed pair had already dropped to `75%`,
- by gain `0.022`, all four seed pairs had dropped below `100%`.

That was enough to keep the public claim honest without pretending this is a full statistical study.

## 5. How this fits with the earlier band-edge notes

This branch now reads as a tighter sequence:

1. [Oversampled 4th-power versus band-edge FLL](oversampled-fourth-power-vs-band-edge-fll.md): what clue the front end is even using.
2. [Band-edge discriminant gain: raw imbalance versus near-lock slope](band-edge-discriminant-gain-and-slope.md): why raw detector output and normalized slope are not the same object.
3. [Band-edge filter shape and near-lock slope](band-edge-filter-shape-and-slope.md): why the old proxy understated the moderate-roll-off slope.
4. [Band-edge filter shape, guardband, and adjacent-channel cost](band-edge-filter-shape-and-guardband.md): why the half-sine slope fix is not free.
5. [Band-edge closed-loop pull with one adjacent interferer](band-edge-closed-loop-adjacent-pull.md): why the wider detector loses under the original `1.0 R_s` stress case.
6. [Band-edge spacing boundary: when the loop preference flips](band-edge-spacing-boundary.md): why `track-ready again` and `residual crossover` are two different spacing boundaries.
7. **This note**: why one bounded loop-gain retuning pass does not erase the spacing result at the first settle point.

That is enough to stop reopening this branch as if it were still a loose tuning question.

## 6. Companion files

This note adds:

- `scripts/generate_band_edge_loop_gain_retuning_figure.py`
- `assets/2026-05-24-band-edge-loop-gain-retuning.csv`
- `assets/2026-05-24-band-edge-loop-gain-retuning.svg`
- `assets/2026-05-24-band-edge-loop-gain-retuning.png`
- `notebooks/band_edge_loop_gain_retuning.ipynb`
- `tests/test_band_edge_loop_gain_retuning.py`

## Source basis

Source framing for the detector path and loop-tuning interpretation comes from:

- Daniel Estévez on band-edge filter construction, adjacent-channel burden, and discriminant gain,
- GNU Radio FLL band-edge documentation,
- GNU Radio source for the half-sine construction and loop-bandwidth normalization,
- Wireless Pi on FLL loop filters and the acquisition-versus-tracking bandwidth tradeoff,
- and the local continuation note in `notes/2026-05-24-band-edge-loop-gain-retuning-research.md`.

## Scope boundary

This stays in the receive-side study lane.
It is not a modem benchmark, not BER, not AGC, and not a recommendation to run loops arbitrarily slow.

It is the smallest retuning follow-up that answers the remaining bounded question honestly.
