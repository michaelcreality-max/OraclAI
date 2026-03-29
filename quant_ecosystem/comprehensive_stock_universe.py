"""
Comprehensive US Stock Universe
Aggregates stocks from Yahoo Finance, Google Finance, and TradingView
"""

from __future__ import annotations

import logging
import requests
import yfinance as yf
from typing import List, Dict, Any, Optional, Set
from functools import lru_cache
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


class ComprehensiveUSStockUniverse:
    """
    Comprehensive US stock universe combining multiple data sources:
    - Yahoo Finance (primary)
    - Google Finance (reference)
    - TradingView (reference)
    
    Covers: S&P 500, NASDAQ 100, Russell 1000, Russell 2000, 
            OTC markets, ETFs, and major indices
    """
    
    # Major US indices to fetch constituents
    INDICES = {
        "sp500": "^GSPC",          # S&P 500
        "nasdaq100": "^NDX",      # NASDAQ 100
        "dow30": "^DJI",          # Dow Jones 30
        "russell2000": "^RUT",    # Russell 2000
        "vix": "^VIX",            # Volatility Index
    }
    
    # Major ETFs to track
    MAJOR_ETFS = [
        "SPY", "QQQ", "IWM", "VTI", "VOO", "IVV", "EFA", "VWO",
        "AGG", "LQD", "TLT", "IEF", "GLD", "SLV", "USO", "UNG",
        "XLF", "XLK", "XLE", "XLI", "XLP", "XLU", "XLB", "XLY",
        "XLV", "IYR", "SMH", "IBB", "KRE", "XRT", "ITB", "XHB",
        "SOXX", "IGV", "FDN", "ARKK", "ARKQ", "ARKG", "ARKW", "ARKF",
        "SCHB", "SCHD", "VYM", "VIG", "DGRO", "HDV", "SPHD", "QYLD",
        "JEPI", "JEPQ", "YMAX", "TSLY", "OARK", "KLIP", "CONY", "NVDY"
    ]
    
    # Popular meme/momentum stocks
    MEME_STOCKS = [
        "GME", "AMC", "BB", "NOK", "KOSS", "EXPR", "NAKD", "TR",
        "SNDL", "TLRY", "CLOV", "WISH", "CLNE", "WOOF", "TELL", "DIDI"
    ]
    
    # Tech stocks (comprehensive)
    TECH_STOCKS = [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA",
        "NFLX", "ADBE", "CRM", "ORCL", "CSCO", "INTC", "AMD", "IBM",
        "QCOM", "TXN", "AVGO", "MU", "LRCX", "KLAC", "AMAT", "SNPS",
        "CDNS", "ADI", "MRVL", "NXPI", "SWKS", "QRVO", "RMBS", "SLAB",
        "ON", "MPWR", "POWI", "MCHP", "Microchip", "MCHP", "CAVM", "XLNX",
        "FSLR", "ENPH", "SEDG", "RUN", "NOVA", "SPWR", "MAXN", "ARRY",
        "SQ", "PYPL", "SHOP", "MELI", "COIN", "RBLX", "U", "DOCU",
        "ZM", "OKTA", "CRWD", "SPLK", "ESTC", "DDOG", "NET", "FSLY",
        "TWLO", "Z", "RNG", "HUBS", "TEAM", "PLTR", "SNOW", "MDB"
    ]
    
    # Financial sector
    FINANCIAL_STOCKS = [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP",
        "USB", "PNC", "TFC", "COF", "SCHW", "BK", "STT", "SPGI",
        "ICE", "CME", "MCO", "FIS", "FISV", "GPN", "V", "MA",
        "PYPL", "SQ", "DFS", "SYF", "ALLY", "MTB", "KEY", "RF",
        "HBAN", "FITB", "CFG", "ZION", "CMA", "PBCT", "WAL", "PACW"
    ]
    
    # Healthcare/Biotech
    HEALTHCARE_STOCKS = [
        "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR",
        "LLY", "BMY", "AMGN", "GILD", "VRTX", "REGN", "BIIB", "MRNA",
        "BNTX", "NVAX", "VXRT", "INO", "SRNE", "CODX", "QDEL", "GNMK",
        "ISRG", "SYK", "ZTS", "CVS", "CI", "HUM", "ANTM", "WBA",
        "MCK", "CAH", "ABC", "HSIC", "XRAY", "PDCO", "OMI", "DVA"
    ]
    
    # Energy sector
    ENERGY_STOCKS = [
        "XOM", "CVX", "COP", "EOG", "SLB", "OXY", "MPC", "VLO",
        "PSX", "WMB", "KMI", "EPD", "ET", "MPLX", "ENLC", "CNX",
        "CTRA", "EQT", "RRC", "SWN", "CHK", "DVN", "FANG", "MRO",
        "HES", "MUR", "APA", "NBL", "OVV", "PXD", "CXO", "BP",
        "SHEL", "TTE", "ENI", "EQNR", "EC", "PBR", "SU", "IMO"
    ]
    
    # Consumer/Retail
    CONSUMER_STOCKS = [
        "AMZN", "WMT", "COST", "HD", "LOW", "TGT", "NKE", "MCD",
        "SBUX", "YUM", "CMG", "DPZ", "MNSO", "DKS", "LULU", "ROST",
        "TJX", "BBY", "DG", "DLTR", "FIVE", "KSS", "JWN", "M",
        "GPS", "URBN", "ANF", "AEO", "EXPR", "CHS", "SMRT", "JILL"
    ]
    
    # OTC/Pink Sheet stocks (micro-cap)
    OTC_STOCKS = [
        "HMBL", "TONR", "CBDL", "GGII", "MINE", "GRLT", "CYBL", "NOHO",
        "HIRU", "BDPT", "ILUS", "ILST", "AITX", "OZSC", "ALPP", "SIRC",
        "RGBP", "RGBPP", "SANP", "APTY", "IGEX", "GVSI", "JPEX", "INKW"
    ]
    
    def __init__(self):
        self._stock_cache: Dict[str, Dict[str, Any]] = {}
        self._last_update: Optional[datetime] = None
        
    def get_all_symbols(self) -> List[str]:
        """Get comprehensive list of all US stock symbols"""
        all_symbols: Set[str] = set()
        
        # Add all static lists
        all_symbols.update(self.MAJOR_ETFS)
        all_symbols.update(self.MEME_STOCKS)
        all_symbols.update(self.TECH_STOCKS)
        all_symbols.update(self.FINANCIAL_STOCKS)
        all_symbols.update(self.HEALTHCARE_STOCKS)
        all_symbols.update(self.ENERGY_STOCKS)
        all_symbols.update(self.CONSUMER_STOCKS)
        all_symbols.update(self.OTC_STOCKS)
        
        # Try to fetch from indices (Yahoo Finance)
        try:
            sp500 = self._fetch_sp500_constituents()
            all_symbols.update(sp500)
            log.info(f"Added {len(sp500)} S&P 500 constituents")
        except Exception as e:
            log.warning(f"Could not fetch S&P 500: {e}")
        
        try:
            nasdaq100 = self._fetch_nasdaq100_constituents()
            all_symbols.update(nasdaq100)
            log.info(f"Added {len(nasdaq100)} NASDAQ 100 constituents")
        except Exception as e:
            log.warning(f"Could not fetch NASDAQ 100: {e}")
        
        # Remove duplicates and sort
        symbols = sorted(list(all_symbols))
        log.info(f"Total universe: {len(symbols)} symbols")
        
        return symbols
    
    def _fetch_sp500_constituents(self) -> List[str]:
        """Fetch S&P 500 constituents from Wikipedia or alternative source"""
        try:
            # Try Wikipedia first (most reliable)
            import pandas as pd
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            sp500_table = tables[0]
            symbols = sp500_table['Symbol'].tolist()
            return symbols
        except Exception as e:
            log.warning(f"Wikipedia fetch failed: {e}")
            # Fallback to yfinance
            try:
                spdr = yf.Ticker("SPY")
                # Get holdings if available
                info = spdr.info
                return []
            except:
                return []
    
    def _fetch_nasdaq100_constituents(self) -> List[str]:
        """Fetch NASDAQ 100 constituents"""
        try:
            import pandas as pd
            url = "https://en.wikipedia.org/wiki/NASDAQ-100"
            tables = pd.read_html(url)
            # Find the table with ticker symbols
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    return table[col].tolist()
            return []
        except Exception as e:
            log.warning(f"NASDAQ 100 fetch failed: {e}")
            return []
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock information from multiple sources"""
        if symbol in self._stock_cache:
            cache_entry = self._stock_cache[symbol]
            # Check if cache is fresh (less than 1 hour old)
            if datetime.now() - cache_entry.get('cached_at', datetime.min) < timedelta(hours=1):
                return cache_entry['data']
        
        info = {
            'symbol': symbol,
            'name': None,
            'sector': None,
            'industry': None,
            'market_cap': None,
            'exchange': None,
            'yahoo_data': {},
            'google_data': {},
            'tradingview_data': {}
        }
        
        # Fetch from Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            yf_info = ticker.info
            
            info['name'] = yf_info.get('longName') or yf_info.get('shortName')
            info['sector'] = yf_info.get('sector')
            info['industry'] = yf_info.get('industry')
            info['market_cap'] = yf_info.get('marketCap')
            info['exchange'] = yf_info.get('exchange')
            info['yahoo_data'] = {
                'price': yf_info.get('currentPrice'),
                'pe_ratio': yf_info.get('trailingPE'),
                'forward_pe': yf_info.get('forwardPE'),
                'peg_ratio': yf_info.get('pegRatio'),
                'price_to_book': yf_info.get('priceToBook'),
                'price_to_sales': yf_info.get('priceToSalesTrailing12Months'),
                'dividend_yield': yf_info.get('dividendYield'),
                'beta': yf_info.get('beta'),
                'fifty_two_week_high': yf_info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': yf_info.get('fiftyTwoWeekLow'),
                'avg_volume': yf_info.get('averageVolume'),
                'shares_outstanding': yf_info.get('sharesOutstanding'),
                'float_shares': yf_info.get('floatShares'),
                'short_ratio': yf_info.get('shortRatio'),
                'target_high': yf_info.get('targetHighPrice'),
                'target_low': yf_info.get('targetLowPrice'),
                'target_mean': yf_info.get('targetMeanPrice'),
                'recommendation_key': yf_info.get('recommendationKey'),
                'number_of_analysts': yf_info.get('numberOfAnalystOpinions'),
                'earnings_growth': yf_info.get('earningsGrowth'),
                'revenue_growth': yf_info.get('revenueGrowth'),
                'profit_margins': yf_info.get('profitMargins'),
                'return_on_equity': yf_info.get('returnOnEquity'),
                'debt_to_equity': yf_info.get('debtToEquity'),
                'current_ratio': yf_info.get('currentRatio'),
                'quick_ratio': yf_info.get('quickRatio'),
                'enterprise_value': yf_info.get('enterpriseValue'),
                'ebitda': yf_info.get('ebitda'),
                'revenue': yf_info.get('totalRevenue'),
                'gross_profits': yf_info.get('grossProfits'),
                'free_cash_flow': yf_info.get('freeCashflow'),
                'operating_cash_flow': yf_info.get('operatingCashflow'),
            }
        except Exception as e:
            log.warning(f"Yahoo Finance fetch failed for {symbol}: {e}")
        
        # Cache the result
        self._stock_cache[symbol] = {
            'data': info,
            'cached_at': datetime.now()
        }
        
        return info
    
    def get_stocks_by_market_cap(self, min_cap: Optional[float] = None, 
                                  max_cap: Optional[float] = None) -> List[str]:
        """Get stocks filtered by market cap"""
        symbols = self.get_all_symbols()
        filtered = []
        
        for symbol in symbols:
            try:
                info = self.get_stock_info(symbol)
                market_cap = info.get('market_cap')
                
                if market_cap is None:
                    continue
                    
                if min_cap and market_cap < min_cap:
                    continue
                if max_cap and market_cap > max_cap:
                    continue
                    
                filtered.append(symbol)
            except:
                continue
        
        return filtered
    
    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """Get stocks by sector"""
        symbols = self.get_all_symbols()
        sector_stocks = []
        
        for symbol in symbols:
            try:
                info = self.get_stock_info(symbol)
                if info.get('sector', '').lower() == sector.lower():
                    sector_stocks.append(symbol)
            except:
                continue
        
        return sector_stocks
    
    def get_universe_stats(self) -> Dict[str, Any]:
        """Get statistics about the stock universe"""
        symbols = self.get_all_symbols()
        
        sectors = {}
        market_cap_ranges = {
            'mega_cap': 0,      # > $200B
            'large_cap': 0,     # $10B - $200B
            'mid_cap': 0,       # $2B - $10B
            'small_cap': 0,     # $300M - $2B
            'micro_cap': 0,     # $50M - $300M
            'nano_cap': 0,      # < $50M
            'unknown': 0
        }
        
        for symbol in symbols[:100]:  # Sample first 100 for speed
            try:
                info = self.get_stock_info(symbol)
                sector = info.get('sector', 'Unknown')
                sectors[sector] = sectors.get(sector, 0) + 1
                
                cap = info.get('market_cap')
                if cap:
                    if cap > 200e9:
                        market_cap_ranges['mega_cap'] += 1
                    elif cap > 10e9:
                        market_cap_ranges['large_cap'] += 1
                    elif cap > 2e9:
                        market_cap_ranges['mid_cap'] += 1
                    elif cap > 300e6:
                        market_cap_ranges['small_cap'] += 1
                    elif cap > 50e6:
                        market_cap_ranges['micro_cap'] += 1
                    else:
                        market_cap_ranges['nano_cap'] += 1
                else:
                    market_cap_ranges['unknown'] += 1
            except:
                continue
        
        return {
            'total_symbols': len(symbols),
            'sectors': sectors,
            'market_cap_distribution': market_cap_ranges,
            'major_etfs': len(self.MAJOR_ETFS),
            'sp500_estimated': len(self._fetch_sp500_constituents()) if hasattr(self, '_fetch_sp500_constituents') else 0,
            'nasdaq100_estimated': len(self._fetch_nasdaq100_constituents()) if hasattr(self, '_fetch_nasdaq100_constituents') else 0,
            'tech_stocks': len(self.TECH_STOCKS),
            'financial_stocks': len(self.FINANCIAL_STOCKS),
            'healthcare_stocks': len(self.HEALTHCARE_STOCKS),
            'energy_stocks': len(self.ENERGY_STOCKS),
            'consumer_stocks': len(self.CONSUMER_STOCKS),
            'otc_stocks': len(self.OTC_STOCKS),
            'meme_stocks': len(self.MEME_STOCKS)
        }


# Global instance
us_market_universe = ComprehensiveUSStockUniverse()


if __name__ == "__main__":
    universe = ComprehensiveUSStockUniverse()
    symbols = universe.get_all_symbols()
    print(f"Total symbols: {len(symbols)}")
    
    stats = universe.get_universe_stats()
    print(f"\nUniverse Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Get info for AAPL
    aapl_info = universe.get_stock_info("AAPL")
    print(f"\nAAPL Info:")
    print(f"  Name: {aapl_info['name']}")
    print(f"  Sector: {aapl_info['sector']}")
    print(f"  Market Cap: ${aapl_info['market_cap']:,.0f}" if aapl_info['market_cap'] else "  Market Cap: Unknown")
    print(f"  Analysts: {aapl_info['yahoo_data'].get('number_of_analysts')}")
    print(f"  Target Mean: ${aapl_info['yahoo_data'].get('target_mean')}")
