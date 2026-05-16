# Receive-side synchronization map

Once the SDR receive notes are laid side by side, the clean story is simple:

**each stage removes one uncertainty and hands a smaller problem to the next stage.**

That is the real value of a receive-side synchronization map.
Not a generic “sync” blob.
A sequence of narrower jobs.

![Receive-side synchronization map](../assets/2026-05-16-receive-side-synchronization-map.png)

## 1. The shortest version

For this repo’s QPSK-first receive story:

1. **pulse shaping and matched filtering** make the waveform sample-worthy,
2. **timing recovery** decides **when** to sample,
3. **carrier acquisition** removes the big common rotation,
4. **lock detection and handoff** decide when fine tracking is trustworthy,
5. **ambiguity resolution** fixes or sidesteps the last 90° QPSK label uncertainty.

The important part is what this sequence does **not** say:
no single block above solves all five jobs.

## 2. One compact table

| stage | main question | what it fixes | what still remains |
|---|---|---|---|
| pulse shaping + matched filter | is the waveform concentrated enough to read symbol structure? | concentrates symbol energy, improves SNR at the matched filter, makes eye/constellation structure usable | it does **not** choose the sampling instant or remove carrier rotation |
| timing recovery | when should I sample? | finds the useful symbol instant and reduces the stream toward one sample per symbol | the sampled constellation can still spin |
| carrier acquisition | how do I remove the big common rotation before decisions are trustworthy? | uses coarse or symmetry-based logic to cancel most of the carrier error | residual phase remains, and QPSK labeling can still be off by 90° |
| lock detection + handoff | am I close enough now to trust fine tracking? | tells the receiver when to switch from coarse acquisition to Costas / decision-directed tracking | carrier can look locked while the absolute labeling is still wrong |
| ambiguity resolution | which QPSK labeling is correct, or can I encode not to care? | uses unique words or differential encoding after lock | this does **not** replace carrier recovery itself |

## 3. Read the chain as shrinking uncertainty

### Pulse shaping and matched filtering

This stage makes the receive waveform worth sampling at all.
It is what turns a smeared band-limited waveform into one whose symbol structure can show up cleanly.

Deeper note:
- [Pulse shaping and matched filtering](pulse-shaping-matched-filtering.md)

### Timing recovery

Timing recovery answers:

**which sample instant best represents each symbol?**

It does not solve carrier rotation.
A receiver can be sampling the right symbol centers and still watch the whole QPSK cloud rotate.

Deeper notes:
- [Symbol timing and eye opening](symbol-timing-and-eye-opening.md)
- [Gardner vs Mueller and Muller](gardner-vs-mueller-and-muller.md)

### Carrier acquisition and tracking

After timing lock, the next problem is no longer “when?”
It becomes:

**how do I de-rotate these symbol-rate samples?**

For QPSK, the useful public story is:

- coarse acquisition first,
- fine tracking second.

That split matters because decision-directed tracking is strongest near lock, not during a cold start with a large residual rotation.

Deeper note:
- [Carrier recovery after timing](carrier-recovery-after-timing.md)

### Lock detection and handoff

This is the stage many simplified diagrams skip.
It is not a new waveform-correction block.
It is the receiver’s internal answer to:

**has acquisition settled enough that fine tracking and hard decisions are now safe to trust?**

That is why this repo keeps lock detection separate from the broader carrier-recovery note.

Deeper note:
- [Carrier lock detection and handoff](carrier-lock-detection-and-handoff.md)

### Ambiguity resolution

A QPSK loop can stop the spin and still leave the absolute quadrant labeling unresolved.
That last 90° uncertainty is not a contradiction.
It is part of the modulation symmetry.

So the final step is small but necessary:

- choose the correct quadrant labeling with known symbols, or
- use differential encoding so a constant quadrant offset does not ruin the payload.

Deeper note:
- [QPSK phase ambiguity resolution](qpsk-phase-ambiguity-resolution.md)

## 4. Scope boundary

This map is intentionally narrow.
It is a **QPSK-first, symbol-rate receive-side map**.

It leaves out several real receiver jobs on purpose, including:

- equalization,
- packet or frame synchronization,
- AGC details,
- large-CFO front-end recovery before the symbol-rate view is usable.

Those are all legitimate topics.
They are just outside the current note packet.

## 5. The main sentence worth remembering

If the receive chain feels confusing, compress it to this:

- matched filtering makes the waveform sample-worthy,
- timing decides **when**,
- carrier recovery decides **how to de-rotate**,
- lock detection decides **when to trust tracking**,
- ambiguity resolution decides **which labels are actually meant**.
