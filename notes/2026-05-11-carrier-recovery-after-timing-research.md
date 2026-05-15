# Carrier recovery after timing — why this is the next SDR note, and what it should cover

## Research question

After `pulse shaping -> symbol timing -> Gardner vs M&M`, what is the next bounded receive-side intuition note for `jarbas-sdr-visual-notes`?

The best candidate is:

**carrier recovery after timing lock**

not as a loop-tuning guide, but as a simple answer to the visual question:

> why can the constellation still spin even after timing is fixed?

## Scope boundary

This pass stays in the same lane as the rest of the repo:

- study and simulation only,
- intuition first,
- no live-emission procedures,
- no aggressive control-law tuning advice.

## What survived source review

- Timing recovery and carrier recovery are related, but they clean up different failure modes.
- After matched filtering and timing lock, you can still have **residual carrier phase / fine frequency error**, which shows up as a rotating constellation.
- **Costas loop** is the right next mental model for PSK because it uses the demodulated I/Q structure itself to drive phase correction without needing a pilot tone.
- **M-th-power / non-data-aided phase estimation** is the right acquisition-side contrast because it exploits constellation symmetry before decisions are trustworthy.
- **Decision-directed recovery** is strongest after the receiver is already close enough that tentative decisions are mostly right.
- Therefore the next note should not be "Costas loop in isolation." It should be a small three-part story:
  1. why timing lock does not stop constellation rotation,
  2. how non-data-aided acquisition can remove large ambiguity,
  3. how Costas / decision-directed tracking keeps the residual phase under control.

## The clean receive-side sequence

The repo now has enough material to show this order explicitly:

1. **pulse shaping + matched filtering** make symbol evidence visible,
2. **timing recovery** decides *when* to sample,
3. **carrier recovery** decides *how to de-rotate* those symbol-rate samples,
4. **symbol decisions** become trustworthy enough to help tracking,
5. only after that does it make sense to talk about stronger equalization / packet plumbing topics.

That ordering is clearer than jumping straight from timing detectors to equalization.

## Why carrier recovery wins over equalization as the next note

I checked the obvious competing direction:

> maybe the next note should be equalization instead.

I do not think so.

The current repo's newest visuals already make one unresolved artifact very obvious: after timing is fixed, the points can still circle or rotate.
That makes carrier recovery the most natural continuation because it answers the next thing the eye notices.

Equalization is important, but it solves a different visual problem: ISI and channel distortion, not a clean global rotation.

## Practical split that seems worth teaching

### 1. M-th-power / non-data-aided acquisition

Teach this as the symmetry trick.
For QPSK, a 4th-power view collapses the modulation symmetry and reveals a common phase trend.

Why it belongs in the note:
- it works before symbol decisions are reliable,
- it gives a clean intuition for coarse phase acquisition,
- it naturally explains phase ambiguity and why a later stage or known sequence still matters.

Main caveat:
- it amplifies noise and is not the cleanest fine-tracking method once you are already close.

### 2. Costas loop / fine carrier tracking

Teach this as the self-correcting de-rotator.
It uses the I/Q structure after downconversion and matched filtering to generate an error signal whose sign tells the receiver which way to rotate back.

Why it belongs in the note:
- it is the standard intuition bridge from "spinning constellation" to "stable points",
- it fits directly after the repo's timing material,
- it explains why fine carrier recovery is usually a feedback problem, not just a one-shot estimate.

Main caveat:
- it wants the receiver to be close enough that the error detector still points the right way.

### 3. Decision-directed tracking

Teach this as the later, trust-the-nearest-symbol mode.
Once decisions are mostly correct, they provide a sharper reference for residual phase tracking.

Why it matters in the note:
- it explains why acquisition and tracking are often different modes,
- it connects naturally to lock detection and handoff logic,
- it prevents the common mistake of treating one loop as if it does the whole job equally well from cold start to steady state.

## Adversarial check

I explicitly looked for whether the note should frame Costas as the whole answer.
That would be too neat.

The better story is:

- **non-data-aided acquisition** gets you close when decisions are not yet safe,
- **Costas / decision-directed tracking** keeps you locked once the constellation is already interpretable.

That split is more honest and also more useful pedagogically.

## Suggested artifact shape for the repo

Best first public pass:

1. one note called something like **"Carrier recovery after timing"**,
2. one SVG with three panels:
   - rotating symbol-rate constellation after timing lock,
   - QPSK 4th-power collapse as the acquisition intuition,
   - de-rotated / tracked constellation with a Costas-style feedback label,
3. one short receive-chain diagram that places this note after the timing notes.

The figure should teach the problem before naming the algorithms.

## Concrete experiments worth doing locally

1. Simulate QPSK with matched filtering, timing lock, and a residual carrier offset.
2. Save a short symbol-rate constellation before carrier recovery.
3. Apply a simple 4th-power phase estimate over a window and show the coarse correction.
4. Apply a lightweight Costas-style feedback update and show the residual tightening.
5. Include one caveat panel or caption saying that acquisition and tracking ranges are not the same thing.

## Accepted sources

### Accepted for primary framing

1. **PySDR synchronization chapter**  
   https://pysdr.org/content/sync.html  
   Accepted because it gives the cleanest receive-chain placement: synchronization spans timing and frequency/phase correction, and the chapter explicitly pairs M&M with Costas in the same educational arc.

2. **Wireless Pi — Costas loop for carrier phase synchronization**  
   https://wirelesspi.com/costas-loop-for-carrier-phase-synchronization/  
   Accepted because it gives the strongest intuitive and mathematical spine for why the Costas error signal points phase correction the right way for BPSK/QPSK.

3. **Wireless Pi — non-data-aided carrier phase estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted because it explains the M-th-power symmetry trick, the acquisition value of non-data-aided estimation, and the noise / ambiguity costs.

4. **Wireless Pi — how to detect a carrier lock in an SDR**  
   https://wirelesspi.com/how-to-detect-a-carrier-lock-in-an-sdr/  
   Accepted because it makes the acquisition-vs-tracking handoff concrete instead of leaving it as hand-waving.

### Accepted as implementation cross-check only

5. **GNU Radio Costas Loop block docs**  
   https://wiki.gnuradio.org/index.php/Costas_Loop  
   Accepted only as an implementation cross-check for practical parameters like loop order and the existence of SNR-aided slicing/tanh behavior.

### Rejected as primary sources

1. **GNU Radio Costas Loop block docs** as the main explanation source  
   Rejected for primary teaching use because the page is too terse and includes wording that makes the loop sound like the main downconversion stage, which is not the clean intuition this repo needs.

2. **DeepWiki FPGA modem Costas page**  
   https://deepwiki.com/lauchinyuan/FPGA_QPSK-modem/3.1-carrier-recovery-(costas-loop)  
   Rejected because it is implementation-dense and too far downstream from the repo's current intuition-first level.

3. **Wikipedia Costas loop page**  
   https://en.wikipedia.org/wiki/Costas_loop  
   Rejected as a final citation target because it is secondary and not needed once better teaching sources are in hand.

## Best next move

Turn this into one bounded repo improvement:

- add a note on carrier recovery after timing,
- center it on the visual problem of constellation rotation,
- contrast non-data-aided acquisition with Costas / decision-directed tracking,
- and leave equalization for a later note once the phase story is already stable.