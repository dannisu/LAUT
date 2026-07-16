import unittest

import numpy as np

from laut.metrics import (
    bias,
    factor_ratio,
    mse_skill_score,
    pattern_correlation,
    relative_error_percent,
    rmse,
)


class MetricsTest(unittest.TestCase):
    def test_paired_metrics_ignore_shared_non_finite_samples(self):
        model = np.array([1.0, 2.0, np.nan, 4.0])
        reference = np.array([0.0, 2.0, 3.0, np.nan])
        self.assertAlmostEqual(bias(model, reference), 0.5)
        self.assertAlmostEqual(rmse(model, reference), np.sqrt(0.5))

    def test_pattern_correlation(self):
        reference = np.arange(6, dtype=float)
        self.assertAlmostEqual(pattern_correlation(reference * 2.0, reference), 1.0)

    def test_relative_error_and_factor(self):
        self.assertAlmostEqual(relative_error_percent([12.0], [10.0]), 20.0)
        self.assertAlmostEqual(factor_ratio([15.0], [10.0]), 1.5)

    def test_parent_skill(self):
        reference = np.array([0.0, 1.0, 2.0])
        parent = np.array([2.0, 3.0, 4.0])
        regional = np.array([1.0, 2.0, 3.0])
        self.assertAlmostEqual(mse_skill_score(regional, reference, parent=parent), 0.75)


if __name__ == "__main__":
    unittest.main()

