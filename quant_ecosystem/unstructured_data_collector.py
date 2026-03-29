"""
Unstructured Data Collection
Gathers news, SEC filings, social media, analyst reports, and other unstructured data
"""

from __future__ import annotations

import logging
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import yfinance as yf
import re

log = logging.getLogger(__name__)


@dataclass
class UnstructuredDataBundle:
    """Collection of all unstructured data for a stock"""
    symbol: str
    collected_at: str
    
    # News and Media
    news_headlines: List[Dict[str, Any]] = field(default_factory=list)
    news_sentiment: str = "neutral"
    news_summary: str = ""
    
    # SEC Filings
    sec_filings: List[Dict[str, Any]] = field(default_factory=list)
    recent_10k: Optional[Dict[str, Any]] = None
    recent_10q: Optional[Dict[str, Any]] = None
    recent_8k: List[Dict[str, Any]] = field(default_factory=list)
    insider_trades: List[Dict[str, Any]] = field(default_factory=list)
    
    # Analyst Data
    analyst_ratings: List[Dict[str, Any]] = field(default_factory=list)
    price_targets: Dict[str, Any] = field(default_factory=dict)
    earnings_estimates: Dict[str, Any] = field(default_factory=dict)
    
    # Social Media
    social_sentiment: Dict[str, Any] = field(default_factory=dict)
    trending_posts: List[Dict[str, Any]] = field(default_factory=list)
    reddit_mentions: int = 0
    twitter_mentions: int = 0
    
    # Market Narrative
    market_stories: List[str] = field(default_factory=list)
    sector_themes: List[str] = field(default_factory=list)
    macro_factors: List[str] = field(default_factory=list)
    
    # Management & Corporate
    earnings_call_transcript: Optional[str] = None
    management_guidance: Optional[str] = None
    recent_presentations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Competitive Landscape
    competitor_news: List[Dict[str, Any]] = field(default_factory=list)
    industry_trends: List[str] = field(default_factory=list)


class UnstructuredDataCollector:
    """
    Collects unstructured data from multiple sources:
    - News APIs and RSS feeds
    - SEC EDGAR database
    - Social media (Reddit, Twitter/X, StockTwits)
    - Analyst reports
    - Earnings transcripts
    - Corporate presentations
    """
    
    def __init__(self):
        self.cache: Dict[str, UnstructuredDataBundle] = {}
        self.cache_ttl = timedelta(minutes=15)
        
    def collect_all_unstructured_data(self, symbol: str) -> UnstructuredDataBundle:
        """Collect all unstructured data for a stock"""
        log.info(f"Collecting unstructured data for {symbol}")
        
        # Check cache
        if symbol in self.cache:
            cached = self.cache[symbol]
            cached_time = datetime.fromisoformat(cached.collected_at)
            if datetime.now() - cached_time < self.cache_ttl:
                log.info(f"Using cached unstructured data for {symbol}")
                return cached
        
        bundle = UnstructuredDataBundle(
            symbol=symbol,
            collected_at=datetime.now().isoformat()
        )
        
        # Collect from all sources
        try:
            self._collect_news_data(symbol, bundle)
        except Exception as e:
            log.error(f"News collection error for {symbol}: {e}")
        
        try:
            self._collect_sec_filings(symbol, bundle)
        except Exception as e:
            log.error(f"SEC filings error for {symbol}: {e}")
        
        try:
            self._collect_analyst_data(symbol, bundle)
        except Exception as e:
            log.error(f"Analyst data error for {symbol}: {e}")
        
        try:
            self._collect_social_sentiment(symbol, bundle)
        except Exception as e:
            log.error(f"Social sentiment error for {symbol}: {e}")
        
        try:
            self._collect_market_narrative(symbol, bundle)
        except Exception as e:
            log.error(f"Market narrative error for {symbol}: {e}")
        
        try:
            self._collect_competitive_intel(symbol, bundle)
        except Exception as e:
            log.error(f"Competitive intel error for {symbol}: {e}")
        
        # Cache the result
        self.cache[symbol] = bundle
        
        log.info(f"Unstructured data collection complete for {symbol}")
        return bundle
    
    def _collect_news_data(self, symbol: str, bundle: UnstructuredDataBundle):
        """Collect news headlines and articles"""
        log.info(f"Collecting news for {symbol}")
        
        try:
            # Get news from Yahoo Finance
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if news:
                headlines = []
                for item in news[:20]:  # Top 20 news items
                    headline = {
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'published': item.get('published', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('link', ''),
                        'sentiment': self._estimate_sentiment(item.get('title', ''))
                    }
                    headlines.append(headline)
                
                bundle.news_headlines = headlines
                
                # Calculate overall news sentiment
                sentiments = [h['sentiment'] for h in headlines]
                positive = sentiments.count('positive')
                negative = sentiments.count('negative')
                
                if positive > negative * 1.5:
                    bundle.news_sentiment = 'positive'
                elif negative > positive * 1.5:
                    bundle.news_sentiment = 'negative'
                else:
                    bundle.news_sentiment = 'neutral'
                
                # Generate summary
                bundle.news_summary = self._generate_news_summary(headlines)
                
        except Exception as e:
            log.warning(f"Could not fetch news from Yahoo Finance: {e}")
    
    def _estimate_sentiment(self, text: str) -> str:
        """Estimate sentiment of text using keyword analysis"""
        text_lower = text.lower()
        
        positive_keywords = ['surge', 'jump', 'rise', 'gain', 'bull', 'growth', 'beat', 'record', 'soar', 'rally', 'outperform', 'upgrade']
        negative_keywords = ['fall', 'drop', 'decline', 'bear', 'loss', 'miss', 'crash', 'plunge', 'tumble', 'underperform', 'downgrade', 'cut']
        
        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def _generate_news_summary(self, headlines: List[Dict[str, Any]]) -> str:
        """Generate a summary of recent news"""
        if not headlines:
            return "No recent news available"
        
        publishers = set(h.get('publisher', '') for h in headlines)
        topics = []
        
        # Extract common themes
        all_text = ' '.join(h.get('title', '') for h in headlines).lower()
        
        if 'earnings' in all_text:
            topics.append('earnings')
        if 'revenue' in all_text or 'sales' in all_text:
            topics.append('revenue')
        if 'guidance' in all_text or 'forecast' in all_text:
            topics.append('guidance')
        if 'analyst' in all_text or 'upgrade' in all_text or 'downgrade' in all_text:
            topics.append('analyst ratings')
        if 'product' in all_text or 'launch' in all_text:
            topics.append('product news')
        if 'acquisition' in all_text or 'merger' in all_text:
            topics.append('M&A activity')
        if 'layoff' in all_text or 'restructuring' in all_text:
            topics.append('workforce changes')
        
        summary = f"{len(headlines)} recent articles from {len(publishers)} sources. "
        if topics:
            summary += f"Key themes: {', '.join(topics)}. "
        
        return summary
    
    def _collect_sec_filings(self, symbol: str, bundle: UnstructuredDataBundle):
        """Collect SEC filing information"""
        log.info(f"Collecting SEC filings for {symbol}")
        
        try:
            # Use SEC EDGAR API (public, no key needed)
            cik = self._get_cik(symbol)
            if cik:
                base_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&output=xml"
                
                # Note: SEC requires user-agent header
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                try:
                    response = requests.get(base_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Parse recent filings
                        filings = self._parse_sec_filings(response.text)
                        bundle.sec_filings = filings[:10]  # Last 10 filings
                        
                        # Find specific forms
                        for filing in filings:
                            form_type = filing.get('form', '')
                            if form_type == '10-K' and not bundle.recent_10k:
                                bundle.recent_10k = filing
                            elif form_type == '10-Q' and not bundle.recent_10q:
                                bundle.recent_10q = filing
                            elif form_type == '8-K':
                                bundle.recent_8k.append(filing)
                        
                        # Get insider trading from Form 4
                        form4_filings = [f for f in filings if f.get('form') == '4']
                        bundle.insider_trades = self._parse_insider_trades(form4_filings[:5])
                        
                except Exception as e:
                    log.warning(f"SEC EDGAR fetch failed: {e}")
        
        except Exception as e:
            log.warning(f"SEC collection error: {e}")
    
    def _get_cik(self, symbol: str) -> Optional[str]:
        """Get CIK number for a ticker symbol"""
        try:
            # Use ticker.info from yfinance which sometimes has CIK
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('cik', None)
        except:
            return None
    
    def _parse_sec_filings(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse SEC filing data from XML"""
        filings = []
        # Basic parsing - would need proper XML parser for production
        # This is a simplified version
        return filings
    
    def _parse_insider_trades(self, form4_list: List[Dict]) -> List[Dict[str, Any]]:
        """Parse Form 4 insider trading data"""
        trades = []
        for form in form4_list:
            trade = {
                'filing_date': form.get('filing_date'),
                'transaction_date': form.get('transaction_date'),
                'owner': form.get('owner', 'Unknown'),
                'transaction_type': form.get('transaction_type', 'Unknown'),
                'shares': form.get('shares', 0),
                'price': form.get('price', 0)
            }
            trades.append(trade)
        return trades
    
    def _collect_analyst_data(self, symbol: str, bundle: UnstructuredDataBundle):
        """Collect analyst ratings and price targets"""
        log.info(f"Collecting analyst data for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Price targets
            bundle.price_targets = {
                'high': info.get('targetHighPrice'),
                'low': info.get('targetLowPrice'),
                'mean': info.get('targetMeanPrice'),
                'median': info.get('targetMedianPrice'),
                'current_price': info.get('currentPrice'),
                'implied_upside': None
            }
            
            # Calculate implied upside
            current = info.get('currentPrice')
            target = info.get('targetMeanPrice')
            if current and target and current > 0:
                bundle.price_targets['implied_upside'] = (target - current) / current
            
            # Analyst ratings
            recommendation_key = info.get('recommendationKey', 'hold')
            num_analysts = info.get('numberOfAnalystOpinions', 0)
            
            bundle.analyst_ratings = [{
                'consensus': recommendation_key,
                'num_analysts': num_analysts,
                'source': 'Yahoo Finance'
            }]
            
            # Get recommendations trend if available
            try:
                recs = ticker.recommendations
                if recs is not None and not recs.empty:
                    latest = recs.iloc[-1]
                    bundle.earnings_estimates = {
                        'strong_buy': latest.get('strongBuy', 0),
                        'buy': latest.get('buy', 0),
                        'hold': latest.get('hold', 0),
                        'sell': latest.get('sell', 0),
                        'strong_sell': latest.get('strongSell', 0)
                    }
            except:
                pass
                
        except Exception as e:
            log.warning(f"Analyst data collection failed: {e}")
    
    def _collect_social_sentiment(self, symbol: str, bundle: UnstructuredDataBundle):
        """Collect social media sentiment"""
        log.info(f"Collecting social sentiment for {symbol}")
        
        # Reddit mentions (placeholder - would need Reddit API)
        try:
            # Would use PRAW or similar Reddit API
            # For now, provide estimated data structure
            bundle.social_sentiment = {
                'reddit': {
                    'mentions_24h': 0,  # Would be actual count
                    'sentiment': 'neutral',
                    'top_subreddits': ['wallstreetbets', 'stocks', 'investing']
                },
                'twitter': {
                    'mentions_24h': 0,
                    'sentiment': 'neutral',
                    'trending_hashtags': []
                },
                'stocktwits': {
                    'bullish_percentage': 50,
                    'bearish_percentage': 50,
                    'watchlist_count': 0
                }
            }
            
            bundle.reddit_mentions = 0  # Would be actual count
            bundle.twitter_mentions = 0  # Would be actual count
            
        except Exception as e:
            log.warning(f"Social sentiment collection failed: {e}")
    
    def _collect_market_narrative(self, symbol: str, bundle: UnstructuredDataBundle):
        """Collect market narratives and themes"""
        log.info(f"Collecting market narrative for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            business_summary = info.get('longBusinessSummary', '')
            
            # Generate sector themes
            themes = []
            if sector == 'Technology':
                themes = ['AI/ML', 'Cloud Computing', 'Digital Transformation', 'Cybersecurity']
            elif sector == 'Healthcare':
                themes = ['Precision Medicine', 'Telehealth', 'Aging Population', 'Drug Innovation']
            elif sector == 'Energy':
                themes = ['Energy Transition', 'Renewables', 'Grid Modernization', 'Carbon Reduction']
            elif sector == 'Financial Services':
                themes = ['Fintech Innovation', 'Digital Banking', 'Blockchain', 'Regulatory Changes']
            elif sector == 'Consumer Cyclical':
                themes = ['E-commerce Growth', 'Consumer Spending', 'Inflation Impact', 'Supply Chain']
            
            bundle.sector_themes = themes
            
            # Extract key phrases from business summary
            if business_summary:
                sentences = business_summary.split('.')[:3]
                bundle.market_stories = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            # Macro factors
            macro = []
            beta = info.get('beta', 1.0)
            if beta > 1.5:
                macro.append('High market sensitivity (volatile)')
            elif beta < 0.8:
                macro.append('Defensive characteristics (low beta)')
            
            if info.get('dividendYield'):
                macro.append('Dividend-paying stock')
            
            bundle.macro_factors = macro
            
        except Exception as e:
            log.warning(f"Market narrative collection failed: {e}")
    
    def _collect_competitive_intel(self, symbol: str, bundle: UnstructuredDataBundle):
        """Collect competitive intelligence"""
        log.info(f"Collecting competitive intel for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            
            # Industry trends based on sector
            trends = []
            if sector == 'Technology':
                trends = ['AI adoption accelerating', 'Cloud migration continuing', 'Semiconductor demand cyclical']
            elif sector == 'Healthcare':
                trends = ['Value-based care transition', 'Genomics breakthroughs', 'Generic competition intensifying']
            elif sector == 'Energy':
                trends = ['Renewable energy growth', 'Oil price volatility', 'Regulatory pressure increasing']
            
            bundle.industry_trends = trends
            
            # Would fetch competitor data here
            bundle.competitor_news = []
            
        except Exception as e:
            log.warning(f"Competitive intel collection failed: {e}")
    
    def get_summary(self, symbol: str) -> str:
        """Generate a text summary of all unstructured data"""
        bundle = self.collect_all_unstructured_data(symbol)
        
        parts = []
        parts.append(f"=== UNSTRUCTURED DATA SUMMARY FOR {symbol} ===\n")
        
        # News
        parts.append(f"📰 NEWS ({len(bundle.news_headlines)} articles, sentiment: {bundle.news_sentiment})")
        parts.append(f"   {bundle.news_summary}\n")
        
        # Analysts
        if bundle.price_targets.get('mean'):
            parts.append(f"📊 ANALYST TARGETS: ${bundle.price_targets['mean']:.2f} " +
                        f"({'+' if bundle.price_targets.get('implied_upside', 0) > 0 else ''}" +
                        f"{bundle.price_targets.get('implied_upside', 0)*100:.1f}% implied upside)\n")
        
        # SEC Filings
        if bundle.recent_8k:
            parts.append(f"📄 RECENT 8-K FILINGS: {len(bundle.recent_8k)} material events\n")
        
        # Insider
        if bundle.insider_trades:
            buys = sum(1 for t in bundle.insider_trades if 'buy' in t.get('transaction_type', '').lower())
            sells = sum(1 for t in bundle.insider_trades if 'sell' in t.get('transaction_type', '').lower())
            parts.append(f"👤 INSIDER ACTIVITY: {buys} buys, {sells} sells\n")
        
        # Social
        parts.append(f"💬 SOCIAL MENTIONS: {bundle.reddit_mentions + bundle.twitter_mentions} total\n")
        
        # Themes
        if bundle.sector_themes:
            parts.append(f"🏷️ KEY THEMES: {', '.join(bundle.sector_themes[:3])}\n")
        
        return '\n'.join(parts)


# Global collector instance
unstructured_data_collector = UnstructuredDataCollector()
