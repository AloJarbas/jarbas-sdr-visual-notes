# Band-edge spacing boundary: when the loop preference flips

The last band-edge note left one clean next question:

- if adjacent power stays fixed at `0 dB`, how far apart do the channels need to be before the wider half-sine lane stops being the worse loop?

This note answers that with one controlled spacing sweep.

![Band-edge spacing boundary after the first adjacent-loop test](../assets/2026-05-24-band-edge-spacing-boundary.png)

## 1. What is being simulated here

Only one knob moves:

- SRRC QPSK
- `4 samples/symbol`
- `3072` symbols
- roll-off `α = 0.35`
- `63`-tap band-edge filters
- one adjacent QPSK interferer
- adjacent power fixed at `0 dB`
- one simple blockwise frequency loop with `96` symbols per update and loop gain `0.02`
- channel spacing swept from `0.80 R_s` to `1.65 R_s`

So this is still **not** BER, not AGC, not timing recovery, and not a full receiver benchmark.
It is one bounded follow-up to the earlier adjacent-loop note.

## 2. The table that matters

| spacing | design | mean tail residual CFO | tail fraction inside `±0.05 R_s` |
|---|---|---:|---:|
| `1.00 R_s` | current proxy | `0.0387 R_s` | `100%` |
| `1.00 R_s` | GNU Radio / half-sine | `0.0995 R_s` | `0%` |
| `1.24 R_s` | current proxy | `0.0028 R_s` | `100%` |
| `1.24 R_s` | GNU Radio / half-sine | `0.0447 R_s` | `100%` |
| `1.57 R_s` | current proxy | `0.00020 R_s` | `100%` |
| `1.57 R_s` | GNU Radio / half-sine | `0.00017 R_s` | `100%` |

Those three rows are the whole point of this pass.

## 3. What the sweep actually shows

### A. There are really **two** boundaries, not one

The vague version of the question was:

- when does the loop preference flip?

The spacing sweep shows that this depends on which metric is being named.

### B. The half-sine lane becomes track-ready again around `1.24 R_s`

Using the same bounded settle summary as the last note (the fraction of the final eight loop blocks that stay inside `±0.05 R_s`), the half-sine lane first gets all the way back inside the band at about `1.24 R_s`.

That is the first important boundary.

So one honest sentence is:

**at `0 dB` adjacent power, the half-sine lane stops failing the `±0.05 R_s` settle band once spacing reaches about `1.24 R_s`.**

### C. But it does **not** beat the proxy on mean residual until about `1.57 R_s`

If the stricter metric is mean absolute tail residual CFO, the crossover comes much later.

At `1.24 R_s`:

- the half-sine lane is finally inside the settle band,
- but it still averages much more pull than the proxy lane.

Only near `1.57 R_s` does the residual ranking actually reverse:

- proxy is about `0.00020 R_s`,
- half-sine is about `0.00017 R_s`.

So the sharper success sentence for this note is:

**at `0 dB` adjacent power, the half-sine lane stops being the worse loop on mean tail residual only once spacing reaches about `1.57 R_s`.**

## 4. How this fits with the earlier band-edge notes

This branch now reads as a more honest sequence:

1. [Oversampled 4th-power versus band-edge FLL](oversampled-fourth-power-vs-band-edge-fll.md): what clue the front end is using.
2. [Band-edge discriminant gain: raw imbalance versus near-lock slope](band-edge-discriminant-gain-and-slope.md): why raw imbalance and normalized slope are not the same object.
3. [Band-edge filter shape and near-lock slope](band-edge-filter-shape-and-slope.md): why the old proxy understated the moderate-roll-off slope.
4. [Band-edge filter shape, guardband, and adjacent-channel cost](band-edge-filter-shape-and-guardband.md): why the half-sine slope fix is not free.
5. [Band-edge closed-loop pull with one adjacent interferer](band-edge-closed-loop-adjacent-pull.md): why the wider lane loses under the original `1.0 R_s` stress case.
6. **This note**: which spacing boundary restores track-ready behavior, and which later spacing boundary actually flips the mean-residual ranking.

That is a much sharper answer than “spacing matters.”

## 5. Companion files

This note adds:

- `scripts/generate_band_edge_spacing_boundary_figure.py`
- `assets/2026-05-24-band-edge-spacing-boundary.csv`
- `assets/2026-05-24-band-edge-spacing-boundary.svg`
- `assets/2026-05-24-band-edge-spacing-boundary.png`
- `notebooks/band_edge_spacing_boundary.ipynb`
- `tests/test_band_edge_spacing_boundary.py`

## Source basis

The detector-path framing still rests on:

- Daniel Estévez on band-edge filter construction, guardband cost, and discriminant gain,
- GNU Radio FLL band-edge documentation,
- GNU Radio source for the half-sine filter construction and loop-gain normalization,
- and the local continuation note in `notes/2026-05-24-band-edge-spacing-boundary-research.md`.

## Scope boundary

This stays in the receive-side study lane.
It is not a modem benchmark and it is not an adjacent-channel specification.
It is the smallest follow-up that pins the spacing boundary to named loop metrics instead of leaving it fuzzy.
