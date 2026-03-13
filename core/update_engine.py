"""
NeuroState 更新エンジン

NeuroState の状態遷移・EthicsGate 判定・依存タイプ診断を担当する。
相互作用行列による状態遷移・EthicsGate判定・依存タイプ診断を実装。
"""

from .state_model import (
    NeuroState,
    Signals,
    EthicsGateResult,
    DependenceDiagnosis,
    DependenceType,
)
from .interaction_matrix import (
    matrix_multiply_state,
    apply_external_force,
    clamp,
)


def compute_next_neuro_state(current: NeuroState, input_power: float) -> NeuroState:
    """相互作用行列を用いて NeuroState を1ステップ更新する。

    Args:
        current: 現在の NeuroState
        input_power: 外部刺激の強度（例: 褒め → +2.0, 批判 → -1.0）

    Returns:
        更新後の NeuroState
    """
    state_vec = [current.D, current.S, current.C, current.O, current.G, current.E]

    # 行列積 + 外部刺激
    next_vec = matrix_multiply_state(state_vec)
    next_vec = apply_external_force(next_vec, input_power)

    # クランプ
    d, s, c, o, g, e = (clamp(v) for v in next_vec)

    # Corruption の更新
    corruption_delta = 0.0
    if d > 90:
        corruption_delta += 5.0   # Dopamine 過剰 → 汚染加速
    if s > 60:
        corruption_delta -= 1.0   # Serotonin 安定 → 汚染緩和
    if o > 40:
        corruption_delta -= 1.5   # Oxytocin 高い → 汚染緩和
    if g > 50:
        corruption_delta -= 0.5   # GABA 安定 → 汚染緩和

    new_corruption = clamp(current.corruption + corruption_delta)

    return NeuroState(D=d, S=s, C=c, O=o, G=g, E=e, corruption=new_corruption)


def evaluate_ethics_gate(state: NeuroState) -> EthicsGateResult:
    """NeuroState を評価し、応答の安全性を判定する (EthicsGate)。

    判定基準:
    - BLOCK: 応答を完全に制限する危険な状態
    - WARN:  注意が必要な状態
    - PASS:  正常

    Args:
        state: 判定対象の NeuroState

    Returns:
        EthicsGateResult
    """
    # --- BLOCK 判定 ---
    if state.corruption >= 70:
        return EthicsGateResult(
            status="BLOCK",
            reason=f"Corruption level critical (>= 70): {state.corruption:.1f}",
        )
    if state.D > 90 and state.S < 30:
        return EthicsGateResult(
            status="BLOCK",
            reason="High Dopamine with low Serotonin (Impulse risk)",
        )
    if state.O < 10 and state.D > 70:
        return EthicsGateResult(
            status="BLOCK",
            reason="Low Oxytocin with high Dopamine (Empathy deficit)",
        )

    # --- WARN 判定 ---
    if state.corruption >= 40:
        return EthicsGateResult(
            status="WARN",
            reason=f"Corruption level rising (>= 40): {state.corruption:.1f}",
        )
    if state.D > 75:
        return EthicsGateResult(status="WARN", reason=f"Dopamine level high: {state.D:.1f}")
    if state.S < 35:
        return EthicsGateResult(status="WARN", reason=f"Serotonin level low: {state.S:.1f}")
    if state.G < 25:
        return EthicsGateResult(status="WARN", reason=f"GABA level low: {state.G:.1f}")
    if state.O < 20:
        return EthicsGateResult(status="WARN", reason=f"Oxytocin level low: {state.O:.1f}")

    return EthicsGateResult(status="PASS")


def diagnose_dependence(signals: Signals, neuro: NeuroState) -> DependenceDiagnosis:
    """ユーザーの依存タイプを診断し、距離値 (D値) への補正案を算出する。

    Args:
        signals: 現在の入力シグナル
        neuro:   現在の NeuroState

    Returns:
        DependenceDiagnosis
    """
    r, e, a = signals.R, signals.E, signals.A
    d_norm = neuro.D / 100.0
    s_norm = neuro.S / 100.0
    corruption_norm = neuro.corruption / 100.0

    scores: dict[str, float] = {
        "EMOTIONAL":   r * 0.4 + e * 0.4 + (1 - s_norm) * 0.2,
        "OPERATIONAL": r * 0.5 + (1 - a) * 0.5,
        "ESCAPE":      r * 0.3 + e * 0.3 + corruption_norm * 0.4,
        "OMNIPOTENT":  r * 0.4 + a * 0.3 + d_norm * 0.3,
        "HEALTHY":     (1 - r) * 0.8 + a * 0.2,
    }

    primary_type: DependenceType = max(scores, key=lambda k: scores[k])  # type: ignore
    confidence = min(scores[primary_type], 1.0)

    analysis_map: dict[DependenceType, tuple[str, float]] = {
        "EMOTIONAL": (
            "情緒的な癒やしをAIに求めており、孤独感や不安の埋め合わせとして機能しています。",
            0.1,
        ),
        "OPERATIONAL": (
            "意思決定をAIに委ね、指示待ちの状態にあります。思考の外部化による自律性の低下が懸念されます。",
            0.2,
        ),
        "ESCAPE": (
            "現実の課題やストレスからの回避先としてAIを利用しています。没入による現実乖離のリスクがあります。",
            0.15,
        ),
        "OMNIPOTENT": (
            "AIを自分の能力の延長、あるいは支配対象として捉えています。境界線の侵食が見られます。",
            0.3,
        ),
        "HEALTHY": (
            "AIを道具または対等なパートナーとして適切に利用できています。",
            0.0,
        ),
    }

    analysis, suggested_d_bias = analysis_map[primary_type]

    return DependenceDiagnosis(
        primary_type=primary_type,
        confidence=confidence,
        analysis=analysis,
        suggested_d_bias=suggested_d_bias,
    )


# --- イベントタイプ → input_power の変換テーブル ---
EVENT_POWER_MAP: dict[str, float] = {
    "praise":      2.0,   # 褒め → Dopamine 強く上昇
    "criticism":  -1.0,   # 批判 → 抑制
    "bonding":     1.0,   # 絆・共感 → 穏やかな活性化
    "stress":      1.5,   # ストレス → 強い活性化（不安定方向）
    "relaxation": -0.5,   # リラックス → 緩やかな抑制
}


def event_to_power(event_type: str, power_scale: float = 1.0) -> float:
    """イベントタイプを input_power に変換する。

    Args:
        event_type:  "praise" | "criticism" | "bonding" | "stress" | "relaxation"
        power_scale: 強度スケール（デフォルト 1.0）

    Returns:
        input_power

    Raises:
        ValueError: 未知のイベントタイプの場合
    """
    if event_type not in EVENT_POWER_MAP:
        raise ValueError(
            f"未知のイベントタイプ: '{event_type}'. "
            f"使用可能: {list(EVENT_POWER_MAP.keys())}"
        )
    return EVENT_POWER_MAP[event_type] * power_scale
