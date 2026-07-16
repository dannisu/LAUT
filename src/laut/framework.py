"""Versioned evaluation-framework loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any
import tomllib


VALID_RANKS = tuple(f"T{i}" for i in range(1, 8))
VALID_STAGES = tuple(f"S{i}" for i in range(5))
VALID_OPERATORS = {"abs_le", "between", "eq", "factor_within", "ge", "gt", "le", "lt"}


@dataclass(frozen=True)
class Limit:
    """A machine-testable acceptance limit."""

    operator: str
    value: float | tuple[float, float]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Limit":
        operator = str(raw["operator"])
        if operator not in VALID_OPERATORS:
            raise ValueError(f"Unsupported limit operator: {operator}")
        value = raw["value"]
        if operator == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("between limits require a two-value array")
            parsed: float | tuple[float, float] = (float(value[0]), float(value[1]))
        else:
            parsed = float(value)
        return cls(operator=operator, value=parsed)

    def matches(self, observed: float) -> bool:
        if self.operator == "abs_le":
            return abs(observed) <= float(self.value)
        if self.operator == "le":
            return observed <= float(self.value)
        if self.operator == "lt":
            return observed < float(self.value)
        if self.operator == "ge":
            return observed >= float(self.value)
        if self.operator == "gt":
            return observed > float(self.value)
        if self.operator == "eq":
            return observed == float(self.value)
        if self.operator == "factor_within":
            factor = float(self.value)
            return factor > 0 and (1.0 / factor) <= observed <= factor
        if self.operator == "between":
            low, high = self.value  # type: ignore[misc]
            return low <= observed <= high
        raise AssertionError(f"Unhandled operator: {self.operator}")


@dataclass(frozen=True)
class Criterion:
    """One atomic diagnostic and its target/acceptance threshold."""

    id: str
    section: str
    rank: str
    name: str
    variable: str
    metric: str
    units: str
    baseline: str
    reference: str
    threshold: Limit
    target: Limit | None = None
    required: bool = True
    applicability: str = "all"
    group: str | None = None
    group_rule: str = "all"
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Criterion":
        target_raw = raw.get("target")
        return cls(
            id=str(raw["id"]),
            section=str(raw["section"]),
            rank=str(raw["rank"]),
            name=str(raw["name"]),
            variable=str(raw["variable"]),
            metric=str(raw["metric"]),
            units=str(raw.get("units", "1")),
            baseline=str(raw["baseline"]),
            reference=str(raw["reference"]),
            threshold=Limit.from_dict(raw["threshold"]),
            target=Limit.from_dict(target_raw) if target_raw else None,
            required=bool(raw.get("required", True)),
            applicability=str(raw.get("applicability", "all")),
            group=str(raw["group"]) if raw.get("group") else None,
            group_rule=str(raw.get("group_rule", "all")),
            notes=str(raw.get("notes", "")),
        )


@dataclass(frozen=True)
class Stage:
    id: str
    name: str
    duration: str
    purpose: str
    gate: str


@dataclass(frozen=True)
class TuningRank:
    id: str
    name: str
    rationale: str
    parameters: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class Framework:
    name: str
    version: str
    status: str
    region: str
    description: str
    criteria: tuple[Criterion, ...]
    stages: tuple[Stage, ...] = ()
    tuning_ranks: tuple[TuningRank, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def criterion(self, criterion_id: str) -> Criterion:
        for criterion in self.criteria:
            if criterion.id == criterion_id:
                return criterion
        raise KeyError(f"Unknown criterion: {criterion_id}")

    def validate(self) -> list[str]:
        errors: list[str] = []
        ids = [criterion.id for criterion in self.criteria]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            errors.append(f"Duplicate criterion IDs: {', '.join(duplicates)}")
        for criterion in self.criteria:
            if criterion.rank not in VALID_RANKS:
                errors.append(f"{criterion.id}: invalid rank {criterion.rank}")
            if criterion.group_rule not in {"all", "any"}:
                errors.append(f"{criterion.id}: group_rule must be all or any")
        stage_ids = {stage.id for stage in self.stages}
        if stage_ids and stage_ids != set(VALID_STAGES):
            errors.append("Stages must define S0 through S4 exactly once")
        rank_ids = {rank.id for rank in self.tuning_ranks}
        if rank_ids and rank_ids != set(VALID_RANKS):
            errors.append("Tuning ranks must define T1 through T7 exactly once")
        return errors


def default_framework_path() -> Path:
    """Return the bundled Southeast Asia framework."""

    return Path(str(files("laut").joinpath("resources/laut-sea-v0.1.0.toml")))


def load_framework(path: str | Path | None = None) -> Framework:
    """Load a framework from TOML, or use LAUT's bundled proposal."""

    source = Path(path) if path else default_framework_path()
    with source.open("rb") as handle:
        raw = tomllib.load(handle)
    meta = raw["framework"]
    framework = Framework(
        name=str(meta["name"]),
        version=str(meta["version"]),
        status=str(meta["status"]),
        region=str(meta["region"]),
        description=str(meta["description"]),
        criteria=tuple(Criterion.from_dict(item) for item in raw.get("criteria", [])),
        stages=tuple(Stage(**item) for item in raw.get("stages", [])),
        tuning_ranks=tuple(
            TuningRank(
                id=str(item["id"]),
                name=str(item["name"]),
                rationale=str(item["rationale"]),
                parameters=tuple(item.get("parameters", [])),
                diagnostics=tuple(item.get("diagnostics", [])),
            )
            for item in raw.get("tuning_ranks", [])
        ),
        metadata={key: value for key, value in meta.items() if key not in {
            "name", "version", "status", "region", "description"
        }},
    )
    errors = framework.validate()
    if errors:
        raise ValueError("Invalid framework:\n- " + "\n- ".join(errors))
    return framework

