"""Feature builders: technical, sentiment from real news, cross-asset."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf


def build_feature_matrix(
    ohlcv: pd.DataFrame,
    ref_close: Optional[pd.Series] = None,
    symbol: Optional[str] = None,
) -> pd.DataFrame:
    """
    Build a wide matrix of base features. Columns are used by genetic search
    and model training. Sentiment_* columns now use real news data when symbol is provided.
    """
    df = ohlcv.copy()
    c = df["close"]
    h = df["high"]
    l = df["low"]
    v = df["volume"].replace(0, np.nan)

    out = pd.DataFrame(index=df.index)
    out["ret_1"] = c.pct_change()
    out["ret_5"] = c.pct_change(5)
    out["ret_20"] = c.pct_change(20)
    out["vol_20"] = out["ret_1"].rolling(20).std()
    out["hl_range"] = (h - l) / c.replace(0, np.nan)
    out["rsi_14"] = _rsi(c, 14)
    out["mom_10"] = c / c.shift(10) - 1.0
    out["vol_z"] = (v - v.rolling(20).mean()) / (v.rolling(20).std() + 1e-9)

    if ref_close is not None:
        ref = ref_close.reindex(df.index).ffill()
        out["beta_proxy"] = out["ret_1"].rolling(20).corr(ref.pct_change())
        out["rel_strength"] = c.pct_change(20) - ref.pct_change(20)
    else:
        out["beta_proxy"] = 0.0
        out["rel_strength"] = 0.0

    # Real sentiment from Yahoo Finance news when symbol is provided
    if symbol:
        try:
            sentiment_data = _calculate_news_sentiment(symbol)
            out["sentiment_news"] = sentiment_data.get('score', 0.0)
            out["sentiment_bullish_pct"] = sentiment_data.get('bullish_pct', 50.0) / 100.0
            out["sentiment_articles_analyzed"] = sentiment_data.get('articles', 0)
        except Exception:
            out["sentiment_news"] = 0.0
            out["sentiment_bullish_pct"] = 0.5
            out["sentiment_articles_analyzed"] = 0
    else:
        out["sentiment_news"] = 0.0
        out["sentiment_bullish_pct"] = 0.5
        out["sentiment_articles_analyzed"] = 0
    
    # Social sentiment placeholder (requires social media APIs)
    out["sentiment_social"] = 0.0
    out["sentiment_options"] = 0.0

    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    return out


def _calculate_news_sentiment(symbol: str) -> dict:
    """Calculate sentiment score from Yahoo Finance news articles"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news[:20] if ticker.news else []
        
        if not news:
            return {'score': 0.0, 'bullish_pct': 50.0, 'articles': 0}
        
        # Sentiment keywords
        bullish_words = ['surge', 'soar', 'jump', 'rally', 'gain', 'profit', 'beat', 'strong', 
                        'growth', 'boom', 'bull', 'buy', 'upgrade', 'outperform', 'exceed']
        bearish_words = ['drop', 'fall', 'plunge', 'crash', 'loss', 'miss', 'weak', 'decline',
                        'bear', 'sell', 'downgrade', 'underperform', 'miss', 'cut']
        
        scores = []
        bullish_count = 0
        bearish_count = 0
        
        for article in news:
            title = article.get('title', '').lower()
            
            b_count = sum(1 for w in bullish_words if w in title)
            be_count = sum(1 for w in bearish_words if w in title)
            
            if b_count > be_count:
                scores.append(1.0)
                bullish_count += 1
            elif be_count > b_count:
                scores.append(-1.0)
                bearish_count += 1
            else:
                scores.append(0.0)
        
        # Normalize to -1 to 1 scale
        avg_score = sum(scores) / len(scores) if scores else 0.0
        bullish_pct = (bullish_count / len(news)) * 100 if news else 50.0
        
        return {
            'score': avg_score,
            'bullish_pct': bullish_pct,
            'articles': len(news),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }
        
    except Exception:
        return {'score': 0.0, 'bullish_pct': 50.0, 'articles': 0}


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = avg_gain / (avg_loss + 1e-12)
    return 100.0 - (100.0 / (1.0 + rs))


def apply_feature_mask(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Subset and order columns; raises if unknown column."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Unknown feature columns: {missing}")
    return df[columns].copy()


def make_target_forward_return(
    close: pd.Series,
    horizon: int = 1,
) -> pd.Series:
    """Next-day (or h-day) log return aligned to same index (drop last NaN in training)."""
    return np.log(close.shift(-horizon) / close).rename("target")
