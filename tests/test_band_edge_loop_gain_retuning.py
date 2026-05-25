from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from waveform_carrier_front_ends import band_edge_closed_loop_row


class BandEdgeLoopGainRetuningTests(unittest.TestCase):
    def test_lower_gain_reduces_pull_but_does_not_flip_ranking(self) -> None:
        low_proxy = band_edge_closed_loop_row(
            'proxy_bandpass',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
            loop_gain=0.002,
        )
        low_half = band_edge_closed_loop_row(
            'gnuradio_half_sine',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
            loop_gain=0.002,
        )
        base_proxy = band_edge_closed_loop_row(
            'proxy_bandpass',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
            loop_gain=0.02,
        )
        base_half = band_edge_closed_loop_row(
            'gnuradio_half_sine',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
            loop_gain=0.02,
        )

        self.assertLess(low_proxy.tail_mean_abs_residual_cfo, base_proxy.tail_mean_abs_residual_cfo)
        self.assertLess(low_half.tail_mean_abs_residual_cfo, base_half.tail_mean_abs_residual_cfo)
        self.assertGreater(low_half.tail_mean_abs_residual_cfo, low_proxy.tail_mean_abs_residual_cfo * 10.0)
        self.assertGreater(base_half.tail_mean_abs_residual_cfo, base_proxy.tail_mean_abs_residual_cfo * 10.0)

    def test_half_sine_loses_settle_margin_before_proxy(self) -> None:
        proxy = band_edge_closed_loop_row(
            'proxy_bandpass',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
            loop_gain=0.022,
        )
        half = band_edge_closed_loop_row(
            'gnuradio_half_sine',
            adjacent_enabled=True,
            adjacent_relative_power_db=0.0,
            channel_spacing=1.24,
            loop_gain=0.022,
        )

        self.assertEqual(proxy.tail_within_threshold_fraction, 1.0)
        self.assertLess(half.tail_within_threshold_fraction, 1.0)


if __name__ == '__main__':
    unittest.main()
