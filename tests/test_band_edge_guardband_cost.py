from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import sweep_band_edge_guardband_cost_comparison


class BandEdgeGuardbandCostTests(unittest.TestCase):
    @staticmethod
    def lookup() -> dict[tuple[str, int, float], tuple[float, float, float]]:
        rows = sweep_band_edge_guardband_cost_comparison(
            [0.20, 0.35, 0.50],
            [63, 255],
            channel_spacings=[0.55 + 0.05 * idx for idx in range(24)],
        )
        return {
            (row.design, row.tap_count, row.rolloff): (
                row.central_slope_wrt_deltaf_over_Rs,
                row.adjacent_capture_at_reference_spacing,
                row.spacing_for_capture_below_threshold,
            )
            for row in rows
        }

    def test_half_sine_buys_slope_by_accepting_more_adjacent_capture(self) -> None:
        lookup = self.lookup()
        proxy_slope, proxy_capture, proxy_spacing = lookup[('proxy_bandpass', 63, 0.35)]
        half_sine_slope, half_sine_capture, half_sine_spacing = lookup[('gnuradio_half_sine', 63, 0.35)]
        self.assertGreater(half_sine_slope, proxy_slope + 0.25)
        self.assertGreater(half_sine_capture, proxy_capture + 0.15)
        self.assertGreater(half_sine_spacing, proxy_spacing)

    def test_half_sine_guardband_cost_survives_at_lower_rolloff(self) -> None:
        lookup = self.lookup()
        proxy_slope, _, proxy_spacing = lookup[('proxy_bandpass', 63, 0.20)]
        half_sine_slope, _, half_sine_spacing = lookup[('gnuradio_half_sine', 63, 0.20)]
        self.assertLess(proxy_slope, 0.60)
        self.assertGreater(half_sine_slope, 0.90)
        self.assertGreaterEqual(half_sine_spacing - proxy_spacing, 0.40)

    def test_tap_count_moves_proxy_slope_more_than_proxy_guardband_threshold(self) -> None:
        lookup = self.lookup()
        slope_63, _, spacing_63 = lookup[('proxy_bandpass', 63, 0.35)]
        slope_255, _, spacing_255 = lookup[('proxy_bandpass', 255, 0.35)]
        self.assertGreater(slope_255, slope_63 + 0.25)
        self.assertLessEqual(abs(spacing_255 - spacing_63), 0.05)


if __name__ == '__main__':
    unittest.main()
