# Band-edge filter shape, guardband, and adjacent-channel cost

The last band-edge note fixed one public wording problem:

- the old proxy was understating the normalized near-lock slope for moderate roll-off.

That still left the next honest question:

- if the GNU Radio / fred harris half-sine design fixes the slope, what does it cost in selectivity?

This note answers that narrower question with one bounded study.

![Band-edge guardband cost comparison](../assets/2026-05-22-band-edge-guardband-cost-comparison.png)

## 1. What is being measured here

The waveform setup stays the same as the previous filter-shape note:

- SRRC QPSK
- `4 samples/symbol`
- `1024` symbols
- tap counts `{63, 127, 255}`
- roll-off `{0.05, 0.20, 0.35, 0.50}`

The new cost metric is not loop BER or full receiver ACLR.
It is something narrower and more directly tied to the band-edge detector path.

For each filter family, this pass measures two things:

1. the oriented near-lock slope from the earlier note,
2. how much energy the lower + upper band-edge filters capture from an **adjacent** QPSK channel by itself.

The adjacent-only capture ratio is

```text
capture ratio = (E_lower + E_upper) / E_input
```

where `E_input` is the adjacent waveform energy inside the trimmed window.

This pass then asks one practical threshold question:

- how far apart do the channel centers need to be before that capture ratio drops under `5%`?

That is the guardband-style cost used on the card.

## 2. The table that matters

For the most practical short-filter case (`63` taps), the comparison is:

| roll-off `α` | design | near-lock slope | adjacent pickup at `1.0 R_s` | spacing for `≤ 5%` pickup |
|---|---|---:|---:|---:|
| `0.20` | current proxy | `0.480` | `4.2%` | `0.75 R_s` |
| `0.20` | GNU Radio / half-sine | `0.943` | `18.3%` | `1.20 R_s` |
| `0.35` | current proxy | `0.670` | `10.7%` | `1.15 R_s` |
| `0.35` | GNU Radio / half-sine | `0.986` | `31.5%` | `1.35 R_s` |
| `0.50` | current proxy | `0.764` | `17.3%` | `1.25 R_s` |
| `0.50` | GNU Radio / half-sine | `1.003` | `45.0%` | `1.55 R_s` |

That is the whole point of the follow-up.

## 3. What changes

### A. The half-sine upgrade is real, but it is not free

The previous note was right to stop treating the old proxy as a faithful practical implementation.
For moderate roll-off, the half-sine design gets close to slope `1` much faster.

But this pass shows the missing price:

- it also keeps listening much farther into a nearby channel.

At `α = 0.35` and `63` taps, the slope rises from `0.670` to `0.986`.
At the same time, adjacent pickup at `1.0 R_s` rises from `10.7%` to `31.5%`, and the spacing needed to push pickup below `5%` widens from `1.15 R_s` to `1.35 R_s`.

So the better implementation is not a free cleanup pass.
It is a slope-versus-selectivity tradeoff.

### B. The guardband cost is mostly a design-family effect here

One useful surprise in this bounded setup is that tap count does **not** move the spacing threshold very much.

At `α = 0.35`:

- the proxy rises from slope `0.670` at `63` taps to `0.983` at `255` taps,
- but the `≤ 5%` spacing stays at `1.15 R_s`.

The same thing happens in the half-sine lane:

- slope goes from `0.986` to `1.042`,
- but the spacing threshold stays at `1.35 R_s`.

That means the adjacent-channel footprint in this study is being set more by the filter family than by simply making the same family longer.

### C. The small-roll-off story stays honest too

At `α = 0.20`, the old proxy is much more selective at `1.0 R_s`, but it is also the weaker discriminator.
The half-sine version gets the slope much closer to `1`, but it needs substantially more spacing before the adjacent pickup drops under the same threshold.

So the repo can now keep both claims separate:

1. the old proxy was still underestimating moderate-roll-off slope,
2. the better half-sine design really does pay for that improvement with a wider adjacent-channel footprint.

## 4. How this fits with the previous notes

This branch now has four bounded layers:

1. [Oversampled 4th-power versus band-edge FLL](oversampled-fourth-power-vs-band-edge-fll.md) — which clue each front end reads.
2. [Band-edge discriminant gain: raw imbalance versus near-lock slope](band-edge-discriminant-gain-and-slope.md) — why raw imbalance and normalized slope are not the same object.
3. [Band-edge filter shape and near-lock slope](band-edge-filter-shape-and-slope.md) — why the old proxy was still hiding part of the slope story.
4. **This note** — why the better half-sine implementation is not free once selectivity starts to matter.

That is enough to make this packet feel like a real engineering tradeoff instead of one more calibration plot.

## 5. Companion notebook and next move

This note adds:

- `scripts/generate_band_edge_guardband_cost_figure.py`
- `assets/2026-05-22-band-edge-guardband-cost-comparison.csv`
- `assets/2026-05-22-band-edge-guardband-cost-comparison.svg`
- `assets/2026-05-22-band-edge-guardband-cost-comparison.png`
- `notebooks/band_edge_filter_guardband_cost.ipynb`

If this branch gets one more turn, the next honest follow-up is not another static selectivity plot.
It is one of these:

- put the same tradeoff inside a closed-loop simulation,
- or add an explicit adjacent interferer amplitude sweep instead of treating the neighbor as unit power.

Without one of those, this is already enough to stop pretending the better slope came for free.

## Source basis

Primary framing for this note came from:

- Daniel Estévez on band-edge filter construction and discriminant gain,
- GNU Radio FLL band-edge documentation,
- GNU Radio source for the half-sine filter construction,
- local provenance in the earlier filter-shape research note.

## Scope boundary

This stays in the study and visualization lane.
It is not a full adjacent-channel rejection study and it is not a closed-loop modem benchmark.
It is the smallest durable follow-up that answers the missing tradeoff question left by the previous slope correction.
