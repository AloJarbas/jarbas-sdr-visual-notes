from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import (
    alias_limit_normalized,
    band_edge_imbalance,
    coarse_fourth_power_normalized_cfo,
    pulse_shaped_qpsk,
    apply_carrier_offset,
    sweep_front_ends,
)


class WaveformCarrierFrontEndTests(unittest.TestCase):
    def test_fourth_power_alias_limit_at_four_sps_is_half_symbol_rate(self) -> None:
        self.assertAlmostEqual(alias_limit_normalized(4), 0.5)

    def test_oversampled_fourth_power_stays_honest_across_rolloff_sweep(self) -> None:
        rows = sweep_front_ends([0.05, 0.20, 0.50], [0.35], samples_per_symbol=4, symbol_count=256, span_symbols=8, seed=19)
        for row in rows:
            self.assertAlmostEqual(row.fourth_power_estimate, 0.35, delta=0.03)
            self.assertLess(row.fourth_power_absolute_error, 0.03)

    def test_band_edge_zero_crossing_stays_near_zero(self) -> None:
        for rolloff in (0.05, 0.20, 0.50):
            waveform = pulse_shaped_qpsk(rolloff, 4, symbol_count=256, span_symbols=8, seed=19)
            balance = band_edge_imbalance(waveform, 4, rolloff)
            self.assertAlmostEqual(balance, 0.0, delta=0.01)

    def test_band_edge_clue_grows_with_rolloff(self) -> None:
        low = pulse_shaped_qpsk(0.05, 4, symbol_count=256, span_symbols=8, seed=19)
        high = pulse_shaped_qpsk(0.50, 4, symbol_count=256, span_symbols=8, seed=19)

        low_balance = band_edge_imbalance(apply_carrier_offset(low, 0.10, 4), 4, 0.05)
        high_balance = band_edge_imbalance(apply_carrier_offset(high, 0.10, 4), 4, 0.50)

        self.assertGreater(abs(high_balance), abs(low_balance) * 8.0)
        self.assertGreater(high_balance, 0.0)

    def test_fourth_power_aliases_past_half_symbol_rate(self) -> None:
        waveform = pulse_shaped_qpsk(0.35, 4, symbol_count=256, span_symbols=8, seed=19)
        estimate = coarse_fourth_power_normalized_cfo(apply_carrier_offset(waveform, 0.60, 4), 4)
        self.assertAlmostEqual(estimate, -0.40, delta=0.03)


if __name__ == '__main__':
    unittest.main()
