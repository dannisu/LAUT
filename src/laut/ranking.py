"""Hierarchy-aware comparison of model configurations."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .criteria import EvaluationRecord, Status
from .framework import Framework, VALID_RANKS


@dataclass(frozen=True)
class ScoreUnit:
    key: str
    rank: str
    status: Status
    points: float
    required: bool


@dataclass(frozen=True)
class ConfigurationScore:
    configuration: str
    stage: str
    mode: str
    rank_scores: dict[str, float]
    weighted_score: float
    coverage: float
    accepted: bool
    failures: int
    missing: int
    position: int = 0


@dataclass(frozen=True)
class Comparison:
    scores: tuple[ConfigurationScore, ...]
    records: tuple[EvaluationRecord, ...]


def _combine_group(records: list[EvaluationRecord]) -> ScoreUnit:
    first = records[0]
    key = first.group or first.criterion_id
    if not first.group:
        return ScoreUnit(key, first.rank, first.status, first.points, first.required)
    statuses = [record.status for record in records]
    rule = first.group_rule
    if rule == "any":
        if Status.TARGET in statuses:
            status = Status.TARGET
        elif Status.PASS in statuses:
            status = Status.PASS
        elif Status.MISSING in statuses:
            status = Status.MISSING
        else:
            status = Status.FAIL
    else:
        if Status.FAIL in statuses:
            status = Status.FAIL
        elif Status.MISSING in statuses:
            status = Status.MISSING
        elif all(item == Status.TARGET for item in statuses):
            status = Status.TARGET
        else:
            status = Status.PASS
    points = {Status.TARGET: 1.0, Status.PASS: 0.5}.get(status, 0.0)
    return ScoreUnit(key, first.rank, status, points, any(record.required for record in records))


def _score_units(records: Iterable[EvaluationRecord]) -> list[ScoreUnit]:
    groups: dict[str, list[EvaluationRecord]] = {}
    for record in records:
        key = record.group or record.criterion_id
        groups.setdefault(key, []).append(record)
    return [_combine_group(group) for group in groups.values()]


def _configuration_score(
    configuration: str,
    records: list[EvaluationRecord],
    framework: Framework,
) -> ConfigurationScore:
    stages = {record.stage for record in records}
    modes = {record.mode for record in records}
    if len(stages) > 1 or len(modes) > 1:
        raise ValueError(f"Configuration {configuration!r} mixes stages or evaluation modes")
    stage = records[0].stage if records else "unknown"
    mode = records[0].mode if records else "forced"
    applicable_ids = {
        criterion.id
        for criterion in framework.criteria
        if criterion.applicability in {"all", mode}
    }
    completed = [record for record in records if record.criterion_id in applicable_ids]
    present_by_id = {record.criterion_id: record for record in completed}
    for criterion in framework.criteria:
        applicable = criterion.applicability in {"all", mode}
        if applicable and criterion.required and criterion.id not in present_by_id:
            from .criteria import evaluate_diagnostic

            completed.append(evaluate_diagnostic(configuration, stage, criterion, None, mode))
    units = _score_units(completed)
    required_units = [unit for unit in units if unit.required]
    rank_scores: dict[str, float] = {}
    for rank in VALID_RANKS:
        rank_units = [unit for unit in required_units if unit.rank == rank]
        rank_scores[rank] = 100.0 * mean(unit.points for unit in rank_units) if rank_units else 0.0
    weights = {rank: 8 - index for index, rank in enumerate(VALID_RANKS, start=1)}
    denominator = sum(weights.values())
    weighted_score = sum(rank_scores[rank] * weights[rank] for rank in VALID_RANKS) / denominator
    expected_unit_keys = {
        criterion.group or criterion.id
        for criterion in framework.criteria
        if criterion.required and criterion.applicability in {"all", mode}
    }
    supplied_unit_keys = {
        criterion.group or criterion.id
        for criterion in framework.criteria
        if criterion.required
        and criterion.applicability in {"all", mode}
        and criterion.id in present_by_id
    }
    coverage = (
        100.0 * len(supplied_unit_keys & expected_unit_keys) / len(expected_unit_keys)
        if expected_unit_keys
        else 100.0
    )
    failures = sum(unit.status == Status.FAIL for unit in required_units)
    missing = sum(unit.status == Status.MISSING for unit in required_units)
    accepted = stage == "S4" and failures == 0 and missing == 0
    return ConfigurationScore(
        configuration=configuration,
        stage=stage,
        mode=mode,
        rank_scores=rank_scores,
        weighted_score=weighted_score,
        coverage=coverage,
        accepted=accepted,
        failures=failures,
        missing=missing,
    )


def compare_configurations(
    records: Iterable[EvaluationRecord], framework: Framework
) -> Comparison:
    """Rank configurations lexicographically from T1 through T7.

    A lower-priority success cannot compensate for a higher-priority weakness. The
    weighted score is included for communication, but does not determine ordering.
    """

    materialized = tuple(records)
    by_configuration: dict[str, list[EvaluationRecord]] = {}
    for record in materialized:
        by_configuration.setdefault(record.configuration, []).append(record)
    scores = [
        _configuration_score(configuration, config_records, framework)
        for configuration, config_records in by_configuration.items()
    ]
    scores.sort(
        key=lambda score: tuple(score.rank_scores[rank] for rank in VALID_RANKS)
        + (score.coverage, score.weighted_score),
        reverse=True,
    )
    positioned = tuple(
        ConfigurationScore(**{**score.__dict__, "position": position})
        for position, score in enumerate(scores, start=1)
    )
    return Comparison(scores=positioned, records=materialized)
