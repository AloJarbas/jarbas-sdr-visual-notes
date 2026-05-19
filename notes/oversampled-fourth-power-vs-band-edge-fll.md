# Oversampled 4th-power versus band-edge FLL

The previous note stopped the symbol-rate story in the right place:

**once a QPSK 4th-power estimator is looking at one sample per symbol, its honest CFO window is limited by that late-stage view.**

The next question is not whether carrier recovery becomes impossible.
It is which earlier front end is the cleaner object.

This sidecar keeps that comparison narrow:

- one pulse-shaped QPSK waveform,
- one oversampled `4 sps` receiver view,
- one SRRC roll-off sweep,
- one symmetry-based front end,
- one band-edge waveform-domain clue.

![Oversampled 4th-power versus band-edge FLL](../assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.png)

## 1. The two branches do not use the same information

### Oversampled 4th-power

This branch still uses the old PSK symmetry trick.
The only real change is **where** the estimator lives.

Instead of waiting until the receiver is already at `1 sps`, it measures phase rotation on the oversampled waveform.
At `4 sps`, the same QPSK 4th-power alias limit becomes

`|Δf| < F_s / 8 = 4 R_s / 8 = 0.5 R_s`.

So this branch is the clean continuation when the teaching point is still:

**blind PSK symmetry removal, just earlier in the chain.**

### Band-edge FLL

This branch uses a different clue.
It does not care about QPSK rotational symmetry first.
It cares about the fact that a pulse-shaped waveform with nonzero roll-off has usable edge energy around the occupied-band boundary.

A carrier offset shifts that waveform against the receiver's expected center, so the upper and lower edge bands stop matching.
That imbalance becomes the discriminator clue.

So this branch is cleaner when the teaching point is:

**waveform-domain coarse recovery from excess-bandwidth structure.**

## 2. The bounded local experiment

The code for this pass lives in:

- `scripts/waveform_carrier_front_ends.py`
- `scripts/generate_waveform_carrier_front_end_figure.py`
- `assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.csv`
- `notebooks/waveform_carrier_front_ends.ipynb`

The experiment stays intentionally small:

- random QPSK symbols,
- SRRC pulse shaping,
- `4 samples/symbol`,
- roll-off sweep `α ∈ {0.05, 0.20, 0.35, 0.50}`,
- CFO sweep on the same waveform,
- two readouts:
  - oversampled 4th-power coarse CFO estimate,
  - a bounded band-edge imbalance metric.

This is not a full band-edge loop implementation.
That is deliberate.
The useful first question is whether the discriminator clue is visibly there, and how strongly it depends on roll-off.

## 3. What the sweep says

### A. The oversampled 4th-power estimate barely cares about roll-off

Across the sweep, the 4th-power estimate stays close to the identity line for `|Δf| / R_s <= 0.45`.
In this experiment the worst absolute error inside that range is about `0.012 R_s`.

That is the key continuity lesson.
The oversampled 4th-power branch is still the same symmetry-based object.
It does **not** need excess bandwidth in the same way the band-edge branch does.

### B. The band-edge clue gets stronger only when roll-off leaves usable edge energy

At one modest offset, `Δf / R_s = 0.10`, the band-edge imbalance grows from about

- `0.007` at `α = 0.05`
- to `0.082` at `α = 0.50`.

That is the second key lesson.
Band-edge logic is not just another generic coarse loop.
It becomes informative because the roll-off leaves real edge energy for the discriminator to push against.

### C. The comparison is really about assumptions

That is the whole point of this note.
The better branch depends on what the receiver is allowed to trust.

| branch | what it exploits | when it is the cleaner object | what this sweep shows |
|---|---|---|---|
| oversampled 4th-power | PSK rotational symmetry | pilot-free PSK, want continuity with the existing carrier packet | estimate stays nearly unchanged across the roll-off sweep until the `4 sps` alias limit arrives |
| band-edge FLL view | excess-bandwidth asymmetry | oversampled pulse-shaped waveform, want a waveform-domain coarse clue | discriminator strength rises sharply with roll-off |
| pilot / preamble methods | known transmitted structure | packet systems allowed to spend known symbols | outside this bounded blind-front-end comparison |

## 4. What this changes in the receive-side packet

The repo can now say something sharper than before:

1. the symbol-rate note explains where the late-stage QPSK story stops,
2. the large-CFO boundary note says why earlier observation rate widens the honest 4th-power window,
3. this sidecar says why **oversampled 4th-power** and **band-edge FLL** are not interchangeable front ends.

They solve a similar early-receiver problem, but they are reading different evidence from the signal.

## 5. What this note does not try to do

It does **not** try to rank every coarse-carrier method.
It does **not** claim that band-edge FLL replaces pilot-aided acquisition.
It does **not** model adjacent-channel leakage, AGC interaction, or a full closed-loop implementation.

Those would all be real next topics, but they are not needed to make the comparison honest.

## 6. Companion notebook and next questions

The companion notebook `notebooks/waveform_carrier_front_ends.ipynb` slows down the assumptions, reads the generated CSV, and leaves a few bounded follow-ups:

- how much of this contrast survives after matched filtering and timing recovery are folded into the same experiment?
- where does the first useful pilot or preamble comparison belong without turning this repo into a full packet receiver survey?
- which older SDR visual now deserves the same rebuildable figure treatment as the newer synchronization packet?

## 7. Source basis

Primary framing for this pass came from:

- Wireless Pi on M-th-power carrier estimation,
- GNU Radio material on FLL band-edge logic,
- PySDR synchronization notes,
- MathWorks receiver examples that keep coarse frequency compensation separate from later fine tracking,
- local provenance in `notes/2026-05-19-waveform-domain-coarse-carrier-front-ends-research.md`.

## Scope boundary

This stays in the study and visualization lane.
The point is not to hand over a full receiver recipe.
The point is to say, cleanly, what each early front end is actually reading from the signal.
