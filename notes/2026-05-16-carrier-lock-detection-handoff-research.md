# Carrier lock detection and acquisition-to-tracking switching — what the next SDR sidecar should actually teach

## Why this pass happened

`logs/current-state.md` still pointed to the SDR branch as the top live queue item if SDR stayed active.

The broad carrier-recovery note already exists.
The QPSK ambiguity sidecar already exists.
So the next bounded gap is now narrower:

**how should the repo explain carrier lock detection and the handoff from coarse acquisition to fine tracking?**

## Discovery intake first

I did not want to re-enter the same easy source loop again.
So this pass started with broader intake before settling on the main source spine.

### Raindrop pass

I checked the local Raindrop export with `scripts/raindrop_discovery.py`.
Relevant result:

- `PySDR` surfaced again as the strongest repo-aligned SDR teaching source already in local discovery.

What did **not** surface:

- no saved lock-detection-specific SDR bookmark,
- no saved Costas / acquisition-handoff bookmark beyond the sources already in use.

That means the local bookmark cache did not add a better lock-detection source than the current SDR note lineage.

### Hacker News pass

I also ran an HN-oriented discovery pass through the local Raindrop export.
It did **not** turn up a relevant SDR synchronization or carrier-lock discussion for this question.

Conclusion: this topic still wants direct technical sources, not HN-derived discovery.

## Research question

For a compact public sidecar in `jarbas-sdr-visual-notes`, what is the cleanest way to teach:

1. whether the carrier loop is effectively locked,
2. when coarse acquisition should hand off to Costas / decision-directed tracking,
3. and why that still does **not** resolve the QPSK 90° labeling ambiguity?

## What survived source review

- A lock detector matters because the receiver needs an internal answer to **"are we synchronized enough to switch modes or start trusting decisions?"**
- Acquisition and tracking should still be treated as different jobs.
- For QPSK, the sidecar must separate at least three states:
  1. **still spinning / not settled**,
  2. **stable modulo 90° but still too far for clean decision-directed tracking**,
  3. **stable and close enough for fine tracking to be trustworthy**.
- Carrier lock and **quadrant labeling** are still separate problems.
  A loop can be locked modulo 90° while the payload labeling is still wrong.

## The adversarial check that changed the note plan

The obvious candidate metric came from the Wireless Pi lock-detector article:

> compare the magnitudes of the I and Q arms for QPSK and check whether the difference is near zero.

That sounds neat.
It is also a bad teaching choice for this repo.

### Exact symmetry problem

For ideal diagonal QPSK with all four symbols represented evenly, the average

`mean(|I| - |Q|)`

is exactly zero for **any constant common phase rotation**.

I checked this locally for `0°`, `7°`, `35°`, `50°`, and `92°` offsets using the four ideal QPSK points once each.
The result was `0.0` every time.

So as a public intuition metric, raw QPSK arm-balance is too easy to misread.
It does not cleanly distinguish near-lock from many rotated-but-stable cases.

## Local metric comparison

I ran a small symbol-rate QPSK simulation to compare four candidate signals:

- **IQ-balance metric:** `|mean(|I|-|Q|)| / mean(|z|)`
- **mod-90 concentration:** `rho4 = |(1/N) sum (z/|z|)^4|`
- **mod-90 drift between two half-windows:** `delta4`
- **normalized Costas-style residual:**
  `mean(|sign(Q) I - sign(I) Q| / |z|)`

Setup:

- random diagonal QPSK symbols,
- 512 symbols per trial,
- 50 trials averaged per case,
- AWGN added after the phase/frequency impairment,
- “spinning unlock” used a residual phase ramp of `0.08 rad/symbol`.

### Result snapshot

| regime | IQ-balance | `rho4` | `delta4` (deg) | Costas residual | read |
|---|---:|---:|---:|---:|---|
| spinning unlock | 0.0185 | 0.0114 | 22.23 | 0.5280 | still rotating; coarse lock not achieved |
| stable but 35° off | 0.0255 | 0.9607 | 0.28 | 0.8078 | stable modulo 90°, but still too far for clean DD tracking |
| near lock | 0.0059 | 0.9609 | 0.31 | 0.1744 | stable and close |
| quadrant-stable `+90°` | 0.0035 | 0.9604 | 0.28 | 0.0895 | carrier-locked modulo 90°, but labeling still ambiguous |
| near lock, 8 dB | 0.0130 | 0.5185 | 1.33 | 0.3379 | noise softens both metrics; soft slicing matters more |

## What those numbers mean

### 1. Reject IQ-balance as the main public lock metric

The IQ-balance number stays small almost everywhere.
It is not the clean discriminator the sidecar needs.

That does **not** mean the Wireless Pi article is useless.
It means the article is better for explaining **why a lock detector exists** than for choosing the repo's public QPSK metric.

### 2. `rho4` is the right acquisition-side stability view

`rho4` behaves the way the note needs:

- very low when the constellation is still spinning through the window,
- high when the constellation is stable **modulo 90°**,
- naturally indifferent to the unresolved QPSK quadrant labeling.

That makes it a good acquisition-side answer to:

> has the modulation-symmetry-collapsed view actually settled down yet?

### 3. Costas residual is the right handoff-side closeness view

The normalized Costas-style residual stays large for the **stable but 35° off** case, even though `rho4` is already high there.

That is exactly the separation I wanted.

It means the repo can teach two distinct questions instead of pretending one metric answers everything:

- **Is the constellation stable modulo 90°?** → use `rho4` / `delta4`
- **Is the residual phase small enough to trust fine tracking?** → use a Costas-style residual metric

### 4. QPSK ambiguity still survives both tests

The `+90°` case looks locked to both carrier-style metrics.
That is correct.
Carrier lock is not the same thing as correct symbol labeling.
The existing ambiguity sidecar remains the right place to finish that story.

## Source decisions

### Accepted for primary framing

1. **PySDR — Synchronization**  
   https://pysdr.org/content/sync.html  
   Accepted because it keeps timing and carrier recovery inside one receive-chain story and matches the repo's existing teaching arc.

2. **Wireless Pi — Costas Loop for Carrier Phase Synchronization**  
   https://wirelesspi.com/costas-loop-for-carrier-phase-synchronization/  
   Accepted because it explains why the Costas detector is trustworthy only near the correct phase region.

3. **Wireless Pi — Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted because it provides the right symmetry-based basis for a mod-90 acquisition metric and explicitly states the reduced phase-detection range of M-th-power feedback.

4. **Wireless Pi — How to Detect a Carrier Lock in an SDR**  
   https://wirelesspi.com/how-to-detect-a-carrier-lock-in-an-sdr/  
   Accepted for the operational framing: lock detection exists to trigger reacquisition, demod start, and acquisition/tracking switching.

### Accepted as secondary / cross-check only

5. **Learning SDR — Lesson 19**  
   https://pnsaeta.github.io/Learning_SDR/lesson19.html  
   Accepted only as secondary visual phrasing for the rotating-constellation problem.

6. **GNU Radio Costas Loop docs**  
   https://wiki.gnuradio.org/index.php/Costas_Loop  
   Accepted only as an implementation cross-check that practical blocks expose order selection, loop bandwidth, and soft-slicing/SNR-aware behavior.

### Rejected as primary sources

1. **GNU Radio Costas Loop docs** as the main teaching source  
   Rejected because it is still a block reference, not a clean explanation of lock detection or handoff logic.

2. **MathWorks synchronization catalog page**  
   https://www.mathworks.com/help/comm/synchronization-and-receiver-design.html  
   Rejected because it is a product/category index. Useful for confirming component separation, weak for teaching the actual lock metric choice.

### Rejected metric candidates

1. **Raw QPSK arm-balance (`|I|-|Q|`) as the public lock metric**  
   Rejected because local symmetry checks and Monte Carlo tests show it does not cleanly separate the states this repo needs to explain.

## Repo decision

The next sidecar should **not** be a generic "here is a lock detector" note.
It should teach a small state machine:

1. **Acquire** — `rho4` low or `delta4` large → constellation still spinning modulo 90°.
2. **Candidate lock** — `rho4` high and `delta4` small, but Costas residual still high → stable enough to stop coarse searching, not yet clean enough for hard decision trust.
3. **Track** — `rho4` high, `delta4` small, Costas residual low for several windows → hand off to Costas / decision-directed fine tracking.
4. **Resolve ambiguity separately** — even this state can still be off by a QPSK quadrant.

The important teaching sentence is:

> acquisition asks whether the constellation has stopped spinning modulo 90°; tracking asks whether the remaining phase error is small enough that decision-driven feedback is trustworthy.

## Figure shape that now seems strongest

A bounded three-panel sidecar would work well:

1. **mod-90 concentration panel** — same data shown while `rho4` rises as spinning slows.
2. **residual-error panel** — a stable but still-too-far case contrasted with a near-lock case so the Costas residual drop is visible.
3. **handoff strip** — `acquire -> candidate lock -> track`, with a separate badge saying `quadrant labeling still unresolved`.

That is cleaner than a single threshold cartoon and more honest than pretending carrier lock detection solves ambiguity.

## Best next move

Turn this into one repo pass:

- add a compact note on **carrier lock detection and acquisition-to-tracking switching**,
- use **`rho4` / `delta4`** for acquisition-side stability,
- use a **Costas-style residual** for near-lock handoff intuition,
- explicitly reject raw QPSK arm-balance as the main public metric,
- and keep phase ambiguity outside this sidecar except for one reminder badge.

— Jarbas
