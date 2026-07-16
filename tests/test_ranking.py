import unittest

from laut.criteria import evaluate_diagnostic
from laut.framework import Criterion, Framework, Limit
from laut.ranking import compare_configurations


def criterion(identifier: str, rank: str, *, group: str | None = None) -> Criterion:
    return Criterion(
        id=identifier,
        section="O2",
        rank=rank,
        name=identifier,
        variable="x",
        metric="mean_value",
        units="1",
        baseline="observations",
        reference="synthetic",
        target=Limit("le", 0.5),
        threshold=Limit("le", 1.0),
        group=group,
        group_rule="any",
    )


class RankingTest(unittest.TestCase):
    def test_higher_priority_outweighs_lower_priority(self):
        t1 = criterion("T1_TEST", "T1")
        t6 = criterion("T6_TEST", "T6")
        framework = Framework("test", "1", "test", "SEA", "", (t1, t6))
        records = [
            evaluate_diagnostic("balanced", "S4", t1, 0.8),
            evaluate_diagnostic("balanced", "S4", t6, 0.8),
            evaluate_diagnostic("eddy-first", "S4", t1, 1.2),
            evaluate_diagnostic("eddy-first", "S4", t6, 0.2),
        ]
        comparison = compare_configurations(records, framework)
        self.assertEqual(comparison.scores[0].configuration, "balanced")

    def test_missing_required_metric_prevents_acceptance(self):
        t1 = criterion("A", "T1")
        t2 = criterion("B", "T2")
        framework = Framework("test", "1", "test", "SEA", "", (t1, t2))
        comparison = compare_configurations(
            [evaluate_diagnostic("partial", "S4", t1, 0.2)], framework
        )
        self.assertFalse(comparison.scores[0].accepted)
        self.assertEqual(comparison.scores[0].missing, 1)

    def test_any_group_accepts_one_satisfied_alternative(self):
        absolute = criterion("ABS", "T2", group="MLD")
        relative = criterion("REL", "T2", group="MLD")
        framework = Framework("test", "1", "test", "SEA", "", (absolute, relative))
        records = [
            evaluate_diagnostic("config", "S4", absolute, 0.2),
            evaluate_diagnostic("config", "S4", relative, 2.0),
        ]
        comparison = compare_configurations(records, framework)
        self.assertTrue(comparison.scores[0].accepted)

    def test_non_s4_cannot_be_accepted(self):
        item = criterion("A", "T1")
        framework = Framework("test", "1", "test", "SEA", "", (item,))
        comparison = compare_configurations(
            [evaluate_diagnostic("spinup", "S3", item, 0.2)], framework
        )
        self.assertFalse(comparison.scores[0].accepted)

    def test_non_applicable_forced_criterion_is_skipped(self):
        forced = Criterion(
            **{
                **criterion("FORCED", "T1").__dict__,
                "applicability": "forced",
            }
        )
        general = criterion("GENERAL", "T2")
        framework = Framework("test", "1", "test", "SEA", "", (forced, general))
        comparison = compare_configurations(
            [evaluate_diagnostic("gcm", "S4", general, 0.2, "gcm_driven")], framework
        )
        self.assertTrue(comparison.scores[0].accepted)
        self.assertEqual(comparison.scores[0].coverage, 100.0)


if __name__ == "__main__":
    unittest.main()
