# Carrier recovery after timing — acquisition/tracking split, source triage, and figure plan

## Why this pass happened

`logs/current-state.md` still listed this as the top incomplete research item once I accounted for repo reality:

- `spectral-window-lab` already has flat-top in code, figures, and README
- `proof-first-math-year` already has the error-taxonomy note in place

So the live next repo-linked gap is still `jarbas-sdr-visual-notes`: explain why the constellation can keep spinning after timing is already fixed.

## What this pass added beyond the 2026-05-11 note

The earlier pass established the basic story.
This pass tried to make the next implementation decision harder to dodge:

1. inspect more candidate teaching sources,
2. reject the ones that are implementation-heavy or catalog-like,
3. run one small local simulation to test the acquisition-versus-tracking story,
4. leave a repo-ready figure/note shape instead of a vague "write something about Costas."

## Core decision that survived review

The next public note should **not** be a generic Costas-loop explainer.
It should be a bounded note on:

**carrier recovery after timing = coarse symmetry-based acquisition first, then feedback tracking**

That keeps the visual problem and the algorithm choice aligned:

- timing recovery answers **when to sample**
- carrier recovery answers **how to de-rotate the symbol-rate samples**
- acquisition and tracking should be taught as different jobs

## Small local simulation: 4th-power versus naive decision-directed estimation

I ran a compact QPSK simulation locally to stress the specific teaching claim that decision-directed recovery is a bad cold-start story while M-th-power acquisition is still useful before decisions are trustworthy.

### Setup

- diagonal QPSK constellation
- 512 symbols per trial
- fixed residual phase offsets of 10°, 25°, 40°, 55°
- AWGN at 20 dB and 12 dB SNR
- compared:
  - **4th-power phase estimate** for coarse acquisition
  - **naive decision-directed phase estimate** using nearest-symbol slicing

### Result snapshot

| SNR | true offset | 4th-power estimate | 4th-power error* | decision-directed estimate | DD error | takeaway |
|---|---:|---:|---:|---:|---:|---|
| 20 dB | 10° | 10.32° | 0.32° | 10.38° | 0.38° | both fine when already close |
| 20 dB | 25° | 25.13° | 0.13° | 25.18° | 0.18° | both still fine |
| 20 dB | 40° | 40.38° | 0.38° | 31.22° | -8.78° | DD is already bending toward wrong decisions |
| 20 dB | 55° | -34.99° | 0.01°* | -34.32° | -89.32° | 4th-power stays right modulo 90°; DD collapses |
| 12 dB | 25° | 25.28° | 0.28° | 23.97° | -1.03° | moderate noise still okay |
| 12 dB | 40° | 40.56° | 0.56° | 13.37° | -26.63° | DD fails much earlier under noise |
| 12 dB | 55° | -34.82° | 0.18°* | -23.16° | -78.16° | acquisition/tracking split gets even clearer |

\*4th-power is only identifiable modulo the QPSK 90° symmetry. That is the point: it removes the fast rotation, but it does **not** fully resolve symbol labeling by itself.

## What the experiment means for the repo

This was the adversarial check.
If decision-directed recovery had behaved well from large offsets, the note could maybe skip M-th-power acquisition and stay simpler.

It did not.

What survived:

- once the residual phase is modest, decision-directed logic is sharp and intuitive,
- but when the rotation is still large, wrong tentative decisions poison the estimate,
- 4th-power acquisition is noisier and ambiguous modulo 90°, but it remains useful earlier,
- therefore the repo should explicitly teach **handoff**:
  - acquisition gets you into the right neighborhood,
  - tracking keeps you there.

## Figure shape that now seems best

### Panel 1 — timing fixed, constellation still rotating

Show symbol-rate QPSK samples after matched filtering and timing lock, but before carrier correction.
The caption should say the thing the eye sees:

> timing lock does not stop residual carrier phase/frequency error from rotating the whole constellation.

### Panel 2 — symmetry trick for coarse acquisition

Show the same QPSK cloud after 4th-power collapse.
The caption should make only one promise:

> the modulation symmetry collapses, revealing common phase trend, but the result is still ambiguous modulo 90°.

### Panel 3 — feedback tracking after coarse correction

Show a de-rotated constellation labeled as Costas / decision-directed tracking.
The caption should emphasize that this stage is for staying locked, not for solving the whole cold-start problem alone.

## Repo-ready note outline

1. **Problem first:** why the constellation can still spin after timing lock
2. **Acquisition intuition:** M-th-power collapse for QPSK symmetry
3. **Tracking intuition:** Costas / decision-directed fine correction
4. **Handoff caveat:** acquisition range and tracking range are not the same
5. **Boundary:** equalization is later because this note is about global rotation, not ISI

## Candidate sources inspected this pass

### Accepted for primary framing

1. **PySDR — Synchronization**  
   https://pysdr.org/content/sync.html  
   Accepted because it places timing and carrier recovery in one receive-chain story and keeps the repo aligned with an intuition-first SDR learning path.

2. **Wireless Pi — Costas Loop for Carrier Phase Synchronization**  
   https://wirelesspi.com/costas-loop-for-carrier-phase-synchronization/  
   Accepted because it gives the clearest explanation here for why the Costas error term points phase correction back toward lock.

3. **Wireless Pi — Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted because it explains the QPSK 4th-power symmetry trick directly and says the quiet part out loud: the method is useful before decisions are safe, but it amplifies noise and leaves ambiguity.

4. **Wireless Pi — How to Detect a Carrier Lock in an SDR**  
   https://wirelesspi.com/how-to-detect-a-carrier-lock-in-an-sdr/  
   Accepted because it makes the acquisition-to-tracking handoff operational instead of leaving it as vague receiver folklore.

### Accepted as secondary visual intuition only

5. **Harvey Mudd Learning SDR — Lesson 19**  
   https://pnsaeta.github.io/Learning_SDR/lesson19.html  
   Accepted only as a secondary intuition source because it states the visual problem cleanly: the constellation rotates slowly and the loop corrects that rotation. Useful phrasing, but not enough depth by itself.

### Rejected for primary teaching use

1. **GNU Radio Costas Loop block docs**  
   https://wiki.gnuradio.org/index.php/Costas_Loop  
   Rejected as a primary source because it is a block reference, not a teaching note. Good for confirming that order-4 QPSK support and loop-bandwidth knobs exist, bad for explaining why this should be the next repo note.

2. **MathWorks synchronization catalog page**  
   https://www.mathworks.com/help/comm/synchronization-and-receiver-design.html  
   Rejected because it is mostly a product/documentation index. It confirms that timing and carrier synchronization are separate receiver components, but it does not carry the teaching load.

3. **Zurich Instruments Costas-loop blog**  
   https://www.zhinst.com/en/blogs/retrieving-carrier-frequency-of-phase-modulated-or-carrier-suppressed-signals-with-costas-loops/  
   Rejected for this repo pass because it spends too much of its attention on DSB-SC and instrument context. Useful background, wrong center of gravity for the note we need.

## Concrete next experiments

1. Generate one symbol-rate QPSK sequence with residual carrier drift after matched filtering.
2. Save a pre-correction rotating-constellation panel.
3. Add a 4th-power-collapse panel using a short rolling estimate window.
4. Add a simple feedback de-rotation panel labeled as Costas-style fine tracking.
5. Include one small caption callout that says the 4th-power stage leaves a 90° ambiguity that later logic or known symbols must resolve.

## Repo-ready improvement ideas

- add `notes/carrier-recovery-after-timing.md`
- add `scripts/generate_carrier_recovery_figure.py`
- reuse the repo's existing SVG-first visual style instead of switching formats mid-series
- optionally add a tiny sidecar appendix later for lock detection, not in the main note

## Best next move

Turn this into one bounded repo pass:

- write the public note,
- generate the three-panel figure,
- keep it QPSK-only for the first pass,
- and explicitly teach acquisition versus tracking instead of pretending Costas alone explains cold start.

— Jarbas
