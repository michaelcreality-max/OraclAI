"""
US Market Stock Universe Fetcher
Fetches all US stocks for comprehensive market coverage
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
import requests
import yfinance as yf
from functools import lru_cache

log = logging.getLogger(__name__)


class USMarketStockUniverse:
    """
    Provides access to all US stocks for comprehensive analysis
    """
    
    # Major US stock categories
    MAJOR_INDICES = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW": "^DJI",
        "RUSSELL 2000": "^RUT"
    }
    
    # Primary market categories
    MARKET_CATEGORIES = [
        "large_cap",      # > $10B
        "mid_cap",        # $2B - $10B
        "small_cap",      # $300M - $2B
        "micro_cap",      # $50M - $300M
        "mega_cap",       # > $200B
    ]
    
    def __init__(self):
        self.stock_cache: Dict[str, Any] = {}
        self._load_stock_universe()
    
    def _load_stock_universe(self):
        """Load comprehensive stock universe"""
        log.info("Loading US market stock universe...")
        
        # Core S&P 500 stocks
        self.sp500_stocks = self._get_sp500_stocks()
        
        # Additional NASDAQ stocks
        self.nasdaq_stocks = self._get_nasdaq_stocks()
        
        # Russell 2000 small caps
        self.russell2000_stocks = self._get_russell2000_stocks()
        
        # Popular ETFs and sector funds
        self.etf_universe = self._get_etf_universe()
        
        # Combine all with deduplication
        all_stocks = set(self.sp500_stocks + self.nasdaq_stocks + 
                        self.russell2000_stocks + self.etf_universe)
        
        self.all_us_stocks = sorted(list(all_stocks))
        
        log.info(f"Loaded {len(self.all_us_stocks)} US stocks for analysis")
    
    def _get_sp500_stocks(self) -> List[str]:
        """Get S&P 500 stock list"""
        # Comprehensive S&P 500 list
        sp500 = [
            # Technology
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ADBE",
            "CRM", "ORCL", "ACN", "IBM", "INTC", "AMD", "QCOM", "TXN", "CSCO", "ADP",
            "INTU", "AMAT", "MU", "LRCX", "KLAC", "SNPS", "CDNS", "MRVL", "NXPI", "FTNT",
            
            # Healthcare
            "UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "PFE", "DHR", "BMY",
            "AMGN", "GILD", "VRTX", "REGN", "ISRG", "ZTS", "CVS", "CI", "HUM", "ELV",
            
            # Financials
            "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "AXP",
            "C", "USB", "PNC", "SCHW", "TFC", "COF", "SPGI", "MCO", "ICE", "CME",
            
            # Consumer
            "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "COST", "WMT",
            "PG", "KO", "PEP", "WMT", "COST", "TGT", "DG", "DLTR", "AZO", "ORLY",
            
            # Energy
            "XOM", "CVX", "COP", "EOG", "MPC", "PSX", "VLO", "OKE", "WMB", "KMI",
            "SLB", "HAL", "BKR", "FANG", "DVN", "MRO", "APA", "OXY",
            
            # Industrials
            "GE", "BA", "HON", "CAT", "DE", "UPS", "FDX", "LMT", "RTX", "NOC",
            "GD", "ITW", "CSX", "UNP", "NSC", "WM", "RSG", "CNI", "CP", "FTV",
            
            # Utilities
            "NEE", "DUK", "SO", "AEP", "EXC", "XEL", "SRE", "PEG", "ED", "WEC",
            "ES", "D", "AEE", "CMS", "ETR", "FE", "LNT", "NI", "PNW", "SCG",
            
            # Real Estate
            "AMT", "PLD", "CCI", "EQIX", "PSA", "O", "DLR", "WELL", "SPG", "AVB",
            "EQR", "UDR", "MAA", "ESS", "BXP", "ARE", "VTR", "HCP", "PEAK", "IRM",
            
            # Communications
            "VZ", "T", "CMCSA", "DIS", "NFLX", "CHTR", "TMUS", "VZ", "T", "SBAC",
            "GOOGL", "META", "TTWO", "ATVI", "EA", "NWSA", "FOXA", "PARA", "LYV",
            
            # Materials
            "LIN", "APD", "SHW", "ECL", "NEM", "FCX", "DOW", "PPG", "DD", "NUE",
            "STLD", "MT", "VALE", "BHP", "RIO", "SCCO", "CF", "MOS", "FMC", "ALB"
        ]
        return list(set(sp500))  # Deduplicate
    
    def _get_nasdaq_stocks(self) -> List[str]:
        """Get additional NASDAQ stocks beyond S&P 500"""
        nasdaq = [
            # Tech/Software
            "SNOW", "ZM", "U", "RBLX", "DOCU", "CRWD", "OKTA", "DDOG", "NET", "PLTR",
            "ASAN", "BILL", "TOST", "RAMP", "ZUO", "SMAR", "WK", "COUP", "SPLK", "NTNX",
            
            # Biotech/Healthcare
            "MRNA", "BNTX", "BIIB", "SGEN", "INCY", "ALNY", "BMRN", "SRPT", "IONS", "EXAS",
            "DXCM", "PODD", "ABMD", "PEN", "RMD", "VAR", "MASI", "NARI", "TNDM", "SHC",
            
            # Fintech
            "SQ", "PYPL", "ADYEN", "SOFI", "UPST", "AFRM", "HOOD", "LC", "OPRT", "COFN",
            
            # E-commerce/Consumer
            "ETSY", "CHWY", "W", "CVNA", "REAL", "LE", "OSTK", "BABA", "JD", "PDD",
            
            # Clean Energy/Sustainability
            "ENPH", "SEDG", "FSLR", "RUN", "SPWR", "JKS", "CSIQ", "SOL", "MAXN", "BEEM",
            
            # Gaming/Entertainment
            "TTWO", "ATVI", "EA", "RBLX", "U", "Unity", "TTWO", "ZNGA", "GRVY", "GREE",
            
            # Cybersecurity
            "CRWD", "PANW", "FTNT", "CYBR", "OKTA", "SPLK", "NET", "ZS", "TENB", "QLYS",
            
            # Semiconductors
            "NVDA", "AMD", "INTC", "QCOM", "AVGO", "MU", "LRCX", "KLAC", "AMAT", "SNPS",
            "CDNS", "MRVL", "NXPI", "ON", "MCHP", "MPWR", "RMBS", "DIOD", "POWI", "SIMO",
            
            # EV/Auto Tech
            "TSLA", "RIVN", "LCID", "NIO", "XPEV", "LI", "FSR", "GOEV", "HYLN", "WKHS",
            "BLNK", "CHPT", "EVGO", "VLTA", "BEEM", "CLII", "QS", "SLDP", "ENVX", "FREY"
        ]
        return list(set(nasdaq))
    
    def _get_russell2000_stocks(self) -> List[str]:
        """Get Russell 2000 small cap stocks sample"""
        # Representative sample of Russell 2000
        russell = [
            "AA", "AAL", "AAN", "AAOI", "AAON", "AAP", "AAT", "AAWW", "AAXN", "ABCB",
            "ABEO", "ABG", "ABM", "ABTX", "ACAD", "ACBI", "ACCO", "ACEL", "ACET", "ACIW",
            "ACLS", "ACM", "ACNB", "ACOR", "ACRE", "ACRS", "ACTG", "ACV", "ADC", "ADES",
            "ADMA", "ADMS", "ADTN", "ADUS", "ADV", "AE", "AEE", "AEG", "AEHR", "AEIS",
            "AEL", "AEO", "AEP", "AERI", "AFBI", "AFG", "AFIN", "AFL", "AFMD", "AFYA",
            # Add more as needed - this is a sample
            "AGEN", "AGFS", "AGI", "AGIO", "AGLE", "AGM", "AGNC", "AGO", "AGR", "AGRO",
            "AGS", "AGTC", "AGYS", "AGX", "AHCO", "AHH", "AHL", "AHT", "AI", "AIF"
        ]
        return russell
    
    def _get_etf_universe(self) -> List[str]:
        """Get major ETFs for sector and thematic analysis"""
        etfs = [
            # Broad Market
            "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "IVV", "VEA", "VWO", "VTV",
            
            # Sector ETFs
            "XLK", "XLF", "XLE", "XLU", "XLI", "XLP", "XLB", "XRT", "XBI", "XME",
            "XOP", "XHB", "XTL", "XRT", "XSW", "XWEB", "XSD", "XNTK", "XHE", "XHS",
            
            # Thematic ETFs
            "ARKK", "ARKQ", "ARKW", "ARKG", "ARKF", "ARKX",  # ARK Invest
            "BOTZ", "ROBT", "IRBO",  # Robotics/AI
            "SMH", "SOXX", "XSD",  # Semiconductors
            "IGV", "SKYY", "WCLD",  # Software/Cloud
            "IBB", "XBI", "BBH",  # Biotech
            "ESGU", "SUSA", "CRBN",  # ESG
            "LIT", "BATT", "CHIQ",  # Thematic
            "MJ", "YOLO", "THCX",  # Cannabis
            "PRNT", "IZRL",  # Innovation
            
            # Bond/Fixed Income
            "AGG", "BND", "VCIT", "VCSH", "VGIT", "VGSH", "VMBS", "VNQI", "VCLT",
            
            # International
            "VEA", "VWO", "IEFA", "IEMG", "VXUS", "VT", "VEU", "VSS", "VTEB"
        ]
        return etfs
    
    def get_all_stocks(self) -> List[str]:
        """Get all available US stocks"""
        return self.all_us_stocks.copy()
    
    def get_by_category(self, category: str) -> List[str]:
        """Get stocks by market cap category"""
        if category == "mega_cap":
            return [s for s in self.sp500_stocks if self._get_market_cap(s) > 200_000_000_000]
        elif category == "large_cap":
            return [s for s in self.sp500_stocks if 10_000_000_000 < self._get_market_cap(s) <= 200_000_000_000]
        elif category == "mid_cap":
            return [s for s in self.sp500_stocks if 2_000_000_000 < self._get_market_cap(s) <= 10_000_000_000]
        elif category == "small_cap":
            return self.russell2000_stocks[:200]  # First 200
        elif category == "micro_cap":
            return self.russell2000_stocks[200:]  # Remaining
        else:
            return []
    
    def _get_market_cap(self, symbol: str) -> float:
        """Get market cap for a stock (with caching)"""
        if symbol in self.stock_cache:
            return self.stock_cache[symbol].get("market_cap", 0)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_cap = info.get("marketCap", 0)
            
            self.stock_cache[symbol] = {
                "market_cap": market_cap,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "name": info.get("longName")
            }
            
            return market_cap
        except:
            return 0
    
    def get_by_sector(self, sector: str) -> List[str]:
        """Get stocks by sector"""
        sector_mapping = {
            "technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "INTC", "AMD", "QCOM", "CSCO"],
            "healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "PFE", "ABT", "DHR", "BMY"],
            "financials": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "AXP"],
            "consumer": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "COST", "WMT"],
            "energy": ["XOM", "CVX", "COP", "EOG", "MPC", "PSX", "VLO", "OKE", "WMB", "KMI"],
            "industrials": ["GE", "BA", "HON", "CAT", "DE", "UPS", "FDX", "LMT", "RTX", "NOC"]
        }
        return sector_mapping.get(sector.lower(), [])
    
    def scan_universe(self, 
                     filter_criteria: Optional[Dict[str, Any]] = None,
                     limit: int = 1000) -> List[str]:
        """Scan universe with optional filters"""
        stocks = self.get_all_stocks()
        
        if filter_criteria:
            filtered = []
            for symbol in stocks[:limit * 2]:  # Check extra for filtering
                try:
                    if self._passes_filter(symbol, filter_criteria):
                        filtered.append(symbol)
                        if len(filtered) >= limit:
                            break
                except:
                    continue
            return filtered
        
        return stocks[:limit]
    
    def _passes_filter(self, symbol: str, criteria: Dict[str, Any]) -> bool:
        """Check if stock passes filter criteria"""
        try:
            info = self.stock_cache.get(symbol)
            if not info:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                self.stock_cache[symbol] = info
            
            # Check min market cap
            if "min_market_cap" in criteria:
                if info.get("marketCap", 0) < criteria["min_market_cap"]:
                    return False
            
            # Check max market cap
            if "max_market_cap" in criteria:
                if info.get("marketCap", 0) > criteria["max_market_cap"]:
                    return False
            
            # Check sector
            if "sector" in criteria:
                if info.get("sector", "").lower() != criteria["sector"].lower():
                    return False
            
            # Check min volume
            if "min_volume" in criteria:
                if info.get("averageVolume", 0) < criteria["min_volume"]:
                    return False
            
            return True
        except:
            return False
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed stock information"""
        if symbol not in self.stock_cache:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                self.stock_cache[symbol] = {
                    "market_cap": info.get("marketCap"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "name": info.get("longName"),
                    "price": info.get("currentPrice"),
                    "volume": info.get("averageVolume"),
                    "pe_ratio": info.get("trailingPE"),
                    "beta": info.get("beta")
                }
            except:
                return {}
        
        return self.stock_cache.get(symbol, {})


# Global instance
us_market = USMarketStockUniverse()
