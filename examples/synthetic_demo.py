"""Generate a complete synthetic comparison without downloading ocean data."""

from __future__ import annotations

import argparse
from pathlib import Path

from laut.criteria import evaluate_diagnostic
from laut.framework import Criterion, Limit, load_framework
from laut.ranking import compare_configurations
from laut.report import write_reports


def target_value(limit: Limit) -> float:
    if limit.operator in {"abs_le", "le", "lt"}:
        return 0.5 * float(limit.value)
    if limit.operator in {"ge", "gt"}:
        return float(limit.value) + 0.1
    if limit.operator == "eq":
        return float(limit.value)
    if limit.operator == "factor_within":
        return 1.0
    low, high = limit.value  # type: ignore[misc]
    return (low + high) / 2.0


def passing_value(criterion: Criterion) -> float:
    threshold = criterion.threshold
    target = criterion.target
    if not target:
        return target_value(threshold)
    if threshold.operator in {"abs_le", "le", "lt"}:
        return (float(target.value) + float(threshold.value)) / 2.0
    if threshold.operator in {"ge", "gt"}:
        return (float(target.value) + float(threshold.value)) / 2.0
    if threshold.operator == "factor_within":
        return (float(target.value) + float(threshold.value)) / 2.0
    if threshold.operator == "eq":
        return float(threshold.value)
    target_low, target_high = target.value  # type: ignore[misc]
    threshold_low, _ = threshold.value  # type: ignore[misc]
    return (threshold_low + target_low) / 2.0 if threshold_low < target_low else target_high


def failing_value(limit: Limit) -> float:
    if limit.operator in {"abs_le", "le", "lt"}:
        return float(limit.value) + max(1.0, abs(float(limit.value)) * 0.2)
    if limit.operator in {"ge", "gt"}:
        return float(limit.value) - max(0.1, abs(float(limit.value)) * 0.2)
    if limit.operator == "eq":
        return float(limit.value) + 1.0
    if limit.operator == "factor_within":
        return float(limit.value) * 1.2
    _, high = limit.value  # type: ignore[misc]
    return high + max(1.0, abs(high) * 0.2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/demo"))
    args = parser.parse_args()
    framework = load_framework()
    records = []
    for criterion in framework.criteria:
        values = {
            "control": passing_value(criterion),
            "t1-improved": target_value(criterion.target or criterion.threshold)
            if criterion.rank == "T1"
            else passing_value(criterion),
            "eddy-first": failing_value(criterion.threshold)
            if criterion.rank == "T1"
            else target_value(criterion.target or criterion.threshold)
            if criterion.rank == "T6"
            else passing_value(criterion),
        }
        for configuration, value in values.items():
            records.append(evaluate_diagnostic(configuration, "S4", criterion, value))
    comparison = compare_configurations(records, framework)
    paths = write_reports(comparison, args.output, framework.status)
    for score in comparison.scores:
        print(
            f"{score.position}. {score.configuration}: T1={score.rank_scores['T1']:.1f}, "
            f"T6={score.rank_scores['T6']:.1f}, accepted={score.accepted}"
        )
    print(f"Wrote {len(paths)} reports to {args.output}")


if __name__ == "__main__":
    main()
