from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import band_edge_closed_loop_row


class BandEdgeClosedLoopPullTests(unittest.TestCase):
    def test_desired_only_baseline_stays_near_zero(self) -> None:
        proxy = band_edge_closed_loop_row('proxy_bandpass', adjacent_enabled=False)
        half_sine = band_edge_closed_loop_row('gnuradio_half_sine', adjacent_enabled=False)

        self.assertLess(proxy.tail_mean_abs_residual_cfo, 0.005)
        self.assertLess(half_sine.tail_mean_abs_residual_cfo, 0.005)
        self.assertEqual(proxy.tail_within_threshold_fraction, 1.0)
        self.assertEqual(half_sine.tail_within_threshold_fraction, 1.0)

    def test_half_sine_pays_more_closed_loop_pull_at_zero_db(self) -> None:
        proxy = band_edge_closed_loop_row('proxy_bandpass', adjacent_enabled=True, adjacent_relative_power_db=0.0)
        half_sine = band_edge_closed_loop_row('gnuradio_half_sine', adjacent_enabled=True, adjacent_relative_power_db=0.0)

        self.assertGreater(half_sine.tail_mean_abs_residual_cfo, proxy.tail_mean_abs_residual_cfo + 0.04)
        self.assertGreaterEqual(proxy.tail_within_threshold_fraction, 0.875)
        self.assertLessEqual(half_sine.tail_within_threshold_fraction, 0.125)


if __name__ == '__main__':
    unittest.main()
