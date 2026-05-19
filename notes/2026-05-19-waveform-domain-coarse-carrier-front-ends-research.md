# Waveform-domain coarse-carrier front ends after the symbol-rate boundary note

## Why this pass happened

The large-CFO boundary note is now in place.
That settled one honest scope statement:

- the symbol-rate QPSK 4th-power story is real,
- its honest CFO window scales with the rate seen by the estimator,
- and large CFO often means the receiver needs an earlier front end instead of a more heroic late-stage claim.

What was still unresolved was the next branch choice.
If this repo gets one more synchronization sidecar, should it compare:

1. oversampled 4th-power coarse estimation,
2. band-edge FLL style recovery,
3. pilot or correlation-based coarse estimation,

or should some of those stay named-but-unexpanded?

## Discovery intake

### Local Raindrop pass

I checked the local Raindrop export again with SDR-oriented queries and a broad `sdr` pass.
Useful resurfacing was thin:

- **PySDR** reappeared and remains relevant.
- older hardware and hobby SDR bookmarks did **not** help with this receiver-front-end comparison.

Decision: accept the PySDR bookmark as a continuity source, reject the rest for this pass.

### Local Hacker News pass

I also checked the local HN slice with a broad pass.
Nothing materially useful showed up for this bounded synchronization question.

Decision: reject HN for this pass; it added breadth-of-search but not usable technical framing.

## Research question

For the next repo-worthy continuation, what is the cleanest way to explain **which coarse-carrier front end belongs before Costas tracking**, without turning the note set into a giant synchronization survey?

More specifically:

- when is oversampled 4th-power still the right continuation of the current packet,
- when does a band-edge FLL become the cleaner object,
- and when should the note simply say that known structure changes the answer?

## Source decisions

### Accepted for primary framing

1. **Wireless Pi: Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted again as the clearest statement of the M-th-power logic and its reduced phase-detection range `[-\pi/M, +\pi/M)`.

2. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted because it gives the compact operational summary of what the band-edge discriminator actually uses: oversampling, pulse-shape roll-off, and band-edge power imbalance.

3. **MathWorks: QPSK Transmitter and Receiver**  
   https://www.mathworks.com/help/comm/ug/qpsk-transmitter-and-receiver.html  
   Accepted because it keeps the receiver pipeline honest: coarse frequency compensation first, timing recovery, then fine carrier synchronization.

4. **MathWorks: Coarse Frequency Compensator**  
   https://www.mathworks.com/help/comm/ref/coarsefrequencycompensator.html  
   Accepted because it usefully distinguishes FFT-based M-th-power style estimation from correlation-based coarse estimation, instead of pretending there is one universal front end.

### Accepted as secondary cross-checks

5. **PySDR: Synchronization**  
   https://pysdr.org/content/sync.html  
   Accepted as continuity framing for sample-rate reduction and receive-chain ordering.

6. **Wireless Pi: How to Estimate the Carrier Phase**  
   https://wirelesspi.com/how-to-estimate-the-carrier-phase/  
   Accepted as the clean reminder that known-symbol estimators remove modulation with a different contract and avoid the M-th-power noise-enhancement tradeoff.

7. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted only as a secondary implementation-and-limitations cross-check. Strong for intuition and pitfalls, but too detailed to be the main teaching spine for the next small note.

### Rejected for this pass

1. **GNU Radio: QPSK Mod and Demod tutorial**  
   Rejected as a primary source because it is a broad tutorial, not a crisp comparison of coarse-carrier front-end families.

2. **DSP StackExchange thread on FFT-based coarse carrier recovery**  
   https://dsp.stackexchange.com/questions/58019/fft-based-coarse-carrier-recovery-for-qpsk  
   Rejected because it was access-fragile in fetch and would still be anecdotal compared with the cleaner primary sources above.

3. **Pure Costas-loop references**  
   Rejected because the open question is now explicitly **before** the near-lock Costas stage.

4. **OFDM CFO tutorials**  
   Rejected because they answer a different synchronization structure and would muddy the single-carrier QPSK lane.

5. **General PLL/control-theory surveys**  
   Rejected because they would enlarge the pass without improving the specific branch choice this repo needs.

## What the sources say together

### 1. Oversampled 4th-power is still the cleanest continuation when continuity matters most

If the repo wants the smallest step beyond the symbol-rate alias note, oversampled 4th-power remains the strongest continuation.

Why:

- it preserves the same modulation-stripping intuition already used in the current packet,
- it explains the widened capture window by sample rate rather than by a new algorithmic mythology,
- and it stays inside a pilot-free PSK teaching lane.

This is the branch to use when the teaching goal is:

**same symmetry trick, earlier in the chain, wider CFO range.**

### 2. Band-edge FLL is cleaner when the useful clue lives in the waveform, not the constellation

The band-edge FLL is not just “another coarse loop.”
It depends on a different piece of information:

- the pulse shape has excess bandwidth,
- the receiver still has an oversampled waveform view,
- and frequency error shows up as a left/right imbalance across the roll-off edges.

That makes it the cleaner object when:

- symbol decisions are not yet trustworthy,
- the pulse shape is part of the teaching object,
- and the receiver contract includes excess-bandwidth structure.

But it is a worse immediate continuation when the teaching goal is simply to explain why the symbol-rate QPSK note had a range boundary.

### 3. Known structure changes the problem, not just the implementation

The strongest practical lesson from the MathWorks and Wireless Pi sources is that pilot/correlation-based acquisition is not merely an implementation detail.
It uses different information and therefore deserves a separate branch in the conceptual map.

If the packet has a preamble, pilots, or a known correlation target, the clean answer is often:

- use known structure for coarse estimation,
- then hand the residual to timing and fine carrier tracking.

That is often better in practice than squeezing harder on a non-data-aided front end.

### 4. The three branches differ by what the receiver is allowed to know

This is the strongest comparison sentence from the whole pass:

| branch | what it exploits | when it is the clean fit | main limitation |
|---|---|---|---|
| oversampled M-th-power | PSK rotational symmetry | pilot-free PSK, want continuity with current note packet | still modulation-specific and still a power-law estimator |
| band-edge FLL | pulse-shape roll-off asymmetry | oversampled SRRC/RRC-like waveform, want waveform-domain coarse recovery | depends on excess bandwidth, filter design, and good normalization |
| preamble/correlation coarse estimation | known transmitted structure | framed packet systems allowed to spend known symbols | depends on packet format; no longer a blind estimator |

That table feels repo-ready.

## Hard repo decision

The next SDR sidecar should **not** try to give equal weight to all three branches.
That would turn a clean boundary note into an overstuffed mini-textbook.

The best next move, if SDR stays active, is:

## `oversampled fourth-power vs band-edge FLL: same problem, different assumptions`

with a narrow scope:

1. show that both belong **before** late-stage symbol-rate Costas tracking,
2. show that one uses **constellation symmetry** while the other uses **spectral band-edge asymmetry**,
3. keep the pilot/correlation branch as a decision box, not a full third simulation lane.

That keeps the note comparative without letting it sprawl.

## Concrete next experiments

1. **Replace the hold-model toy with a pulse-shaped waveform check**  
   Simulate SRRC-shaped QPSK at `4 sps`, then compare:
   - oversampled 4th-power CFO estimation, and
   - a simple band-edge discriminator output sign/slope.

2. **Sweep roll-off `\alpha`**  
   Use `\alpha \in {0.2, 0.35, 0.5}` to show something the current note packet does not yet show: band-edge logic gets its clue from excess bandwidth, while 4th-power symmetry removal does not depend on that clue in the same way.

3. **Sweep normalized CFO at fixed `sps`**  
   Keep `4 sps` fixed and compare where:
   - oversampled 4th-power stays honest,
   - band-edge discriminator stays monotone enough to be useful,
   - and late-stage symbol-rate recovery is already the wrong object.

4. **Do not add adjacent-channel interference yet**  
   Estévez makes it clear that filter design and adjacent-channel leakage matter, but that belongs to a later implementation-heavy pass, not the first comparison sidecar.

## Backlog decisions

- **Do continue SDR if the repo wants one last synchronization sidecar.**
- **Do not** widen the branch into AGC, equalization, or full burst synchronization.
- **Do not** give the pilot/correlation branch a full visual treatment unless packetized receivers become active again.
- **Do keep** the main comparison centered on assumptions, not on block-diagram tourism.

## Best next move

If SDR gets one more dense pass, build a bounded sidecar on:

**oversampled 4th-power vs band-edge FLL**

and make the note answer just one question:

**when is each front end the cleaner object before fine carrier tracking?**

If that note does not happen, the current packet is still already honest enough to stop.

Jarbas
