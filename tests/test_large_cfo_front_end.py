from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from large_cfo_front_end import alias_limit_normalized, sweep_normalized_cfo


class LargeCfoFrontEndTests(unittest.TestCase):
    def test_alias_limit_scales_linearly_with_samples_per_symbol(self) -> None:
        self.assertAlmostEqual(alias_limit_normalized(1), 0.125)
        self.assertAlmostEqual(alias_limit_normalized(2), 0.250)
        self.assertAlmostEqual(alias_limit_normalized(4), 0.500)

    def test_same_cfo_aliases_at_one_sps_but_not_four_sps(self) -> None:
        rows = sweep_normalized_cfo([1, 4], [0.30], symbol_count=192, noise_std=0.012, seed=19)
        by_sps = {row.samples_per_symbol: row for row in rows}

        self.assertAlmostEqual(by_sps[1].estimated_normalized_cfo, 0.05, delta=0.03)
        self.assertFalse(by_sps[1].honest)

        self.assertAlmostEqual(by_sps[4].estimated_normalized_cfo, 0.30, delta=0.03)
        self.assertTrue(by_sps[4].honest)

    def test_two_sps_limit_is_visible_near_point_three_rs(self) -> None:
        rows = sweep_normalized_cfo([2], [0.24, 0.30], symbol_count=192, noise_std=0.012, seed=19)
        by_cfo = {round(row.normalized_cfo, 2): row for row in rows}

        self.assertTrue(by_cfo[0.24].honest)
        self.assertFalse(by_cfo[0.30].honest)


if __name__ == '__main__':
    unittest.main()
