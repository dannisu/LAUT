import unittest

from laut.criteria import Status, evaluate_diagnostic
from laut.framework import Limit, load_framework


class FrameworkAndCriteriaTest(unittest.TestCase):
    def test_default_framework_is_complete(self):
        framework = load_framework()
        self.assertEqual(framework.status, "proposal")
        self.assertEqual({stage.id for stage in framework.stages}, {f"S{i}" for i in range(5)})
        self.assertEqual({rank.id for rank in framework.tuning_ranks}, {f"T{i}" for i in range(1, 8)})
        self.assertGreaterEqual(len(framework.criteria), 50)

    def test_limit_operators(self):
        self.assertTrue(Limit("abs_le", 1.0).matches(-1.0))
        self.assertTrue(Limit("between", (10.0, 20.0)).matches(15.0))
        self.assertTrue(Limit("factor_within", 2.0).matches(0.5))
        self.assertFalse(Limit("factor_within", 2.0).matches(2.1))

    def test_target_pass_fail_and_missing(self):
        criterion = load_framework().criterion("O2_SST_BIAS")
        self.assertEqual(evaluate_diagnostic("a", "S4", criterion, 0.4).status, Status.TARGET)
        self.assertEqual(evaluate_diagnostic("a", "S4", criterion, 0.8).status, Status.PASS)
        self.assertEqual(evaluate_diagnostic("a", "S4", criterion, 1.1).status, Status.FAIL)
        self.assertEqual(evaluate_diagnostic("a", "S4", criterion, None).status, Status.MISSING)


if __name__ == "__main__":
    unittest.main()

