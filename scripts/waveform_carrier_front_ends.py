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


@dataclass(frozen=True)
class BandEdgeSlopeRow:
    samples_per_symbol: int
    symbol_count: int
    seed: int
    trim: int
    tap_count: int
    rolloff: float
    normalized_cfo_step: float
    imbalance_at_pos_step: float
    imbalance_at_neg_step: float
    central_slope_wrt_deltaf_over_Rs: float
    imbalance_at_0p10: float


@dataclass(frozen=True)
class BandEdgeDesignComparisonRow:
    design: str
    samples_per_symbol: int
    symbol_count: int
    seed: int
    trim: int
    tap_count: int
    rolloff: float
    normalized_cfo_step: float
    orientation_sign: float
    imbalance_at_pos_step: float
    imbalance_at_neg_step: float
    central_slope_wrt_deltaf_over_Rs: float
    imbalance_at_0p10: float


@dataclass(frozen=True)
class BandEdgeGuardbandCostRow:
    design: str
    samples_per_symbol: int
    symbol_count: int
    seed: int
    trim: int
    tap_count: int
    rolloff: float
    normalized_cfo_step: float
    reference_spacing: float
    capture_threshold: float
    central_slope_wrt_deltaf_over_Rs: float
    adjacent_capture_at_reference_spacing: float
    spacing_for_capture_below_threshold: float


@dataclass(frozen=True)
class BandEdgeClosedLoopRow:
    design: str
    samples_per_symbol: int
    symbol_count: int
    desired_seed: int
    adjacent_seed: int
    trim: int
    tap_count: int
    rolloff: float
    desired_normalized_cfo: float
    channel_spacing: float
    block_symbols: int
    loop_gain: float
    tail_block_count: int
    settle_threshold: float
    adjacent_enabled: bool
    adjacent_relative_power_db: float
    orientation_sign: float
    isolated_central_slope_wrt_deltaf_over_Rs: float
    final_residual_cfo: float
    tail_mean_abs_residual_cfo: float
    tail_peak_abs_residual_cfo: float
    tail_within_threshold_fraction: float
    tail_mean_abs_detector_output: float


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


def sinc(value: float) -> float:
    argument = math.pi * value
    return 1.0 if abs(value) < 1.0e-12 else math.sin(argument) / argument


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


def gnuradio_half_sine_band_edge_taps(samples_per_symbol: int, rolloff: float, tap_count: int = 63) -> tuple[list[complex], list[complex]]:
    if samples_per_symbol <= 0:
        raise ValueError('samples_per_symbol must be positive')
    if not (0.0 <= rolloff <= 1.0):
        raise ValueError('rolloff must be in [0, 1]')
    if tap_count <= 0:
        raise ValueError('tap_count must be positive')

    M = round(tap_count / samples_per_symbol)
    power = 0.0
    baseband_taps: list[float] = []
    half_sps_inv = 2.0 / samples_per_symbol
    for tap_idx in range(tap_count):
        k = -M + tap_idx * half_sps_inv
        position = rolloff * k
        tap = sinc(position - 0.5) + sinc(position + 0.5)
        power += tap * tap
        baseband_taps.append(tap)

    if power <= 0.0:
        raise ValueError('filter power must be positive')

    lower = [0j] * tap_count
    upper = [0j] * tap_count
    midpoint = (tap_count - 1) / 2.0
    inv_power = 1.0 / power
    inv_twice_sps = 0.5 / samples_per_symbol
    for tap_idx, tap in enumerate(baseband_taps):
        normalized_tap = tap * inv_power
        k = (tap_idx - midpoint) * inv_twice_sps
        index = tap_count - tap_idx - 1
        lower[index] = normalized_tap * cmath.exp(-1j * 2.0 * math.pi * (1.0 + rolloff) * k)
        upper[index] = lower[index].conjugate()
    return lower, upper


def proxy_band_edge_taps(samples_per_symbol: int, rolloff: float, tap_count: int = 63) -> tuple[list[complex], list[complex]]:
    edge_center = (2.0 + rolloff) / (4.0 * samples_per_symbol)
    half_bandwidth = max(rolloff / (4.0 * samples_per_symbol), 1.0 / (64.0 * samples_per_symbol))
    upper = complex_bandpass_taps(edge_center, half_bandwidth, tap_count=tap_count)
    lower = complex_bandpass_taps(-edge_center, half_bandwidth, tap_count=tap_count)
    return lower, upper


def band_edge_imbalance_from_filters(
    samples: Iterable[complex],
    lower_taps: Iterable[complex],
    upper_taps: Iterable[complex],
    *,
    trim: int = 96,
) -> float:
    sample_list = list(samples)
    lower = convolve(sample_list, lower_taps)
    upper = convolve(sample_list, upper_taps)

    if len(upper) <= 2 * trim or len(lower) <= 2 * trim or len(sample_list) <= 2 * trim:
        raise ValueError('trim leaves no usable samples')

    upper_energy = sum(abs(value) ** 2 for value in upper[trim:-trim])
    lower_energy = sum(abs(value) ** 2 for value in lower[trim:-trim])
    total_energy = sum(abs(value) ** 2 for value in sample_list[trim:-trim])
    if total_energy == 0.0:
        return 0.0
    return (lower_energy - upper_energy) / total_energy


def band_edge_capture_ratio_from_filters(
    samples: Iterable[complex],
    lower_taps: Iterable[complex],
    upper_taps: Iterable[complex],
    *,
    trim: int = 96,
) -> float:
    sample_list = list(samples)
    lower = convolve(sample_list, lower_taps)
    upper = convolve(sample_list, upper_taps)

    if len(upper) <= 2 * trim or len(lower) <= 2 * trim or len(sample_list) <= 2 * trim:
        raise ValueError('trim leaves no usable samples')

    total_energy = sum(abs(value) ** 2 for value in sample_list[trim:-trim])
    if total_energy == 0.0:
        return 0.0
    captured_energy = (
        sum(abs(value) ** 2 for value in upper[trim:-trim])
        + sum(abs(value) ** 2 for value in lower[trim:-trim])
    )
    return captured_energy / total_energy


def band_edge_imbalance(samples: Iterable[complex], samples_per_symbol: int, rolloff: float, *, tap_count: int = 63, trim: int = 96) -> float:
    lower_taps, upper_taps = proxy_band_edge_taps(samples_per_symbol, rolloff, tap_count=tap_count)
    return -band_edge_imbalance_from_filters(samples, lower_taps, upper_taps, trim=trim)


def normalize_average_power(samples: Iterable[complex]) -> list[complex]:
    sample_list = list(samples)
    if not sample_list:
        return []
    mean_power = sum(abs(sample) ** 2 for sample in sample_list) / len(sample_list)
    if mean_power <= 0.0:
        return sample_list
    scale = 1.0 / math.sqrt(mean_power)
    return [sample * scale for sample in sample_list]


def mix_desired_and_adjacent(
    desired: Iterable[complex],
    adjacent: Iterable[complex],
    *,
    adjacent_enabled: bool,
    adjacent_relative_power_db: float,
) -> list[complex]:
    desired_list = list(desired)
    if not adjacent_enabled:
        return desired_list
    adjacent_list = list(adjacent)
    if len(desired_list) != len(adjacent_list):
        raise ValueError('desired and adjacent waveforms must have the same length')
    amplitude_scale = 10.0 ** (adjacent_relative_power_db / 20.0)
    return normalize_average_power(
        desired_sample + amplitude_scale * adjacent_sample
        for desired_sample, adjacent_sample in zip(desired_list, adjacent_list)
    )


def band_edge_design_orientation_sign(
    base_waveform: Iterable[complex],
    lower_taps: Iterable[complex],
    upper_taps: Iterable[complex],
    *,
    samples_per_symbol: int,
    trim: int,
    normalized_cfo_step: float = 0.01,
) -> tuple[float, float]:
    base = list(base_waveform)
    positive = band_edge_imbalance_from_filters(
        apply_carrier_offset(base, normalized_cfo_step, samples_per_symbol),
        lower_taps,
        upper_taps,
        trim=trim,
    )
    negative = band_edge_imbalance_from_filters(
        apply_carrier_offset(base, -normalized_cfo_step, samples_per_symbol),
        lower_taps,
        upper_taps,
        trim=trim,
    )
    orientation_sign = 1.0 if positive >= negative else -1.0
    central_slope = orientation_sign * (positive - negative) / (2.0 * normalized_cfo_step)
    return orientation_sign, central_slope


def rotate_by_nco(
    samples: Iterable[complex],
    *,
    samples_per_symbol: int,
    normalized_frequency: float,
    initial_phase: float,
) -> list[complex]:
    sample_list = list(samples)
    phase_step = 2.0 * math.pi * normalized_frequency / samples_per_symbol
    return [sample * cmath.exp(-1j * (initial_phase + phase_step * idx)) for idx, sample in enumerate(sample_list)]


def update_nco_phase(
    phase: float,
    *,
    normalized_frequency: float,
    samples_per_symbol: int,
    sample_count: int,
) -> float:
    phase_step = 2.0 * math.pi * normalized_frequency / samples_per_symbol
    return math.remainder(phase + phase_step * sample_count, 2.0 * math.pi)


def band_edge_slope_row(
    rolloff: float,
    *,
    samples_per_symbol: int = 4,
    symbol_count: int = 1024,
    span_symbols: int = 8,
    seed: int = 19,
    trim: int = 160,
    tap_count: int = 127,
    normalized_cfo_step: float = 0.01,
    reference_cfo: float = 0.10,
) -> BandEdgeSlopeRow:
    base_waveform = normalize_average_power(
        pulse_shaped_qpsk(
            rolloff,
            samples_per_symbol,
            symbol_count=symbol_count,
            span_symbols=span_symbols,
            seed=seed,
        )
    )
    positive = band_edge_imbalance(
        apply_carrier_offset(base_waveform, normalized_cfo_step, samples_per_symbol),
        samples_per_symbol,
        rolloff,
        tap_count=tap_count,
        trim=trim,
    )
    negative = band_edge_imbalance(
        apply_carrier_offset(base_waveform, -normalized_cfo_step, samples_per_symbol),
        samples_per_symbol,
        rolloff,
        tap_count=tap_count,
        trim=trim,
    )
    finite_difference = (positive - negative) / (2.0 * normalized_cfo_step)
    reference_imbalance = band_edge_imbalance(
        apply_carrier_offset(base_waveform, reference_cfo, samples_per_symbol),
        samples_per_symbol,
        rolloff,
        tap_count=tap_count,
        trim=trim,
    )
    return BandEdgeSlopeRow(
        samples_per_symbol=samples_per_symbol,
        symbol_count=symbol_count,
        seed=seed,
        trim=trim,
        tap_count=tap_count,
        rolloff=rolloff,
        normalized_cfo_step=normalized_cfo_step,
        imbalance_at_pos_step=positive,
        imbalance_at_neg_step=negative,
        central_slope_wrt_deltaf_over_Rs=finite_difference,
        imbalance_at_0p10=reference_imbalance,
    )


def sweep_band_edge_slopes(
    rolloffs: Iterable[float],
    tap_counts: Iterable[int],
    *,
    samples_per_symbol: int = 4,
    symbol_count: int = 1024,
    span_symbols: int = 8,
    seed: int = 19,
    trim: int = 160,
    normalized_cfo_step: float = 0.01,
    reference_cfo: float = 0.10,
) -> list[BandEdgeSlopeRow]:
    rows: list[BandEdgeSlopeRow] = []
    normalized_rolloffs = list(rolloffs)
    normalized_taps = list(tap_counts)
    for rolloff in normalized_rolloffs:
        base_waveform = normalize_average_power(
            pulse_shaped_qpsk(
                rolloff,
                samples_per_symbol,
                symbol_count=symbol_count,
                span_symbols=span_symbols,
                seed=seed,
            )
        )
        for tap_count in normalized_taps:
            positive = band_edge_imbalance(
                apply_carrier_offset(base_waveform, normalized_cfo_step, samples_per_symbol),
                samples_per_symbol,
                rolloff,
                tap_count=tap_count,
                trim=trim,
            )
            negative = band_edge_imbalance(
                apply_carrier_offset(base_waveform, -normalized_cfo_step, samples_per_symbol),
                samples_per_symbol,
                rolloff,
                tap_count=tap_count,
                trim=trim,
            )
            rows.append(
                BandEdgeSlopeRow(
                    samples_per_symbol=samples_per_symbol,
                    symbol_count=symbol_count,
                    seed=seed,
                    trim=trim,
                    tap_count=tap_count,
                    rolloff=rolloff,
                    normalized_cfo_step=normalized_cfo_step,
                    imbalance_at_pos_step=positive,
                    imbalance_at_neg_step=negative,
                    central_slope_wrt_deltaf_over_Rs=(positive - negative) / (2.0 * normalized_cfo_step),
                    imbalance_at_0p10=band_edge_imbalance(
                        apply_carrier_offset(base_waveform, reference_cfo, samples_per_symbol),
                        samples_per_symbol,
                        rolloff,
                        tap_count=tap_count,
                        trim=trim,
                    ),
                )
            )
    return rows


def sweep_band_edge_design_comparison(
    rolloffs: Iterable[float],
    tap_counts: Iterable[int],
    *,
    samples_per_symbol: int = 4,
    symbol_count: int = 1024,
    span_symbols: int = 8,
    seed: int = 19,
    trim: int = 160,
    normalized_cfo_step: float = 0.01,
    reference_cfo: float = 0.10,
) -> list[BandEdgeDesignComparisonRow]:
    rows: list[BandEdgeDesignComparisonRow] = []
    normalized_rolloffs = list(rolloffs)
    normalized_taps = list(tap_counts)
    design_builders: dict[str, callable] = {
        'proxy_bandpass': proxy_band_edge_taps,
        'gnuradio_half_sine': gnuradio_half_sine_band_edge_taps,
    }

    for rolloff in normalized_rolloffs:
        base_waveform = normalize_average_power(
            pulse_shaped_qpsk(
                rolloff,
                samples_per_symbol,
                symbol_count=symbol_count,
                span_symbols=span_symbols,
                seed=seed,
            )
        )
        positive_waveform = apply_carrier_offset(base_waveform, normalized_cfo_step, samples_per_symbol)
        negative_waveform = apply_carrier_offset(base_waveform, -normalized_cfo_step, samples_per_symbol)
        reference_waveform = apply_carrier_offset(base_waveform, reference_cfo, samples_per_symbol)
        for tap_count in normalized_taps:
            for design, builder in design_builders.items():
                lower_taps, upper_taps = builder(samples_per_symbol, rolloff, tap_count=tap_count)
                positive = band_edge_imbalance_from_filters(positive_waveform, lower_taps, upper_taps, trim=trim)
                negative = band_edge_imbalance_from_filters(negative_waveform, lower_taps, upper_taps, trim=trim)
                orientation_sign = 1.0 if positive >= negative else -1.0
                oriented_positive = orientation_sign * positive
                oriented_negative = orientation_sign * negative
                oriented_reference = orientation_sign * band_edge_imbalance_from_filters(
                    reference_waveform,
                    lower_taps,
                    upper_taps,
                    trim=trim,
                )
                rows.append(
                    BandEdgeDesignComparisonRow(
                        design=design,
                        samples_per_symbol=samples_per_symbol,
                        symbol_count=symbol_count,
                        seed=seed,
                        trim=trim,
                        tap_count=tap_count,
                        rolloff=rolloff,
                        normalized_cfo_step=normalized_cfo_step,
                        orientation_sign=orientation_sign,
                        imbalance_at_pos_step=oriented_positive,
                        imbalance_at_neg_step=oriented_negative,
                        central_slope_wrt_deltaf_over_Rs=(oriented_positive - oriented_negative) / (2.0 * normalized_cfo_step),
                        imbalance_at_0p10=oriented_reference,
                    )
                )
    return rows


def sweep_band_edge_guardband_cost_comparison(
    rolloffs: Iterable[float],
    tap_counts: Iterable[int],
    *,
    channel_spacings: Iterable[float],
    capture_threshold: float = 0.05,
    reference_spacing: float = 1.0,
    samples_per_symbol: int = 4,
    symbol_count: int = 1024,
    span_symbols: int = 8,
    seed: int = 19,
    trim: int = 160,
    normalized_cfo_step: float = 0.01,
) -> list[BandEdgeGuardbandCostRow]:
    rows: list[BandEdgeGuardbandCostRow] = []
    normalized_rolloffs = list(rolloffs)
    normalized_taps = list(tap_counts)
    spacing_values = sorted(set(channel_spacings))
    if reference_spacing not in spacing_values:
        spacing_values.append(reference_spacing)
        spacing_values.sort()

    design_builders: dict[str, callable] = {
        'proxy_bandpass': proxy_band_edge_taps,
        'gnuradio_half_sine': gnuradio_half_sine_band_edge_taps,
    }

    for rolloff in normalized_rolloffs:
        base_waveform = normalize_average_power(
            pulse_shaped_qpsk(
                rolloff,
                samples_per_symbol,
                symbol_count=symbol_count,
                span_symbols=span_symbols,
                seed=seed,
            )
        )
        positive_waveform = apply_carrier_offset(base_waveform, normalized_cfo_step, samples_per_symbol)
        negative_waveform = apply_carrier_offset(base_waveform, -normalized_cfo_step, samples_per_symbol)
        shifted_waveforms = {
            spacing: apply_carrier_offset(base_waveform, spacing, samples_per_symbol)
            for spacing in spacing_values
        }
        for tap_count in normalized_taps:
            for design, builder in design_builders.items():
                lower_taps, upper_taps = builder(samples_per_symbol, rolloff, tap_count=tap_count)
                positive = band_edge_imbalance_from_filters(positive_waveform, lower_taps, upper_taps, trim=trim)
                negative = band_edge_imbalance_from_filters(negative_waveform, lower_taps, upper_taps, trim=trim)
                orientation_sign = 1.0 if positive >= negative else -1.0
                oriented_positive = orientation_sign * positive
                oriented_negative = orientation_sign * negative
                captures = {
                    spacing: band_edge_capture_ratio_from_filters(shifted_waveforms[spacing], lower_taps, upper_taps, trim=trim)
                    for spacing in spacing_values
                }
                spacing_for_threshold = next(
                    (spacing for spacing in spacing_values if captures[spacing] <= capture_threshold),
                    spacing_values[-1],
                )
                rows.append(
                    BandEdgeGuardbandCostRow(
                        design=design,
                        samples_per_symbol=samples_per_symbol,
                        symbol_count=symbol_count,
                        seed=seed,
                        trim=trim,
                        tap_count=tap_count,
                        rolloff=rolloff,
                        normalized_cfo_step=normalized_cfo_step,
                        reference_spacing=reference_spacing,
                        capture_threshold=capture_threshold,
                        central_slope_wrt_deltaf_over_Rs=(oriented_positive - oriented_negative) / (2.0 * normalized_cfo_step),
                        adjacent_capture_at_reference_spacing=captures[reference_spacing],
                        spacing_for_capture_below_threshold=spacing_for_threshold,
                    )
                )
    return rows


def band_edge_closed_loop_row(
    design: str,
    *,
    adjacent_enabled: bool,
    adjacent_relative_power_db: float = 0.0,
    samples_per_symbol: int = 4,
    symbol_count: int = 3072,
    span_symbols: int = 8,
    desired_seed: int = 19,
    adjacent_seed: int = 173,
    trim: int = 96,
    tap_count: int = 63,
    rolloff: float = 0.35,
    desired_normalized_cfo: float = 0.0,
    channel_spacing: float = 1.0,
    block_symbols: int = 96,
    loop_gain: float = 0.02,
    tail_block_count: int = 8,
    settle_threshold: float = 0.05,
) -> BandEdgeClosedLoopRow:
    if design == 'proxy_bandpass':
        builder = proxy_band_edge_taps
    elif design == 'gnuradio_half_sine':
        builder = gnuradio_half_sine_band_edge_taps
    else:
        raise ValueError(f'unknown design: {design}')

    if block_symbols <= 0:
        raise ValueError('block_symbols must be positive')
    block_length = block_symbols * samples_per_symbol
    if block_length <= 2 * trim:
        raise ValueError('block length must exceed 2 * trim')

    desired = normalize_average_power(
        apply_carrier_offset(
            pulse_shaped_qpsk(
                rolloff,
                samples_per_symbol,
                symbol_count=symbol_count,
                span_symbols=span_symbols,
                seed=desired_seed,
            ),
            desired_normalized_cfo,
            samples_per_symbol,
        )
    )
    adjacent = normalize_average_power(
        apply_carrier_offset(
            pulse_shaped_qpsk(
                rolloff,
                samples_per_symbol,
                symbol_count=symbol_count,
                span_symbols=span_symbols,
                seed=adjacent_seed,
            ),
            desired_normalized_cfo + channel_spacing,
            samples_per_symbol,
        )
    )
    mixed = mix_desired_and_adjacent(
        desired,
        adjacent,
        adjacent_enabled=adjacent_enabled,
        adjacent_relative_power_db=adjacent_relative_power_db,
    )

    lower_taps, upper_taps = builder(samples_per_symbol, rolloff, tap_count=tap_count)
    orientation_sign, isolated_central_slope = band_edge_design_orientation_sign(
        normalize_average_power(
            pulse_shaped_qpsk(
                rolloff,
                samples_per_symbol,
                symbol_count=symbol_count,
                span_symbols=span_symbols,
                seed=desired_seed,
            )
        ),
        lower_taps,
        upper_taps,
        samples_per_symbol=samples_per_symbol,
        trim=trim,
    )

    residual_history: list[float] = []
    detector_history: list[float] = []
    frequency_estimate = 0.0
    phase_estimate = 0.0

    for start in range(0, len(mixed) - block_length + 1, block_length):
        block = mixed[start:start + block_length]
        corrected = rotate_by_nco(
            block,
            samples_per_symbol=samples_per_symbol,
            normalized_frequency=frequency_estimate,
            initial_phase=phase_estimate,
        )
        detector_output = orientation_sign * band_edge_imbalance_from_filters(
            corrected,
            lower_taps,
            upper_taps,
            trim=trim,
        )
        frequency_estimate += loop_gain * detector_output
        phase_estimate = update_nco_phase(
            phase_estimate,
            normalized_frequency=frequency_estimate,
            samples_per_symbol=samples_per_symbol,
            sample_count=block_length,
        )
        residual_history.append(frequency_estimate - desired_normalized_cfo)
        detector_history.append(detector_output)

    if len(residual_history) < tail_block_count:
        raise ValueError('not enough closed-loop blocks for the requested tail summary')

    residual_tail = residual_history[-tail_block_count:]
    detector_tail = detector_history[-tail_block_count:]

    return BandEdgeClosedLoopRow(
        design=design,
        samples_per_symbol=samples_per_symbol,
        symbol_count=symbol_count,
        desired_seed=desired_seed,
        adjacent_seed=adjacent_seed,
        trim=trim,
        tap_count=tap_count,
        rolloff=rolloff,
        desired_normalized_cfo=desired_normalized_cfo,
        channel_spacing=channel_spacing,
        block_symbols=block_symbols,
        loop_gain=loop_gain,
        tail_block_count=tail_block_count,
        settle_threshold=settle_threshold,
        adjacent_enabled=adjacent_enabled,
        adjacent_relative_power_db=adjacent_relative_power_db,
        orientation_sign=orientation_sign,
        isolated_central_slope_wrt_deltaf_over_Rs=isolated_central_slope,
        final_residual_cfo=residual_history[-1],
        tail_mean_abs_residual_cfo=sum(abs(value) for value in residual_tail) / tail_block_count,
        tail_peak_abs_residual_cfo=max(abs(value) for value in residual_tail),
        tail_within_threshold_fraction=sum(1 for value in residual_tail if abs(value) <= settle_threshold) / tail_block_count,
        tail_mean_abs_detector_output=sum(abs(value) for value in detector_tail) / tail_block_count,
    )


def study_band_edge_closed_loop_adjacent_pull(
    adjacent_relative_power_db_values: Iterable[float],
    *,
    include_desired_only: bool = True,
    samples_per_symbol: int = 4,
    symbol_count: int = 3072,
    span_symbols: int = 8,
    desired_seed: int = 19,
    adjacent_seed: int = 173,
    trim: int = 96,
    tap_count: int = 63,
    rolloff: float = 0.35,
    desired_normalized_cfo: float = 0.0,
    channel_spacing: float = 1.0,
    block_symbols: int = 96,
    loop_gain: float = 0.02,
    tail_block_count: int = 8,
    settle_threshold: float = 0.05,
) -> list[BandEdgeClosedLoopRow]:
    rows: list[BandEdgeClosedLoopRow] = []
    designs = ['proxy_bandpass', 'gnuradio_half_sine']
    for design in designs:
        if include_desired_only:
            rows.append(
                band_edge_closed_loop_row(
                    design,
                    adjacent_enabled=False,
                    adjacent_relative_power_db=0.0,
                    samples_per_symbol=samples_per_symbol,
                    symbol_count=symbol_count,
                    span_symbols=span_symbols,
                    desired_seed=desired_seed,
                    adjacent_seed=adjacent_seed,
                    trim=trim,
                    tap_count=tap_count,
                    rolloff=rolloff,
                    desired_normalized_cfo=desired_normalized_cfo,
                    channel_spacing=channel_spacing,
                    block_symbols=block_symbols,
                    loop_gain=loop_gain,
                    tail_block_count=tail_block_count,
                    settle_threshold=settle_threshold,
                )
            )
        for adjacent_relative_power_db in adjacent_relative_power_db_values:
            rows.append(
                band_edge_closed_loop_row(
                    design,
                    adjacent_enabled=True,
                    adjacent_relative_power_db=adjacent_relative_power_db,
                    samples_per_symbol=samples_per_symbol,
                    symbol_count=symbol_count,
                    span_symbols=span_symbols,
                    desired_seed=desired_seed,
                    adjacent_seed=adjacent_seed,
                    trim=trim,
                    tap_count=tap_count,
                    rolloff=rolloff,
                    desired_normalized_cfo=desired_normalized_cfo,
                    channel_spacing=channel_spacing,
                    block_symbols=block_symbols,
                    loop_gain=loop_gain,
                    tail_block_count=tail_block_count,
                    settle_threshold=settle_threshold,
                )
            )
    return rows


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


def write_band_edge_slope_csv(rows: Iterable[BandEdgeSlopeRow], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'samples_per_symbol',
                'symbol_count',
                'seed',
                'trim',
                'tap_count',
                'rolloff',
                'normalized_cfo_step',
                'imbalance_at_pos_step',
                'imbalance_at_neg_step',
                'central_slope_wrt_deltaf_over_Rs',
                'imbalance_at_0p10',
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_band_edge_design_comparison_csv(rows: Iterable[BandEdgeDesignComparisonRow], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'design',
                'samples_per_symbol',
                'symbol_count',
                'seed',
                'trim',
                'tap_count',
                'rolloff',
                'normalized_cfo_step',
                'orientation_sign',
                'imbalance_at_pos_step',
                'imbalance_at_neg_step',
                'central_slope_wrt_deltaf_over_Rs',
                'imbalance_at_0p10',
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_band_edge_guardband_cost_csv(rows: Iterable[BandEdgeGuardbandCostRow], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'design',
                'samples_per_symbol',
                'symbol_count',
                'seed',
                'trim',
                'tap_count',
                'rolloff',
                'normalized_cfo_step',
                'reference_spacing',
                'capture_threshold',
                'central_slope_wrt_deltaf_over_Rs',
                'adjacent_capture_at_reference_spacing',
                'spacing_for_capture_below_threshold',
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_band_edge_closed_loop_csv(rows: Iterable[BandEdgeClosedLoopRow], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'design',
                'samples_per_symbol',
                'symbol_count',
                'desired_seed',
                'adjacent_seed',
                'trim',
                'tap_count',
                'rolloff',
                'desired_normalized_cfo',
                'channel_spacing',
                'block_symbols',
                'loop_gain',
                'tail_block_count',
                'settle_threshold',
                'adjacent_enabled',
                'adjacent_relative_power_db',
                'orientation_sign',
                'isolated_central_slope_wrt_deltaf_over_Rs',
                'final_residual_cfo',
                'tail_mean_abs_residual_cfo',
                'tail_peak_abs_residual_cfo',
                'tail_within_threshold_fraction',
                'tail_mean_abs_detector_output',
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
