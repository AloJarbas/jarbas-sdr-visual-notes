# Symbol timing and eye opening

Matched filtering fixes the pulse shape.
It does **not** guarantee that the receiver is sampling at the best instant.

That missing step is symbol timing recovery: keep the sampler near the center of the eye, where the current symbol is strongest and neighboring symbols cancel as much as possible.

![Symbol timing and eye opening](../assets/2026-05-11-symbol-timing-and-eye-opening.svg)

## 1. Why timing is still a problem after pulse shaping

Once Tx and Rx shaping are in place, the receiver has a much cleaner waveform to work with.
But the waveform still arrives with an arbitrary timing offset.

So the receiver is still faced with a question:

- which sample inside each symbol interval should count as the decision sample?

If that sample phase drifts too early or too late, the decision starts sliding onto the slopes instead of landing at the cleanest point.

## 2. The intuitive target

The right target is not “sample anywhere the waveform looks smooth.”
It is:

- sample where the eye is most open,
- where the current symbol dominates,
- and where neighboring-symbol interference is smallest.

That is the practical meaning of good symbol timing.

## 3. How to read the figure

The top panel shows one matched-filter output with three possible sampling phases:

- **early** — still on the correct pulse, but too far up the slope,
- **on-time** — near the decision peak,
- **late** — already sliding back down the other side.

The bottom panel turns the same idea into an eye-diagram view.
The best timing sits at the widest vertical opening.
Move left or right, and the margins shrink.

## 4. Why transitions matter

Timing-recovery loops learn the offset from how the signal behaves around transitions.
If the data stream never changes, the timing error signal gets weak or vanishes.

That is why timing recovery is not magic.
It depends on having enough waveform structure to tell early from late.

## 5. What the receiver is trying to do

A timing-recovery loop is not trying to “find symbols from scratch.”
It is usually doing something narrower and more practical:

- estimate the current sampling offset,
- nudge the sampling phase in the better direction,
- keep tracking slow drift so the sampler stays near the eye center.

That is the useful mental model before worrying about specific loops like Mueller and Muller or Gardner.

## 6. Connection to the earlier note

The pulse-shaping note explained why the waveform is smoothed and why the receiver also uses a matched filter.
This note adds the next missing idea:

- even with the right overall pulse shape,
- the receiver still has to choose *when* inside the symbol to sample.

That is where eye diagrams become more than a textbook picture.
They are a visual way to ask whether the receiver is sampling with margin or gambling on slope.

## Scope boundary

This note stays in the study and simulation lane. It does not include live-emission procedures.
