from __future__ import annotations

import cmath
import csv
import math
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

QPSK_ANGLES = [math.pi / 4.0 + k * math.pi / 2.0 for k in range(4)]


@dataclass(frozen=True)
class SweepRow:
    samples_per_symbol: int
    normalized_cfo: float
    estimated_normalized_cfo: float
    absolute_error: float
    honest: bool


def qpsk_symbols(count: int, seed: int = 0) -> list[complex]:
    rng = random.Random(seed)
    return [cmath.exp(1j * rng.choice(QPSK_ANGLES)) for _ in range(count)]


def oversampled_hold(symbols: Iterable[complex], samples_per_symbol: int) -> list[complex]:
    held: list[complex] = []
    for symbol in symbols:
        held.extend([symbol] * samples_per_symbol)
    return held


def apply_carrier_offset(
    samples: Iterable[complex],
    normalized_cfo: float,
    samples_per_symbol: int,
    *,
    noise_std: float = 0.0,
    seed: int = 0,
) -> list[complex]:
    rng = random.Random(seed)
    phase_step = 2.0 * math.pi * normalized_cfo / samples_per_symbol
    out: list[complex] = []
    for idx, sample in enumerate(samples):
        rotated = sample * cmath.exp(1j * phase_step * idx)
        if noise_std:
            rotated += complex(rng.gauss(0.0, noise_std), rng.gauss(0.0, noise_std))
        out.append(rotated)
    return out


def coarse_fourth_power_normalized_cfo(samples: Iterable[complex], samples_per_symbol: int) -> float:
    powered = [sample ** 4 for sample in samples]
    if len(powered) < 2:
        raise ValueError('need at least two samples')
    mean_step = sum(powered[idx] * powered[idx - 1].conjugate() for idx in range(1, len(powered))) / (len(powered) - 1)
    phase_step = cmath.phase(mean_step) / 4.0
    return phase_step * samples_per_symbol / (2.0 * math.pi)


def alias_limit_normalized(samples_per_symbol: int) -> float:
    return samples_per_symbol / 8.0


def sweep_normalized_cfo(
    samples_per_symbol_values: Iterable[int],
    normalized_cfo_values: Iterable[float],
    *,
    symbol_count: int = 160,
    noise_std: float = 0.01,
    seed: int = 0,
    honesty_tolerance: float = 0.03,
) -> list[SweepRow]:
    rows: list[SweepRow] = []
    base_symbols = qpsk_symbols(symbol_count, seed=seed)
    for samples_per_symbol in samples_per_symbol_values:
        baseband = oversampled_hold(base_symbols, samples_per_symbol)
        for idx, normalized_cfo in enumerate(normalized_cfo_values):
            received = apply_carrier_offset(
                baseband,
                normalized_cfo,
                samples_per_symbol,
                noise_std=noise_std,
                seed=seed + samples_per_symbol * 1000 + idx,
            )
            estimate = coarse_fourth_power_normalized_cfo(received, samples_per_symbol)
            absolute_error = abs(estimate - normalized_cfo)
            rows.append(
                SweepRow(
                    samples_per_symbol=samples_per_symbol,
                    normalized_cfo=normalized_cfo,
                    estimated_normalized_cfo=estimate,
                    absolute_error=absolute_error,
                    honest=absolute_error <= honesty_tolerance,
                )
            )
    return rows


def write_csv(rows: Iterable[SweepRow], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['samples_per_symbol', 'normalized_cfo', 'estimated_normalized_cfo', 'absolute_error', 'honest'],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
