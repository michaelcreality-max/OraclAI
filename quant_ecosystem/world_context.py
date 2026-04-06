"""
Continuous learning from the world: economic / earnings / headline hooks (extensible).
Fetches real news from RSS feeds, Yahoo Finance, and other free sources.
"""

from __future__ import annotations

import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional


def fetch_yahoo_finance_news(symbol: str) -> Dict[str, Any]:
    """Fetch real news from Yahoo Finance (free, no API key needed)"""
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news[:10] if ticker.news else []
        
        headlines = []
        for article in news:
            if article.get('title'):
                headlines.append({
                    'title': article.get('title'),
                    'publisher': article.get('publisher', 'Unknown'),
                    'published': article.get('published', ''),
                    'link': article.get('link', ''),
                    'summary': article.get('summary', '')[:150] + '...' if article.get('summary') else ''
                })
        
        # Estimate sentiment from headlines (simple keyword approach)
        sentiment = estimate_sentiment([h['title'] for h in headlines])
        
        return {
            'symbol': symbol.upper().strip(),
            'headlines': headlines,
            'sentiment_estimate': sentiment,
            'source': 'yahoo_finance',
            'count': len(headlines),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'symbol': symbol.upper().strip(),
            'headlines': [],
            'sentiment_estimate': 0.0,
            'source': 'yahoo_finance',
            'error': str(e),
            'count': 0
        }


def estimate_sentiment(headlines: List[str]) -> float:
    """
    Simple sentiment estimation based on keyword matching.
    Returns score between -1.0 (negative) and 1.0 (positive)
    """
    positive_words = [
        'surge', 'soar', 'jump', 'rally', 'gain', 'profit', 'beat', 'strong',
        'growth', 'boom', 'record', 'high', 'bull', 'buy', 'upgrade', 'outperform'
    ]
    negative_words = [
        'drop', 'fall', 'plunge', 'crash', 'loss', 'miss', 'weak', 'decline',
        'bear', 'sell', 'downgrade', 'underperform', 'concern', 'risk', 'lawsuit'
    ]
    
    if not headlines:
        return 0.0
    
    text = ' '.join(headlines).lower()
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    # Normalize score
    raw_score = (pos_count - neg_count) / max(len(headlines), 1)
    return max(-1.0, min(1.0, raw_score))


def fetch_headline_stub(symbol: str) -> Dict[str, Any]:
    """DEPRECATED: Use fetch_yahoo_finance_news instead for real data."""
    return fetch_yahoo_finance_news(symbol)


def fetch_rss_titles(url: str, limit: int = 8) -> List[str]:
    """Fetch headlines from RSS feed"""
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
    """Get comprehensive world context for a symbol including real news"""
    sym = symbol.upper().strip()
    rss = os.environ.get("WORLD_RSS_URL", "").strip()
    
    # Get real news from Yahoo Finance
    news_data = fetch_yahoo_finance_news(sym)
    
    out: Dict[str, Any] = {
        "symbol": sym,
        "news": news_data,
        "sentiment": {
            "score": news_data['sentiment_estimate'],
            "interpretation": interpret_sentiment(news_data['sentiment_estimate']),
            "based_on": f"{news_data['count']} headlines"
        },
        "macro_events": [
            {"type": "placeholder", "description": "Wire FRED / calendar API for CPI, FOMC, NFP."},
        ],
        "earnings_nlp": {
            "status": "not_configured",
            "hint": "Transcribe earnings calls and run sentiment + factor tagging offline.",
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Add RSS headlines if configured
    if rss:
        rss_titles = fetch_rss_titles(rss)
        out["rss_headlines"] = rss_titles
        out["rss_source"] = rss
    
    return out


def interpret_sentiment(score: float) -> str:
    """Convert numeric sentiment to human-readable label"""
    if score > 0.3:
        return "Bullish"
    elif score > 0.1:
        return "Slightly Bullish"
    elif score < -0.3:
        return "Bearish"
    elif score < -0.1:
        return "Slightly Bearish"
    else:
        return "Neutral"
