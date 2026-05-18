# Carrier offset, pull-in, and the `\pi/4` alias cliff

The previous note explained **why** carrier recovery still matters after timing lock.
This follow-up answers a narrower question:

**how much carrier offset can the loop absorb by itself, when does coarse help become mandatory, and what breaks once the 4th-power estimate aliases?**

![Carrier offset, pull-in, and the alias cliff](../assets/2026-05-17-carrier-offset-pull-in-alias.png)

## 1. The shortest split

For this repo, the useful receive-side picture is not just “small offset” versus “large offset.”
It is three regimes:

1. **loop-alone region** — the residual offset is close enough to center that decision-directed tracking can finish the job by itself,
2. **coarse-help region** — the loop is no longer enough on its own, but a QPSK 4th-power coarse estimate can pull the residual into the right neighborhood first,
3. **alias region** — the same 4th-power estimate wraps to the wrong answer once the offset crosses the `\pi/4` boundary.

That third regime is the one most likely to fool you.
A constellation can still look tidy there while the decoded labels are wrong.

## 2. Why Costas-style tracking is only a near-center story

A Costas or other decision-directed loop is strongest once the residual phase and frequency error are already small enough that tentative symbol decisions are mostly right.
That is the “near-lock” region.

Near the center, the loop can clean up the leftover rotation directly.
Farther out, wrong quadrant decisions start polluting the error signal, so the loop is no longer telling a clean story about the true carrier offset.

That is why the practical receive chain splits into:

- **coarse acquisition** to remove the big common rotation first,
- **fine tracking** to keep the residual near zero afterward.

If you want the earlier bridge from timing lock into carrier recovery, go back to [Carrier recovery after timing](carrier-recovery-after-timing.md).
This note is the bounded follow-up about **offset size**.

## 3. What the 4th-power front end buys you

For QPSK, raising the symbol-rate samples to the 4th power removes the data symmetry and exposes the common carrier trend.
That widens the useful handoff region before the Costas loop takes over.

In the local `costas-loop-lab` evidence behind this note:

- at `+0.200 rad/sample`, phase-only tracking is already fine,
- at `+0.350 rad/sample`, phase-only tracking is clearly degraded while coarse-plus-tracking stays clean,
- at `+0.700 rad/sample`, coarse-plus-tracking is still behaving honestly.

So the right public takeaway is not “the loop works everywhere if tuned hard enough.”
It is simpler and truer:

- **the loop owns the center**,
- **the 4th-power front end widens the handoff band**,
- **but the widening has a hard scope boundary**.

## 4. The hard boundary is about `[-\pi/4, +\pi/4)`

The same QPSK symmetry that makes the 4th-power trick useful also limits it.
Because the phase detector is effectively working on `4\theta`, the honest unambiguous range is only

`[-\pi/4, +\pi/4)`

for this symbol-rate QPSK setup.

The local adversarial check in `notes/2026-05-17-carrier-offset-pull-in-research.md` makes the cliff visible instead of leaving it as a textbook footnote:

| offset (rad/sample) | phase-only tracked RMS | coarse+tracking RMS | coarse estimate | best constant-rotation symbol accuracy | read |
|---|---:|---:|---:|---:|---|
| `+0.200` | 0.057 | 0.057 | `+0.2002` | 1.000 | loop alone is already fine |
| `+0.350` | 0.278 | 0.057 | `+0.3493` | 1.000 | coarse help clearly matters |
| `+0.785` | 0.425 | 0.057 | `+0.7850` | 1.000 | right at the edge; still honest here |
| `+0.790` | 0.427 | 0.057 | `-0.7808` | 0.250 | alias just kicked in |
| `+0.850` | 0.427 | 0.057 | `-0.7215` | 0.250 | farther past the cliff |

Two things matter in that table:

- `+0.785` still behaves honestly,
- `+0.790` already wraps to the wrong coarse estimate.

That is the cliff.

## 5. Why the alias case is worse than “the loop looks noisy”

The ugly part is not just that the front end fails.
It is that the usual nearest-constellation geometry can still look excellent once the estimate aliases.

So beyond the boundary, a public note needs to separate three different ideas:

- **constellation geometry looks clean**,
- **carrier handoff metric looks calm**,
- **decoded labels are actually correct**.

Above the alias edge, those are no longer the same statement.

Short version:

**clean constellation geometry is not the same thing as correct payload recovery.**

That is the whole reason this topic is worth its own sidecar.

## 6. What this means for the receive story in this repo

The receive-side synchronization packet now reads more honestly:

1. timing recovery decides **when** to sample,
2. coarse carrier acquisition removes large common rotation **only within its honest range**,
3. fine tracking keeps the residual small **once the handoff is real**,
4. ambiguity resolution still handles the remaining QPSK label issue.

This note adds one missing caution to that chain:

- coarse acquisition helps a lot,
- but it does **not** make the front end unbounded.

## 7. Source basis

Primary framing used here:

- PySDR synchronization chapter for the receive-chain split,
- Wireless Pi on Costas loops for the near-lock / decision-directed viewpoint,
- Wireless Pi on non-data-aided M-th-power estimation for the `[-\pi/4, +\pi/4)` bound,
- local experiment evidence from [`costas-loop-lab`'s acquisition report](https://github.com/AloJarbas/costas-loop-lab/blob/main/reports/qpsk-frequency-acquisition.md) and [`costas-loop-lab`'s gain-tradeoff report](https://github.com/AloJarbas/costas-loop-lab/blob/main/reports/qpsk-loop-gain-tradeoffs.md).

Accepted versus rejected source triage for this note lives in:

- `notes/2026-05-17-carrier-offset-pull-in-research.md`

## Scope boundary

This note stays QPSK-only and symbol-rate only.
That is enough to make the three regimes visible without pretending to be a full PLL taxonomy.
