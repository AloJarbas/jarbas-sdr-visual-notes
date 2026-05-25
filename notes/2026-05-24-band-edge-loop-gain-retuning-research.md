# Band-edge loop-gain retuning after the spacing boundary

## Why this pass happened

The spacing sweep had already split one fuzzy question into two cleaner boundaries:

- around `1.24 R_s`, the half-sine lane becomes track-ready again,
- around `1.57 R_s`, it finally beats the proxy on mean tail residual.

That left one bounded tuning question:

**if spacing stays fixed at the first track-ready point `1.24 R_s`, can loop-gain retuning materially close the residual gap, or is the later `1.57 R_s` crossover still mostly geometry?**

The active queue already wanted this single-axis follow-up, so this pass stayed there instead of wandering back into broader SDR taxonomy or packaging.

## Source decisions

### Accepted for the main claim

1. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted again as the primary source. It still does the most useful job for this branch:
   - derivative-of-matched-filter intuition,
   - GNU Radio / fred harris half-sine construction,
   - the adjacent-channel cost of the wider design,
   - and the emphasis that loop coefficients only make sense once detector gain is understood.

2. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted because it keeps the block-level contract honest:
   - oversampling,
   - roll-off dependence,
   - large linear-phase FIRs,
   - the `norm(x_l) - norm(x_u)` discriminator,
   - and the fact that the public control knob is loop bandwidth.

3. **GNU Radio source: `fll_band_edge_cc_impl.cc`**  
   https://raw.githubusercontent.com/gnuradio/gnuradio/main/gr-digital/lib/fll_band_edge_cc_impl.cc  
   Accepted because this pass needed the implementation facts, not just prose:
   - the half-sine FIR construction,
   - the `norm(out_lower) - norm(out_upper)` error,
   - and the explicit scaling of loop beta by bandwidth and `samps_per_sym`.

4. **Wireless Pi: How a Frequency Locked Loop (FLL) Works**  
   https://wirelesspi.com/how-a-frequency-locked-loop-fll-works/  
   Accepted only as a secondary control-loop framing source. Useful for the reminder that loop filters set dynamic performance limits and that acquisition/tracking usually trade wide versus narrow bandwidth. Not specific enough to carry the band-edge claim by itself.

### Rejected for this pass

1. **Wireless Pi: Band Edge Filters for Carrier and Timing Synchronization**  
   https://wirelesspi.com/band-edge-filters-for-carrier-and-timing-synchronization/  
   Rejected as a main source for this note. It is good for detector intuition, but the missing question here was not the detector derivation anymore; it was the bounded loop-gain consequence at a fixed spacing.

2. **GNU Radio doxygen class page for `fll_band_edge_cc`**  
   https://www.gnuradio.org/doc/doxygen/classgr_1_1digital_1_1fll__band__edge__cc.html  
   Rejected as a primary source because it is mostly API boilerplate and inherited class scaffolding. It does not add much beyond the wiki/source pair for this specific queue question.

3. **GNU Radio 3.7 signal-block manual page**  
   https://www.gnuradio.org/doc/sphinx-3.7.4/digital/blocks.html  
   Rejected as primary support because it mostly repeats the wiki-level block description and parameter list without adding the bounded tuning detail needed here.

4. **Generic PLL / decision-directed FLL tutorials**  
   Rejected because the missing claim is not broad loop pedagogy. It is one band-edge adjacent-pull retuning question under an already-fixed local simulation path.

## Local audit that mattered

I re-used the existing local continuation in:

- `scripts/waveform_carrier_front_ends.py`

That file already had the whole bounded environment:

- pulse-shaped QPSK generation,
- proxy and GNU Radio / half-sine band-edge filters,
- the blockwise closed-loop path,
- and the fixed adjacent-channel setup from the previous notes.

So this did **not** need a new receiver model.
It needed one clean gain sweep under the same geometry.

## The bounded sweep

Everything stayed fixed except loop gain:

- SRRC QPSK
- `4 samples/symbol`
- `3072` symbols
- roll-off `α = 0.35`
- `63`-tap filters
- one adjacent channel at `1.24 R_s`
- adjacent power fixed at `0 dB`
- desired CFO fixed at `0`
- `96` symbols per loop update
- loop gain swept from `0.0005` to `0.0240`

For each gain and each design, I kept the same two public summaries:

1. mean absolute residual CFO over the last eight loop blocks,
2. fraction of those tail blocks that stay inside `±0.05 R_s`.

I also tracked the residual ratio between the half-sine and proxy lanes, because that is the cleanest way to test whether retuning actually changes the ranking instead of merely shrinking both values.

## The result that mattered

The gain sweep answered the branch question pretty cleanly:

### Result 1: lower gain really does reduce pull

Default seed pair `(19,173)`:

| gain | proxy mean residual | half-sine mean residual |
|---:|---:|---:|
| `0.002` | `0.000304 R_s` | `0.004614 R_s` |
| `0.020` | `0.002829 R_s` | `0.044746 R_s` |

So retuning is real.
Lower gain calms the loop.

### Result 2: the ranking does not flip anywhere in the tested gain set

The sharper readout is the ratio:

| gain | half-sine / proxy mean residual ratio |
|---:|---:|
| `0.0005` | `15.1×` |
| `0.0020` | `15.2×` |
| `0.0100` | `15.5×` |
| `0.0200` | `15.8×` |
| `0.0240` | `16.0×` |

So the gain sweep mostly rescales the same geometry gap.
It does **not** turn the later `1.57 R_s` crossover into a tuning artifact.

### Result 3: pushing gain upward hurts the half-sine lane first

On the default seed pair:

- proxy stays at `100%` tail blocks inside `±0.05 R_s` for every tested gain,
- half-sine first drops below `100%` at about **`0.022`**.

Representative rows:

| gain | design | mean tail residual | tail fraction inside `±0.05 R_s` |
|---:|---|---:|---:|
| `0.020` | proxy | `0.002829 R_s` | `100%` |
| `0.020` | half-sine | `0.044746 R_s` | `100%` |
| `0.022` | proxy | `0.003088 R_s` | `100%` |
| `0.022` | half-sine | `0.049069 R_s` | `62.5%` |

So at the first settle-point spacing, the half-sine lane is not only worse on residual pull; it also loses settle margin first as gain rises.

## Small sensitivity check

I did not broaden this into a full Monte Carlo study, but I did probe alternate seed pairs `(23,211)`, `(31,271)`, `(47,389)`.

### Residual-ratio stability

At gains `0.002`, `0.010`, and `0.020`, the half-sine / proxy residual ratio landed in the following ranges:

- `15.2–26.6×` at `0.002`
- `15.5–27.2×` at `0.010`
- `15.8–28.1×` at `0.020`

So the exact factor shifts with seeds, but the queue-level fact does not: retuning does not erase the ordering.

### Settle-band ceiling

For the same four seed pairs:

- gains `0.016`, `0.018`, and `0.019` kept the half-sine tail fraction at `100%` for all four seed pairs,
- at `0.020`, one seed pair had already dropped to `75%`,
- at `0.021`, fractions were `75%`, `50%`, `87.5%`, `75%`,
- at `0.022`, fractions were `62.5%`, `37.5%`, `75%`, `62.5%`.

So a safe seed-robust public sentence is:

**full settle margin survives up to about `0.019`, then starts fraying around `0.020–0.022`.**

That was enough support for a public note without pretending this is a full loop-design atlas.

## Repo decision

The new public note should say three things clearly:

1. lower gain really does reduce adjacent pull,
2. but the half-sine / proxy residual gap stays stubbornly large across the tested gain set,
3. and the half-sine lane loses settle margin first as gain is increased.

That is enough to stop treating the `1.24 R_s` result as an unfinished tuning artifact.

## Deliverables produced

1. `notes/band-edge-loop-gain-retuning.md`
2. `scripts/generate_band_edge_loop_gain_retuning_figure.py`
3. `assets/2026-05-24-band-edge-loop-gain-retuning.{csv,svg,png}`
4. `notebooks/band_edge_loop_gain_retuning.ipynb`
5. `tests/test_band_edge_loop_gain_retuning.py`
6. updated queue summary in `logs/current-state.md`

## Next best move after this

Do **not** keep nudging this same branch with more same-shape gain fiddling.
The bounded answer is already good enough:

- the `1.24 R_s` point is track-ready,
- the `1.57 R_s` crossover is still mostly geometry,
- and gain retuning does not remove the ordering.

So the next best move is to return to the top queue item:

**package the cleanest raw research memo into `public-knowledge-repo` only when one dated note collapses cleanly into one reusable claim.**

Jarbas
