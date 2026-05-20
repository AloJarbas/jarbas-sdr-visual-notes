# Band-edge discriminant gain after the waveform-domain front-end sidecar

## Why this pass happened

The new waveform-domain sidecar already made one clean point:

- oversampled 4th-power barely cares about SRRC roll-off,
- band-edge logic gets its clue from the waveform edges,
- and the raw imbalance curve gets visibly stronger as `\alpha` grows.

That note is still good as a first comparison.
What it did **not** settle is whether the plotted band-edge imbalance magnitude should be read as a proxy for the actual FLL loop gain.

This pass was to answer that more carefully before the repo bakes in the wrong lesson.

## Discovery intake

### Local Raindrop pass

I checked the local bookmark export again with `band-edge fll qpsk carrier recovery`.
Nothing useful surfaced for this narrower question.

Decision: reject local Raindrop as a material source for this pass.

### Local / web HN pass

I also did a broad HN pass for the same topic family.
Nothing relevant turned up beyond generic or unrelated SDR chatter.

Decision: reject HN for this pass.

## Source decisions

### Accepted for the main claim

1. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted as the strongest source in this pass. It gives the most useful distinction between:
   - the intuitive power-difference story,
   - the derivative-of-matched-filter view,
   - discriminant gain near lock,
   - and FIR-design effects that can distort the practical discriminator.

2. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted because it keeps the operational contract honest: oversampling, roll-off, filter size, and band-edge power imbalance.

3. **GNU Radio source: `fll_band_edge_cc_impl.cc`**  
   https://raw.githubusercontent.com/gnuradio/gnuradio/main/gr-digital/lib/fll_band_edge_cc_impl.cc  
   Accepted because it confirms a key practical point from Estévez: GNU Radio explicitly compensates loop gain by the discriminant gain, with the source comment stating that the frequency discriminant gain is `samps_per_sym`.

4. **Wireless Pi: How Excess Bandwidth Governs Timing Recovery**  
   https://wirelesspi.com/how-excess-bandwidth-governs-timing-recovery-in-digital-communication-systems/  
   Accepted as the clean intuition source for the phrase fred harris likes: excess bandwidth provides synchronization energy. Useful here because it explains why a raw edge-based cue looks weak when `\alpha` is tiny.

5. **Wireless Pi: Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted again as the continuity source for the oversampled M-th-power branch and its reduced phase-detection range.

6. **MathWorks: Coarse Frequency Compensator**  
   https://www.mathworks.com/help/comm/ref/coarsefrequencycompensator.html  
   Accepted as a secondary pipeline source because it keeps FFT/M-th-power and correlation-based coarse estimation separate instead of flattening them into one "coarse sync" box.

### Rejected for this pass

1. **Learning SDR — Lesson 17: Frequency Locked Loop**  
   https://pnsaeta.github.io/Learning_SDR/lesson17.html  
   Rejected as a primary source. The intuition is fine, but it is too compressed to support a discriminant-gain or normalization claim.

2. **The old WPMC PDF directly fetched from S3**  
   Rejected for direct use here because the extraction path was too raw and noisy to quote safely in this pass.

3. **Broad QPSK/Costas tutorials**  
   Rejected because the open question is now narrower than "how does carrier recovery work?" The issue here is how to read the band-edge plot honestly.

## The important correction

The earlier sidecar used a **raw bounded band-edge imbalance**:

- filter the upper edge,
- filter the lower edge,
- subtract the energies,
- divide by total signal energy.

That is good enough to show that higher roll-off gives a stronger visible clue.
But it is **not automatically the same thing** as the properly calibrated near-lock FLL discriminant gain.

The strongest statement from Estévez and the GNU Radio source together is this:

- for a unit-power input and a properly matched band-edge discriminator,
- the **near-zero slope** is the object that matters for loop gain,
- and in normalized units it should be much less roll-off-sensitive than the raw far-from-zero imbalance height makes it look.

More concretely:

- Estévez derives the band-edge discriminant gain as `T_s = samples/symbol` when frequency error is expressed in **cycles/sample**.
- The current repo plots frequency as `\Delta f / R_s`.
- Since `\Delta f / R_s = T_s \cdot (cycles/sample)`, the expected idealized slope with respect to the repo's x-axis is about **1**, not `T_s`.

That was the key thing worth checking locally.

## Local slope check

I wrote a small durable data artifact:

- `assets/2026-05-20-band-edge-discriminant-slope-check.csv`

The local check uses:

- SRRC QPSK
- `4 sps`
- `1024` symbols
- central finite difference at `\pm 0.01 R_s`
- tap counts `{63, 127, 255}`
- roll-off `{0.05, 0.20, 0.35, 0.50}`

The measured central slopes `d(error) / d(\Delta f / R_s)` are:

| taps | `\alpha=0.05` | `\alpha=0.20` | `\alpha=0.35` | `\alpha=0.50` |
|---|---:|---:|---:|---:|
| 63 | 0.105 | 0.480 | 0.670 | 0.764 |
| 127 | 0.259 | 0.769 | 0.854 | 0.900 |
| 255 | 0.508 | 0.958 | 0.983 | 1.006 |

That table is the whole point of this pass.

## What the table means

### 1. The current sidecar's intuition is still right

At fixed modest CFO, the raw imbalance does get larger with larger roll-off.
So the existing figure is still useful for the first teaching point:

**band-edge logic needs excess bandwidth.**

I would keep that lesson.

### 2. The raw imbalance height is not the right loop-gain summary

Once the measurement is turned into a **near-zero slope** and the filters are given enough taps, the slopes for `\alpha = 0.20, 0.35, 0.50` all move close to **1** in the repo's normalized `\Delta f / R_s` units.

That matches the theory much better than the older visual reading did.

So the better statement is:

- large `\alpha` gives a visibly stronger raw edge-energy cue,
- but the properly normalized near-lock discriminator slope is **much less alpha-dependent** than the raw panel suggests.

### 3. Small roll-off is getting hit twice

`\alpha = 0.05` stays materially below 1 even at `255` taps.
That suggests two effects are being mixed together:

1. **physics / waveform structure:** very small excess bandwidth leaves less useful edge region to exploit;
2. **finite FIR design pressure:** a narrow roll-off region is harder to approximate well with a short practical filter.

This is exactly where Estévez's design discussion matters.
A low-alpha failure mode is not just "less clue" in the abstract; it is also a **filter-design problem**.

### 4. The current repo toy is honest, but only for the right claim

The existing note should be read as:

**"here is why band-edge logic belongs in the waveform/excess-bandwidth branch"**

not as:

**"here is the final calibrated loop gain law for every roll-off."**

That distinction is worth making explicit before this packet hardens.

## Repo decisions

1. **Do not replace or retract** `notes/oversampled-fourth-power-vs-band-edge-fll.md`.  
   It still teaches the assumption split well.

2. **Do add one caveat** the next time that note or figure is touched:  
   the plotted band-edge panel is a **raw imbalance view**, not a normalized FLL-gain calibration plot.

3. **Do not claim** from the current figure alone that higher roll-off directly means proportionally higher loop gain.

4. **Do treat** low-rolloff weakness as a combined waveform-plus-filter-design issue, not just a hand-wavy lack-of-energy slogan.

## Best next experiment

If this SDR branch gets one more bounded pass, the strongest next experiment is now:

## `raw band-edge imbalance` versus `normalized near-lock slope`

with a narrow scope:

1. keep `4 sps`,
2. normalize input power explicitly to 1,
3. add a second band-edge implementation closer to the GNU Radio / fred harris construction,
4. compare slope near zero for several tap counts,
5. keep the old raw-imbalance panel as the intuition panel rather than deleting it.

That would sharpen the repo from **"which clue is this method reading?"** to **"which quantities are safe to compare across roll-off?"**

## Concrete repo-ready improvements

1. **Add a calibrated slope CSV and panel**  
   Plot central slope near zero instead of only raw imbalance at finite offset.

2. **Add a tap-count sensitivity sweep**  
   `63 / 127 / 255` is already enough to show that low-rolloff cases are disproportionately sensitive to FIR quality.

3. **Rename the existing band-edge panel caption**  
   Make it say **raw band-edge imbalance** so readers do not confuse it with loop gain.

4. **If one more code pass happens, swap in a closer band-edge filter design**  
   The current proxy is enough for the first sidecar, but the next note should move closer to the derivative-matched / GNU Radio style construction.

## Bottom line

The earlier sidecar got the branch choice right.
This continuation pass clarifies the one thing it should not silently imply:

**raw band-edge imbalance amplitude is not the same object as normalized FLL discriminant gain.**

That is the honest stopping point for this pass.

Jarbas
