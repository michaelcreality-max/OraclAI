"""
Background polling of near–real-time quotes (yfinance).
Refreshes watched symbols on a fixed interval (default 25s, configurable 20–30s).

Note: Yahoo Finance data is delayed / aggregated; this is not exchange tick data.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


def _interval_seconds() -> float:
    raw = os.environ.get("MARKET_REFRESH_SECONDS", "25")
    try:
        v = float(raw)
    except ValueError:
        v = 25.0
    return max(20.0, min(45.0, v))


def _max_watched() -> int:
    try:
        return max(10, int(os.environ.get("MAX_WATCHED_SYMBOLS", "200")))
    except ValueError:
        return 200


class RealtimeMarketStore:
    """Thread-safe cache of latest quotes; background thread refreshes on an interval."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._watched: Set[str] = set()
        self._quotes: Dict[str, Dict[str, Any]] = {}
        self._last_refresh: Dict[str, float] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._started = False

    def start_background_poller(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            self._stop.clear()
            self._thread = threading.Thread(target=self._poll_loop, name="market-poller", daemon=True)
            self._thread.start()
            log.info(
                "Market poller started (interval=%ss, max_symbols=%s)",
                _interval_seconds(),
                _max_watched(),
            )

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    def watch(self, symbol: str) -> None:
        sym = str(symbol).upper().strip()
        if not sym:
            return
        with self._lock:
            if len(self._watched) >= _max_watched() and sym not in self._watched:
                return
            self._watched.add(sym)

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        sym = str(symbol).upper().strip()
        with self._lock:
            return dict(self._quotes[sym]) if sym in self._quotes else None

    def ensure_fresh(self, symbol: str) -> Dict[str, Any]:
        """Register symbol and return a quote at most ~one interval old (fetch now if missing/stale)."""
        sym = str(symbol).upper().strip()
        self.watch(sym)
        interval = _interval_seconds()
        with self._lock:
            age = time.time() - self._last_refresh.get(sym, 0)
            cached = self._quotes.get(sym)
        if cached and age < interval:
            return dict(cached)
        try:
            q = self._fetch_quote(sym)
            with self._lock:
                self._quotes[sym] = q
                self._last_refresh[sym] = time.time()
            return dict(q)
        except Exception as e:
            log.warning("ensure_fresh failed for %s: %s", sym, e)
            return dict(cached) if cached else {"symbol": sym, "error": str(e)}

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "poller_running": self._started and self._thread is not None and self._thread.is_alive(),
                "refresh_interval_seconds": _interval_seconds(),
                "watched_symbols_count": len(self._watched),
                "cached_symbols_count": len(self._quotes),
            }

    def _poll_loop(self) -> None:
        interval = _interval_seconds()
        while not self._stop.is_set():
            symbols: List[str]
            with self._lock:
                symbols = list(self._watched)
            for sym in symbols:
                if self._stop.is_set():
                    break
                try:
                    q = self._fetch_quote(sym)
                    with self._lock:
                        self._quotes[sym] = q
                        self._last_refresh[sym] = time.time()
                except Exception as e:
                    log.debug("Quote fetch failed for %s: %s", sym, e)
            if self._stop.wait(timeout=interval):
                break

    def _fetch_quote(self, symbol: str) -> Dict[str, Any]:
        t = yf.Ticker(symbol)
        last_price: Optional[float] = None
        volume: Optional[float] = None
        data_as_of: Optional[str] = None

        try:
            fi = t.fast_info
            for key in ("last_price", "regular_market_price", "last_market_price"):
                v = None
                if isinstance(fi, dict):
                    v = fi.get(key)
                else:
                    v = getattr(fi, key, None)
                if v is not None:
                    last_price = float(v)
                    break
        except Exception:
            pass

        try:
            intra = t.history(period="1d", interval="1m", auto_adjust=True)
            if intra is not None and len(intra) > 0:
                row = intra.iloc[-1]
                last_price = float(row["Close"])
                volume = float(row["Volume"]) if "Volume" in row else volume
                ts = intra.index[-1]
                if hasattr(ts, "isoformat"):
                    data_as_of = ts.isoformat()
                else:
                    data_as_of = str(ts)
        except Exception:
            pass

        if last_price is None:
            try:
                d1 = t.history(period="5d", interval="5m", auto_adjust=True)
                if d1 is not None and len(d1) > 0:
                    row = d1.iloc[-1]
                    last_price = float(row["Close"])
                    volume = float(row["Volume"]) if volume is None and "Volume" in row else volume
                    ts = d1.index[-1]
                    data_as_of = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            except Exception:
                pass

        prev_close: Optional[float] = None
        try:
            fi = t.fast_info
            if hasattr(fi, "previous_close"):
                prev_close = getattr(fi, "previous_close", None)
            elif isinstance(fi, dict):
                prev_close = fi.get("previous_close")
            if prev_close is not None:
                prev_close = float(prev_close)
        except Exception:
            pass

        change_pct: Optional[float] = None
        if last_price is not None and prev_close:
            try:
                change_pct = (last_price - float(prev_close)) / float(prev_close) * 100.0
            except (TypeError, ValueError, ZeroDivisionError):
                pass

        now = datetime.now(timezone.utc).isoformat()
        return {
            "symbol": symbol,
            "last_price": last_price,
            "previous_close": float(prev_close) if prev_close is not None else None,
            "change_percent": round(change_pct, 4) if change_pct is not None else None,
            "volume": volume,
            "data_as_of": data_as_of or now,
            "fetched_at": now,
            "source": "yfinance",
            "refresh_interval_seconds": _interval_seconds(),
        }


_store: Optional[RealtimeMarketStore] = None
_store_lock = threading.Lock()


def get_market_store() -> RealtimeMarketStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = RealtimeMarketStore()
        return _store


def _poller_disabled() -> bool:
    return os.environ.get("DISABLE_MARKET_POLLER", "").strip().lower() in ("1", "true", "yes")


def start_market_poller() -> None:
    if _poller_disabled():
        log.info("Market poller disabled (DISABLE_MARKET_POLLER is set)")
        return
    get_market_store().start_background_poller()


def apply_quote_to_history(hist: pd.DataFrame, quote: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Patch the latest daily bar with the most recent polled price/volume."""
    if hist is None or len(hist) == 0 or not quote:
        return hist
    lp = quote.get("last_price")
    if lp is None:
        return hist
    try:
        lp = float(lp)
    except (TypeError, ValueError):
        return hist
    out = hist.copy()
    i = out.index[-1]
    out.loc[i, "Close"] = lp
    vol = quote.get("volume")
    if vol is not None:
        try:
            v = float(vol)
            if not pd.isna(out.loc[i, "Volume"]):
                out.loc[i, "Volume"] = max(v, float(out.loc[i, "Volume"]))
            else:
                out.loc[i, "Volume"] = v
        except (TypeError, ValueError):
            pass
    return out
