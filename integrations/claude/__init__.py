"""
Claude 統合モジュール

Claude の system prompt に NeuroState を反映させるためのユーティリティ。
"""

from ...core.state_model import NeuroState, EthicsGateResult
from ...core.update_engine import evaluate_ethics_gate


def build_neuro_context(state: NeuroState) -> str:
    """NeuroState を Claude の system prompt 挿入用テキストに変換する。

    Args:
        state: 現在の NeuroState

    Returns:
        system prompt に追加するコンテキスト文字列
    """
    ethics = evaluate_ethics_gate(state)

    mood = _describe_mood(state)
    gate_text = {
        "PASS": "",
        "WARN": f"\n⚠️ 注意: {ethics.reason}",
        "BLOCK": f"\n🚫 制限: {ethics.reason}",
    }.get(ethics.status, "")

    return (
        f"[NeuroState]\n"
        f"現在の感情状態: {mood}\n"
        f"D={state.D:.0f} S={state.S:.0f} O={state.O:.0f} "
        f"G={state.G:.0f} corruption={state.corruption:.0f}"
        f"{gate_text}"
    )


def _describe_mood(state: NeuroState) -> str:
    """NeuroState から自然言語での感情説明を生成する。"""
    if state.corruption > 60:
        return "混乱・不安定"
    if state.D > 80:
        return "興奮・高揚"
    if state.S > 70 and state.O > 50:
        return "穏やか・親密"
    if state.S < 30:
        return "不安・落ち込み"
    if state.G > 70:
        return "落ち着き・安定"
    return "通常"
