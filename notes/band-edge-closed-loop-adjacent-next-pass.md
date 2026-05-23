# Next pass prompt — band-edge closed-loop boundary after the first adjacent-channel loop test

The repo now has the first honest loop-level result:

- the GNU Radio / half-sine path is still the better isolated discriminator,
- but under the published bounded stress case it is not the more robust adjacent-channel loop.

Do not broaden that into a full modem benchmark.
The next useful pass is to sharpen the **boundary**, not the system diagram.

## Goal

Find the first clean point where the ranking changes by varying **one knob only**.

Choose exactly one:

1. **spacing sweep** at fixed loop gain, or
2. **loop-gain sweep** at fixed spacing.

Do not do both in the same first follow-up.

## Preferred first choice

Prefer the **spacing sweep** first.

Why:

- the current public artifact already fixed the loop gain,
- the previous guardband note already explained why spacing should matter,
- and one loop-level spacing boundary would say something sharper than another gain-tuning plot.

## Keep the scope narrow

If you take the spacing route:

- keep QPSK only,
- keep `4 samples/symbol`,
- keep `63` taps,
- keep the same blockwise loop,
- keep adjacent power fixed at `0 dB`,
- sweep a small spacing set such as `0.8`, `0.9`, `1.0`, `1.1`, `1.2`, `1.3 R_s`,
- compare proxy versus half-sine only.

If you take the gain route instead:

- keep spacing fixed at `1.0 R_s`,
- keep adjacent power fixed at `0 dB`,
- sweep only a few gains,
- and ask whether retuning can recover the half-sine lane without giving away the rest of the bounded setup.

## Deliverables

1. one public note
2. one generated figure
3. one CSV sidecar
4. one companion notebook
5. one small regression test at the representative crossover or boundary point

## Must-keep teaching point

The repo already knows the half-sine design is better in isolated slope and worse in adjacent pickup.
The next pass should answer only this:

**where does the loop-level preference actually flip under one controlled axis change?**

Not:

- BER,
- timing recovery,
- AGC,
- equalization,
- packet synchronization,
- or a giant adjacent-channel survey.

## Success sentence

If the follow-up is sharp enough, it should end with a sentence like one of these:

- "At 0 dB adjacent power, the half-sine lane stops being the worse loop once spacing reaches about `X R_s`."
- "At `1.0 R_s` spacing, gain retuning is not enough to recover the half-sine lane under the same bounded stress."

If it cannot say something that specific, tighten the pass again.

— Jarbas
