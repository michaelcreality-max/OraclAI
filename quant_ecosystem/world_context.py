"""
Continuous learning from the world: economic / earnings / headline hooks (extensible).
Without paid data feeds, we expose structure + optional RSS or manual headlines.
"""

from __future__ import annotations

import os
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional


def fetch_headline_stub(symbol: str) -> Dict[str, Any]:
    """Placeholder narrative when no feed configured."""
    return {
        "symbol": symbol.upper().strip(),
        "headlines": [],
        "sentiment_estimate": 0.0,
        "source": "none",
        "note": "Set WORLD_RSS_URL or integrate your news API for live headlines.",
    }


def fetch_rss_titles(url: str, limit: int = 8) -> List[str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "quant-ecosystem/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        titles = []
        for item in root.iter():
            if item.tag.endswith("item"):
                for ch in item:
                    if ch.tag.endswith("title") and ch.text:
                        titles.append(ch.text.strip())
                        break
            if len(titles) >= limit:
                break
        return titles[:limit]
    except Exception as e:
        return [f"(rss_error: {e})"]


def world_context(symbol: str) -> Dict[str, Any]:
    sym = symbol.upper().strip()
    rss = os.environ.get("WORLD_RSS_URL", "").strip()
    out: Dict[str, Any] = {
        "symbol": sym,
        "macro_events": [
            {"type": "placeholder", "description": "Wire FRED / calendar API for CPI, FOMC, NFP."},
        ],
        "earnings_nlp": {
            "status": "not_configured",
            "hint": "Transcribe earnings calls and run sentiment + factor tagging offline.",
        },
    }
    if rss:
        out["headlines"] = fetch_rss_titles(rss)
        out["headline_source"] = rss
    else:
        h = fetch_headline_stub(sym)
        out["headlines"] = h["headlines"]
        out["headline_source"] = h["source"]
    return out
