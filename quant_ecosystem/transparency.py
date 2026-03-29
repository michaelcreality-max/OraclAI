"""
Transparency / trust engine: model history, mistakes, confidence decay logging.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional


@dataclass
class TransparencyEvent:
    ts: str
    kind: str
    symbol: str
    detail: Dict[str, Any]


class TransparencyLedger:
    """In-memory ring buffer for API deployments (swap for DB in production)."""

    def __init__(self, max_events: int = 500):
        self._events: Deque[TransparencyEvent] = deque(maxlen=max_events)
        self._model_scores: Dict[str, List[Dict[str, Any]]] = {}

    def log(
        self,
        *,
        kind: str,
        symbol: str,
        detail: Dict[str, Any],
        ts: Optional[str] = None,
    ) -> None:
        event = TransparencyEvent(
            ts=ts or datetime.utcnow().isoformat() + "Z",
            kind=kind,
            symbol=symbol.upper().strip(),
            detail=detail,
        )
        self._events.append(event)

    def record_model_score(self, model_id: str, score: float, meta: Optional[Dict[str, Any]] = None) -> None:
        self._model_scores.setdefault(model_id, []).append(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
                "score": score,
                "meta": meta or {},
            }
        )

    def confidence_decay(
        self,
        model_id: str,
        *,
        halflife_events: int = 10,
    ) -> Optional[float]:
        hist = self._model_scores.get(model_id)
        if not hist:
            return None
        w = 0.0
        tw = 0.0
        for i, row in enumerate(reversed(hist[-halflife_events:])):
            weight = 0.5 ** (i / max(1, halflife_events / 2))
            w += weight * float(row["score"])
            tw += weight
        return float(w / tw) if tw else None

    def recent(self, *, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        items = list(self._events)
        if symbol:
            items = [e for e in items if e.symbol.upper() == symbol.upper()]
        items = items[-limit:]
        return [
            {"ts": e.ts, "kind": e.kind, "symbol": e.symbol, "detail": e.detail}
            for e in reversed(items)
        ]


# Process-global ledger for Flask (single worker); use external store for multi-worker
_GLOBAL_LEDGER = TransparencyLedger()


def get_ledger() -> TransparencyLedger:
    return _GLOBAL_LEDGER
