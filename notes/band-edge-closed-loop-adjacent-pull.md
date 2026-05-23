# Band-edge closed-loop pull with one adjacent interferer

The last band-edge note stopped one bad shortcut:

- the GNU Radio / fred harris half-sine design really does fix the moderate-roll-off isolated-slope story,
- but it is not free because the detector path also listens farther into a nearby channel.

That still left the next honest question:

- what happens after that wider detector path is pushed through one actual loop instead of one more static detector card?

This note answers that with one bounded closed-loop stress test.

![Band-edge closed-loop pull with one adjacent interferer](../assets/2026-05-23-band-edge-closed-loop-adjacent-pull.png)

## 1. What is being simulated here

Keep the scope narrow:

- SRRC QPSK
- `4 samples/symbol`
- `3072` symbols
- roll-off `α = 0.35`
- `63`-tap band-edge filters
- one adjacent QPSK interferer at `1.0 R_s` spacing
- the desired channel already sits at the correct carrier (`Δf = 0`)
- one simple **blockwise** frequency loop with `96` symbols per update and loop gain `0.02`

So this is **not** a full streaming GNU Radio block clone.
It is one bounded control test:

- start the loop on the right carrier,
- mix in one adjacent channel,
- and measure how far the detector path pulls the loop away from the truth.

The two summary metrics are:

1. mean absolute residual CFO over the last eight loop blocks,
2. fraction of those tail blocks that stay inside `±0.05 R_s`.

That second number is not BER and not packet success.
It is just a small settle-quality summary for the same bounded loop.

## 2. The table that matters

| adjacent level | design | mean tail residual CFO | tail fraction inside `±0.05 R_s` |
|---|---|---:|---:|
| desired only | current proxy | `0.0003 R_s` | `100%` |
| desired only | GNU Radio / half-sine | `0.0000 R_s` | `100%` |
| `-12 dB` | current proxy | `0.0056 R_s` | `100%` |
| `-12 dB` | GNU Radio / half-sine | `0.0107 R_s` | `100%` |
| `-6 dB` | current proxy | `0.0159 R_s` | `100%` |
| `-6 dB` | GNU Radio / half-sine | `0.0363 R_s` | `100%` |
| `0 dB` | current proxy | `0.0387 R_s` | `100%` |
| `0 dB` | GNU Radio / half-sine | `0.0995 R_s` | `0%` |
| `+6 dB` | current proxy | `0.0644 R_s` | `0%` |
| `+6 dB` | GNU Radio / half-sine | `0.1780 R_s` | `0%` |

That is the whole point of this pass.

## 3. What changes once the loop is real

### A. The wide half-sine lane is not intrinsically unstable

On the desired-only waveform, both designs stay pinned near zero:

- proxy tail pull is about `0.0003 R_s`,
- half-sine tail pull is effectively zero.

So the problem here is not “the half-sine detector is too noisy to use.”
The problem is the mixed-signal case.

### B. `0 dB` adjacent power is already enough to flip the practical preference in this bounded setup

At `0 dB` adjacent power:

- the proxy loop still averages about `0.0387 R_s` of tail pull,
- the half-sine loop averages about `0.0995 R_s`,
- the proxy tail stays inside `±0.05 R_s` for all eight tail blocks,
- the half-sine tail stays inside that band for none of them.

That is the sharper public sentence this branch was missing:

**the half-sine path is the better isolated discriminator, but not the more robust adjacent-channel loop under this bounded stress case.**

### C. By `+6 dB`, both loops are stressed, but the wider detector still pays more

At `+6 dB` adjacent power:

- proxy tail pull reaches about `0.064 R_s`,
- half-sine tail pull reaches about `0.178 R_s`.

So the wider detector does not just lose the threshold first.
It keeps getting pulled much farther once the neighbor dominates.

## 4. How this fits with the earlier band-edge notes

This lane now reads as one coherent sequence:

1. [Oversampled 4th-power versus band-edge FLL](oversampled-fourth-power-vs-band-edge-fll.md) — what the front end is even looking at.
2. [Band-edge discriminant gain: raw imbalance versus near-lock slope](band-edge-discriminant-gain-and-slope.md) — why raw detector output and normalized slope are not the same object.
3. [Band-edge filter shape and near-lock slope](band-edge-filter-shape-and-slope.md) — why the old proxy was understating moderate-roll-off slope.
4. [Band-edge filter shape, guardband, and adjacent-channel cost](band-edge-filter-shape-and-guardband.md) — why the half-sine slope fix is not free.
5. **This note** — what that tradeoff does after one nearby channel is mixed into one actual loop.

That is enough to stop treating the whole question as detector-only.

## 5. Companion files

This note adds:

- `scripts/generate_band_edge_closed_loop_adjacent_figure.py`
- `assets/2026-05-23-band-edge-closed-loop-adjacent-pull.csv`
- `assets/2026-05-23-band-edge-closed-loop-adjacent-pull.svg`
- `assets/2026-05-23-band-edge-closed-loop-adjacent-pull.png`
- `notebooks/band_edge_closed_loop_adjacent_pull.ipynb`
- `tests/test_band_edge_closed_loop_pull.py`

## Source basis

Source framing for the band-edge detector path still comes from:

- Daniel Estévez on band-edge filter construction and detector gain,
- GNU Radio FLL band-edge documentation,
- GNU Radio source for the half-sine construction,
- and the local continuation note in `notes/2026-05-23-band-edge-adjacent-power-closed-loop-research.md`.

## Scope boundary

This is still a receive-side study artifact.
It is not a full modem benchmark, not BER, not AGC, not timing recovery, and not an adjacent-channel rejection spec.

It is the smallest loop-level follow-up that answers the next missing question honestly.
