"""Turn diagnostic values into transparent target/pass/fail records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import math
from typing import Any

from .framework import Criterion


class Status(StrEnum):
    TARGET = "target"
    PASS = "pass"
    FAIL = "fail"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


STATUS_POINTS = {
    Status.TARGET: 1.0,
    Status.PASS: 0.5,
    Status.FAIL: 0.0,
    Status.MISSING: 0.0,
    Status.NOT_APPLICABLE: 0.0,
}


@dataclass(frozen=True)
class EvaluationRecord:
    configuration: str
    stage: str
    mode: str
    criterion_id: str
    section: str
    rank: str
    name: str
    value: float | None
    units: str
    status: Status
    points: float
    baseline: str
    reference: str
    required: bool
    group: str | None = None
    group_rule: str = "all"
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = str(self.status)
        return result


def evaluate_diagnostic(
    configuration: str,
    stage: str,
    criterion: Criterion,
    value: float | None,
    mode: str = "forced",
) -> EvaluationRecord:
    """Evaluate one precomputed or pipeline-derived diagnostic value."""

    if value is None or not math.isfinite(float(value)):
        status = Status.MISSING
        message = "No finite diagnostic value supplied."
        normalized_value = None
    else:
        normalized_value = float(value)
        if criterion.target and criterion.target.matches(normalized_value):
            status = Status.TARGET
            message = "Meets the development target."
        elif criterion.threshold.matches(normalized_value):
            status = Status.PASS
            message = "Within the acceptance threshold."
        else:
            status = Status.FAIL
            message = "Outside the acceptance threshold."
    return EvaluationRecord(
        configuration=configuration,
        stage=stage,
        mode=mode,
        criterion_id=criterion.id,
        section=criterion.section,
        rank=criterion.rank,
        name=criterion.name,
        value=normalized_value,
        units=criterion.units,
        status=status,
        points=STATUS_POINTS[status],
        baseline=criterion.baseline,
        reference=criterion.reference,
        required=criterion.required,
        group=criterion.group,
        group_rule=criterion.group_rule,
        message=message,
    )
