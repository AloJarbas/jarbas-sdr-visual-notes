# Carrier offset, pull-in, and the `\pi/4` alias cliff: source triage and repo plan

## Why this pass happened

The lock-detection / handoff sidecar is no longer the open gap.
That note now exists.

So the next bounded SDR question is the one already hinted at in `GITHUB_PORTFOLIO.md`:

**what should this repo teach about carrier-offset size, loop pull-in, and the point where the 4th-power front end stops being trustworthy?**

This needed a denser pass than just rereading the same Costas-loop explanations.
The repo already has a broad carrier-recovery note.
The missing thing is a compact intuition packet for **which offsets the loop can absorb, which ones need coarse help first, and what breaks at the alias boundary**.

## Discovery intake first

I checked the broader intake before settling back into the SDR source spine.

### Raindrop pass

I ran local discovery with `scripts/raindrop_discovery.py` for `costas` and `carrier`.
It returned no stronger bookmarked source than the SDR sources already in use.

### Hacker News pass

I also ran an HN-filtered discovery query for SDR-adjacent material.
It returned nothing relevant for this specific synchronization question.

Conclusion: for this pass, the useful material still comes from the existing SDR teaching sources plus local experiment evidence.

## Research question

For one bounded follow-up note in `jarbas-sdr-visual-notes`, what is the cleanest way to teach:

1. why a Costas loop alone is a **near-center** story rather than the whole carrier-offset story,
2. how a 4th-power coarse frequency estimate widens the usable handoff region,
3. and why the same front end silently lies once the residual offset crosses the `\pi/4` alias limit?

## What survived source review

- The repo should keep the teaching split between **coarse acquisition** and **fine tracking**.
- A bounded carrier-offset note is worth doing only if it shows **three different regimes**, not a vague "bigger offset is harder" slogan.
- The important bound for the existing symbol-rate QPSK front end is the **`[-\pi/4, +\pi/4)` capture range** of the 4th-power frequency estimate.
- The nastiest failure mode is not just "the loop looks noisy."
  It is worse: **the constellation can look geometrically clean while the decoded symbol stream is wrong** because the coarse estimate aliased.
- That means a public note should explicitly separate:
  - visual lock,
  - carrier handoff success,
  - and actual decoded-label correctness.

## Local adversarial check

The old acquisition-range report already showed the useful center story:

- phase-only coarse correction plus Costas tracking stays clean only near the center,
- frequency-plus-phase coarse acquisition widens the handoff region to about `\pm 0.75 rad/sample` in the current sweep.

That was helpful, but not adversarial enough.
It still stopped just short of the actual alias edge.

So this pass extended the local check with the existing `costas-loop-lab` code and asked a meaner question:

> what happens just below and just above `\pi/4`, and does the usual nearest-constellation RMS metric still tell the truth?

### Setup

- local package: `costas-loop-lab`
- 900 QPSK symbols
- fixed phase offset `0.85 rad`
- AWGN `noise_std = 0.04`
- Costas gains `alpha=0.11`, `beta=0.0045`
- coarse prefix `64`
- compared:
  - **phase-only coarse + Costas**
  - **4th-power frequency+phase coarse + Costas**
- added one extra check the current report did **not** use:
  - **best constant-quadrant-rotation symbol accuracy** against the known transmitted symbols after trimming startup

That last metric matters because plain geometric closeness to the nearest QPSK point can stay low even when the payload is already wrong.

### Result snapshot

| offset (rad/sample) | phase-only tracked RMS | freq-acquired tracked RMS | coarse freq estimate | best constant-rotation symbol accuracy | read |
|---|---:|---:|---:|---:|---|
| `+0.200` | 0.057 | 0.057 | `+0.2002` | 1.000 | easy center case; loop alone is already fine |
| `+0.350` | 0.278 | 0.057 | `+0.3493` | 1.000 | coarse front end clearly widens pull-in |
| `+0.700` | 0.426 | 0.057 | `+0.6995` | 1.000 | still inside the 4th-power window; handoff stays honest |
| `+0.785` | 0.425 | 0.057 | `+0.7850` | 1.000 | right at the `\pi/4` edge; still honest in this toy setup |
| `+0.790` | 0.427 | 0.057 | `-0.7808` | 0.250 | alias just kicked in; geometric cloud still looks clean, decoded stream is effectively random under any fixed quadrant relabeling |
| `+0.850` | 0.427 | 0.057 | `-0.7215` | 0.250 | same failure mode, farther past the cliff |

## What those numbers mean

### 1. The useful public split is really three regimes, not two

The note should not stop at "loop only" versus "loop plus coarse acquisition."
It wants **three** bands:

1. **center band:** the loop can finish the job by itself,
2. **handoff band:** the loop needs coarse frequency help first,
3. **alias band:** the 4th-power estimate folds to the wrong answer and a clean-looking cloud stops meaning correct decoding.

That third regime is the real reason this topic is worth a note.
Without it, the public story still sounds like folklore.

### 2. `\pi/4` is not just a theoretical footnote here

The existing `costas-loop-lab` README already says the 4th-power estimate wraps beyond roughly `|freq_offset| < \pi/4`.
This pass confirms that the boundary is visibly sharp in the current toy model:

- `0.785` behaves honestly,
- `0.790` already aliases.

That is a much better public teaching hook than vague lock-range language.

### 3. Nearest-constellation RMS is not enough above the alias edge

This was the main surprise worth keeping.

For `+0.790` and `+0.850`:

- the tracked RMS to the **nearest QPSK point** still looks excellent,
- but the **decoded stream** is no longer recoverable by any single global 90° relabeling.

So a clean constellation plot can lie.
That is the sentence the next note should earn.

### 4. This topic belongs in `jarbas-sdr-visual-notes`, not only in `costas-loop-lab`

`costas-loop-lab` already proves the acquisition-range effect numerically.
But `jarbas-sdr-visual-notes` is the right place to explain the intuition in one compact public note:

- when the loop is enough,
- when coarse help becomes mandatory,
- and why there is still a hard scope boundary.

## Source decisions

### Accepted for primary framing

1. **PySDR: Synchronization**  
   https://pysdr.org/content/sync.html  
   Accepted because it keeps timing and carrier correction inside one receive-chain story and supports the repo's existing teaching arc.

2. **Wireless Pi: Costas Loop for Carrier Phase Synchronization**  
   https://wirelesspi.com/costas-loop-for-carrier-phase-synchronization/  
   Accepted because it is still the clearest source here for why Costas-style feedback is a near-lock tool and why the error signal only behaves nicely near the correct region.

3. **Wireless Pi: Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted because it states the exact thing this note needs: M-th-power methods remove PSK data symmetry, but the phase-detection range is reduced to `[-\pi/M, +\pi/M)`.

### Accepted as secondary / cross-check only

4. **Wireless Pi: How to Detect a Carrier Lock in an SDR**  
   https://wirelesspi.com/how-to-detect-a-carrier-lock-in-an-sdr/  
   Accepted only as secondary framing because it reinforces acquisition-versus-tracking switching, but it is not the main source for the alias-bound story.

5. **Learning SDR: Lesson 19**  
   https://pnsaeta.github.io/Learning_SDR/lesson19.html  
   Accepted only as a light visual-intuition source for the rotating-constellation story.

6. **`costas-loop-lab/reports/qpsk-frequency-acquisition.md`**  
   Accepted as local experiment evidence because it already documents the widened pull-in region before the alias edge.

7. **`costas-loop-lab/reports/qpsk-loop-gain-tradeoffs.md`**  
   Accepted as local cross-check because it reinforces that loop tuning matters **after** the front end gets the residual into the right neighborhood.

### Accepted for terminology cross-check only

8. **arXiv:1511.04435, A Survey on Dynamic Analysis of the Costas Loop**  
   https://arxiv.org/abs/1511.04435  
   Accepted only for vocabulary (`lock-in`, `pull-in`, `hold-in`) and rejected as the main spine because it is much more control-theory heavy than this repo needs.

### Rejected as primary sources

1. **GNU Radio Costas Loop docs**  
   https://wiki.gnuradio.org/index.php/Costas_Loop  
   Rejected as the main teaching source because it is a block reference and parameter list, not a clear explanation of the three carrier-offset regimes.

2. **Learning SDR** as the main source  
   Rejected because it is too light for the alias-boundary and handoff story.

3. **arXiv Costas-loop survey** as the main source  
   Rejected because it would drag the note toward PLL taxonomy instead of the bounded receive-side intuition the repo actually needs.

### Rejected metric candidates

1. **Nearest-constellation RMS alone** as the public success metric  
   Rejected because it stays deceptively low beyond the `\pi/4` alias edge even while the decoded stream is wrong.

## Repo decision

The next SDR sidecar should be a bounded note on:

**carrier offset, pull-in, and the `\pi/4` alias cliff**

The note should teach a three-regime picture:

1. **loop-alone region:** small offsets where phase-only tracking already works,
2. **coarse-help region:** larger offsets where 4th-power acquisition makes the Costas handoff viable,
3. **alias region:** offsets past `\pi/4` where the 4th-power estimate wraps and a clean-looking constellation no longer guarantees correct symbols.

## Figure shape that now seems strongest

A compact three-panel note would work well:

1. **offset-axis regime strip**  
   show `loop alone -> coarse-help handoff -> alias cliff` on one axis.

2. **comparison panel**  
   one medium-offset case where phase-only fails but coarse+tracking succeeds.

3. **alias warning panel**  
   one just-over-the-edge case where the cloud looks tidy but the decoded labels are wrong, with a caption that says exactly that.

If the note needs a fourth visual, add a tiny callout table with `0.785` versus `0.790` to make the cliff feel real instead of theoretical.

## Best next move

Turn this into one repo-ready public follow-up:

- add a compact note on **carrier offset, pull-in, and the `\pi/4` alias cliff**,
- reuse the local `costas-loop-lab` evidence instead of inventing a fresh simulation mythology,
- explicitly say that **clean geometry is not the same thing as correct decoding** once the coarse estimate aliases,
- and keep the whole pass QPSK-only and symbol-rate only.

— Jarbas
