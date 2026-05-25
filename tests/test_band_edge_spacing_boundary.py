from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import band_edge_closed_loop_row


class BandEdgeSpacingBoundaryTests(unittest.TestCase):
    def test_half_sine_regains_settle_band_before_mean_residual_flip(self) -> None:
        proxy_settle = band_edge_closed_loop_row(
            'proxy_bandpass',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
        )
        half_settle = band_edge_closed_loop_row(
            'gnuradio_half_sine',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
        )
        proxy_cross = band_edge_closed_loop_row(
            'proxy_bandpass',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.57,
        )
        half_cross = band_edge_closed_loop_row(
            'gnuradio_half_sine',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.57,
        )

        self.assertEqual(proxy_settle.tail_within_threshold_fraction, 1.0)
        self.assertEqual(half_settle.tail_within_threshold_fraction, 1.0)
        self.assertGreater(half_settle.tail_mean_abs_residual_cfo, proxy_settle.tail_mean_abs_residual_cfo + 0.03)
        self.assertLess(half_cross.tail_mean_abs_residual_cfo, proxy_cross.tail_mean_abs_residual_cfo)


if __name__ == '__main__':
    unittest.main()
