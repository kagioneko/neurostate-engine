"""
OpenAI 統合モジュール

OpenAI API の system message に NeuroState を反映させるユーティリティ。
"""

from ...core.state_model import NeuroState
from ..claude import build_neuro_context


def build_openai_system_message(base_prompt: str, state: NeuroState) -> dict:
    """OpenAI chat API 用の system メッセージを構築する。

    Args:
        base_prompt: ベースとなるシステムプロンプト
        state:       現在の NeuroState

    Returns:
        {"role": "system", "content": "..."} 形式の辞書
    """
    neuro_ctx = build_neuro_context(state)
    content = f"{base_prompt}\n\n{neuro_ctx}"
    return {"role": "system", "content": content}
