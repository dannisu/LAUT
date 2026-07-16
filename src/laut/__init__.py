"""LAUT: regional ocean-model evaluation for Southeast Asia."""

from .criteria import EvaluationRecord, Status, evaluate_diagnostic
from .framework import Criterion, Framework, load_framework
from .ranking import Comparison, compare_configurations

__all__ = [
    "Comparison",
    "Criterion",
    "EvaluationRecord",
    "Framework",
    "Status",
    "compare_configurations",
    "evaluate_diagnostic",
    "load_framework",
]

__version__ = "0.1.0"

