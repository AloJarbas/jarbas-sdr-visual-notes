# When the symbol-rate carrier-recovery story stops being enough

The previous note on the `\pi/4` alias cliff settled one bounded claim:

**for a timed, symbol-rate QPSK stream, a 4th-power coarse estimate is only honest inside a limited frequency window.**

What that note did **not** say is that carrier recovery in general stops there.
It said something narrower:

- the estimator sees **one sample per symbol**,
- its per-sample phase increment must stay inside `|\omega| < \pi/4`,
- so the corresponding CFO range in hertz is tied to the rate of the samples you fed it.

That last point is the whole bridge to the next front-end question.

![Large-CFO front-end boundary](../assets/2026-05-19-large-cfo-front-end-boundary.png)

## 1. The clean derivation

Wireless Pi gives the QPSK 4th-power phase-detection range as

`|\omega| < \pi/4`

where `\omega` is the per-sample phase increment.
If the observation sample rate is `F_s`, then

`\omega = 2\pi \Delta f / F_s`

so the honest coarse-frequency window is

`|\Delta f| < F_s / 8`.

If the receiver is looking at `L` samples per symbol and the symbol rate is `R_s`, then `F_s = L R_s`, so

`|\Delta f| < L R_s / 8`.

That is the missing sentence.
The earlier alias note was not a mysterious QPSK curse.
It was a statement about **which rate the estimator was seeing**.

## 2. The smallest local check

The repo now includes a compact toy sweep in

- `scripts/generate_large_cfo_front_end_figure.py`
- `assets/2026-05-19-large-cfo-front-end-boundary.csv`
- `notebooks/large_cfo_front_end_boundary.ipynb`

The model is deliberately small:

- timed QPSK symbols,
- a hold-model oversampled waveform,
- one shared physical CFO,
- the same 4th-power phase-difference estimator applied at `1`, `2`, and `4` samples per symbol.

That is enough to test the rate-scaling claim without pretending we have already modeled a full matched-filter front end.

One useful checkpoint is `\Delta f / R_s = 0.30`:

| observation rate | honest limit | estimated `\Delta f / R_s` | read |
|---|---:|---:|---|
| `1 sample/symbol` | `0.125` | about `0.05` | aliased |
| `2 samples/symbol` | `0.25` | about `-0.20` | already past the window |
| `4 samples/symbol` | `0.50` | about `0.30` | still honest |

So the same physical offset can look impossible in the symbol-rate view and perfectly reasonable in an earlier oversampled one.

## 3. What this changes in the receive story

The repo's carrier packet now reads more honestly:

1. timing recovery decides **when** symbol-rate sampling is trustworthy,
2. the existing symbol-rate alias note explains what the 4th-power estimate can do **once the receiver is already there**,
3. larger CFO is not solved by pretending that late-stage view has infinite range,
4. larger CFO belongs to an **earlier front end**.

That front end can take more than one shape.

## 4. The three branches worth naming

### A. Stay in the current symbol-rate lane

This is still the right story when the residual CFO is modest and the receiver is already operating at one sample per symbol.
That is the lane covered by:

- [Carrier recovery after timing](carrier-recovery-after-timing.md)
- [Carrier offset, pull-in, and the `\pi/4` alias cliff](carrier-offset-pull-in-and-alias.md)
- [QPSK phase ambiguity resolution](qpsk-phase-ambiguity-resolution.md)

### B. Move the coarse estimate earlier

If you still want a non-data-aided carrier front end, the clean continuation is not to overstate the 1 sps note.
It is to run the same basic idea **before decimation**.

That widens the absolute CFO window because the estimator now sees a higher sample rate.
In some receivers the same earlier stage can also use waveform-domain tools such as band-edge FLL logic, where pulse-shape asymmetry across the roll-off edges becomes the clue instead of symbol decisions.

### C. Use known structure when the packet format allows it

If the system has pilots, a preamble, or some other correlation target, then a pilot-aided coarse estimate is often the cleaner answer.
That does not contradict the non-data-aided story.
It just belongs to a different receiver contract.

## 5. What this note is, and what it is not

This is a scope-boundary card, not a full modem taxonomy.
It does three things only:

1. restates that the old alias note was a **symbol-rate** result,
2. shows that the honest CFO window scales with observation rate,
3. names the two main escape hatches once the CFO is too large for that late-stage view.

It does **not** try to cover AGC, frame sync, equalization, or every coarse-carrier architecture in one pass.
That would make the note larger and less honest at the same time.

## 6. Companion notebook and next questions

The companion notebook `notebooks/large_cfo_front_end_boundary.ipynb` slows down the derivation, reproduces the toy sweep, and leaves a few bounded problems:

- at what point does an oversampled 4th-power front end stop being the right next step and a waveform-domain FLL become the cleaner object?
- how much of this picture survives once pulse shaping and matched filtering replace the hold-model toy waveform?
- when does a pilot or preamble make the whole non-data-aided branch the wrong thing to optimize?

## 7. Source basis

Primary framing here came from:

- Wireless Pi on non-data-aided M-th-power carrier estimation for the detection-range statement,
- PySDR synchronization notes for the ordering of coarse carrier, timing, and fine tracking,
- the GNU Radio FLL band-edge material as a compact waveform-domain reference point,
- the practical receiver split shown in MathWorks' QPSK receiver example,
- local provenance in `notes/2026-05-18-large-cfo-front-end-research.md`.

## Scope boundary

This note stays QPSK-focused and deliberately small.
The point is not to claim a universal coarse-carrier recipe.
The point is to stop the symbol-rate story exactly where it stops being true.
