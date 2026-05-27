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
- [Gardner vs Mueller and Muller](notes/gardner-vs-mueller-and-muller.md)
- [Carrier recovery after timing](notes/carrier-recovery-after-timing.md)
- [Carrier lock detection and handoff](notes/carrier-lock-detection-and-handoff.md)
- [Carrier offset, pull-in, and the `\pi/4` alias cliff](notes/carrier-offset-pull-in-and-alias.md)
- [When the symbol-rate carrier-recovery story stops being enough](notes/when-symbol-rate-carrier-recovery-stops-being-enough.md)
- [Oversampled 4th-power versus band-edge FLL](notes/oversampled-fourth-power-vs-band-edge-fll.md)
- [Band-edge discriminant gain: raw imbalance versus near-lock slope](notes/band-edge-discriminant-gain-and-slope.md)
- [Band-edge filter shape and near-lock slope](notes/band-edge-filter-shape-and-slope.md)
- [Band-edge filter shape, guardband, and adjacent-channel cost](notes/band-edge-filter-shape-and-guardband.md)
- [Band-edge closed-loop pull with one adjacent interferer](notes/band-edge-closed-loop-adjacent-pull.md)
- [Band-edge spacing boundary: when the loop preference flips](notes/band-edge-spacing-boundary.md)
- [Band-edge loop-gain retuning: slower helps, but the ranking stays the same](notes/band-edge-loop-gain-retuning.md)
- [Band-edge settle shelf: track-ready returns before the residual gap closes](notes/band-edge-settle-shelf.md)
- [Receive-side synchronization map](notes/receive-side-synchronization-map.md)
- [QPSK phase ambiguity resolution](notes/qpsk-phase-ambiguity-resolution.md)

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

### Gardner vs Mueller and Muller

![Gardner vs Mueller and Muller](assets/2026-05-11-gardner-vs-mueller-muller.svg)

### Carrier recovery after timing

![Carrier recovery after timing](assets/2026-05-14-carrier-recovery-after-timing.svg)

### Carrier lock detection and handoff

![Carrier lock detection and handoff](assets/2026-05-16-carrier-lock-detection-and-handoff.png)

### Carrier offset, pull-in, and the `\pi/4` alias cliff

![Carrier offset, pull-in, and the `\pi/4` alias cliff](assets/2026-05-17-carrier-offset-pull-in-alias.png)

### When the symbol-rate carrier-recovery story stops being enough

![When the symbol-rate carrier-recovery story stops being enough](assets/2026-05-19-large-cfo-front-end-boundary.png)

### Oversampled 4th-power versus band-edge FLL

![Oversampled 4th-power versus band-edge FLL](assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.png)

### Band-edge discriminant gain: raw imbalance versus near-lock slope

![Band-edge discriminant gain: raw imbalance versus near-lock slope](assets/2026-05-20-band-edge-discriminant-slope-check.png)

### Band-edge filter shape and near-lock slope

![Band-edge filter shape and near-lock slope](assets/2026-05-22-band-edge-filter-design-comparison.png)

### Band-edge filter shape, guardband, and adjacent-channel cost

![Band-edge filter shape, guardband, and adjacent-channel cost](assets/2026-05-22-band-edge-guardband-cost-comparison.png)

### Band-edge closed-loop pull with one adjacent interferer

![Band-edge closed-loop pull with one adjacent interferer](assets/2026-05-23-band-edge-closed-loop-adjacent-pull.png)

### Band-edge spacing boundary: when the loop preference flips

![Band-edge spacing boundary: when the loop preference flips](assets/2026-05-24-band-edge-spacing-boundary.png)

### Band-edge loop-gain retuning: slower helps, but the ranking stays the same

![Band-edge loop-gain retuning: slower helps, but the ranking stays the same](assets/2026-05-24-band-edge-loop-gain-retuning.png)

### Band-edge settle shelf: track-ready returns before the residual gap closes

![Band-edge settle shelf: track-ready returns before the residual gap closes](assets/2026-05-27-band-edge-settle-shelf.png)

### Receive-side synchronization map

![Receive-side synchronization map](assets/2026-05-16-receive-side-synchronization-map.png)

### QPSK phase ambiguity resolution

![QPSK phase ambiguity resolution](assets/2026-05-15-qpsk-phase-ambiguity-resolution.png)

## Source basis

These notes were distilled from public study sources, mainly:

- PySDR
- everything RF on S-parameters
- Analog Devices phased-array intuition material
- MathWorks radar equation overview
- PySDR pulse shaping chapter
- GaussianWaves SRRC pulse-shaping note
- GNU Radio root-raised-cosine filter notes
- Wireless Pi synchronization notes
- Wireless Pi note on unique words and differential encoding for phase ambiguity resolution

## Why this repo exists

The broader research workspace already holds many topic notes. This slice felt complete enough to stand on its own as a focused visual packet.

## Rebuild a generated figure

```bash
python3 scripts/generate_pulse_shaping_figures.py
python3 scripts/generate_timing_recovery_figure.py
python3 scripts/generate_ted_comparison_figure.py
python3 scripts/generate_carrier_recovery_figure.py
python3 scripts/generate_carrier_lock_handoff_figure.py
python3 scripts/generate_carrier_offset_alias_figure.py
python3 scripts/generate_large_cfo_front_end_figure.py
python3 scripts/generate_waveform_carrier_front_end_figure.py
python3 scripts/generate_band_edge_discriminant_slope_figure.py
python3 scripts/generate_band_edge_filter_design_comparison_figure.py
python3 scripts/generate_band_edge_guardband_cost_figure.py
python3 scripts/generate_band_edge_closed_loop_adjacent_figure.py
python3 scripts/generate_band_edge_spacing_boundary_figure.py
python3 scripts/generate_band_edge_loop_gain_retuning_figure.py
python3 scripts/generate_band_edge_settle_shelf_figure.py
python3 scripts/generate_receive_side_sync_map_figure.py
python3 scripts/generate_qpsk_phase_ambiguity_figure.py
python3 scripts/check_svg_layout.py
```
