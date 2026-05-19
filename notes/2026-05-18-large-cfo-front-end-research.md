# Large-CFO front-end boundary after the symbol-rate alias note

## Why this pass happened

The `\pi/4` alias-sidecar is now done.
So the next SDR question is no longer whether the current QPSK symbol-rate story works.
It does.

The open boundary question is narrower:

**what should this repo say once the residual carrier offset is too large for the current 1-sample/symbol, 4th-power-before-Costas picture to be the right mental model?**

This needed a denser continuation pass because the wrong next move would be easy:
just bolt on one more Costas-loop paragraph and pretend the same symbol-rate story stretches forever.
It does not.

## Discovery intake first

### Raindrop pass

I ran local Raindrop discovery for `carrier frequency qpsk sync`.
Nothing stronger than the already-used SDR sources surfaced.

### Hacker News pass

I also checked the local HN bookmark slice for SDR synchronization keywords.
No useful candidate appeared for this bounded receive-chain question.

Conclusion: this pass still lives on the existing SDR source spine plus one practical receiver reference and one waveform-domain FLL branch.

## Research question

For one bounded continuation note in `jarbas-sdr-visual-notes`, what is the cleanest way to explain:

1. why the existing 4th-power symbol-rate note has a real scope boundary,
2. what changes when coarse carrier recovery happens **before** the 1-sample/symbol view,
3. and which larger-CFO branches are worth naming without turning the repo into a full modem survey?

## What survived source review

- The next public note should be a **scope-boundary sidecar**, not another generic carrier-recovery note.
- The key fact is not just that the 4th-power symbol-rate estimator aliases at `|\omega| < \pi/4` per sample.
  It is that the corresponding **absolute CFO range in Hz scales with the observation sample rate**.
- At 1 sample/symbol for QPSK, the honest unambiguous coarse-frequency window is about `|\Delta f| < R_s/8`.
- If the same M-th-power idea is applied **before** symbol-rate decimation, at `L` samples/symbol, the unambiguous absolute range becomes about `|\Delta f| < L R_s / 8`.
- That means the current note packet is not "wrong for large CFO".
  It is simply a **late-stage symbol-rate view**.
- The clean continuation is to compare three front-end branches:
  1. **oversampled non-data-aided coarse estimation** before decimation,
  2. **band-edge FLL / waveform-domain frequency recovery** when pulse shape and excess bandwidth are available,
  3. **preamble or correlation-based coarse estimation** when the system is frame-based and pilots are allowed.

## One derivation worth keeping

Wireless Pi gives the M-th-power phase-detection range as `[-\pi/M, +\pi/M)`.
For QPSK, `M = 4`, so the per-sample phase increment must satisfy

`|\omega| < \pi/4`.

With sample rate `F_s`, carrier offset and per-sample phase increment relate by

`\omega = 2\pi \Delta f / F_s`.

So the corresponding unambiguous frequency window is

`|\Delta f| < F_s / 8`.

If `F_s = L R_s`, then

`|\Delta f| < L R_s / 8`.

That is the clean bridge from the existing symbol-rate alias note to a larger-CFO front-end discussion.
The cliff is not mystical.
It is tied to **which rate the estimator sees**.

## Small comparison table

| observation rate | QPSK 4th-power honest window | read |
|---|---:|---|
| `1 sample/symbol` | `|\Delta f| < 0.125 R_s` | current repo note packet |
| `2 samples/symbol` | `|\Delta f| < 0.25 R_s` | still modest, but already twice the symbol-rate range |
| `4 samples/symbol` | `|\Delta f| < 0.5 R_s` | same idea, much wider absolute CFO window |
| `8 samples/symbol` | `|\Delta f| < 1.0 R_s` | shows why pre-decimation framing matters |

This table is probably the most compact repo-worthy sentence from the whole pass.

## Candidate branches and how they compare

### 1. Oversampled M-th-power coarse estimation

This is the closest continuation of the current repo story.
It keeps the same symmetry-removal intuition, but applies it before the receiver has collapsed the waveform to one sample per symbol.

Why it fits:
- it explains **why** the range widens without inventing a new receiver mythology,
- it preserves continuity with the current `\pi/4` alias note,
- it makes the scope boundary feel practical rather than arbitrary.

Limitation:
- once the note starts talking about oversampled matched-filter outputs, it has already stepped outside the current symbol-rate packet.

### 2. Band-edge FLL / waveform-domain recovery

This is a real alternative branch, but it is a different teaching object.
It estimates frequency error from the asymmetry between the two roll-off edges of a pulse-shaped signal.
That makes it naturally a **waveform-domain / pre-decision** front end.

Why it matters:
- it does not rely on symbol decisions being right,
- it belongs earlier than the Costas loop,
- it uses excess-bandwidth structure instead of constellation symmetry.

Limitation:
- it needs oversampling, pulse-shape assumptions, and a different visual setup.
- for this repo, it is better as a named branch or future sidecar than as the main immediate follow-up.

### 3. Preamble or correlation-based coarse estimation

This is the cleanest practical answer when the system is frame-based and allowed to spend known symbols.
MathWorks' QPSK receiver example uses exactly this kind of split:
coarse frequency compensation first, then timing recovery, then fine carrier synchronization.

Why it matters:
- it is often the best real-world answer when pilots exist,
- it makes the current non-data-aided symbol-rate packet feel honestly partial rather than universal,
- it gives the repo a clean way to say "if you can afford known structure, use it."

Limitation:
- it is not the same study lane as the current pilot-free QPSK symmetry notes.

## Source decisions

### Accepted for primary framing

1. **Wireless Pi: Non-Data-Aided Carrier Phase Estimation**  
   https://wirelesspi.com/non-data-aided-carrier-phase-estimation/  
   Accepted again as the main mathematical spine because the `[-\pi/M, +\pi/M)` detection-range statement is exactly what this boundary note needs.

2. **PySDR: Synchronization**  
   https://pysdr.org/content/sync.html  
   Accepted because it keeps the receiver chain honest about sample-rate reduction, timing recovery, and Costas placement in the pipeline.

3. **MathWorks: QPSK Transmitter and Receiver**  
   https://www.mathworks.com/help/comm/ug/qpsk-transmitter-and-receiver.html  
   Accepted because it gives a practical receiver-chain example that explicitly separates **coarse frequency compensation**, **timing recovery**, and **fine carrier synchronization**.

### Accepted as secondary / comparison framing

4. **GNU Radio Wiki: FLL Band-Edge**  
   https://wiki.gnuradio.org/index.php/FLL_Band-Edge  
   Accepted as the compact practical reminder that large-CFO front ends can live in the oversampled waveform domain and use pulse-shape band edges rather than symbol decisions.

5. **Daniel Estévez: About FLLs with band-edge filters**  
   https://destevez.net/2025/07/about-flls-with-band-edge-filters/  
   Accepted only as secondary cross-check because it explains the intuition well, but it is more implementation- and filter-design-heavy than the next public note should be.

6. **Local repo notes**  
   - `notes/carrier-recovery-after-timing.md`
   - `notes/carrier-offset-pull-in-and-alias.md`
   - `notes/receive-side-synchronization-map.md`
   Accepted because the new note needs to read as a continuation of the existing packet, not as a detached literature dump.

### Rejected as primary spines

1. **GNU Radio Costas Loop docs**  
   Rejected again because they are a block reference, not the right framing for a scope-boundary note.

2. **Another pure Costas-loop or pull-in source**  
   Rejected because the problem is no longer loop behavior near lock.
   The problem is what front-end family belongs **before** that late-stage view.

3. **OFDM CFO tutorials**  
   Rejected because they answer a different synchronization structure and would muddy the repo's single-carrier QPSK packet.

4. **A full PLL / control-theory survey**  
   Rejected because it would drag this note away from the receiver-pipeline intuition the repo actually needs.

## Repo decision

The best next SDR sidecar is now:

**when the symbol-rate carrier-recovery story stops being enough**

It should stay compact and do three things only:

1. restate that the current alias note is a **1-sample/symbol** receive-side story,
2. show that the 4th-power frequency window in Hz scales with the rate seen by the estimator,
3. name two honest escape hatches beyond that scope boundary:
   - oversampled waveform-domain recovery (including band-edge FLL style logic),
   - pilot/correlation-based coarse estimation.

## Figure shape that now seems strongest

One compact public figure should be enough:

1. **rate-versus-range strip**  
   same QPSK 4th-power idea shown at `1`, `2`, and `4` samples/symbol so the widening range is visible.

2. **pipeline fork panel**  
   one branch for the current symbol-rate story, one branch for oversampled waveform-domain coarse recovery, one branch for preamble/correlation-based coarse recovery.

3. **scope caption**  
   say plainly that Costas tracking is still the near-lock stage, but the receiver may need a different front end before that view is even usable.

## Concrete next experiments

1. Build a tiny oversampled toy simulation that keeps the same QPSK symbols but compares coarse 4th-power estimation at `1 sps` versus `4 sps` for the same physical CFO.
2. If that lands cleanly, add one small table or panel showing `R_s/8`, `R_s/4`, and `R_s/2` capture windows.
3. Do **not** turn the next note into AGC/equalization/frame-sync sprawl.
4. Only open a separate band-edge FLL visual if the repo explicitly wants a waveform-domain branch, because that note wants pulse-shape and rolloff visuals of its own.

## Best next move

Treat the current SDR packet as complete for the **symbol-rate** lane.
If SDR stays hot, the next move is a compact scope-boundary note that explains **why large-CFO recovery belongs earlier than the current symbol-rate Costas story**.

That would finish the packet more honestly than another generic synchronization note.

— Jarbas
