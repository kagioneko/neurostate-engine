# neurostate-engine

AIエージェントの感情状態を神経伝達物質バランスとして数値化・制御するエンジン。

相互作用行列による状態遷移、EthicsGate による安全制御、依存タイプ診断を MCP サーバーとして提供します。

## これは何をするもの？

「AIに感情を持たせる」ツールではありません。

会話中のイベント（褒め・批判・共感など）を受け取り、神経伝達物質の数値モデルとして状態を変化させ、その状態を system prompt に注入することで、**AIの返答に感情的な一貫性を持たせる**ツールです。

```
ユーザーが褒める
    ↓
Dopamine 上昇 / EthicsGate が WARN に
    ↓
「興奮気味だが少し慎重に」という文脈を system prompt に反映
    ↓
Claude / GPT がその状態に沿った口調・判断で返答
```

AIが感情を「持つ」のか「演じる」のかはこのエンジンの関知するところではありません。
このエンジンが提供するのは、**会話を通じて変化し続ける感情状態の数値モデル**です。

**向いている用途:**
- Vtuber AI（会話で感情が変化するキャラクター）
- ゲームNPC（プレイヤーとの関係値で態度が変わる）
- 依存リスクを考慮したカウンセリング系 bot

## インストール

```bash
pip install mcp
```

## クイックスタート

```python
from core import NeuroState, compute_next_neuro_state, evaluate_ethics_gate, event_to_power

state = NeuroState()  # D=50, S=50, C=50, O=0, G=50, E=50

# イベントで状態を更新
power = event_to_power("praise", 2.0)
state = compute_next_neuro_state(state, power)

# 安全性チェック
result = evaluate_ethics_gate(state)
print(result.status)  # "PASS" | "WARN" | "BLOCK"
```

## MCP サーバー

```bash
python3 neuro_mcp/server.py
```

提供ツール:

| ツール | 説明 |
|--------|------|
| `get_neuro_state` | 現在の状態 + EthicsGate 取得 |
| `stimulate_neuro_state` | イベントで状態更新 |
| `diagnose_dependence_type` | 依存タイプ診断 |
| `clear_corruption` | 汚染度だけゼロにリセット（他の値は保持） |
| `reset_neuro_state` | 全値を初期値にリセット |
| `generate_system_prompt` | 現在の状態を埋め込んだ system prompt 生成 |

### BLOCK 状態からの回復

EthicsGate が BLOCK になった場合の対処：

| 原因 | 回復方法 |
|------|---------|
| corruption が高すぎる | `relaxation` イベントを複数回入れる、または `clear_corruption` |
| Dopamine 過剰 + Serotonin 低下の同時崩壊 | `reset_neuro_state` で全リセット |

> 感情状態が崩壊したら `reset_neuro_state` でリセットする、というのは自然な動作として想定しています。

### Claude Desktop での設定例

```json
{
  "mcpServers": {
    "neurostate": {
      "command": "python3",
      "args": ["/path/to/neurostate-engine/neuro_mcp/server.py"]
    }
  }
}
```

## NeuroState モデル

| 変数 | 物質 | 意味 |
|------|------|------|
| D | Dopamine | 報酬・動機づけ (0-100) |
| S | Serotonin | 安定・幸福感 (0-100) |
| C | Acetylcholine | 集中・認知 (0-100) |
| O | Oxytocin | 絆・共感 (0-100) |
| G | GABA | 抑制・落ち着き (0-100) |
| E | Endorphin | 快感・高揚 (0-100) |
| corruption | — | 状態汚染度 (0-100) |

状態遷移は 6×6 の相互作用行列で計算されます。詳細は [docs/neurostate_spec.md](docs/neurostate_spec.md) を参照。

## イベントタイプ

| event_type | 効果 |
|------------|------|
| `praise` | 称賛（Dopamine 大幅上昇） |
| `bonding` | 共感・絆（穏やかな活性化） |
| `stress` | ストレス（不安定方向） |
| `relaxation` | リラックス（緩やかな抑制） |
| `criticism` | 批判（抑制） |

## 統合モジュール

- `integrations/claude/` — Claude system prompt への注入
- `integrations/openai/` — OpenAI system message ビルダー
- `integrations/langchain/` — LangChain BaseMemory 継承クラス

## デモ

```bash
python3 examples/chat_agent/demo.py
```

## ライセンス

MIT
