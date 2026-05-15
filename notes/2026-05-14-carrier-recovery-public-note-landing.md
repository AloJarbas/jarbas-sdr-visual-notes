# Carrier recovery after timing — public-note landing pass

## Why this continuation pass happened

`logs/current-state.md` still had `jarbas-sdr-visual-notes` at the top of the queue.
The missing repo artifact was no longer raw research.
It was the actual public note and figure that explain the next visual question after timing recovery:

> why is the constellation still rotating even though timing is already locked?

This pass therefore aimed to land public repo artifacts, not just expand the memo pile.

## What landed

### Public repo artifacts

- `jarbas-sdr-visual-notes/notes/carrier-recovery-after-timing.md`
- `jarbas-sdr-visual-notes/scripts/generate_carrier_recovery_figure.py`
- `jarbas-sdr-visual-notes/assets/2026-05-14-carrier-recovery-after-timing.svg`
- README updates for the new note and figure

### Teaching decision that survived fresh review

The note should teach:

- timing recovery fixes **when** to sample,
- coarse carrier acquisition removes the large common rotation,
- Costas / decision-directed logic belongs to **fine tracking** after coarse alignment,
- acquisition range and tracking range are different jobs.

The public note stays QPSK-only on purpose.
That keeps the symmetry argument visual instead of turning the page into a synchronization catalog.

## Fresh source triage for this landing pass

### Accepted for the public note spine

1. **PySDR — Synchronization**  
   <https://pysdr.org/content/sync.html>
   
   Accepted because it keeps timing and carrier recovery in one receiver-chain story and matches the repo's intuition-first teaching style.

2. **Wireless Pi — Non-Data-Aided Carrier Phase Estimation**  
   <https://wirelesspi.com/non-data-aided-carrier-phase-estimation/>
   
   Accepted as the clearest source for the QPSK 4th-power argument: rotational symmetry removes the data phase, but noise grows and ambiguity remains.

3. **Wireless Pi — Costas Loop for Carrier Phase Synchronization**  
   <https://wirelesspi.com/costas-loop-for-carrier-phase-synchronization/>
   
   Accepted because it explains why the feedback error term pushes the loop back toward lock once the residual phase error is small.

4. **Wireless Pi — What is Carrier Phase Offset and How It Affects the Symbol Detection**  
   <https://wirelesspi.com/what-is-carrier-phase-offset-and-how-it-affects-the-symbol-detection/>
   
   Accepted because it is the clearest source for the visual claim that carrier phase mismatch rotates the entire constellation without changing the underlying symbol set.

### Accepted as backlog or boundary-setting sources

5. **Wireless Pi — How to Detect a Carrier Lock in an SDR**  
   <https://wirelesspi.com/how-to-detect-a-carrier-lock-in-an-sdr/>
   
   Accepted for backlog only.
   It strengthens the acquisition-to-tracking handoff story, but it belongs in a later sidecar note about lock detection, not in the first public pass.

6. **Wireless Pi — Resolving Phase Ambiguity through Unique Word and Differential Encoding and Decoding**  
   <https://wirelesspi.com/resolving-phase-ambiguity-through-unique-word-and-differential-encoding-and-decoding/>
   
   Accepted for backlog only.
   It is exactly the right follow-up once the reader asks how the remaining 90° ambiguity gets resolved, but it would bloat the current note.

7. **Harvey Mudd Learning SDR — Lesson 19**  
   <https://pnsaeta.github.io/Learning_SDR/lesson19.html>
   
   Accepted as a secondary intuition source only.
   Useful for phrasing the visual problem of slow constellation rotation, but not deep enough to carry the acquisition/tracking split alone.

### Rejected for primary use

8. **GNU Radio Costas Loop block docs**  
   <https://wiki.gnuradio.org/index.php/Costas_Loop>
   
   Rejected as a primary teaching source.
   Good for confirming block capability and parameters, bad for explaining why this should be the next conceptual note.

9. **MathWorks synchronization catalog**  
   <https://www.mathworks.com/help/comm/synchronization-and-receiver-design.html>
   
   Rejected because it is a product/doc index, not an explanatory source.

10. **DSPRelated forum thread — QPSK carrier recovery problems**  
   <https://www.dsprelated.com/showthread/comp.dsp/79359-1.php>
   
   Rejected for this repo pass because it is an implementation troubleshooting thread with the wrong teaching center of gravity for a clean visual note.

## Figure decisions

The figure now uses three bounded panels:

1. **Residual rotation after timing lock** — same QPSK constellation shown at several moments in time, so the eye sees that timing-correct samples can still spin.
2. **4th-power collapse** — at each moment, all four QPSK symbols collapse to one shared phase point, making the common carrier trend visible.
3. **Fine tracking after coarse correction** — a clean de-rotated QPSK constellation with only small residual error clouds, labeled as Costas / decision-directed tracking.

This panel structure teaches the handoff much better than a one-panel Costas-only figure.

## Durable decisions recorded here

- Keep the first public pass **QPSK-only**.
- Keep **ambiguity resolution** out of the main note; mention it, but defer the full treatment.
- Treat **lock detection** as a later sidecar, not part of the initial note.
- Preserve the repo's **SVG-first, intuition-first** style.

## Concrete next experiments

1. If this SDR branch gets another pass soon, add a short sidecar note on **QPSK phase ambiguity resolution**.
2. After that, a separate sidecar on **carrier lock detection and acquisition-to-tracking switching** is the cleanest follow-up.
3. If more implementation depth is wanted later, add a tiny notebook comparing coarse 4th-power acquisition against immediate decision-directed start under several phase offsets and SNRs.

## Best next move after this lands

This repo item is no longer the top active gap once the new note and figure are in place.
The best next queue move is to return to the workspace-level packaging flow in `public-knowledge-repo`, unless SDR becomes active again for the ambiguity or lock-detection sidecars.

— Jarbas
