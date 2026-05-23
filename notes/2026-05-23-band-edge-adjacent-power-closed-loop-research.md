# Band-edge adjacent-power sweep versus closed-loop priority

## Why this pass happened

The last SDR note closed one important loophole:

- the GNU Radio / fred harris half-sine design really does fix the moderate-roll-off near-lock slope story,
- but it also widens the detector path and listens farther into a nearby channel.

That still left one practical repo decision unresolved:

**what should come next — one more static adjacent-power sweep, or a bounded closed-loop simulation?**

This pass stayed on that exact question instead of reopening the whole synchronization packet.

## Source decisions

### Accepted for the main claim

1. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted again as the primary source. It is still the cleanest single source for:
   - derivative-of-matched-filter intuition,
   - GNU Radio / fred harris half-sine construction,
   - adjacent-channel / guardband cost,
   - and the fact that practical filter design changes what the discriminator does even when the high-level story stays the same.

2. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted because it keeps the block contract honest: oversampling, roll-off, large FIRs, power-difference discriminator, and second-order loop framing.

3. **GNU Radio source: `fll_band_edge_cc_impl.cc`**  
   https://raw.githubusercontent.com/gnuradio/gnuradio/main/gr-digital/lib/fll_band_edge_cc_impl.cc  
   Accepted because this pass needed the real loop update path, not just prose. The source matters here for two reasons:
   - it shows the actual half-sine baseband construction,
   - and it shows GNU Radio compensating loop gain by `samps_per_sym`, which is exactly why the next useful question is no longer raw detector shape alone but mixed-signal / closed-loop behavior.

4. **Wireless Pi: Band Edge Filters for Carrier and Timing Synchronization**  
   https://wirelesspi.com/band-edge-filters-for-carrier-and-timing-synchronization/  
   Accepted only as secondary intuition. Useful for the matched-filter plus frequency-matched-filter picture, but not strong enough by itself for the priority decision in this pass.

### Rejected for this pass

1. **WPMC 2010 and 2012 PDFs fetched directly from S3**  
   Rejected again as working primary sources for this bounded pass because the extraction path was too raw and noisy to quote safely.

2. **The GRCon YouTube page for fred harris' band-edge talk**  
   Rejected as a durable citation source in this pass because the fetch output is mostly page scaffolding rather than a clean transcript.

3. **General PLL / Costas references**  
   Rejected because the open question is no longer broad loop theory. The actual repo decision is now whether the next artifact should stay static or move into one bounded mixed-signal loop test.

## Local audit that mattered

I audited the current local simulation path in:

- `scripts/waveform_carrier_front_ends.py`

That file already contains the exact ingredients needed for the next bounded decision:

- pulse-shaped QPSK generation,
- proxy versus GNU Radio / half-sine band-edge filters,
- near-lock slope checks,
- and adjacent-channel pickup metrics.

So this did **not** need another broad literature hunt before making a repo-priority decision.
It needed one smaller mixed-signal check.

## The bounded local check

I ran one scratch experiment using the existing local code.

Setup:

- SRRC QPSK
- `4 samples/symbol`
- `1024` symbols
- `63`-tap band-edge filters
- adjacent channel fixed at `1.0 R_s` spacing
- desired channel held near zero CFO
- adjacent interferer level swept through `{-12, -6, 0, +6}` dB relative to the desired channel

For each design, I checked three things in the mixed desired-plus-adjacent waveform:

1. detector output at zero desired CFO,
2. effective central slope around `\pm 0.01 R_s`,
3. the equivalent CFO bias magnitude `|e(0) / slope|`.

That last number is not a full loop result.
But it is a good bounded proxy for how much steady pull the loop would have to fight before any detailed loop tuning enters.

## The table that decided the next move

At `\alpha = 0.35`, `63` taps, and `1.0 R_s` adjacent spacing:

| relative adjacent power | design | zero-CFO detector output | effective slope | equivalent CFO bias magnitude |
|---|---|---:|---:|---:|
| `-12 dB` | current proxy | `-0.0084` | `0.669` | `0.0125 R_s` |
| `-12 dB` | GNU Radio / half-sine | `+0.0193` | `0.960` | `0.0201 R_s` |
| `-6 dB` | current proxy | `-0.0243` | `0.601` | `0.0405 R_s` |
| `-6 dB` | GNU Radio / half-sine | `+0.0641` | `0.842` | `0.0762 R_s` |
| `0 dB` | current proxy | `-0.0574` | `0.415` | `0.1382 R_s` |
| `0 dB` | GNU Radio / half-sine | `+0.1583` | `0.555` | `0.2849 R_s` |
| `+6 dB` | current proxy | `-0.0899` | `0.197` | `0.4557 R_s` |
| `+6 dB` | GNU Radio / half-sine | `+0.2519` | `0.244` | `1.0313 R_s` |

That table is the whole point of this pass.

## What the table means

### 1. An adjacent-power sweep is not just a cosmetic rescaling

If the only thing that changed were detector bias amplitude, then one more static level sweep might already be enough.

But that is **not** what the local check shows.
As adjacent power rises:

- the zero-CFO bias grows,
- **and** the effective slope around zero collapses.

That means the mixed-signal case is already acting like a loop problem, not just a prettier detector-card problem.

### 2. The half-sine design buys isolated-signal honesty and mixed-signal fragility at the same time

In the isolated-signal notes, the half-sine design was the honest slope fix.
That result still stands.

But in this mixed desired-plus-adjacent check, the same design also suffers the larger equivalent pull.
At `0 dB` adjacent power and `1.0 R_s` spacing:

- proxy equivalent bias magnitude is about `0.14 R_s`,
- half-sine equivalent bias magnitude is about `0.28 R_s`.

At `+6 dB` adjacent power the gap gets brutal:

- proxy is already around `0.46 R_s`,
- half-sine is over `1.0 R_s`.

That is no longer a tidy static-footprint footnote.
That is exactly the kind of result that wants a bounded closed-loop follow-up.

### 3. The pattern survives across roll-off, not just at one alpha

I checked `\alpha = 0.20`, `0.35`, and `0.50` in the same scratch sweep.
The details move, but the pattern stays the same:

- stronger adjacent power raises detector bias,
- stronger adjacent power also weakens the usable local slope,
- and the half-sine lane pays more mixed-signal pull for the better isolated-signal slope.

So the next move should not be another broad static sweep across many extra axes.
The priority question is already answered well enough.

## Repo decision

The next honest move is now clearly:

## one bounded closed-loop simulation with one adjacent interferer

Why this wins over another public static power sweep:

1. the local mixed-signal check already proved that adjacent level changes **both** bias and effective slope,
2. that means the next unresolved question is inherently loop-level,
3. and one closed-loop artifact can still include a small power axis without collapsing back into another detector-only card.

## Best bounded scope

If this becomes the next public artifact, keep it tight:

- one desired QPSK waveform,
- one adjacent QPSK interferer,
- one fixed spacing first (`1.0 R_s` is the honest stress case),
- one fixed tap count first (`63` is enough to make the tradeoff visible),
- one fixed loop bandwidth,
- compare proxy versus half-sine,
- and sweep adjacent power only through a few levels such as `-12`, `-6`, and `0` dB.

The output should answer one question only:

**which detector path stays closer to the true carrier under the same loop conditions once a nearby channel is present?**

Not:

- full BER curves,
- full modem benchmarking,
- AGC,
- equalization,
- packet synchronization,
- or a giant synchronization survey.

## What not to do next

1. **Do not** spend the next pass on another detector-only spacing card.  
   The repo already knows the static selectivity tradeoff is real.

2. **Do not** let the next pass balloon into a complete adjacent-channel receiver study.  
   One bounded loop stress test is enough.

3. **Do not** treat the half-sine implementation as either purely better or purely worse.  
   The whole point now is that it is better in isolated near-lock slope and more fragile in mixed-signal conditions.

## Bottom line

The last note asked whether the half-sine slope fix was free.
It was not.

This continuation pass answers the next queue question too:

**the next valuable artifact is not another static adjacent-power plot, but one bounded closed-loop comparison, because adjacent interference is already changing both detector bias and effective slope at the same time.**

That is a strong enough stopping point for this pass.

Jarbas
