# Band-edge filter shape and near-lock slope

The last band-edge note fixed one important wording problem:

- raw edge-energy imbalance is not the same thing as normalized near-lock slope.

That still left one narrower loophole:

- was the current repo proxy itself too crude to show the real normalized-slope story cleanly?

This note answers that question with one bounded comparison.

![Band-edge filter design comparison](../assets/2026-05-22-band-edge-filter-design-comparison.png)

## 1. The two designs in this pass

The setup stays the same as the earlier slope note:

- SRRC QPSK
- `4 samples/symbol`
- `1024` symbols
- central finite difference at `±0.01 R_s`
- tap counts `{63, 127, 255}`
- roll-off `{0.05, 0.20, 0.35, 0.50}`

The only new comparison is the band-edge filter design itself:

1. the current repo's **proxy bandpass** construction,
2. a **GNU Radio / half-sine style** construction based on the fred harris approach.

To keep the comparison about slope instead of sign conventions, the plotted discriminator is oriented so positive CFO gives a positive local slope in both families.

## 2. The table that matters

At `α = 0.35`, the oriented near-lock slopes are:

| design | 63 taps | 127 taps | 255 taps |
|---|---:|---:|---:|
| current proxy | `0.670` | `0.854` | `0.983` |
| GNU Radio / half-sine | `0.986` | `1.003` | `1.042` |

That is the whole point of this follow-up.

## 3. What changes

### A. The current proxy really is underplaying the normalized slope

The old proxy is still useful for showing where the clue comes from.
But for moderate roll-off it does not reach the normalized target slope very quickly unless the filters get long.

So the earlier gap was not just a plotting accident.
A lot of it was the filter shape.

### B. A better band-edge design gets close to the normalized target much sooner

Once the half-sine style design is used, the `α = 0.20`, `0.35`, and `0.50` cases are already close to slope `1` with only `63` taps.

That is the practical repo-level correction:

- the old proxy was good enough for intuition,
- but it should not be mistaken for a faithful practical band-edge implementation.

### C. Tiny roll-off still stays weak

`α = 0.05` remains soft even with the half-sine design.
So the small-roll-off caveat survives the implementation upgrade.

That means the repo can now split two different facts cleanly:

1. moderate-roll-off underestimation was partly a **filter-shape problem**,
2. tiny roll-off is still a **real excess-bandwidth weakness**.

## 4. How this fits with the previous notes

This SDR packet now has three distinct layers:

1. [Oversampled 4th-power versus band-edge FLL](oversampled-fourth-power-vs-band-edge-fll.md) — which clue each front end reads.
2. [Band-edge discriminant gain: raw imbalance versus near-lock slope](band-edge-discriminant-gain-and-slope.md) — why raw imbalance and normalized slope are not the same object.
3. **This note** — why the current proxy filter shape was still hiding part of the normalized story.

That keeps the packet honest without turning it into a full modem survey.

## 5. Companion notebook and next move

This note adds:

- `scripts/generate_band_edge_filter_design_comparison_figure.py`
- `assets/2026-05-22-band-edge-filter-design-comparison.csv`
- `assets/2026-05-22-band-edge-filter-design-comparison.svg`
- `assets/2026-05-22-band-edge-filter-design-comparison.png`
- `notebooks/band_edge_filter_design_comparison.ipynb`

If this branch gets one more bounded pass, the next honest question is not another slope sweep.
It is the tradeoff Estévez warns about:

- how much selectivity / guardband cost comes with the wider half-sine style design?

That would be a better final follow-up than repeating more calibration plots.

## Source basis

Primary framing for this note came from:

- Daniel Estévez on band-edge filter construction and discriminant gain,
- GNU Radio FLL band-edge documentation,
- GNU Radio source for the actual half-sine filter construction,
- local provenance in `notes/2026-05-22-band-edge-filter-shape-research.md`.

## Scope boundary

This stays in the study and visualization lane.
It is not a full adjacent-channel or closed-loop performance study.
It is the smallest durable comparison that answers whether the current proxy was understating the band-edge slope story.
