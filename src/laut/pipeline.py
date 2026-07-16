"""Manifest-driven evaluation pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib

import numpy as np

from .catalog import Catalog, align_arrays
from .criteria import EvaluationRecord, evaluate_diagnostic
from .framework import Framework, load_framework
from .metrics import compute_metric
from .ranking import Comparison, compare_configurations


@dataclass(frozen=True)
class RunResult:
    framework: Framework
    comparison: Comparison
    output_dir: Path


def _resolve(base: Path, candidate: str | Path) -> Path:
    path = Path(candidate).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def _configuration_map(raw: dict[str, Any]) -> dict[str, tuple[str, str]]:
    configurations = {
        str(item["id"]): (str(item.get("stage", "unknown")), str(item.get("mode", "forced")))
        for item in raw.get("configurations", [])
    }
    if not configurations:
        raise ValueError("A run manifest needs at least one [[configurations]] entry")
    return configurations


def records_from_diagnostics(
    path: str | Path,
    framework: Framework,
    default_stage: str = "S4",
    default_mode: str = "forced",
) -> list[EvaluationRecord]:
    """Read long-form CSV: configuration,criterion_id,value[,stage]."""

    table = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
    if table.size == 0:
        return []
    rows = np.atleast_1d(table)
    names = set(table.dtype.names or ())
    required = {"configuration", "criterion_id", "value"}
    if not required.issubset(names):
        raise ValueError(f"Diagnostics CSV requires columns: {', '.join(sorted(required))}")
    records: list[EvaluationRecord] = []
    for row in rows:
        criterion = framework.criterion(str(row["criterion_id"]))
        stage = str(row["stage"]) if "stage" in names else default_stage
        mode = str(row["mode"]) if "mode" in names else default_mode
        if criterion.applicability not in {"all", mode}:
            continue
        value = float(row["value"])
        records.append(evaluate_diagnostic(str(row["configuration"]), stage, criterion, value, mode))
    return records


def run_manifest(path: str | Path) -> RunResult:
    """Execute a TOML run manifest and return comparison-ready records."""

    manifest_path = Path(path).resolve()
    with manifest_path.open("rb") as handle:
        raw = tomllib.load(handle)
    base = manifest_path.parent
    framework_path = raw.get("framework")
    framework = load_framework(_resolve(base, framework_path) if framework_path else None)
    catalog_path = _resolve(base, raw["catalog"])
    output_dir = _resolve(base, raw.get("output_dir", "outputs/laut-run"))
    configurations = _configuration_map(raw)
    records: list[EvaluationRecord] = []
    with Catalog.from_toml(catalog_path) as catalog:
        catalog_errors = catalog.validate()
        if catalog_errors:
            raise ValueError("Invalid catalog:\n- " + "\n- ".join(catalog_errors))
        for item in raw.get("evaluations", []):
            configuration = str(item["configuration"])
            if configuration not in configurations:
                raise ValueError(f"Evaluation references undeclared configuration: {configuration}")
            stage, mode = configurations[configuration]
            criterion = framework.criterion(str(item["criterion_id"]))
            if criterion.applicability not in {"all", mode}:
                continue
            if "value" in item:
                value = float(item["value"])
            else:
                variable = str(item.get("variable", criterion.variable))
                model_variable = str(item.get("model_variable", variable))
                reference_variable = str(item.get("reference_variable", variable))
                model = catalog.array(str(item["model_source"]), model_variable)
                reference = None
                if item.get("reference_source"):
                    reference = catalog.array(str(item["reference_source"]), reference_variable)
                    model, reference = align_arrays(
                        model, reference, str(item.get("alignment", "exact"))
                    )
                elif criterion.metric not in {"manual_boolean", "mean_value"}:
                    raise ValueError(
                        f"{criterion.id} uses {criterion.metric} and requires reference_source"
                    )
                parent = None
                if item.get("parent_source"):
                    if reference is None:
                        raise ValueError(f"{criterion.id} has parent_source but no reference_source")
                    parent = catalog.array(
                        str(item["parent_source"]), str(item.get("parent_variable", variable))
                    )
                    parent, _ = align_arrays(parent, reference, str(item.get("alignment", "exact")))
                value = compute_metric(
                    criterion.metric,
                    model,
                    reference,
                    parent=parent,
                    **dict(item.get("metric_parameters", {})),
                )
            records.append(evaluate_diagnostic(configuration, stage, criterion, value, mode))
    present_configurations = {record.configuration for record in records}
    for configuration, (stage, mode) in configurations.items():
        if configuration in present_configurations:
            continue
        first = next(
            (
                criterion
                for criterion in framework.criteria
                if criterion.required and criterion.applicability in {"all", mode}
            ),
            None,
        )
        if first is not None:
            records.append(evaluate_diagnostic(configuration, stage, first, None, mode))
    return RunResult(
        framework=framework,
        comparison=compare_configurations(records, framework),
        output_dir=output_dir,
    )
