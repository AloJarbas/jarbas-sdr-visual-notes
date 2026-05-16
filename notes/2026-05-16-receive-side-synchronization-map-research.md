# Receive-side synchronization map: integrating the current SDR note lane without collapsing the stages

## Why this pass happened

The SDR branch is still the strongest live queue in the workspace, and the repo now has a real receive-side packet:

- pulse shaping and matched filtering,
- timing recovery,
- carrier recovery,
- lock detection and handoff,
- QPSK ambiguity resolution.

What it still lacked was one compact map that puts those notes on the same page.

`notes/receive-first-sdr-chain.md` is broader and earlier.
It introduces the repo.
It does **not** yet act as the synchronization spine for the newer QPSK receive-side sequence.

So the next bounded question became:

**how should the repo show these stages as one receive-side chain without pretending they are all the same job?**

## Research question

For a compact public sidecar in `jarbas-sdr-visual-notes`, what is the cleanest way to place:

1. pulse shaping / matched filtering,
2. timing recovery,
3. coarse carrier acquisition and fine tracking,
4. lock detection / acquisition-to-tracking handoff,
5. and QPSK ambiguity resolution

on one visual spine, while keeping the scope narrow and honest?

## What survived source review

- The right teaching axis is **not** “here are five synchronization buzzwords.”
  It is **which uncertainty gets removed at each stage**.
- Pulse shaping and matched filtering belong on the map because they make the waveform **sample-worthy**, even though they are not themselves timing or carrier synchronization blocks.
- Timing recovery should stay ahead of symbol-rate carrier phase tracking in this repo’s public story.
  The symbol-rate view only becomes trustworthy after the receiver knows **when** to sample.
- Carrier acquisition and carrier tracking are still different jobs.
  The map should say so explicitly instead of compressing them into one vague “Costas loop” box.
- Lock detection is not a separate waveform-correction block.
  It is the receiver’s internal answer to **“has acquisition settled enough to trust tracking and decisions?”**
- QPSK ambiguity resolution is a separate final stage.
  Carrier lock can stop the spin while absolute quadrant labeling remains unresolved.
- Large-CFO front-end recovery is real, but the first public map should keep it outside the frame instead of bloating into a full modem architecture.

## Source decisions

### Accepted for primary framing

1. **PySDR: Synchronization**  
   https://pysdr.org/content/sync.html  
   Accepted because it keeps timing and carrier processing inside one receive-chain story and explicitly treats synchronization as receive-side work before demodulation.

2. **Wireless Pi: Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted because it gives the cleanest explanation for why coarse M-th-power acquisition belongs before decisions are trustworthy.

3. **Wireless Pi: Costas Loop for Carrier Phase Synchronization**  
   https://wirelesspi.com/costas-loop-for-carrier-phase-synchronization/  
   Accepted because it is the clearest source in this set for why decision-directed or Costas-style tracking is a near-lock job, not the whole cold-start story.

4. **Wireless Pi: How to Detect a Carrier Lock in an SDR**  
   https://wirelesspi.com/how-to-detect-a-carrier-lock-in-an-sdr/  
   Accepted because it frames lock detection as operational transition logic: reacquisition, mode switching, and when to trust decisions.

5. **Wireless Pi: Resolving Phase Ambiguity through Unique Word and Differential Encoding and Decoding**  
   https://wirelesspi.com/resolving-phase-ambiguity-through-unique-word-and-differential-encoding-and-decoding/  
   Accepted because it cleanly separates carrier lock from the final QPSK label-resolution job.

### Accepted only as boundary-setting cross-checks

6. **Wireless Pi: Classification of Carrier Frequency Synchronization Techniques**  
   https://wirelesspi.com/classification-of-carrier-frequency-synchronization-techniques/  
   Accepted only as a scope check. It is useful for stating that large CFO can require a non-timing-aided front-end stage before the symbol-rate story starts. That is real, but outside this first public map.

### Rejected as primary sources

1. **GNU Radio Costas Loop docs**  
   https://wiki.gnuradio.org/index.php/Costas_Loop  
   Rejected as the main spine because it is a block reference with parameter notes, not a clean pedagogical ordering of receive-side stages.

## Repo decision

The new sidecar should teach one horizontal receive-side sequence where each stage answers one distinct question:

1. **Pulse shaping / matched filtering**: is the waveform concentrated enough that useful symbol structure appears?
2. **Timing recovery**: when should the receiver sample?
3. **Carrier acquisition**: how do we remove the big common rotation before decisions are trustworthy?
4. **Lock detection / handoff**: are we close enough now to trust fine tracking and hard decisions?
5. **Ambiguity resolution**: which QPSK labeling is correct, or how do we stop caring about the absolute label?

The note should keep repeating one idea:

> each stage removes one uncertainty and hands a smaller problem to the next stage.

That is stronger than a generic block diagram and more honest than pretending one “sync” block solves everything.

## Figure shape that now seems strongest

Use one wide five-stage spine.
For each stage, show:

- the main question,
- what the stage fixes,
- and what is still unresolved afterward.

The “still unresolved” row matters a lot.
That is what prevents the visual from collapsing back into folklore.

A good final-state label is something like:

`stable labeled symbols` or `payload-ready symbols`

because that makes the ambiguity-resolution role visible.

## Best next move

Land one repo pass that adds:

- `notes/receive-side-synchronization-map.md`
- one generated figure and PNG export
- README links so the new note becomes part of the visible receive-side packet

After that, the strongest next move is probably to rebuild the older broad receive-first chain visual with the same reproducible figure tooling, not to widen the synchronization lane again immediately.

Jarbas
