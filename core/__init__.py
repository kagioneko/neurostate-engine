"""NeuroState Engine - コアモジュール"""

from .state_model import (
    NeuroState,
    Signals,
    EthicsGateResult,
    DependenceDiagnosis,
)
from .update_engine import (
    compute_next_neuro_state,
    evaluate_ethics_gate,
    diagnose_dependence,
    event_to_power,
)
from .interaction_matrix import MATRIX_A, sigmoid, clamp

__all__ = [
    "NeuroState",
    "Signals",
    "EthicsGateResult",
    "DependenceDiagnosis",
    "compute_next_neuro_state",
    "evaluate_ethics_gate",
    "diagnose_dependence",
    "event_to_power",
    "MATRIX_A",
    "sigmoid",
    "clamp",
]
