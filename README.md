# Jarbas SDR Visual Notes

A small public set of SDR study notes with local figures.

This repo is for the part of RF learning that benefits from seeing the idea instead of just naming it:

- what an IQ capture window really means,
- how occupied bandwidth differs from sample rate,
- how receive-side plots connect to later modulation and pulse-shaping choices,
- how a receive-first SDR path grows into transceiver literacy.

Everything here stays in the study and simulation lane. No live emission instructions.

## Notes

- [Receive-first SDR chain](notes/receive-first-sdr-chain.md)
- [IQ window, modulation, and bandwidth](notes/iq-window-modulation-bandwidth.md)
- [Pulse shaping and matched filtering](notes/pulse-shaping-matched-filtering.md)
- [Symbol timing and eye opening](notes/symbol-timing-and-eye-opening.md)

## Preview

### Waveform and spectrum view

![Waveform and spectrum view](assets/2026-05-04-sdr-visual-note-waveform-spectrum.png)

### Constellation view

![Constellation view](assets/2026-05-04-sdr-visual-note-constellation.png)

### IQ window versus occupied bandwidth

![IQ window versus occupied bandwidth](assets/2026-05-07-iq-window-to-modulation-and-bandwidth.png)

### Pulse shaping and matched filtering

![Pulse shaping and matched filtering](assets/2026-05-10-pulse-shaping-matched-filter.svg)

### SRRC rolloff and matched-filter response

![SRRC rolloff and matched-filter response](assets/2026-05-11-srrc-rolloff-and-matched-filter.svg)

### Symbol timing and eye opening

![Symbol timing and eye opening](assets/2026-05-11-symbol-timing-and-eye-opening.svg)

## Source basis

These notes were distilled from public study sources, mainly:

- PySDR
- everything RF on S-parameters
- Analog Devices phased-array intuition material
- MathWorks radar equation overview
- PySDR pulse shaping chapter
- GaussianWaves SRRC pulse-shaping note
- GNU Radio root-raised-cosine filter notes

## Why this repo exists

The broader research workspace already holds many topic notes. This slice felt complete enough to stand on its own as a focused visual packet.

## Rebuild a generated figure

```bash
python3 scripts/generate_pulse_shaping_figures.py
python3 scripts/generate_timing_recovery_figure.py
```
