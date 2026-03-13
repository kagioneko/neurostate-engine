"""
LangChain 統合モジュール

LangChain の BaseMemory を継承した NeuroState メモリクラス。
チェーン実行時に感情状態を自動で system prompt に注入する。
"""

from __future__ import annotations

from typing import Any

from ...core.state_model import NeuroState, Signals
from ...core.update_engine import (
    compute_next_neuro_state,
    evaluate_ethics_gate,
    event_to_power,
)
from ..claude import build_neuro_context

try:
    from langchain.memory import BaseMemory
    from langchain.schema import BaseMessage
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False


if _LANGCHAIN_AVAILABLE:
    class NeuroStateMemory(BaseMemory):
        """LangChain チェーンに NeuroState を注入するメモリクラス。

        使用例:
            memory = NeuroStateMemory()
            chain = LLMChain(llm=llm, prompt=prompt, memory=memory)
        """

        neuro_state: NeuroState = NeuroState()
        memory_key: str = "neuro_context"

        @property
        def memory_variables(self) -> list[str]:
            return [self.memory_key]

        def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
            return {self.memory_key: build_neuro_context(self.neuro_state)}

        def save_context(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
            """チェーン実行後に NeuroState を更新する。

            inputs に "event_type" キーがあれば stimulate を実行する。
            """
            event_type = inputs.get("event_type")
            if event_type:
                power = event_to_power(event_type, float(inputs.get("power", 1.0)))
                self.neuro_state = compute_next_neuro_state(self.neuro_state, power)

        def clear(self) -> None:
            self.neuro_state = NeuroState()

else:
    # LangChain が未インストールの場合はスタブ
    class NeuroStateMemory:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "LangChain がインストールされていません。\n"
                "pip install langchain"
            )
