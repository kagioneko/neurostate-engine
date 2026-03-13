"""
NeuroState 相互作用行列

6種類の神経伝達物質間の相互作用を定義する行列と、
関連する数学的ユーティリティ関数。

行インデックス: [D, S, C, O, G, E]
"""

import math
from typing import List

# 神経伝達物質間の相互作用行列
# 行 i = 物質 i の次状態への寄与
# MATRIX_A[i][j] = 物質 j が物質 i に与える影響
MATRIX_A: List[List[float]] = [
    [0.90, -0.10,  0.10,  0.00, -0.20,  0.10],  # D (Dopamine)
    [-0.10,  0.90, -0.05,  0.00,  0.20, -0.05],  # S (Serotonin)
    [0.10,  0.00,  0.95,  0.00,  0.00,  0.10],  # C (Acetylcholine)
    [0.00,  0.20,  0.00,  0.90, -0.10,  0.20],  # O (Oxytocin)
    [-0.15,  0.30,  0.00, -0.10,  0.90, -0.20],  # G (GABA)
    [0.20, -0.20,  0.10,  0.10, -0.30,  0.90],  # E (Endorphin)
]

# 外部刺激の各物質への影響係数
# input_power に掛け合わせて加算される
EXTERNAL_FORCE_COEFFS: List[float] = [
    1.0,   # D: input_power そのまま
    0.0,   # S: 外部刺激の影響なし（自律回復）
    0.5,   # C: input_power * 0.5
    0.3,   # O: input_power * 0.3
    -0.4,  # G: input_power * -0.4（興奮すると抑制が下がる）
    0.6,   # E: input_power * 0.6
]


def sigmoid(x: float, k: float = 2.0, m: float = 0.0) -> float:
    """シグモイド関数。

    Args:
        x: 入力値
        k: 傾きパラメータ（大きいほど急峻）
        m: 中心オフセット
    """
    return 1.0 / (1.0 + math.exp(-k * (x - m)))


def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """値を [min_val, max_val] の範囲にクランプする。"""
    return max(min_val, min(max_val, value))


def matrix_multiply_state(state_vec: List[float]) -> List[float]:
    """MATRIX_A × state_vec を計算する。

    Args:
        state_vec: [D, S, C, O, G, E] の現在値リスト

    Returns:
        次状態への行列積結果
    """
    result = [0.0] * 6
    for i in range(6):
        for j in range(6):
            result[i] += MATRIX_A[i][j] * state_vec[j]
    return result


def apply_external_force(state_vec: List[float], input_power: float) -> List[float]:
    """外部刺激を状態ベクトルに加算する。

    Args:
        state_vec: 行列積後の状態ベクトル
        input_power: 外部刺激の強度（正: 活性化、負: 抑制）

    Returns:
        外部刺激を加算した状態ベクトル
    """
    return [
        state_vec[i] + EXTERNAL_FORCE_COEFFS[i] * input_power
        for i in range(6)
    ]
