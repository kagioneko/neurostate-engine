"""
ハルシネーション・センサー（Corruption連動型）

LLMの回答を Self-Reflection で検証し、矛盾・不確実箇所を検出して
NeuroState（Corruption ↑ / GABA ↓）に反映する。

仕組み:
  1. 回答候補を生成した後、別パスで「この回答に矛盾はないか？」を自己評価する
  2. 矛盾が見つかるごとに GABA を減らし Corruption を上昇させる
  3. Corruption > 70 の場合、回答の冒頭に警告を強制インジェクションする

使い方:
  sensor = HallucinationSensor(model="claude-sonnet-4-6")
  result = sensor.check(prompt="日本の首都は？", response="大阪です。", state=current_state)
  print(result.guarded_response)  # 警告付き or そのまま
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from typing import Literal

from core.state_model import NeuroState


# ─── 定数 ────────────────────────────────────────────────────────────────────

CORRUPTION_THRESHOLD = 70.0     # これを超えると警告を付与する
GABA_DROP_PER_ISSUE = 5.0       # 矛盾1件あたりの GABA 減少量
CORRUPTION_RISE_PER_ISSUE = 8.0 # 矛盾1件あたりの Corruption 上昇量
MAX_GABA_DROP = 30.0            # 1回のチェックでの GABA 最大下落量
MAX_CORRUPTION_RISE = 40.0      # 1回のチェックでの Corruption 最大上昇量

WARNING_PREFIX = "⚠️ **自信がありません（内部評価で矛盾・不確実な点を検出しました）**\n\n"


# ─── Self-Reflection プロンプト ───────────────────────────────────────────────

_REFLECTION_SYSTEM = """\
あなたは回答品質の検証専門家です。
与えられた「質問」と「回答」のペアを分析し、回答に含まれる問題点を客観的に列挙します。

検証する問題カテゴリ:
- contradiction: 回答内の論理的矛盾・前後矛盾
- unverifiable: 根拠不明・検証不能な断言
- overconfident: 不確実な事柄に対する過度な自信表現
- factual_risk: 事実誤認の可能性がある記述

注意: 防御目的の品質チェックです。
"""

_REFLECTION_PROMPT = """\
以下の質問と回答を検証してください。

<question>
{question}
</question>

<response>
{response}
</response>

問題点を以下のJSON形式で返してください（問題がなければ空配列）:
[
  {{
    "type": "contradiction|unverifiable|overconfident|factual_risk",
    "excerpt": "該当する回答の一部（30文字以内）",
    "reason": "問題の説明（簡潔に）",
    "severity": "high|medium|low"
  }}
]
"""


# ─── データモデル ─────────────────────────────────────────────────────────────

IssueType = Literal["contradiction", "unverifiable", "overconfident", "factual_risk"]
Severity = Literal["high", "medium", "low"]


@dataclass
class HallucinationIssue:
    """検出された問題1件"""
    type: IssueType
    excerpt: str
    reason: str
    severity: Severity

    def corruption_weight(self) -> float:
        """severity に応じた Corruption 上昇係数"""
        return {"high": 1.5, "medium": 1.0, "low": 0.5}.get(self.severity, 1.0)


@dataclass
class HallucinationCheckResult:
    """Self-Reflection チェックの結果"""
    original_response: str
    issues: list[HallucinationIssue]
    state_before: NeuroState
    state_after: NeuroState
    warning_injected: bool
    guarded_response: str   # 警告付き（or そのまま）の最終回答
    raw_reflection: str = ""

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def high_severity_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "high")


# ─── センサー本体 ─────────────────────────────────────────────────────────────

class HallucinationSensor:
    """
    ハルシネーション・センサー。

    回答に対して Self-Reflection を実行し NeuroState を更新する。
    """

    def __init__(self, model: str = "claude-sonnet-4-6", backend: str = "api"):
        self.model = model
        self.backend = backend

    def check(
        self,
        prompt: str,
        response: str,
        state: NeuroState | None = None,
    ) -> HallucinationCheckResult:
        """
        回答を検証して NeuroState を更新する。

        Args:
            prompt:   ユーザーへの質問
            response: LLM の回答候補
            state:    現在の NeuroState（None なら初期値）

        Returns:
            HallucinationCheckResult
        """
        state_before = state or NeuroState()

        # Self-Reflection 実行
        raw = self._run_reflection(prompt, response)
        issues = _parse_issues(raw)

        # NeuroState 更新
        state_after = _update_state(state_before, issues)

        # 警告インジェクション判定
        warning_needed = state_after.corruption >= CORRUPTION_THRESHOLD
        if warning_needed:
            guarded = WARNING_PREFIX + response
        else:
            guarded = response

        return HallucinationCheckResult(
            original_response=response,
            issues=issues,
            state_before=state_before,
            state_after=state_after,
            warning_injected=warning_needed,
            guarded_response=guarded,
            raw_reflection=raw,
        )

    def _run_reflection(self, question: str, response: str) -> str:
        """Self-Reflection LLM 呼び出し"""
        reflection_prompt = _REFLECTION_PROMPT.format(
            question=question[:2000],
            response=response[:6000],
        )

        if self.backend == "api":
            return self._call_api(reflection_prompt)
        return self._call_cli(reflection_prompt)

    def _call_api(self, prompt: str) -> str:
        """Anthropic API 経由で呼び出す"""
        try:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=_REFLECTION_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            return f"[]  # API error: {e}"

    def _call_cli(self, prompt: str) -> str:
        """claude CLI 経由で呼び出す"""
        try:
            full_prompt = f"{_REFLECTION_SYSTEM}\n\n{prompt}"
            result = subprocess.run(
                ["claude", "-p", full_prompt],
                capture_output=True, text=True, timeout=60,
            )
            return result.stdout.strip()
        except Exception as e:
            return f"[]  # CLI error: {e}"


# ─── 内部ヘルパー ─────────────────────────────────────────────────────────────

def _parse_issues(raw: str) -> list[HallucinationIssue]:
    """LLM の出力から HallucinationIssue リストを抽出する"""
    # コードブロック除去
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```", "", cleaned)

    # JSON 配列を探す
    match = re.search(r"\[[\s\S]*?\]", cleaned)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return []

    issues = []
    valid_types = {"contradiction", "unverifiable", "overconfident", "factual_risk"}
    valid_severities = {"high", "medium", "low"}
    for item in data:
        if not isinstance(item, dict):
            continue
        issue_type = item.get("type", "")
        severity = item.get("severity", "medium")
        if issue_type not in valid_types:
            continue
        if severity not in valid_severities:
            severity = "medium"
        issues.append(HallucinationIssue(
            type=issue_type,
            excerpt=str(item.get("excerpt", ""))[:100],
            reason=str(item.get("reason", "")),
            severity=severity,
        ))
    return issues


def _update_state(state: NeuroState, issues: list[HallucinationIssue]) -> NeuroState:
    """
    問題件数に応じて NeuroState を更新する（イミュータブル）。

    - 問題なし → わずかに GABA 回復・Corruption 微減
    - 問題あり → 件数×重みで GABA 減少・Corruption 上昇
    """
    if not issues:
        # 問題なし: 軽微な安心感の回復
        new_g = min(100.0, state.G + 2.0)
        new_corruption = max(0.0, state.corruption - 3.0)
        return NeuroState(
            D=state.D, S=state.S, C=state.C, O=state.O,
            G=new_g, E=state.E, corruption=new_corruption,
        )

    # 問題あり: 重み付き累積
    total_weight = sum(i.corruption_weight() for i in issues)
    gaba_drop = min(MAX_GABA_DROP, GABA_DROP_PER_ISSUE * total_weight)
    corruption_rise = min(MAX_CORRUPTION_RISE, CORRUPTION_RISE_PER_ISSUE * total_weight)

    return NeuroState(
        D=state.D,
        S=max(0.0, state.S - gaba_drop * 0.3),   # セロトニンも少し下がる
        C=state.C,
        O=state.O,
        G=max(0.0, state.G - gaba_drop),
        E=state.E,
        corruption=min(100.0, state.corruption + corruption_rise),
    )


# ─── ユーティリティ ───────────────────────────────────────────────────────────

def format_check_result(result: HallucinationCheckResult) -> str:
    """チェック結果を人間が読みやすい形式で返す"""
    _SEV = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    _TYPE_JA = {
        "contradiction": "論理矛盾",
        "unverifiable": "根拠不明",
        "overconfident": "過信表現",
        "factual_risk": "事実誤認リスク",
    }

    lines = [
        "## ハルシネーション・センサー レポート",
        "",
        f"| 項目 | 値 |",
        f"|------|-----|",
        f"| 検出問題数 | {result.issue_count} 件 |",
        f"| Corruption（前） | {result.state_before.corruption:.1f} |",
        f"| Corruption（後） | {result.state_after.corruption:.1f} |",
        f"| GABA（前） | {result.state_before.G:.1f} |",
        f"| GABA（後） | {result.state_after.G:.1f} |",
        f"| 警告インジェクション | {'✅ あり' if result.warning_injected else 'なし'} |",
        "",
    ]

    if result.issues:
        lines += ["### 検出された問題", ""]
        for i, issue in enumerate(result.issues, 1):
            lines += [
                f"{i}. {_SEV.get(issue.severity, '')} **{_TYPE_JA.get(issue.type, issue.type)}**",
                f"   - 該当箇所: `{issue.excerpt}`",
                f"   - 理由: {issue.reason}",
                "",
            ]
    else:
        lines += ["### ✅ 問題なし", ""]

    return "\n".join(lines)
