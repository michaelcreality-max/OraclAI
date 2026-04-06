"""
Data Collection Agent
Central data provider that gathers and serves real-time information to all other agents
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import yfinance as yf
import requests

log = logging.getLogger(__name__)


@dataclass
class DataRequest:
    """Request for specific data from an agent"""
    agent_id: str
    request_type: str
    symbol: str
    parameters: Dict[str, Any]
    timestamp: datetime
    urgency: str = "normal"  # normal, high, critical


@dataclass
class DataResponse:
    """Response to a data request"""
    request_id: str
    data_type: str
    data: Dict[str, Any]
    timestamp: datetime
    processing_time: float
    cache_hit: bool = False


class DataCollectionAgent:
    """
    Central data collection agent that:
    - Gathers all real-time stock data on startup
    - Provides additional information to other agents on request
    - Manages data caching and updates
    - Tracks agent requests for audit purposes
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=5)  # 5 minute cache
        self.request_log: List[DataRequest] = []
        self.agent_queries: Dict[str, List[Dict]] = {}  # Track what each agent asked for
        
    def collect_initial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect comprehensive initial data for a stock
        This is called once at the start of analysis
        """
        log.info(f"DataCollectionAgent: Collecting initial data for {symbol}")
        start_time = time.time()
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Core stock data
            info = ticker.info
            hist = ticker.history(period="6mo")
            
            data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "collection_time": time.time() - start_time,
                
                # Price data
                "price_data": {
                    "current_price": info.get("currentPrice"),
                    "open": info.get("open"),
                    "high": info.get("dayHigh"),
                    "low": info.get("dayLow"),
                    "previous_close": info.get("previousClose"),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                    "volume": info.get("volume"),
                    "average_volume": info.get("averageVolume"),
                },
                
                # Fundamental data
                "fundamentals": {
                    "market_cap": info.get("marketCap"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "price_to_book": info.get("priceToBook"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months"),
                    "enterprise_value": info.get("enterpriseValue"),
                    "profit_margins": info.get("profitMargins"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "current_ratio": info.get("currentRatio"),
                    "quick_ratio": info.get("quickRatio"),
                    "dividend_yield": info.get("dividendYield"),
                    "dividend_rate": info.get("dividendRate"),
                    "ex_dividend_date": info.get("exDividendDate"),
                    "beta": info.get("beta"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "employees": info.get("fullTimeEmployees"),
                },
                
                # Historical data summary
                "historical": {
                    "six_month_high": hist['High'].max() if not hist.empty else None,
                    "six_month_low": hist['Low'].min() if not hist.empty else None,
                    "average_volume_6m": hist['Volume'].mean() if not hist.empty else None,
                    "volatility": hist['Close'].pct_change().std() * (252 ** 0.5) if not hist.empty else None,
                    "trend_6m": "up" if not hist.empty and hist['Close'][-1] > hist['Close'][0] else "down",
                },
                
                # Metadata
                "company_info": {
                    "name": info.get("longName"),
                    "country": info.get("country"),
                    "website": info.get("website"),
                    "business_summary": info.get("longBusinessSummary", "")[:500],
                }
            }
            
            # Cache the data
            self.cache[symbol] = data
            self.cache_timestamp[symbol] = datetime.now()
            
            log.info(f"DataCollectionAgent: Collected data for {symbol} in {data['collection_time']:.2f}s")
            return data
            
        except Exception as e:
            log.error(f"DataCollectionAgent: Error collecting data for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    def request_data(self, agent_id: str, request_type: str, symbol: str, 
                    parameters: Dict[str, Any] = None, urgency: str = "normal") -> DataResponse:
        """
        Handle data requests from other agents
        Agents can request additional information during their analysis
        """
        parameters = parameters or {}
        request_id = f"{agent_id}_{request_type}_{int(time.time() * 1000)}"
        request_start = time.time()
        
        # Log the request
        data_request = DataRequest(
            agent_id=agent_id,
            request_type=request_type,
            symbol=symbol,
            parameters=parameters,
            timestamp=datetime.now(),
            urgency=urgency
        )
        self.request_log.append(data_request)
        
        # Track agent queries
        if agent_id not in self.agent_queries:
            self.agent_queries[agent_id] = []
        self.agent_queries[agent_id].append({
            "type": request_type,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        })
        
        log.info(f"DataCollectionAgent: {agent_id} requested {request_type} for {symbol}")
        
        # Check cache first
        cache_key = f"{symbol}_{request_type}"
        if cache_key in self.cache:
            cache_time = self.cache_timestamp.get(cache_key)
            if cache_time and datetime.now() - cache_time < self.cache_ttl:
                log.info(f"DataCollectionAgent: Cache hit for {cache_key}")
                return DataResponse(
                    request_id=request_id,
                    data_type=request_type,
                    data=self.cache[cache_key],
                    timestamp=datetime.now(),
                    processing_time=time.time() - request_start,
                    cache_hit=True
                )
        
        # Fetch requested data
        try:
            if request_type == "geopolitical_context":
                data = self._fetch_geopolitical_context(symbol, parameters)
            elif request_type == "environmental_factors":
                data = self._fetch_environmental_factors(symbol, parameters)
            elif request_type == "detailed_fundamentals":
                data = self._fetch_detailed_fundamentals(symbol, parameters)
            elif request_type == "sector_analysis":
                data = self._fetch_sector_analysis(symbol, parameters)
            elif request_type == "peer_comparison":
                data = self._fetch_peer_comparison(symbol, parameters)
            elif request_type == "analyst_ratings":
                data = self._fetch_analyst_ratings(symbol, parameters)
            elif request_type == "institutional_ownership":
                data = self._fetch_institutional_ownership(symbol, parameters)
            elif request_type == "short_interest":
                data = self._fetch_short_interest(symbol, parameters)
            elif request_type == "options_data":
                data = self._fetch_options_data(symbol, parameters)
            elif request_type == "earnings_calendar":
                data = self._fetch_earnings_calendar(symbol, parameters)
            elif request_type == "insider_trading":
                data = self._fetch_insider_trading(symbol, parameters)
            elif request_type == "supply_chain":
                data = self._fetch_supply_chain_data(symbol, parameters)
            else:
                data = {"error": f"Unknown request type: {request_type}"}
            
            # Cache the result
            self.cache[cache_key] = data
            self.cache_timestamp[cache_key] = datetime.now()
            
            processing_time = time.time() - request_start
            log.info(f"DataCollectionAgent: Fetched {request_type} in {processing_time:.2f}s")
            
            return DataResponse(
                request_id=request_id,
                data_type=request_type,
                data=data,
                timestamp=datetime.now(),
                processing_time=processing_time,
                cache_hit=False
            )
            
        except Exception as e:
            log.error(f"DataCollectionAgent: Error fetching {request_type}: {e}")
            return DataResponse(
                request_id=request_id,
                data_type=request_type,
                data={"error": str(e)},
                timestamp=datetime.now(),
                processing_time=time.time() - request_start,
                cache_hit=False
            )
    
    def _fetch_geopolitical_context(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch geopolitical factors affecting the stock"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "country_exposure": info.get("country", "Unknown"),
            "geographic_revenue_breakdown": info.get("revenueBreakdown", {}),
            "trade_sensitivity": self._assess_trade_sensitivity(info),
            "sanctions_risk": self._calculate_sanctions_risk(info),
            "political_stability_score": self._calculate_political_stability(info),
            "regulatory_environment": self._get_regulatory_environment(info),
        }
    
    def _fetch_environmental_factors(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch environmental and ESG factors"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "carbon_intensity": self._estimate_carbon_intensity(info),
            "esg_risk_score": info.get("esgScore", None),
            "environmental_exposure": self._assess_environmental_exposure(info),
            "climate_risk": self._assess_climate_risk(info),
            "sustainability_rating": info.get("sustainabilityRating", "N/A"),
        }
    
    def _fetch_detailed_fundamentals(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch detailed fundamental metrics"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "income_statement": {
                "revenue": info.get("totalRevenue"),
                "gross_profit": info.get("grossProfits"),
                "operating_income": info.get("operatingIncome"),
                "net_income": info.get("netIncome"),
                "ebitda": info.get("ebitda"),
            },
            "balance_sheet": {
                "total_assets": info.get("totalAssets"),
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "shareholders_equity": info.get("totalStockholderEquity"),
                "working_capital": info.get("workingCapital"),
            },
            "cash_flow": {
                "operating_cash_flow": info.get("operatingCashflow"),
                "free_cash_flow": info.get("freeCashflow"),
                "capital_expenditure": info.get("capitalExpenditures"),
            },
            "valuation_metrics": {
                "pe_trailing": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "pb_ratio": info.get("priceToBook"),
                "pcf_ratio": info.get("priceToCashflow"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "ev_revenue": info.get("enterpriseToRevenue"),
            }
        }
    
    def _fetch_sector_analysis(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Analyze sector performance and positioning"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        sector = info.get("sector", "Unknown")
        
        # Sector performance comparison would go here
        return {
            "sector": sector,
            "industry": info.get("industry", "Unknown"),
            "sector_rank": self._get_sector_rank(info),
            "industry_rank": self._get_industry_rank(info),
            "competitive_position": self._assess_competitive_position(info),
            "market_share_estimate": info.get("marketShare", "Unknown"),
            "sector_growth_rate": self._get_sector_growth_rate(sector),
            "industry_momentum": self._get_industry_momentum(info),
        }
    
    def _fetch_peer_comparison(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Compare against peer companies"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Peer comparison would integrate with sector data
        current_pe = info.get("trailingPE", 0)
        sector_pe = self._get_sector_avg_pe(sector) if 'sector' in locals() else 15
        
        # Determine PE comparison
        if current_pe > 0 and sector_pe > 0:
            pe_ratio = current_pe / sector_pe
            if pe_ratio > 1.3:
                pe_comparison = "above_average"
            elif pe_ratio < 0.7:
                pe_comparison = "below_average"
            else:
                pe_comparison = "average"
        else:
            pe_comparison = "unknown"
        
        # Growth comparison
        growth = info.get("revenueGrowth", 0)
        if growth > 0.15:
            growth_comparison = "above_average"
        elif growth < 0.05:
            growth_comparison = "below_average"
        else:
            growth_comparison = "average"
        
        # Margin comparison
        margins = info.get("profitMargins", 0)
        if margins > 0.15:
            margin_comparison = "above_average"
        elif margins < 0.08:
            margin_comparison = "below_average"
        else:
            margin_comparison = "average"
        
        return {
            "peers": info.get("companyPeers", []),
            "peer_metrics": {
                "pe_comparison": pe_comparison,
                "growth_comparison": growth_comparison,
                "margin_comparison": margin_comparison,
            },
            "competitive_advantages": self._identify_competitive_advantages(info),
            "competitive_disadvantages": self._identify_competitive_disadvantages(info),
        }
    
    def _fetch_analyst_ratings(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch analyst ratings and price targets"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "recommendation_key": info.get("recommendationKey"),
            "recommendation_mean": info.get("recommendationMean"),
            "number_of_analysts": info.get("numberOfAnalystOpinions"),
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_mean": info.get("targetMeanPrice"),
            "target_median": info.get("targetMedianPrice"),
            "current_price": info.get("currentPrice"),
            "upside_potential": self._calculate_upside_potential(info),
        }
    
    def _fetch_institutional_ownership(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch institutional ownership data"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Calculate institutional activity from holdings change
        held_pct = info.get("heldPercentInstitutions", 0)
        
        # Infer activity based on institutional concentration
        if held_pct > 0.85:
            activity = "accumulating"
        elif held_pct > 0.70:
            activity = "stable"
        elif held_pct > 0.50:
            activity = "reducing"
        else:
            activity = "unknown"
        
        return {
            "held_percent_institutions": held_pct,
            "held_percent_insiders": info.get("heldPercentInsiders"),
            "institutional_concentration": self._assess_institutional_concentration(info),
            "recent_institutional_activity": activity,
            "top_institutional_holders": self._get_top_institutions(info),
        }
    
    def _get_top_institutions(self, info: Dict) -> List[Dict]:
        """Extract top institutional holders from company data"""
        # Try to get from info, return empty if not available
        holders = info.get("institutionalHolders", [])
        if holders:
            return [
                {
                    "name": h.get("name", "Unknown"),
                    "shares": h.get("shares", 0),
                    "date": h.get("date", "N/A")
                }
                for h in holders[:10]
            ]
        return []
    
    def _fetch_short_interest(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch short interest data"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Calculate short interest trend
        short_ratio = info.get("shortRatio", 0)
        short_pct = info.get("shortPercentOfFloat", 0)
        
        # Determine trend based on short ratio and percentage
        if short_ratio > 5 or short_pct > 0.10:
            trend = "elevated_short_interest"
        elif short_ratio > 3 or short_pct > 0.05:
            trend = "moderate_short_interest"
        elif short_ratio > 1:
            trend = "normal_short_interest"
        else:
            trend = "low_short_interest"
        
        return {
            "short_ratio": short_ratio,
            "short_percent_of_float": short_pct,
            "short_percent_of_shares_outstanding": self._calculate_short_percent(info),
            "days_to_cover": short_ratio,
            "short_interest_trend": trend,
        }
    
    def _fetch_options_data(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch options market data"""
        ticker = yf.Ticker(symbol)
        
        try:
            # Get options expiration dates
            expirations = ticker.options
            
            if expirations:
                # Get nearest expiration options chain
                opt_chain = ticker.option_chain(expirations[0])
                
                calls = opt_chain.calls
                puts = opt_chain.puts
                
                return {
                    "available_expirations": expirations[:5],
                    "put_call_ratio": len(puts) / len(calls) if len(calls) > 0 else 0,
                    "implied_volatility_avg": calls['impliedVolatility'].mean() if not calls.empty else 0,
                    "options_volume": int(calls['volume'].sum() + puts['volume'].sum()),
                    "max_pain_price": self._calculate_max_pain(opt_chain),
                    "unusual_activity": self._detect_unusual_options_activity(opt_chain),
                }
            else:
                return {"error": "No options data available"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _fetch_earnings_calendar(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch earnings calendar and history"""
        ticker = yf.Ticker(symbol)
        
        try:
            calendar = ticker.calendar
            earnings_dates = ticker.earnings_dates
            
            return {
                "next_earnings_date": calendar.index[0] if calendar is not None and not calendar.empty else None,
                "earnings_history": earnings_dates.to_dict() if earnings_dates is not None else {},
                "eps_estimate": calendar.iloc[0]['EPS Estimate'] if calendar is not None and not calendar.empty else None,
                "revenue_estimate": calendar.iloc[0]['Revenue Estimate'] if calendar is not None and not calendar.empty else None,
                "earnings_surprise_history": self._get_earnings_surprises(ticker),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _fetch_insider_trading(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch insider trading activity"""
        ticker = yf.Ticker(symbol)
        
        try:
            insider_transactions = ticker.insider_transactions
            insider_purchases = ticker.insider_purchases
            
            # Calculate net insider activity from transaction data
            if not insider_transactions.empty:
                buys = insider_transactions[insider_transactions['Transaction'].str.contains('Buy', case=False, na=False)]
                sells = insider_transactions[insider_transactions['Transaction'].str.contains('Sell', case=False, na=False)]
                
                buy_shares = buys['Shares'].sum() if 'Shares' in buys.columns else len(buys)
                sell_shares = sells['Shares'].sum() if 'Shares' in sells.columns else len(sells)
                
                if buy_shares > sell_shares * 2:
                    net_activity = "net_buying"
                elif sell_shares > buy_shares * 2:
                    net_activity = "net_selling"
                elif buy_shares > 0 and sell_shares > 0:
                    net_activity = "mixed_activity"
                else:
                    net_activity = "minimal_activity"
            else:
                net_activity = "no_data"
            
            return {
                "recent_transactions": insider_transactions.to_dict() if insider_transactions is not None else [],
                "insider_buying_6m": insider_purchases.get('6m', 0) if insider_purchases else 0,
                "insider_selling_6m": insider_purchases.get('6m', 0) if insider_purchases else 0,
                "net_insider_activity": net_activity,
                "insider_sentiment": self._assess_insider_sentiment(insider_transactions),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _fetch_supply_chain_data(self, symbol: str, parameters: Dict) -> Dict[str, Any]:
        """Fetch supply chain and operational data"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Identify key suppliers and customers from sector analysis
        sector = info.get("sector", "").lower()
        industry = info.get("industry", "").lower()
        
        # Infer supply chain relationships based on sector
        key_suppliers = []
        key_customers = []
        
        if "technology" in sector:
            key_suppliers = ["semiconductor manufacturers", "component suppliers"]
            key_customers = ["enterprise clients", "retail consumers"]
        elif "automobiles" in industry:
            key_suppliers = ["auto parts manufacturers", "battery suppliers"]
            key_customers = ["dealerships", "fleet operators"]
        elif "retail" in sector:
            key_suppliers = ["manufacturers", "distributors"]
            key_customers = ["end consumers"]
        elif "healthcare" in sector:
            key_suppliers = ["medical device suppliers", "pharmaceutical suppliers"]
            key_customers = ["hospitals", "patients"]
        elif "energy" in sector:
            key_suppliers = ["equipment suppliers", "service providers"]
            key_customers = ["utilities", "industrial consumers"]
        
        return {
            "sector": info.get("sector"),
            "supply_chain_risk": self._assess_supply_chain_risk(info),
            "geographic_diversification": self._assess_geographic_diversification(info),
            "key_suppliers": key_suppliers,
            "key_customers": key_customers,
            "inventory_turnover": info.get("inventoryTurnover"),
            "operating_efficiency": self._assess_operating_efficiency(info),
        }
    
    # Helper methods for analysis
    def _assess_trade_sensitivity(self, info: Dict) -> str:
        """Assess sensitivity to trade policies"""
        sector = info.get("sector", "").lower()
        if sector in ["technology", "manufacturing", "consumer cyclical"]:
            return "high"
        elif sector in ["healthcare", "utilities", "consumer defensive"]:
            return "low"
        return "medium"

    def _calculate_sanctions_risk(self, info: Dict) -> str:
        """
        Calculate sanctions risk based on country exposure and sector.
        Higher risk for certain countries and sensitive sectors.
        """
        country = info.get("country", "US").upper()
        sector = info.get("sector", "").lower()
        
        # High-risk countries (sanctions-prone regions)
        elevated_risk_countries = ["RU", "IR", "KP", "SY", "CU", "VE"]
        moderate_risk_countries = ["CN", "TR", "PK", "BD", "MM"]
        
        # High-risk sectors for sanctions
        sensitive_sectors = ["energy", "materials", "defense", "aerospace"]
        
        if country in elevated_risk_countries:
            return "elevated_sanctions_risk"
        
        if country in moderate_risk_countries:
            if sector in sensitive_sectors:
                return "moderate_sanctions_risk"
            return "low_moderate_sanctions_risk"
        
        if sector in sensitive_sectors and country != "US":
            return "low_sanctions_monitoring_required"
        
        return "low_sanctions_risk"

    def _calculate_political_stability(self, info: Dict) -> float:
        """
        Calculate political stability score (0-1 scale).
        Based on country, sector sensitivity, and regulatory environment.
        """
        country = info.get("country", "US").upper()
        sector = info.get("sector", "").lower()
        
        # Base stability by country (simplified scoring)
        country_stability = {
            "US": 0.85, "CA": 0.90, "GB": 0.85, "DE": 0.88, "FR": 0.82,
            "JP": 0.87, "AU": 0.86, "CH": 0.89, "NL": 0.85, "SE": 0.88,
            "CN": 0.70, "IN": 0.65, "BR": 0.55, "RU": 0.35, "SA": 0.50,
            "ZA": 0.60, "MX": 0.65, "ID": 0.60, "TR": 0.50, "AR": 0.55
        }
        
        base_score = country_stability.get(country, 0.60)
        
        # Adjust for sector regulatory sensitivity
        heavily_regulated = ["financials", "healthcare", "utilities", "energy"]
        moderately_regulated = ["telecommunications", "transportation", "real estate"]
        
        if sector in heavily_regulated:
            # Regulated sectors have more political/regulatory risk
            base_score -= 0.05
        elif sector in moderately_regulated:
            base_score -= 0.02
        
        # Adjust for company size (larger = more politically connected/stable)
        market_cap = info.get("marketCap", 0)
        if market_cap > 100_000_000_000:
            base_score += 0.05
        elif market_cap > 10_000_000_000:
            base_score += 0.02
        
        return round(max(0.0, min(1.0, base_score)), 2)

    def _get_regulatory_environment(self, info: Dict) -> str:
        """Get regulatory environment for sector"""
        sector = info.get("sector", "").lower()
        if sector in ["healthcare", "financials", "utilities"]:
            return "highly_regulated"
        elif sector in ["technology"]:
            return "increasing_regulation"
        return "moderate_regulation"
    
    def _estimate_carbon_intensity(self, info: Dict) -> str:
        """Estimate carbon intensity based on sector"""
        sector = info.get("sector", "").lower()
        high_carbon = ["energy", "materials", "utilities", "industrials"]
        if sector in high_carbon:
            return "high"
        return "low_to_moderate"
    
    def _assess_environmental_exposure(self, info: Dict) -> str:
        """Assess environmental risk exposure"""
        sector = info.get("sector", "").lower()
        if sector in ["energy", "materials", "utilities"]:
            return "high"
        return "moderate"
    
    def _assess_climate_risk(self, info: Dict) -> str:
        """Assess climate-related risks"""
        sector = info.get("sector", "").lower()
        if sector in ["energy", "utilities", "materials", "realestate"]:
            return "significant"
        return "moderate"
    
    def _get_sector_rank(self, info: Dict) -> str:
        """Get company rank within sector"""
        market_cap = info.get("marketCap", 0)
        if market_cap > 100_000_000_000:
            return "leader"
        elif market_cap > 10_000_000_000:
            return "major_player"
        return "mid_tier"
    
    def _get_industry_rank(self, info: Dict) -> str:
        """Get company rank within industry"""
        return self._get_sector_rank(info)  # Simplified
    
    def _assess_competitive_position(self, info: Dict) -> str:
        """Assess competitive position"""
        roe = info.get("returnOnEquity", 0)
        margins = info.get("profitMargins", 0)
        
        if roe > 0.15 and margins > 0.15:
            return "strong_competitive_advantage"
        elif roe > 0.10 and margins > 0.10:
            return "competitive"
        return "challenged"
    
    def _get_sector_growth_rate(self, sector: str) -> float:
        """Get estimated sector growth rate"""
        growth_rates = {
            "technology": 0.15,
            "healthcare": 0.12,
            "communication services": 0.10,
            "consumer cyclical": 0.08,
            "industrials": 0.06,
            "financials": 0.05,
            "consumer defensive": 0.04,
            "utilities": 0.03,
            "energy": 0.02,
            "materials": 0.04,
            "real estate": 0.04,
        }
        return growth_rates.get(sector.lower(), 0.05)
    
    def _get_industry_momentum(self, info: Dict) -> str:
        """Get industry momentum"""
        growth = info.get("revenueGrowth", 0)
        if growth > 0.20:
            return "strong_momentum"
        elif growth > 0.10:
            return "positive_momentum"
        elif growth > 0:
            return "stable"
        return "declining"
    
    def _identify_competitive_advantages(self, info: Dict) -> List[str]:
        """Identify competitive advantages"""
        advantages = []
        
        if info.get("profitMargins", 0) > 0.20:
            advantages.append("High profit margins")
        if info.get("returnOnEquity", 0) > 0.15:
            advantages.append("Strong ROE")
        if info.get("marketCap", 0) > 100_000_000_000:
            advantages.append("Scale advantage")
        if info.get("revenueGrowth", 0) > 0.15:
            advantages.append("Growth momentum")
        
        return advantages
    
    def _identify_competitive_disadvantages(self, info: Dict) -> List[str]:
        """Identify competitive disadvantages"""
        disadvantages = []
        
        if info.get("profitMargins", 0) < 0.05:
            disadvantages.append("Low margins")
        if info.get("debtToEquity", 0) > 1.0:
            disadvantages.append("High leverage")
        if info.get("currentRatio", 2) < 1.0:
            disadvantages.append("Liquidity concerns")
        
        return disadvantages
    
    def _calculate_upside_potential(self, info: Dict) -> float:
        """Calculate upside potential to target price"""
        current = info.get("currentPrice", 0)
        target = info.get("targetMeanPrice", 0)
        
        if current > 0 and target > 0:
            return (target - current) / current
        return 0
    
    def _assess_institutional_concentration(self, info: Dict) -> str:
        """Assess institutional ownership concentration"""
        held = info.get("heldPercentInstitutions", 0)
        if held > 0.80:
            return "highly_concentrated"
        elif held > 0.50:
            return "moderately_concentrated"
        return "diversified"
    
    def _calculate_short_percent(self, info: Dict) -> float:
        """Calculate short percent of shares outstanding"""
        shares = info.get("sharesOutstanding", 0)
        short = info.get("sharesShort", 0)
        
        if shares > 0 and short > 0:
            return short / shares
        return 0
    
    def _calculate_max_pain(self, opt_chain) -> float:
        """Calculate max pain price for options"""
        # Simplified calculation
        try:
            calls = opt_chain.calls
            if not calls.empty:
                return calls['strike'].mean()
        except:
            pass
        return 0
    
    def _detect_unusual_options_activity(self, opt_chain) -> bool:
        """Detect unusual options activity"""
        try:
            calls = opt_chain.calls
            puts = opt_chain.puts
            total_volume = calls['volume'].sum() + puts['volume'].sum()
            avg_oi = calls['openInterest'].mean() + puts['openInterest'].mean()
            
            if total_volume > avg_oi * 2:
                return True
        except:
            pass
        return False
    
    def _get_earnings_surprises(self, ticker) -> List[Dict]:
        """Get historical earnings surprises"""
        try:
            earnings = ticker.earnings
            if earnings is not None:
                return earnings.to_dict()
        except:
            pass
        return []
    
    def _assess_insider_sentiment(self, transactions) -> str:
        """Assess insider trading sentiment"""
        if transactions is None or transactions.empty:
            return "neutral"
        
        buys = len(transactions[transactions['Transaction'] == 'Buy'])
        sells = len(transactions[transactions['Transaction'] == 'Sell'])
        
        if buys > sells * 2:
            return "bullish"
        elif sells > buys * 2:
            return "bearish"
        return "neutral"
    
    def _assess_supply_chain_risk(self, info: Dict) -> str:
        """Assess supply chain risk"""
        sector = info.get("sector", "").lower()
        if sector in ["technology", "automobiles"]:
            return "moderate_to_high"
        return "low_to_moderate"
    
    def _assess_geographic_diversification(self, info: Dict) -> str:
        """
        Assess geographic diversification based on revenue breakdown data.
        Analyzes revenue concentration across regions to assess geographic risk.
        """
        revenue_breakdown = info.get("revenueBreakdown", {})
        
        if not revenue_breakdown:
            # If no data, infer from company characteristics
            country = info.get("country", "US")
            if country == "US" and info.get("marketCap", 0) > 50_000_000_000:
                return "likely_diversified_large_cap"
            return "unknown_no_data"
        
        # Analyze concentration
        if isinstance(revenue_breakdown, dict):
            regions = list(revenue_breakdown.keys())
            values = list(revenue_breakdown.values())
            
            if len(regions) == 0:
                return "no_regional_data"
            
            # Calculate concentration metrics
            total_revenue = sum(values)
            if total_revenue == 0:
                return "invalid_data"
            
            # Calculate Herfindahl index for concentration
            shares = [v / total_revenue for v in values]
            herfindahl = sum(s ** 2 for s in shares)
            
            # Number of significant regions (>5% of revenue)
            significant_regions = sum(1 for s in shares if s > 0.05)
            
            if herfindahl < 0.3 and significant_regions >= 3:
                return "well_diversified"
            elif herfindahl < 0.5 and significant_regions >= 2:
                return "moderately_diversified"
            elif herfindahl > 0.7:
                return "highly_concentrated"
            else:
                return "limited_diversification"
        
        return "data_format_unknown"
    
    def _assess_operating_efficiency(self, info: Dict) -> str:
        """Assess operating efficiency"""
        margins = info.get("operatingMargins", 0)
        if margins > 0.20:
            return "highly_efficient"
        elif margins > 0.10:
            return "efficient"
        return "needs_improvement"
    
    def get_request_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of all data requests for a symbol"""
        symbol_requests = [r for r in self.request_log if r.symbol == symbol]
        
        by_agent = {}
        for req in symbol_requests:
            if req.agent_id not in by_agent:
                by_agent[req.agent_id] = []
            by_agent[req.agent_id].append({
                "type": req.request_type,
                "timestamp": req.timestamp.isoformat(),
                "urgency": req.urgency
            })
        
        return {
            "symbol": symbol,
            "total_requests": len(symbol_requests),
            "by_agent": by_agent,
            "unique_request_types": list(set(r.request_type for r in symbol_requests)),
            "cache_efficiency": self._calculate_cache_efficiency(symbol)
        }
    
    def _calculate_cache_efficiency(self, symbol: str) -> float:
        """
        Calculate cache hit rate for a symbol based on request log.
        Tracks duplicate requests within a time window to measure cache effectiveness.
        """
        symbol_requests = [r for r in self.request_log if r.symbol == symbol]
        if not symbol_requests or len(symbol_requests) < 2:
            return 0.0
        
        # Sort by timestamp
        sorted_requests = sorted(symbol_requests, key=lambda x: x.timestamp, reverse=True)
        
        # Look for requests within cache window (15 minutes)
        from datetime import timedelta
        cache_window = timedelta(minutes=15)
        
        hits = 0
        misses = 0
        
        for i, request in enumerate(sorted_requests[:-1]):
            # Check if same request type was made within cache window
            similar_requests = [
                r for r in sorted_requests[i+1:]
                if r.request_type == request.request_type
                and (request.timestamp - r.timestamp) <= cache_window
            ]
            
            if similar_requests:
                hits += 1
            else:
                misses += 1
        
        total = hits + misses
        if total == 0:
            return 0.0
        
        efficiency = hits / total
        return round(efficiency, 4)


# Global data collection agent instance
data_collection_agent = DataCollectionAgent()
