"""
Per-user adaptation: risk tolerance, style, and personalization of ensemble outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class UserTradingProfile:
    user_id: str
    risk_tolerance: float = 0.5  # 0 conservative ... 1 aggressive
    style: str = "balanced"  # balanced | income | growth | speculative
    max_drawdown_tolerance: float = 0.15
    horizon_days: int = 30
    preferences: Dict[str, Any] = field(default_factory=dict)


def profile_from_dict(data: Optional[Dict[str, Any]]) -> UserTradingProfile:
    if not data:
        return UserTradingProfile(user_id="anonymous")
    uid = str(data.get("user_id") or data.get("id") or "anonymous")
    try:
        rt = float(data.get("risk_tolerance", 0.5))
    except (TypeError, ValueError):
        rt = 0.5
    rt = max(0.0, min(1.0, rt))
    style = str(data.get("style", "balanced") or "balanced")
    try:
        mdd = float(data.get("max_drawdown_tolerance", 0.15))
    except (TypeError, ValueError):
        mdd = 0.15
    try:
        horizon = int(data.get("horizon_days", 30))
    except (TypeError, ValueError):
        horizon = 30
    return UserTradingProfile(
        user_id=uid,
        risk_tolerance=rt,
        style=style,
        max_drawdown_tolerance=mdd,
        horizon_days=max(1, horizon),
        preferences={k: v for k, v in data.items() if k not in ("user_id", "id")},
    )


def adapt_signal(
    raw: Dict[str, Any],
    profile: UserTradingProfile,
    *,
    debate_action: Optional[str] = None,
) -> Dict[str, Any]:
    """Scale confidence and bias action toward user risk profile."""
    conf = float(raw.get("confidence", 0.5) or 0.5)
    direction = str(raw.get("direction", "neutral"))

    # Conservative users dampen confidence and avoid aggressive 'buy' on marginal cases
    conf_adapted = conf * (0.65 + 0.35 * profile.risk_tolerance)
    if profile.style == "income":
        conf_adapted *= 0.9
    if profile.style == "speculative":
        conf_adapted = min(0.99, conf_adapted * 1.08)

    action = debate_action or raw.get("suggested_action", "hold")
    if profile.risk_tolerance < 0.35 and action == "buy" and conf_adapted < 0.55:
        action = "hold"

    return {
        "user_id": profile.user_id,
        "adapted_confidence": round(conf_adapted, 4),
        "direction": direction,
        "suggested_action": action,
        "rationale": "Adjusted for risk_tolerance and style; conservative profiles require higher conviction.",
    }
