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
    
    # Get real market context data
    macro_events = _get_market_context(sym)
    
    out: Dict[str, Any] = {
        "symbol": sym,
        "news": news_data,
        "sentiment": {
            "score": news_data['sentiment_estimate'],
            "interpretation": interpret_sentiment(news_data['sentiment_estimate']),
            "based_on": f"{news_data['count']} headlines"
        },
        "macro_events": macro_events,
        "earnings_nlp": {
            "status": "available" if news_data.get('earnings_date') else "not_configured",
            "next_earnings": news_data.get('earnings_date', 'N/A'),
            "hint": "Use news-based sentiment as proxy for earnings sentiment"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Add RSS headlines if configured
    if rss:
        rss_titles = fetch_rss_titles(rss)
        out["rss_headlines"] = rss_titles
        out["rss_source"] = rss
    
    return out


def _get_market_context(symbol: str) -> List[Dict[str, Any]]:
    """Get real market context data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        events = []
        
        # Market status
        market_state = info.get('marketState', 'unknown')
        events.append({
            "type": "market_status",
            "state": market_state,
            "exchange": info.get('exchange', 'N/A'),
            "currency": info.get('currency', 'USD')
        })
        
        # Volatility context
        beta = info.get('beta', 1.0)
        volatility_level = "high" if beta > 1.5 else "low" if beta < 0.8 else "normal"
        events.append({
            "type": "volatility_context",
            "beta": beta,
            "level": volatility_level,
            "market_sensitivity": f"{beta:.2f}x market moves"
        })
        
        # Earnings context
        earnings_date = info.get('earningsDate')
        if earnings_date:
            if isinstance(earnings_date, list) and len(earnings_date) > 0:
                next_earnings = earnings_date[0]
            else:
                next_earnings = earnings_date
            events.append({
                "type": "earnings_event",
                "date": str(next_earnings) if next_earnings else "N/A",
                "event": "Upcoming earnings announcement"
            })
        
        # Dividend context
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield and dividend_yield > 0:
            events.append({
                "type": "dividend_context",
                "yield_percent": round(dividend_yield * 100, 2),
                "event": "Dividend-paying stock"
            })
        
        # Price context
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
        
        if current_price and fifty_two_week_high and fifty_two_week_low:
            price_range_pct = ((current_price - fifty_two_week_low) / 
                             (fifty_two_week_high - fifty_two_week_low) * 100) if fifty_two_week_high != fifty_two_week_low else 50
            
            position_desc = "near highs" if price_range_pct > 80 else "near lows" if price_range_pct < 20 else "mid-range"
            
            events.append({
                "type": "price_context",
                "current_price": current_price,
                "52w_range": f"${fifty_two_week_low:.2f} - ${fifty_two_week_high:.2f}",
                "position_in_range": f"{price_range_pct:.1f}% ({position_desc})"
            })
        
        # Analyst consensus
        recommendation = info.get('recommendationKey', 'none')
        if recommendation and recommendation != 'none':
            events.append({
                "type": "analyst_consensus",
                "recommendation": recommendation,
                "target_price": info.get('targetMeanPrice', 'N/A'),
                "num_analysts": info.get('numberOfAnalystOpinions', 'N/A')
            })
        
        return events
        
    except Exception as e:
        return [{"type": "error", "message": f"Could not fetch market context: {e}"}]


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
