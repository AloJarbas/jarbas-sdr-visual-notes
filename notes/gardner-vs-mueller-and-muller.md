# Gardner vs Mueller and Muller

Both loops are trying to solve the same problem:
keep the receiver sampling near the best symbol instant.

But they do **not** read the same clue from the waveform.

![Gardner vs Mueller and Muller](../assets/2026-05-11-gardner-vs-mueller-muller.svg)

## 1. The shortest distinction

- **Gardner** watches the midpoint between symbol decisions.
- **Mueller and Muller (M&M)** compares adjacent symbol-spaced samples after the matched filter and a tentative decision step.

That is the clean mental split.

## 2. What Gardner is looking at

Gardner is built around a midpoint sample.
At about 2 samples per symbol, it can ask a useful question:

- is the half-symbol sample sitting where the zero crossing ought to be?

If that midpoint leans too far toward the previous symbol or the next one, the sign of the error tells the loop which direction to nudge the timing.

Why people like it:

- it does not need final symbol decisions yet,
- it fits naturally before a harder decision-directed stage,
- it matches the eye-diagram intuition well.

Main catch:

- it wants that midpoint view, so it is tied to having enough samples to see it.

## 3. What M&M is looking at

Mueller and Muller works later in the chain.
After matched filtering, it compares adjacent symbol-spaced samples and uses tentative symbol decisions to remove the data sign.

The intuition is:

- if timing is right, the neighboring pulse contributions should balance,
- if timing is off, that balance tilts,
- the tilt becomes the timing-error signal.

Why people like it:

- it can operate at 1 sample per symbol,
- it makes sense after the receiver is already close enough to start trusting decisions.

Main catch:

- if the tentative decisions are wrong too often, the timing cue gets contaminated.

## 4. A practical way to remember them

If you want the fast memory hook:

- **Gardner** reads the **midpoint**.
- **M&M** reads the **neighbor balance**.

Or more bluntly:

- Gardner asks whether the zero crossing is centered.
- M&M asks whether the adjacent symbol-spaced samples look symmetric once the symbol signs are stripped away.

## 5. Where this fits in the receive story

This repo now has a cleaner receive-side sequence:

1. pulse shaping and matched filtering make the waveform sample-worthy,
2. symbol timing says *when* to sample,
3. specific timing detectors differ in what waveform evidence they trust.

This note lives at step 3, but stays deliberately bounded.
It is an intuition layer, not a tuning guide.

## 6. Strongest caveat

This comparison is useful for choosing a mental model.
It is **not** enough by itself to tune a real loop or declare one detector universally better.
Pulse shape, rolloff, oversampling, SNR, and decision quality all change the tradeoff.

## Scope boundary

This note stays in the study and simulation lane. It does not include live-emission procedures.
