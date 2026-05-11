# Pulse shaping and matched filtering

If the receive-side FFT view is already clear, the next useful thing to make intuitive is this:

> digital symbols are not supposed to stay blocky all the way to the sampler.

The transmitter smooths them on purpose, and the receiver uses a matched filter so the right sample times still land on clean decisions.

![Pulse shaping and matched filtering](../assets/2026-05-10-pulse-shaping-matched-filter.svg)

![SRRC rolloff and matched-filter response](../assets/2026-05-11-srrc-rolloff-and-matched-filter.svg)

## 1. Why raw block pulses are a bad default

A rectangular symbol pulse is easy to imagine, but it sprays too much energy across frequency.

That is the core tradeoff:

- sharp edges in time
- broad spread in frequency

So practical digital systems shape the pulses before transmission.

## 2. Pulse shaping is allowed to overlap symbols

This is the part that feels wrong until it clicks.

A good pulse-shaping filter does **not** keep each symbol isolated in time. It lets neighboring pulses overlap, but it does so in a controlled way.

The condition that matters is not “no overlap ever.”
The condition that matters is:

- at the intended sampling instant,
- the current symbol contributes strongly,
- the neighboring symbols sum to zero.

That is the zero-ISI idea in the useful engineering sense.

## 3. Why the receiver also filters

The receiver wants a narrow-enough filter too:

- to reject nearby noise and interference,
- to recover timing more cleanly,
- to improve symbol decisions before slicing.

So the practical modern move is to split the shaping work between Tx and Rx.

That is where the matched-filter story becomes natural instead of mystical.

## 4. The common pulse pair to remember

A clean mnemonic is:

- transmitter: **root-raised-cosine** style shaping
- receiver: **matched root-raised-cosine** filter
- together: approximately a **raised-cosine** overall response

That keeps spectrum tighter while still preserving clean symbol sampling when timing is right.

## 5. The one parameter worth keeping in your head

The rolloff factor `beta` controls how much excess bandwidth you allow.

Small `beta` means:

- tighter spectrum,
- longer / sharper time-domain behavior,
- less room for timing slop.

Larger `beta` means:

- wider occupied bandwidth,
- gentler time-domain behavior,
- easier practical timing and implementation.

So once again, there is no free lunch.

## 6. One generated view worth keeping

The new generated figure adds one thing the conceptual sketch does not:

- you can see three SRRC pulse shapes at once,
- you can see how larger `beta` settles faster in time,
- you can see the matched Tx+Rx response peaking at the decision instant while neighboring symbol instants fall near zero.

Regenerate it with:

```bash
python3 scripts/generate_pulse_shaping_figures.py
```

## 7. How this connects back to SDR plots

This is the bridge back to the earlier notes:

- sample rate tells you the capture window,
- symbol rate and pulse shaping tell you the occupied bandwidth,
- matched filtering explains why the receiver does not just “look at the raw waveform and guess.”

That is the point where receive-side FFT literacy starts turning into actual communication-system judgment.

## Scope boundary

This note stays in the study and simulation lane. It does not include live-emission procedures.
