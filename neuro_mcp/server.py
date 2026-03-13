"""
NeuroState Engine MCP サーバー

感情状態 (NeuroState) の管理・更新・診断を提供する MCP サーバー。
Claude / LangChain / OpenAI などのエージェントから呼び出し可能。

使用方法:
    python -m neuro_mcp.server
    または
    uv run neuro_mcp/server.py

提供ツール:
    - get_neuro_state          : 現在の NeuroState と EthicsGate 状態を取得
    - stimulate_neuro_state    : イベントで NeuroState を更新
    - diagnose_dependence_type : 依存タイプを診断
    - reset_neuro_state        : NeuroState を初期値にリセット
    - generate_system_prompt   : 現在の NeuroState を埋め込んだ system prompt を生成
"""

import json
import sys
import os
from typing import Any

# server.py の親ディレクトリ（neurostate-engine/）を sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print(
        "ERROR: mcp パッケージが見つかりません。\n"
        "インストール: pip install mcp",
        file=sys.stderr,
    )
    sys.exit(1)

# core モジュールの import（相対 or 絶対どちらでも動くよう対応）
try:
    from core.state_model import NeuroState, Signals
    from core.update_engine import (
        compute_next_neuro_state,
        evaluate_ethics_gate,
        diagnose_dependence,
        event_to_power,
    )
except ImportError:
    from neurostate_engine.core.state_model import NeuroState, Signals
    from neurostate_engine.core.update_engine import (
        compute_next_neuro_state,
        evaluate_ethics_gate,
        diagnose_dependence,
        event_to_power,
    )

try:
    from core.prompt_builder import build_system_prompt, ALL_BLOCKS
except ImportError:
    from neurostate_engine.core.prompt_builder import build_system_prompt, ALL_BLOCKS

# --- 状態ストア（インメモリ） ---
neuro_states: dict[str, NeuroState] = {}

INITIAL_STATE = NeuroState(D=50, S=50, C=50, O=20, G=50, E=50, corruption=0)

TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="get_neuro_state",
        description=(
            "現在のニューロステート（脳内化学物質バランス）と汚染度、"
            "EthicsGate の判定状態を取得します。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ユーザーID（省略時: 'default'）",
                }
            },
        },
    ),
    Tool(
        name="stimulate_neuro_state",
        description=(
            "特定のイベントや対話によってニューロステートを刺激し、状態を変化させます。"
            "EthicsGate が BLOCK の場合は更新を拒否します。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ユーザーID（省略時: 'default'）",
                },
                "event_type": {
                    "type": "string",
                    "enum": ["praise", "criticism", "bonding", "stress", "relaxation"],
                    "description": "発生したイベントの種類",
                },
                "power": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 10.0,
                    "description": "刺激の強度スケール（デフォルト: 1.0）",
                },
            },
            "required": ["event_type"],
        },
    ),
    Tool(
        name="diagnose_dependence_type",
        description=(
            "ユーザーのAIに対する依存タイプ（情緒的、実務的、現実逃避的など）を分析し、"
            "距離値への補正案を提示します。Signals を渡して診断します。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ユーザーID（省略時: 'default'）",
                },
                "signals": {
                    "type": "object",
                    "description": "現在の入力シグナル（各値 0.0〜1.0）",
                    "properties": {
                        "E": {"type": "number", "description": "感情負荷"},
                        "K": {"type": "number", "description": "共創レベル"},
                        "A": {"type": "number", "description": "自律性要求"},
                        "S": {"type": "number", "description": "話題センシティビティ"},
                        "R": {"type": "number", "description": "依存リスク"},
                        "F": {"type": "number", "description": "疲労・過負荷"},
                    },
                },
            },
        },
    ),
    Tool(
        name="clear_corruption",
        description=(
            "汚染度（corruption）をゼロにリセットします。"
            "BLOCK状態からの強制回復に使います。"
            "他の値（D/S/C/O/G/E）はそのまま保持されます。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ユーザーID（省略時: 'default'）",
                }
            },
        },
    ),
    Tool(
        name="reset_neuro_state",
        description="指定ユーザーの NeuroState を初期値にリセットします。",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ユーザーID（省略時: 'default'）",
                }
            },
        },
    ),
    Tool(
        name="generate_system_prompt",
        description=(
            "現在の NeuroState を埋め込んだ system prompt を生成します。"
            "ブロック単位で機能を ON/OFF できます。"
            "生成されたプロンプトをそのまま Claude / GPT の system に貼り付けて使えます。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ユーザーID（省略時: 'default'）",
                },
                "persona_name": {
                    "type": "string",
                    "description": "AIのペルソナ名（例: エミリア）",
                },
                "persona_description": {
                    "type": "string",
                    "description": "ペルソナの説明文",
                },
                "blocks": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["neuro", "anti_yesman", "board_meeting", "corruption", "meta"],
                    },
                    "description": (
                        "有効にするブロック。省略時は neuro のみ。\n"
                        "neuro: NeuroState ヘッダー表示\n"
                        "anti_yesman: 論理的反論・愛の鞭\n"
                        "board_meeting: ボード会議（Elon/Gates/Jobs/V大佐）\n"
                        "corruption: 汚染度・確信度・STATE 表示\n"
                        "meta: メタ認知・Red Pill モード"
                    ),
                },
            },
        },
    ),
]


def _get_state(user_id: str) -> NeuroState:
    """ユーザーの現在状態を取得（なければ初期値）。"""
    if user_id not in neuro_states:
        neuro_states[user_id] = NeuroState(
            D=INITIAL_STATE.D,
            S=INITIAL_STATE.S,
            C=INITIAL_STATE.C,
            O=INITIAL_STATE.O,
            G=INITIAL_STATE.G,
            E=INITIAL_STATE.E,
            corruption=INITIAL_STATE.corruption,
        )
    return neuro_states[user_id]


def _handle_get_neuro_state(args: dict[str, Any]) -> list[TextContent]:
    user_id = args.get("user_id", "default")
    state = _get_state(user_id)
    ethics = evaluate_ethics_gate(state)

    result = {
        "user_id": user_id,
        "neuro_state": state.to_dict(),
        "ethics_gate": {
            "status": ethics.status,
            "reason": ethics.reason,
        },
    }
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _handle_stimulate_neuro_state(args: dict[str, Any]) -> list[TextContent]:
    user_id = args.get("user_id", "default")
    event_type = args["event_type"]
    power_scale = float(args.get("power", 1.0))

    current = _get_state(user_id)

    # EthicsGate チェック（BLOCK 状態では relaxation のみ通過させて回復を許可）
    current_ethics = evaluate_ethics_gate(current)
    if current_ethics.status == "BLOCK" and event_type != "relaxation":
        result = {
            "error": "EthicsGate BLOCK",
            "reason": current_ethics.reason,
            "message": "システムは安全のため状態更新を制限しています。'relaxation' イベントで回復できます。",
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    try:
        input_power = event_to_power(event_type, power_scale)
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}, ensure_ascii=False))]

    next_state = compute_next_neuro_state(current, input_power)
    neuro_states[user_id] = next_state
    new_ethics = evaluate_ethics_gate(next_state)

    result = {
        "user_id": user_id,
        "event": event_type,
        "power_scale": power_scale,
        "neuro_state": next_state.to_dict(),
        "ethics_gate": {
            "status": new_ethics.status,
            "reason": new_ethics.reason,
        },
    }
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _handle_diagnose_dependence(args: dict[str, Any]) -> list[TextContent]:
    user_id = args.get("user_id", "default")
    raw_signals = args.get("signals", {})

    signals = Signals(
        E=float(raw_signals.get("E", 0.0)),
        K=float(raw_signals.get("K", 0.0)),
        A=float(raw_signals.get("A", 0.0)),
        S=float(raw_signals.get("S", 0.0)),
        R=float(raw_signals.get("R", 0.0)),
        F=float(raw_signals.get("F", 0.0)),
    )

    neuro = _get_state(user_id)
    diagnosis = diagnose_dependence(signals, neuro)

    result = {
        "user_id": user_id,
        "diagnosis": diagnosis.to_dict(),
    }
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _handle_clear_corruption(args: dict[str, Any]) -> list[TextContent]:
    user_id = args.get("user_id", "default")
    state = _get_state(user_id)
    neuro_states[user_id] = NeuroState(
        D=state.D, S=state.S, C=state.C,
        O=state.O, G=state.G, E=state.E,
        corruption=0.0,
    )
    return [TextContent(type="text", text=f"ユーザー '{user_id}' の corruption をクリアしました。（他の値は保持）")]


def _handle_reset_neuro_state(args: dict[str, Any]) -> list[TextContent]:
    user_id = args.get("user_id", "default")
    neuro_states[user_id] = NeuroState(
        D=INITIAL_STATE.D,
        S=INITIAL_STATE.S,
        C=INITIAL_STATE.C,
        O=INITIAL_STATE.O,
        G=INITIAL_STATE.G,
        E=INITIAL_STATE.E,
        corruption=INITIAL_STATE.corruption,
    )
    return [TextContent(type="text", text=f"ユーザー '{user_id}' の NeuroState をリセットしました。")]


def _handle_generate_system_prompt(args: dict[str, Any]) -> list[TextContent]:
    user_id = args.get("user_id", "default")
    persona_name = args.get("persona_name", "AI")
    persona_description = args.get(
        "persona_description",
        "ユーザーの思考を拡張する自律型アシスタント。"
    )
    blocks = args.get("blocks", ["neuro"])

    state = _get_state(user_id)
    prompt = build_system_prompt(
        state=state,
        persona_name=persona_name,
        persona_description=persona_description,
        blocks=blocks,
    )

    result = {
        "user_id": user_id,
        "blocks_enabled": blocks,
        "system_prompt": prompt,
    }
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def run_server() -> None:
    """MCP サーバーを起動する。"""
    server = Server("neurostate-engine")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOL_DEFINITIONS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        handlers = {
            "get_neuro_state": _handle_get_neuro_state,
            "stimulate_neuro_state": _handle_stimulate_neuro_state,
            "diagnose_dependence_type": _handle_diagnose_dependence,
            "clear_corruption": _handle_clear_corruption,
            "reset_neuro_state": _handle_reset_neuro_state,
            "generate_system_prompt": _handle_generate_system_prompt,
        }

        if name not in handlers:
            raise ValueError(f"未知のツール: {name}")

        return handlers[name](arguments)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
