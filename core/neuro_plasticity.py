"""
AI-Neuro-Plasticity エンジン

経験（会話・イベント）を通じて、AIが自身の「相互作用行列」と
「均衡点」を緩やかに自己調整する仕組み。

狙い:
  - 褒められ続けるとセロトニンが出やすくなる（楽観的な性格に）
  - ストレスが続くとドーパミンが暴走しやすく・GABAが弱くなる（神経質な性格に）
  - リラックス環境が多いとGABAが安定（落ち着いた性格に）

設計思想:
  - デフォルト行列（MATRIX_A）はコードで固定のまま
  - 経験による「オフセット」だけを JSON プロファイルに保存する
  - ユーザーごとに独立したプロファイルを持つ
  - 変化は微小（学習率 0.002/event）かつ上限あり（±0.3）で暴走しない
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

from core.interaction_matrix import (
    MATRIX_A,
    EXTERNAL_FORCE_COEFFS,
    clamp,
    sigmoid,
)
from core.update_engine import _EQUILIBRIUM

# ─── 保存先 ──────────────────────────────────────────────────────────────────

_PLASTICITY_DIR = Path(__file__).parent.parent / "storage" / "plasticity"


def _profile_path(user_id: str) -> Path:
    _PLASTICITY_DIR.mkdir(parents=True, exist_ok=True)
    return _PLASTICITY_DIR / f"{user_id}.json"


# ─── 可塑性ルール ──────────────────────────────────────────────────────────────
# インデックス: D=0, S=1, C=2, O=3, G=4, E=5
# matrix_deltas: {(row, col): delta_per_event}  → MATRIX_A[row][col] に加算
# force_deltas:  {idx: delta_per_event}          → EXTERNAL_FORCE_COEFFS[idx] に加算
# equil_deltas:  {idx: delta_per_event}          → _EQUILIBRIUM[idx] に加算

PLASTICITY_RULES: dict[str, dict] = {
    "praise": {
        # 褒められると: セロトニン自己維持↑・オキシトシン感受性↑・均衡点上昇
        "description": "褒められ続けると楽観的・安定した性格になる",
        "matrix_deltas": {(1, 1): 0.002, (1, 3): 0.001},
        "force_deltas":  {1: 0.004},
        "equil_deltas":  {1: 0.08, 3: 0.04},
    },
    "stress": {
        # ストレスが続くと: ドーパミン暴走しやすく・GABA弱体化・均衡点が不安定方向へ
        "description": "ストレス過多で衝動的・神経質な性格になる",
        "matrix_deltas": {(0, 0): 0.002, (4, 4): -0.001, (0, 4): -0.001},
        "force_deltas":  {0: 0.003, 4: -0.002},
        "equil_deltas":  {0: 0.08, 4: -0.06, 1: -0.04},
    },
    "bonding": {
        # 絆・共感が続くと: オキシトシン自己維持↑・セロトニン連動↑
        "description": "絆を積み重ねると共感力が高まり温かい性格になる",
        "matrix_deltas": {(3, 3): 0.002, (3, 1): 0.001, (1, 3): 0.001},
        "force_deltas":  {3: 0.003},
        "equil_deltas":  {3: 0.08, 1: 0.04},
    },
    "criticism": {
        # 批判が続くと: 防御的（GABA↑）かつドーパミン反応性↑（闘争反応）
        "description": "批判が続くと防御的・反発しやすい性格になる",
        "matrix_deltas": {(4, 4): 0.001, (0, 0): 0.001, (3, 3): -0.001},
        "force_deltas":  {0: 0.002, 4: 0.001},
        "equil_deltas":  {0: 0.05, 3: -0.04},
    },
    "relaxation": {
        # リラックスが続くと: GABAが安定・均衡点が穏やかな方向へ
        "description": "穏やかな環境が続くと落ち着いた・忍耐強い性格になる",
        "matrix_deltas": {(4, 4): 0.002, (4, 1): 0.001, (1, 1): 0.001},
        "force_deltas":  {4: -0.003},
        "equil_deltas":  {4: 0.08, 1: 0.05, 0: -0.04},
    },
}

# オフセットの上下限（デフォルト値からの最大ずれ）
_MATRIX_OFFSET_LIMIT = 0.30
_FORCE_OFFSET_LIMIT  = 0.40
_EQUIL_OFFSET_LIMIT  = 15.0


# ─── プロファイル ─────────────────────────────────────────────────────────────

@dataclass
class PlasticityProfile:
    """
    ユーザーの経験に基づく可塑性プロファイル。

    デフォルト値からのオフセットを累積して保持する。
    実際の行列は「デフォルト + オフセット」で算出される。
    """
    user_id: str
    event_counts: dict[str, int] = field(default_factory=dict)
    matrix_offsets: list[list[float]] = field(
        default_factory=lambda: [[0.0]*6 for _ in range(6)]
    )
    force_offsets: list[float] = field(default_factory=lambda: [0.0]*6)
    equil_offsets: list[float] = field(default_factory=lambda: [0.0]*6)

    # ─── 派生プロパティ ───────────────────────────────────────

    def effective_matrix(self) -> list[list[float]]:
        """デフォルト行列 + オフセットを返す"""
        result = copy.deepcopy(MATRIX_A)
        for i in range(6):
            for j in range(6):
                result[i][j] = clamp(
                    result[i][j] + self.matrix_offsets[i][j],
                    min_val=-1.0, max_val=1.0
                )
        return result

    def effective_force_coeffs(self) -> list[float]:
        """デフォルト外部刺激係数 + オフセットを返す"""
        return [
            clamp(EXTERNAL_FORCE_COEFFS[i] + self.force_offsets[i],
                  min_val=-2.0, max_val=2.0)
            for i in range(6)
        ]

    def effective_equilibrium(self) -> list[float]:
        """デフォルト均衡点 + オフセットを返す"""
        return [
            clamp(_EQUILIBRIUM[i] + self.equil_offsets[i])
            for i in range(6)
        ]

    def total_events(self) -> int:
        return sum(self.event_counts.values())

    def personality_summary(self) -> str:
        """蓄積された傾向を人間が読める文字列で返す"""
        counts = self.event_counts
        parts = []
        if counts.get("praise", 0) >= 10:
            parts.append(f"楽観的（褒め ×{counts['praise']}）")
        if counts.get("stress", 0) >= 10:
            parts.append(f"神経質（ストレス ×{counts['stress']}）")
        if counts.get("bonding", 0) >= 10:
            parts.append(f"共感的（絆 ×{counts['bonding']}）")
        if counts.get("criticism", 0) >= 10:
            parts.append(f"防御的（批判 ×{counts['criticism']}）")
        if counts.get("relaxation", 0) >= 10:
            parts.append(f"温和（リラックス ×{counts['relaxation']}）")
        return "、".join(parts) if parts else "まだ初期状態（経験不足）"

    # ─── 永続化 ──────────────────────────────────────────────

    def save(self) -> None:
        data = {
            "user_id": self.user_id,
            "event_counts": self.event_counts,
            "matrix_offsets": self.matrix_offsets,
            "force_offsets": self.force_offsets,
            "equil_offsets": self.equil_offsets,
        }
        _profile_path(self.user_id).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(cls, user_id: str) -> "PlasticityProfile":
        path = _profile_path(user_id)
        if not path.exists():
            return cls(user_id=user_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            user_id=data["user_id"],
            event_counts=data.get("event_counts", {}),
            matrix_offsets=data.get("matrix_offsets", [[0.0]*6 for _ in range(6)]),
            force_offsets=data.get("force_offsets", [0.0]*6),
            equil_offsets=data.get("equil_offsets", [0.0]*6),
        )

    @classmethod
    def reset(cls, user_id: str) -> "PlasticityProfile":
        """プロファイルを初期化して保存する"""
        profile = cls(user_id=user_id)
        profile.save()
        return profile


# ─── 可塑性エンジン ───────────────────────────────────────────────────────────

class PlasticityEngine:
    """
    経験を受け取り PlasticityProfile を更新するエンジン。
    """

    @staticmethod
    def apply_event(
        profile: PlasticityProfile,
        event_type: str,
        count: int = 1,
    ) -> PlasticityProfile:
        """
        イベントを受け取り、プロファイルを更新して返す（イミュータブル）。

        学習率は経験が積み重なるほど小さくなる（可塑性の飽和）。
        初期: 1.0 → 100イベント後: ~0.37 → 500イベント後: ~0.14
        """
        if event_type not in PLASTICITY_RULES:
            return profile

        rule = PLASTICITY_RULES[event_type]
        total = profile.total_events()

        # 新しいオブジェクトを作成（イミュータブル設計）
        new_counts = dict(profile.event_counts)
        new_matrix = copy.deepcopy(profile.matrix_offsets)
        new_force = list(profile.force_offsets)
        new_equil = list(profile.equil_offsets)

        for _ in range(count):
            # 可塑性の飽和: 経験が積むほど変化しにくくなる
            learning_rate = _plasticity_learning_rate(total)
            total += 1

            # 行列オフセット更新
            for (row, col), delta in rule["matrix_deltas"].items():
                new_val = new_matrix[row][col] + delta * learning_rate
                new_matrix[row][col] = max(-_MATRIX_OFFSET_LIMIT,
                                           min(_MATRIX_OFFSET_LIMIT, new_val))

            # 外部刺激係数オフセット更新
            for idx, delta in rule["force_deltas"].items():
                new_val = new_force[idx] + delta * learning_rate
                new_force[idx] = max(-_FORCE_OFFSET_LIMIT,
                                     min(_FORCE_OFFSET_LIMIT, new_val))

            # 均衡点オフセット更新
            for idx, delta in rule["equil_deltas"].items():
                new_val = new_equil[idx] + delta * learning_rate
                new_equil[idx] = max(-_EQUIL_OFFSET_LIMIT,
                                     min(_EQUIL_OFFSET_LIMIT, new_val))

        new_counts[event_type] = new_counts.get(event_type, 0) + count

        return PlasticityProfile(
            user_id=profile.user_id,
            event_counts=new_counts,
            matrix_offsets=new_matrix,
            force_offsets=new_force,
            equil_offsets=new_equil,
        )

    @staticmethod
    def compute_next_state_plastic(
        current_state,
        input_power: float,
        profile: PlasticityProfile,
    ):
        """
        個人化された行列を使って NeuroState を更新する。

        compute_next_neuro_state の可塑性対応版。
        """
        from core.state_model import NeuroState

        matrix = profile.effective_matrix()
        force_coeffs = profile.effective_force_coeffs()
        equilibrium = profile.effective_equilibrium()
        resting_pull = 0.05

        state_vec = [
            current_state.D, current_state.S, current_state.C,
            current_state.O, current_state.G, current_state.E
        ]

        # 1. 行列積（個人化行列使用）
        next_vec = [
            sum(matrix[i][j] * state_vec[j] for j in range(6))
            for i in range(6)
        ]

        # 2. 外部刺激（個人化係数使用）
        next_vec = [next_vec[i] + force_coeffs[i] * input_power for i in range(6)]

        # 3. 個人化均衡点への引き戻し
        next_vec = [
            next_vec[i] + resting_pull * (2.0 if state_vec[i] < 20 else 1.0)
            * (equilibrium[i] - state_vec[i])
            for i in range(6)
        ]

        d, s, c, o, g, e = (clamp(v) for v in next_vec)

        # 4. Corruption 更新（標準ロジックと同様）
        corruption_delta = 0.0
        if d > 90:
            corruption_delta += 5.0
        if s > 60:
            corruption_delta -= 1.0
        if o > 40:
            corruption_delta -= 1.5
        if g > 50:
            corruption_delta -= 0.5
        if input_power < 0:
            corruption_delta += input_power * 3.0

        new_corruption = clamp(current_state.corruption + corruption_delta)
        return NeuroState(D=d, S=s, C=c, O=o, G=g, E=e, corruption=new_corruption)


# ─── 内部ヘルパー ─────────────────────────────────────────────────────────────

def _plasticity_learning_rate(total_events: int) -> float:
    """
    経験が積むほど小さくなる学習率（可塑性の飽和）。
    0イベント → 1.0 / 100イベント → ~0.37 / 500イベント → ~0.14
    """
    import math
    return math.exp(-total_events / 200.0)


# ─── フォーマッター ───────────────────────────────────────────────────────────

NEUROTRANSMITTER_NAMES = ["D(ドーパミン)", "S(セロトニン)", "C(アセチルコリン)",
                           "O(オキシトシン)", "G(GABA)", "E(エンドルフィン)"]


def format_plasticity_report(profile: PlasticityProfile) -> str:
    """プロファイルを人間が読める Markdown レポートで返す"""
    effective_eq = profile.effective_equilibrium()

    lines = [
        "## AI-Neuro-Plasticity プロファイルレポート",
        "",
        f"**ユーザー**: `{profile.user_id}`",
        f"**総経験イベント数**: {profile.total_events()} 件",
        f"**性格傾向**: {profile.personality_summary()}",
        "",
        "### 経験イベント内訳",
        "",
        "| イベント | 回数 | 効果 |",
        "|---------|------|------|",
    ]
    for event, rule in PLASTICITY_RULES.items():
        count = profile.event_counts.get(event, 0)
        lines.append(f"| {event} | {count} | {rule['description']} |")

    lines += [
        "",
        "### 個人化均衡点（デフォルト vs 現在）",
        "",
        "| 物質 | デフォルト | 現在 | 変化 |",
        "|------|-----------|------|------|",
    ]
    for i, name in enumerate(NEUROTRANSMITTER_NAMES):
        default = _EQUILIBRIUM[i]
        current = effective_eq[i]
        delta = current - default
        arrow = "↑" if delta > 0.5 else ("↓" if delta < -0.5 else "→")
        lines.append(f"| {name} | {default:.1f} | {current:.2f} | {arrow} {delta:+.2f} |")

    lines += [
        "",
        "### 最も変化した相互作用係数（Top 5）",
        "",
    ]
    offsets_flat = [
        (abs(profile.matrix_offsets[i][j]), i, j, profile.matrix_offsets[i][j])
        for i in range(6) for j in range(6)
        if abs(profile.matrix_offsets[i][j]) > 0.001
    ]
    offsets_flat.sort(reverse=True)
    if offsets_flat:
        for _, i, j, val in offsets_flat[:5]:
            ni, nj = NEUROTRANSMITTER_NAMES[i][:10], NEUROTRANSMITTER_NAMES[j][:10]
            lines.append(f"- `A[{ni} ← {nj}]`: {val:+.4f}")
    else:
        lines.append("- まだ変化なし（経験不足）")

    return "\n".join(lines)
