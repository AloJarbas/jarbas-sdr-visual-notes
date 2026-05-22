# Band-edge filter shape after the slope-calibration pass

## Why this pass happened

The last SDR pass already fixed the main wording problem:

- raw band-edge imbalance is not the same object as normalized near-lock slope,
- the old proxy panel still works as intuition,
- and the only remaining technical caveat was whether the current proxy filter shape was itself hiding too much of the real band-edge story.

That is the only question this pass needed to answer.

Not:

- whether band-edge FLL exists,
- whether excess bandwidth matters,
- or whether the repo needs a giant synchronization survey.

Just this:

**if the current boxy proxy is replaced with a GNU Radio / fred harris style half-sine band-edge design, does the normalized-slope story materially change?**

## Discovery intake

### Local Raindrop pass

I ran the local Raindrop discovery helper on `band-edge`.
Nothing useful surfaced for this narrower filter-design question.

Decision: reject local Raindrop as a material source for this pass.

### Local HN pass

I also ran the local HN slice with `sdr synchronization`.
Nothing useful showed up.

Decision: reject HN for this pass.

## Source decisions

### Accepted for the main claim

1. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted as the strongest source again. This is the source that actually makes the next comparison worth doing:
   - ideal derivative-of-matched-filter view,
   - GNU Radio / fred harris half-sine FIR construction,
   - Remez alternative,
   - and the point that discriminant gain near lock depends on how well the practical filter matches the ideal roll-off-region behavior.

2. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted because it keeps the operational contract honest: oversampling, roll-off, large filters, and the practical `|x_l|^2 - |x_u|^2` discriminator.

3. **GNU Radio source: `fll_band_edge_cc_impl.cc`**  
   https://raw.githubusercontent.com/gnuradio/gnuradio/main/gr-digital/lib/fll_band_edge_cc_impl.cc  
   Accepted because this pass specifically needed the actual filter-construction formula rather than just a prose summary. The half-sine baseband taps and modulation placement in `design_filter()` are the core implementation reference here.

### Accepted only as secondary context

4. **Wireless Pi: Band Edge Filters for Carrier and Timing Synchronization**  
   https://wirelesspi.com/band-edge-filters-for-carrier-and-timing-synchronization/  
   Accepted only as a secondary intuition source. It is helpful on the matched-filter / frequency-matched-filter story, but it is not the source I would trust for the implementation comparison by itself.

### Rejected for this pass

1. **Wireless Pi: How Excess Bandwidth Governs Timing Recovery**  
   Rejected for this pass because it is the right intuition source for why excess bandwidth matters at all, but the open question is now narrower than that.

2. **The WPMC PDF fetched directly from S3**  
   Rejected again because the extraction path is too raw and noisy to use cleanly in this bounded pass.

3. **General PLL / Costas references**  
   Rejected because the remaining question is filter shape inside the band-edge branch, not loop theory in general.

## The bounded local experiment

I added one comparison artifact set:

- `scripts/generate_band_edge_filter_design_comparison_figure.py`
- `assets/2026-05-22-band-edge-filter-design-comparison.csv`
- `assets/2026-05-22-band-edge-filter-design-comparison.svg`
- `assets/2026-05-22-band-edge-filter-design-comparison.png`
- `notebooks/band_edge_filter_design_comparison.ipynb`
- `notes/band-edge-filter-shape-and-slope.md`

The setup stays intentionally narrow:

- SRRC QPSK
- `4 samples/symbol`
- `1024` symbols
- central finite difference at `±0.01 R_s`
- tap counts `{63, 127, 255}`
- roll-off `{0.05, 0.20, 0.35, 0.50}`
- two band-edge designs:
  1. the current repo proxy bandpass construction
  2. a GNU Radio / fred harris style half-sine construction copied from the source logic

To avoid a pointless sign-convention fight, the comparison stores an **oriented** discriminator output so positive CFO always corresponds to positive local slope.

## The result that mattered

At `α = 0.35`, the near-lock slopes are:

| design | 63 taps | 127 taps | 255 taps |
|---|---:|---:|---:|
| current proxy | `0.670` | `0.854` | `0.983` |
| GNU Radio / half-sine | `0.986` | `1.003` | `1.042` |

That table is the whole pass.

## What it means

### 1. The current proxy really is shape-limited

The old proxy does not only blur the raw clue visually.
It also underestimates the normalized near-lock slope at moderate roll-off unless the filters get fairly long.

So the remaining gap in the last note was not just:

- finite sample count,
- finite difference noise,
- or bad luck.

A lot of it was simply the filter shape.

### 2. The GNU Radio / half-sine construction recovers the normalized story much sooner

With the half-sine style design, the slope is already near `1` for `α = 0.20`, `0.35`, and `0.50` even at `63` taps.

That matters because it changes the repo's honest wording from:

- "the normalized slope gets closer to 1 if you keep lengthening the current proxy"

into:

- "the normalized slope is already basically there once the practical filter shape matches the real band-edge idea well enough."

That is a materially better claim.

### 3. Tiny roll-off still stays weak

At `α = 0.05`, the half-sine design only reaches about `0.799` at `63` taps.
It stays below the normalized target even when taps rise.

That means the small-roll-off weakness survives the design upgrade.
So the repo can now separate two effects much more cleanly:

1. **filter-shape mismatch** was hurting the moderate-roll-off cases in the proxy implementation;
2. **very small excess bandwidth** remains an actually weak operating regime.

### 4. The old raw-imbalance panel remains fine for the right job

This pass does **not** invalidate the earlier intuition panel.
It still teaches the right first lesson:

**band-edge logic gets its clue from excess bandwidth.**

What changes is the interpretation of the more calibrated slope story.
The repo should stop quietly treating the current proxy as though it were already a faithful band-edge implementation.

## Repo decisions

1. **Keep** `notes/oversampled-fourth-power-vs-band-edge-fll.md` as the intuition split.
2. **Keep** `notes/band-edge-discriminant-gain-and-slope.md` as the raw-versus-calibrated correction.
3. **Add** `notes/band-edge-filter-shape-and-slope.md` as the implementation-quality follow-up.
4. **Do not** present the old proxy as the final practical band-edge design anymore.
5. **Do not** reopen a broader SDR synchronization taxonomy from here.

## Best next move

If SDR gets one more bounded pass, the strongest next experiment is now:

## `half-sine band-edge slope benefit` versus `guardband / adjacent-channel cost`

Why that one:

- Estévez explicitly warns that the GNU Radio / fred harris construction is wider than necessary,
- the normalized-slope question is now answered well enough,
- and the next honest tradeoff is no longer slope calibration but **selectivity cost**.

That means:

- no more generic slope sweeps,
- no bigger front-end taxonomy,
- just a bounded filter-shape benefit versus guardband burden check if the repo wants one last SDR sidecar.

## Bottom line

The earlier slope note found the right question.
This pass answers it.

**Yes — the current proxy filter shape was materially understating the band-edge near-lock slope.**

A GNU Radio / fred harris style half-sine construction gets the moderate-roll-off cases close to the normalized target much sooner.
The only weak case that really survives the upgrade is very small roll-off.

That is a clean enough stopping point.

Jarbas
