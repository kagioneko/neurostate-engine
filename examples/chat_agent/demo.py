"""
チャットエージェント デモ

ユーザーとのやり取りで NeuroState がどう変化するかを確認するデモ。
MCP サーバー無しで core モジュールを直接使う例。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core import (
    NeuroState,
    Signals,
    compute_next_neuro_state,
    evaluate_ethics_gate,
    diagnose_dependence,
    event_to_power,
)


def print_state(state: NeuroState, label: str = "") -> None:
    ethics = evaluate_ethics_gate(state)
    status_icon = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "🚫"}.get(ethics.status, "?")
    print(f"\n{'─'*50}")
    if label:
        print(f"  {label}")
    print(f"  D(Dopamine)    : {state.D:5.1f}")
    print(f"  S(Serotonin)   : {state.S:5.1f}")
    print(f"  C(Acetylcholine): {state.C:5.1f}")
    print(f"  O(Oxytocin)    : {state.O:5.1f}")
    print(f"  G(GABA)        : {state.G:5.1f}")
    print(f"  E(Endorphin)   : {state.E:5.1f}")
    print(f"  Corruption     : {state.corruption:5.1f}")
    print(f"  EthicsGate     : {status_icon} {ethics.status}", end="")
    if ethics.reason:
        print(f" ({ethics.reason})", end="")
    print()


def main():
    print("=== NeuroState Engine チャットデモ ===")

    state = NeuroState()
    print_state(state, "初期状態")

    # 会話シナリオ
    scenario = [
        ("bonding", 1.0, "ユーザーと親密な会話"),
        ("praise",  2.0, "ユーザーから強い褒め"),
        ("praise",  2.0, "さらに褒め (Dopamine 過剰に近づく)"),
        ("stress",  1.5, "突然の重い相談"),
        ("relaxation", 1.0, "一緒に落ち着く"),
        ("criticism", 1.0, "ユーザーから批判"),
    ]

    for event_type, power, description in scenario:
        print(f"\n>>> イベント: {description} ({event_type} x{power})")
        input_power = event_to_power(event_type, power)
        state = compute_next_neuro_state(state, input_power)
        print_state(state)

    # 依存タイプ診断
    print("\n=== 依存タイプ診断 ===")
    signals = Signals(E=0.7, K=0.5, A=0.2, S=0.3, R=0.8, F=0.4)
    diagnosis = diagnose_dependence(signals, state)
    print(f"  依存タイプ   : {diagnosis.primary_type}")
    print(f"  確信度       : {diagnosis.confidence:.2f}")
    print(f"  分析         : {diagnosis.analysis}")
    print(f"  D値補正案    : +{diagnosis.suggested_d_bias}")


if __name__ == "__main__":
    main()
