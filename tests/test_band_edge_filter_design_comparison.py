from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import sweep_band_edge_design_comparison


class BandEdgeFilterDesignComparisonTests(unittest.TestCase):
    @staticmethod
    def lookup() -> dict[tuple[str, int, float], float]:
        rows = sweep_band_edge_design_comparison([0.05, 0.20, 0.35, 0.50], [63, 127, 255])
        return {
            (row.design, row.tap_count, row.rolloff): row.central_slope_wrt_deltaf_over_Rs
            for row in rows
        }

    def test_half_sine_design_hits_unity_faster_than_proxy(self) -> None:
        slopes = self.lookup()
        self.assertLess(slopes[('proxy_bandpass', 63, 0.35)], 0.75)
        self.assertGreater(slopes[('gnuradio_half_sine', 63, 0.35)], 0.95)

    def test_proxy_needs_long_filters_to_reach_unity(self) -> None:
        slopes = self.lookup()
        self.assertLess(slopes[('proxy_bandpass', 63, 0.20)], slopes[('proxy_bandpass', 255, 0.20)])
        self.assertGreater(slopes[('proxy_bandpass', 255, 0.20)], 0.90)

    def test_low_rolloff_stays_soft_even_for_half_sine_design(self) -> None:
        slopes = self.lookup()
        self.assertLess(slopes[('gnuradio_half_sine', 63, 0.05)], 0.85)
        self.assertGreater(slopes[('gnuradio_half_sine', 63, 0.20)], 0.90)


if __name__ == '__main__':
    unittest.main()
