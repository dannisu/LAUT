"""Small, dependency-light metrics used by LAUT pipelines."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np


ArrayLike = Any


def _paired(model: ArrayLike, reference: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    model_array, reference_array = np.broadcast_arrays(
        np.asarray(model, dtype=float), np.asarray(reference, dtype=float)
    )
    mask = np.isfinite(model_array) & np.isfinite(reference_array)
    if not mask.any():
        return np.array([], dtype=float), np.array([], dtype=float)
    return model_array[mask], reference_array[mask]


def bias(model: ArrayLike, reference: ArrayLike, **_: Any) -> float:
    model_array, reference_array = _paired(model, reference)
    return float(np.mean(model_array - reference_array)) if model_array.size else float("nan")


def rmse(model: ArrayLike, reference: ArrayLike, **_: Any) -> float:
    model_array, reference_array = _paired(model, reference)
    return (
        float(np.sqrt(np.mean(np.square(model_array - reference_array))))
        if model_array.size
        else float("nan")
    )


def pattern_correlation(model: ArrayLike, reference: ArrayLike, **_: Any) -> float:
    model_array, reference_array = _paired(model, reference)
    if model_array.size < 2 or np.std(model_array) == 0 or np.std(reference_array) == 0:
        return float("nan")
    return float(np.corrcoef(model_array, reference_array)[0, 1])


def absolute_error(model: ArrayLike, reference: ArrayLike, **_: Any) -> float:
    model_array, reference_array = _paired(model, reference)
    return float(abs(np.mean(model_array) - np.mean(reference_array))) if model_array.size else float("nan")


def relative_error_percent(model: ArrayLike, reference: ArrayLike, **_: Any) -> float:
    model_array, reference_array = _paired(model, reference)
    if not model_array.size:
        return float("nan")
    denominator = abs(float(np.mean(reference_array)))
    if denominator == 0:
        return float("nan")
    return 100.0 * abs(float(np.mean(model_array)) - float(np.mean(reference_array))) / denominator


def factor_ratio(model: ArrayLike, reference: ArrayLike, **_: Any) -> float:
    model_array, reference_array = _paired(model, reference)
    if not model_array.size:
        return float("nan")
    denominator = abs(float(np.mean(reference_array)))
    if denominator == 0:
        return float("nan")
    return abs(float(np.mean(model_array))) / denominator


def mse_skill_score(
    model: ArrayLike,
    reference: ArrayLike,
    *,
    parent: ArrayLike | None = None,
    **_: Any,
) -> float:
    if parent is None:
        raise ValueError("mse_skill_score requires a parent-model array")
    model_array, reference_array = _paired(model, reference)
    parent_array, parent_reference = _paired(parent, reference)
    if not model_array.size or not parent_array.size:
        return float("nan")
    model_mse = np.mean(np.square(model_array - reference_array))
    parent_mse = np.mean(np.square(parent_array - parent_reference))
    return float(1.0 - model_mse / parent_mse) if parent_mse != 0 else float("nan")


def mean_value(model: ArrayLike, reference: ArrayLike | None = None, **_: Any) -> float:
    values = np.asarray(model, dtype=float)
    return float(np.nanmean(values)) if np.isfinite(values).any() else float("nan")


METRICS: dict[str, Callable[..., float]] = {
    "absolute_error": absolute_error,
    "bias": bias,
    "factor_ratio": factor_ratio,
    "manual_boolean": mean_value,
    "mean_value": mean_value,
    "mse_skill_score": mse_skill_score,
    "pattern_correlation": pattern_correlation,
    "relative_error_percent": relative_error_percent,
    "rmse": rmse,
}


def compute_metric(
    name: str,
    model: ArrayLike,
    reference: ArrayLike | None = None,
    *,
    parent: ArrayLike | None = None,
    **parameters: Any,
) -> float:
    """Compute a named metric with a consistent API."""

    try:
        metric = METRICS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown metric {name!r}; available: {', '.join(sorted(METRICS))}") from exc
    return metric(model, reference, parent=parent, **parameters)

