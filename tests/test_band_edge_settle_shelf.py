from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import study_band_edge_settle_shelf


class BandEdgeSettleShelfTests(unittest.TestCase):
    def test_low_gain_reopens_settle_band_but_ratio_rises_with_spacing(self) -> None:
        rows = study_band_edge_settle_shelf(
            [1.20, 1.24, 1.30],
            [0.002],
            adjacent_relative_power_db=0.0,
        )

        self.assertEqual([row.half_sine_tail_within_threshold_fraction for row in rows], [1.0, 1.0, 1.0])
        ratios = [row.residual_ratio_half_to_proxy for row in rows]
        self.assertLess(ratios[0], ratios[1])
        self.assertLess(ratios[1], ratios[2])
        self.assertGreater(ratios[0], 8.0)

    def test_baseline_gain_recovers_settle_before_residual_gap_closes(self) -> None:
        rows = study_band_edge_settle_shelf(
            [1.20, 1.22, 1.24, 1.30],
            [0.020],
            adjacent_relative_power_db=0.0,
        )

        proxy_fractions = [row.proxy_tail_within_threshold_fraction for row in rows]
        half_fractions = [row.half_sine_tail_within_threshold_fraction for row in rows]
        ratios = [row.residual_ratio_half_to_proxy for row in rows]

        self.assertEqual(proxy_fractions, [1.0, 1.0, 1.0, 1.0])
        self.assertEqual(half_fractions[:2], [0.0, 0.375])
        self.assertEqual(half_fractions[2:], [1.0, 1.0])
        self.assertGreater(ratios[2], 15.0)
        self.assertGreater(ratios[3], ratios[2])


if __name__ == '__main__':
    unittest.main()
