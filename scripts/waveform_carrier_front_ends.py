from __future__ import annotations

import cmath
import csv
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

QPSK_ANGLES = [math.pi / 4.0 + idx * math.pi / 2.0 for idx in range(4)]


@dataclass(frozen=True)
class FrontEndSweepRow:
    rolloff: float
    normalized_cfo: float
    fourth_power_estimate: float
    fourth_power_absolute_error: float
    band_edge_imbalance: float


def qpsk_symbols(count: int, seed: int = 0) -> list[complex]:
    rng = random.Random(seed)
    constellation = [cmath.exp(1j * angle) for angle in QPSK_ANGLES]
    return [rng.choice(constellation) for _ in range(count)]


def upsample(symbols: Iterable[complex], samples_per_symbol: int) -> list[complex]:
    out: list[complex] = []
    for symbol in symbols:
        out.append(symbol)
        out.extend([0j] * (samples_per_symbol - 1))
    return out


def convolve(samples: Iterable[complex], taps: Iterable[complex]) -> list[complex]:
    sample_list = list(samples)
    tap_list = list(taps)
    out = [0j] * (len(sample_list) + len(tap_list) - 1)
    for sample_idx, sample in enumerate(sample_list):
        if sample == 0:
            continue
        for tap_idx, tap in enumerate(tap_list):
            out[sample_idx + tap_idx] += sample * tap
    return out


def srrc_taps(rolloff: float, samples_per_symbol: int, span_symbols: int = 8) -> list[float]:
    if not (0.0 < rolloff <= 1.0):
        raise ValueError('rolloff must be in (0, 1]')
    taps: list[float] = []
    for n in range(-span_symbols * samples_per_symbol, span_symbols * samples_per_symbol + 1):
        t = n / samples_per_symbol
        if abs(t) < 1.0e-12:
            value = 1.0 + rolloff * (4.0 / math.pi - 1.0)
        elif abs(abs(4.0 * rolloff * t) - 1.0) < 1.0e-9:
            value = (rolloff / math.sqrt(2.0)) * (
                (1.0 + 2.0 / math.pi) * math.sin(math.pi / (4.0 * rolloff))
                + (1.0 - 2.0 / math.pi) * math.cos(math.pi / (4.0 * rolloff))
            )
        else:
            numerator = math.sin(math.pi * t * (1.0 - rolloff)) + 4.0 * rolloff * t * math.cos(math.pi * t * (1.0 + rolloff))
            denominator = math.pi * t * (1.0 - (4.0 * rolloff * t) ** 2)
            value = numerator / denominator
        taps.append(value)
    energy = math.sqrt(sum(value * value for value in taps))
    return [value / energy for value in taps]


def pulse_shaped_qpsk(rolloff: float, samples_per_symbol: int, *, symbol_count: int = 256, span_symbols: int = 8, seed: int = 0) -> list[complex]:
    symbols = qpsk_symbols(symbol_count, seed=seed)
    taps = srrc_taps(rolloff, samples_per_symbol, span_symbols=span_symbols)
    return convolve(upsample(symbols, samples_per_symbol), taps)


def apply_carrier_offset(samples: Iterable[complex], normalized_cfo: float, samples_per_symbol: int) -> list[complex]:
    phase_step = 2.0 * math.pi * normalized_cfo / samples_per_symbol
    return [sample * cmath.exp(1j * phase_step * idx) for idx, sample in enumerate(samples)]


def coarse_fourth_power_normalized_cfo(samples: Iterable[complex], samples_per_symbol: int) -> float:
    powered = [sample ** 4 for sample in samples]
    if len(powered) < 2:
        raise ValueError('need at least two samples')
    mean_step = sum(powered[idx] * powered[idx - 1].conjugate() for idx in range(1, len(powered))) / (len(powered) - 1)
    phase_step = cmath.phase(mean_step) / 4.0
    return phase_step * samples_per_symbol / (2.0 * math.pi)


def alias_limit_normalized(samples_per_symbol: int) -> float:
    return samples_per_symbol / 8.0


def lowpass_taps(cutoff_cycles_per_sample: float, tap_count: int = 63) -> list[float]:
    if cutoff_cycles_per_sample <= 0.0 or cutoff_cycles_per_sample >= 0.5:
        raise ValueError('cutoff must be inside (0, 0.5) cycles/sample')
    midpoint = (tap_count - 1) / 2.0
    taps: list[float] = []
    for tap_idx in range(tap_count):
        time_offset = tap_idx - midpoint
        if abs(time_offset) < 1.0e-12:
            ideal = 2.0 * cutoff_cycles_per_sample
        else:
            ideal = math.sin(2.0 * math.pi * cutoff_cycles_per_sample * time_offset) / (math.pi * time_offset)
        window = 0.54 - 0.46 * math.cos(2.0 * math.pi * tap_idx / (tap_count - 1))
        taps.append(ideal * window)
    return taps


def complex_bandpass_taps(center_cycles_per_sample: float, half_bandwidth_cycles_per_sample: float, tap_count: int = 63) -> list[complex]:
    prototype = lowpass_taps(half_bandwidth_cycles_per_sample, tap_count=tap_count)
    midpoint = (tap_count - 1) / 2.0
    return [
        value * cmath.exp(1j * 2.0 * math.pi * center_cycles_per_sample * (tap_idx - midpoint))
        for tap_idx, value in enumerate(prototype)
    ]


def band_edge_imbalance(samples: Iterable[complex], samples_per_symbol: int, rolloff: float, *, tap_count: int = 63, trim: int = 96) -> float:
    sample_list = list(samples)
    edge_center = (2.0 + rolloff) / (4.0 * samples_per_symbol)
    half_bandwidth = max(rolloff / (4.0 * samples_per_symbol), 1.0 / (64.0 * samples_per_symbol))
    upper = convolve(sample_list, complex_bandpass_taps(edge_center, half_bandwidth, tap_count=tap_count))
    lower = convolve(sample_list, complex_bandpass_taps(-edge_center, half_bandwidth, tap_count=tap_count))

    if len(upper) <= 2 * trim or len(lower) <= 2 * trim or len(sample_list) <= 2 * trim:
        raise ValueError('trim leaves no usable samples')

    upper_energy = sum(abs(value) ** 2 for value in upper[trim:-trim])
    lower_energy = sum(abs(value) ** 2 for value in lower[trim:-trim])
    total_energy = sum(abs(value) ** 2 for value in sample_list[trim:-trim])
    if total_energy == 0.0:
        return 0.0
    return (upper_energy - lower_energy) / total_energy


def sweep_front_ends(
    rolloffs: Iterable[float],
    normalized_cfo_values: Iterable[float],
    *,
    samples_per_symbol: int = 4,
    symbol_count: int = 256,
    span_symbols: int = 8,
    seed: int = 0,
) -> list[FrontEndSweepRow]:
    rows: list[FrontEndSweepRow] = []
    normalized_values = list(normalized_cfo_values)
    for rolloff_idx, rolloff in enumerate(rolloffs):
        base_waveform = pulse_shaped_qpsk(
            rolloff,
            samples_per_symbol,
            symbol_count=symbol_count,
            span_symbols=span_symbols,
            seed=seed + 100 * rolloff_idx,
        )
        for normalized_cfo in normalized_values:
            received = apply_carrier_offset(base_waveform, normalized_cfo, samples_per_symbol)
            fourth_estimate = coarse_fourth_power_normalized_cfo(received, samples_per_symbol)
            rows.append(
                FrontEndSweepRow(
                    rolloff=rolloff,
                    normalized_cfo=normalized_cfo,
                    fourth_power_estimate=fourth_estimate,
                    fourth_power_absolute_error=abs(fourth_estimate - normalized_cfo),
                    band_edge_imbalance=band_edge_imbalance(received, samples_per_symbol, rolloff),
                )
            )
    return rows


def write_csv(rows: Iterable[FrontEndSweepRow], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'rolloff',
                'normalized_cfo',
                'fourth_power_estimate',
                'fourth_power_absolute_error',
                'band_edge_imbalance',
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
