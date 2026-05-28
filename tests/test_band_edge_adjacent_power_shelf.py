from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import study_band_edge_adjacent_power_shelf


class BandEdgeAdjacentPowerShelfTests(unittest.TestCase):
    def test_weaker_adjacent_power_clears_settle_band_earlier(self) -> None:
        rows = study_band_edge_adjacent_power_shelf(
            [1.20, 1.24, 1.30],
            [3.0, 0.0, -3.0],
            loop_gain=0.020,
        )
        by_key = {(row.adjacent_relative_power_db, row.channel_spacing): row for row in rows}

        self.assertEqual(by_key[(3.0, 1.24)].half_sine_tail_within_threshold_fraction, 0.0)
        self.assertEqual(by_key[(0.0, 1.24)].half_sine_tail_within_threshold_fraction, 1.0)
        self.assertEqual(by_key[(-3.0, 1.20)].half_sine_tail_within_threshold_fraction, 1.0)
        self.assertEqual(by_key[(-3.0, 1.24)].half_sine_tail_within_threshold_fraction, 1.0)
        self.assertEqual(by_key[(-3.0, 1.30)].half_sine_tail_within_threshold_fraction, 1.0)

    def test_residual_ranking_survives_after_threshold_metric_recovers(self) -> None:
        rows = study_band_edge_adjacent_power_shelf(
            [1.20, 1.24, 1.30],
            [0.0, -3.0, -9.0],
            loop_gain=0.020,
        )
        by_key = {(row.adjacent_relative_power_db, row.channel_spacing): row for row in rows}

        relief = [by_key[(-3.0, spacing)] for spacing in (1.20, 1.24, 1.30)]
        weak = [by_key[(-9.0, spacing)] for spacing in (1.20, 1.24, 1.30)]

        self.assertTrue(all(row.half_sine_tail_within_threshold_fraction == 1.0 for row in relief))
        self.assertGreater(relief[0].residual_ratio_half_to_proxy, 8.0)
        self.assertGreater(relief[1].residual_ratio_half_to_proxy, relief[0].residual_ratio_half_to_proxy)
        self.assertGreater(relief[2].residual_ratio_half_to_proxy, relief[1].residual_ratio_half_to_proxy)

        self.assertTrue(all(row.absolute_gap_half_minus_proxy > 0.0 for row in weak))
        self.assertGreater(weak[1].residual_ratio_half_to_proxy, 8.0)
        self.assertLess(weak[0].absolute_gap_half_minus_proxy, by_key[(0.0, 1.20)].absolute_gap_half_minus_proxy)


if __name__ == '__main__':
    unittest.main()
