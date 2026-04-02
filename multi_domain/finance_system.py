"""
OraclAI Professional Finance Intelligence System
Citadel-Level Quantitative Analysis (No External APIs)

Multi-Agent Architecture:
- QuantitativeAnalyst: Mathematical modeling, algorithmic trading, risk metrics
- FundamentalAnalyst: Financial statements, valuation, company analysis
- TechnicalAnalyst: Chart patterns, indicators, market timing
- MacroStrategist: Economic cycles, policy, global markets
- RiskManager: Portfolio risk, hedging, drawdown control
- PortfolioManager: Asset allocation, optimization, rebalancing
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition, DebateResult

# Comprehensive finance knowledge bases
QUANTITATIVE_METHODS = {
    'statistical_arbitrage': {
        'pairs_trading': ['cointegration', 'mean reversion', 'z-score', 'correlation'],
        'factor_models': ['PCA', 'Fama-French', 'momentum factors', 'value factors'],
        'machine_learning': ['random forest', 'gradient boosting', 'neural networks', 'SVM'],
    },
    'time_series': {
        'arima': ['autoregressive', 'moving average', 'seasonality', 'differencing'],
        'garch': ['volatility clustering', 'ARCH effects', 'conditional heteroskedasticity'],
        'kalman_filter': ['state space', 'filtering', 'smoothing', 'prediction'],
    },
    'options_pricing': {
        'black_scholes': ['implied volatility', 'greeks', 'put-call parity', 'arbitrage'],
        'binomial': ['risk-neutral pricing', 'replication', 'delta hedging'],
        'monte_carlo': ['simulation', 'path generation', 'variance reduction', 'American options'],
    },
    'risk_metrics': {
        'var': ['historical VaR', 'parametric VaR', 'Monte Carlo VaR', 'CVaR'],
        'drawdown': ['max drawdown', 'underwater curve', 'recovery time', 'Calmar ratio'],
        ' Greeks': ['delta', 'gamma', 'theta', 'vega', 'rho', 'vomma'],
    }
}

FUNDAMENTAL_ANALYSIS = {
    'valuation': {
        'dcf': ['free cash flow', 'WACC', 'terminal value', 'discounting'],
        'multiples': ['P/E', 'EV/EBITDA', 'P/B', 'PEG', 'comparable companies'],
        'asset_based': ['NAV', 'liquidation value', 'replacement cost', 'sum of parts'],
    },
    'financial_statements': {
        'income': ['revenue', 'EBITDA', 'net income', 'margins', 'EPS', 'growth rates'],
        'balance': ['assets', 'liabilities', 'equity', 'working capital', 'debt ratios'],
        'cash_flow': ['operating', 'investing', 'financing', 'FCF', 'cash conversion'],
    },
    'quality_metrics': {
        'profitability': ['ROE', 'ROA', 'ROIC', 'gross margin', 'operating margin'],
        'efficiency': ['asset turnover', 'inventory turnover', 'receivables days'],
        'leverage': ['debt/equity', 'interest coverage', 'debt/EBITDA', 'current ratio'],
    }
}

TECHNICAL_ANALYSIS = {
    'trend_indicators': {
        'moving_averages': ['SMA', 'EMA', 'WMA', 'golden cross', 'death cross'],
        'macd': ['signal line', 'histogram', 'divergence', 'momentum'],
        'adx': ['trend strength', 'DI+', 'DI-', 'trading range'],
    },
    'momentum': {
        'rsi': ['overbought', 'oversold', 'divergence', 'failure swings'],
        'stochastic': ['%K', '%D', 'slow', 'fast', 'crossovers'],
        'cci': ['commodity channel', 'mean deviation', 'cyclical'],
    },
    'volatility': {
        'bollinger': ['bands', 'squeeze', 'breakout', '%B indicator'],
        'atr': ['average true range', 'position sizing', 'stop loss'],
        'keltner': ['channels', 'EMA based', 'volatility envelopes'],
    },
    'volume': {
        'obv': ['on balance volume', 'accumulation', 'distribution'],
        'vwap': ['volume weighted', 'intraday', 'execution benchmark'],
        'mfi': ['money flow', 'buying pressure', 'selling pressure'],
    }
}

MACRO_ECONOMICS = {
    'indicators': {
        'growth': ['GDP', 'industrial production', 'retail sales', 'PMI'],
        'inflation': ['CPI', 'PPI', 'PCE', 'employment cost', 'inflation expectations'],
        'labor': ['unemployment', 'NFP', 'wage growth', 'participation rate'],
    },
    'monetary_policy': {
        'fed': ['FOMC', 'fed funds rate', 'QE', 'QT', 'forward guidance'],
        'ecb': ['refinancing rate', 'APP', 'TLTRO', 'fragmentation'],
        'boj': ['yield curve control', 'QQE', 'negative rates'],
    },
    'cycles': {
        'business': ['expansion', 'peak', 'contraction', 'trough', 'leading indicators'],
        'credit': ['lending standards', 'credit spreads', 'financial conditions'],
        'inventory': ['stock-to-sales', 'manufacturing', 'restocking'],
    }
}

ALTERNATIVE_DATA = {
    'sentiment': ['news sentiment', 'social media', 'search trends', 'options flow'],
    'satellite': ['parking lots', 'retail traffic', 'supply chain', 'energy usage'],
    'credit_card': ['consumer spending', 'trending items', 'geographic patterns'],
    'web_scraping': ['job postings', 'pricing data', 'product reviews', 'app downloads'],
}


class QuantitativeAnalystAgent(BaseAgent):
    """
    Citadel-Level Quantitative Analyst
    Expert in: Mathematical modeling, algorithmic trading, statistical arbitrage
    """
    
    def __init__(self):
        super().__init__(
            name="QuantitativeAnalyst",
            role="Citadel Quantitative Analyst",
            expertise=[
                'statistical arbitrage', 'algorithmic trading', 'machine learning',
                'time series analysis', 'factor modeling', 'risk modeling',
                'portfolio optimization', 'market microstructure', 'high frequency'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Identify quant strategy
        strategy = self._identify_strategy(query_lower)
        
        # Detect market regime
        regime = self._detect_regime(query_lower)
        
        # Generate professional quant reasoning
        reasoning = self._generate_quant_reasoning(strategy, regime)
        
        # Calculate confidence
        confidence = 0.92 if strategy != 'general' else 0.85
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Strategy: {strategy}", f"Regime: {regime}"]
        )
    
    def _identify_strategy(self, query: str) -> str:
        """Identify quantitative strategy"""
        strategies = {
            'stat_arb': ['pairs', 'cointegration', 'mean reversion', 'correlation'],
            'momentum': ['momentum', 'trend following', 'breakout', 'acceleration'],
            'ml_alpha': ['machine learning', 'prediction', 'classification', 'features'],
            'volatility': ['volatility', 'variance swap', 'VIX', 'options'],
            'market_making': ['spread', 'order book', 'liquidity', 'microstructure'],
        }
        
        for strategy, keywords in strategies.items():
            if any(kw in query for kw in keywords):
                return strategy
        return 'general'
    
    def _detect_regime(self, query: str) -> str:
        """Detect market regime"""
        if any(w in query for w in ['volatile', 'uncertainty', 'crisis', 'crash']):
            return 'high_volatility'
        if any(w in query for w in ['trending', 'momentum', 'breakout']):
            return 'trending'
        if any(w in query for w in ['range', 'sideways', 'mean reversion']):
            return 'mean_reverting'
        return 'normal'
    
    def _generate_quant_reasoning(self, strategy: str, regime: str) -> str:
        """Generate Citadel-level quant reasoning"""
        reasoning = f"Quantitative analysis ({strategy} strategy): "
        
        if strategy == 'stat_arb':
            reasoning += "Cointegration testing required. Z-score thresholds typically 2.0-2.5σ. "
            reasoning += "Monitor half-life of mean reversion."
        elif strategy == 'momentum':
            reasoning += "Time-series momentum vs cross-sectional. Lookback 1-12 months optimal. "
            reasoning += "Include volatility scaling for risk-adjusted positions."
        elif strategy == 'ml_alpha':
            reasoning += "Feature engineering critical. Avoid overfitting with walk-forward validation. "
            reasoning += "Ensemble methods reduce model risk."
        elif strategy == 'volatility':
            reasoning += "Implied vs realized spread is key edge. GARCH models for forecasting. "
            reasoning += "Delta-hedge frequency impacts P&L."
        
        reasoning += f" Current regime ({regime}) affects strategy capacity and Sharpe."
        
        return reasoning


class FundamentalAnalystAgent(BaseAgent):
    """
    Goldman Sachs-Level Fundamental Analyst
    Expert in: Financial statements, valuation, company analysis
    """
    
    def __init__(self):
        super().__init__(
            name="FundamentalAnalyst",
            role="Goldman Sachs Fundamental Analyst",
            expertise=[
                'financial statement analysis', 'DCF valuation', 'comparable analysis',
                'industry analysis', 'competitive advantage', 'margin analysis',
                'cash flow analysis', 'earnings quality', 'corporate governance'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Identify valuation approach
        valuation = self._identify_valuation(query_lower)
        
        # Check for specific metrics
        metrics = self._identify_metrics(query_lower)
        
        reasoning = self._generate_fundamental_reasoning(valuation, metrics)
        
        confidence = 0.88
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Valuation: {valuation}"] + metrics[:2]
        )
    
    def _identify_valuation(self, query: str) -> str:
        """Identify valuation methodology"""
        if any(w in query for w in ['dcf', 'discounted cash flow', 'free cash flow']):
            return 'DCF'
        if any(w in query for w in ['multiple', 'pe ratio', 'ev/ebitda', 'comparable']):
            return 'Multiples'
        if any(w in query for w in ['nav', 'asset', 'book value']):
            return 'Asset-based'
        return 'Combined'
    
    def _identify_metrics(self, query: str) -> List[str]:
        """Identify financial metrics mentioned"""
        metrics = []
        metric_keywords = {
            'ROE': ['roe', 'return on equity'],
            'ROIC': ['roic', 'return on invested capital'],
            'Margins': ['margin', 'profitability', 'gross margin', 'operating margin'],
            'Growth': ['growth', 'cagr', 'revenue growth', 'earnings growth'],
            'Leverage': ['debt', 'leverage', 'debt/equity', 'interest coverage'],
        }
        
        for metric, keywords in metric_keywords.items():
            if any(kw in query for kw in keywords):
                metrics.append(metric)
        
        return metrics
    
    def _generate_fundamental_reasoning(self, valuation: str, metrics: List[str]) -> str:
        """Generate GS-level fundamental reasoning"""
        reasoning = f"Fundamental analysis ({valuation} approach): "
        
        if valuation == 'DCF':
            reasoning += "Key assumptions: revenue growth, margins, capex, working capital, WACC. "
            reasoning += "Terminal value often 60-80% of total. Sensitivity analysis required."
        elif valuation == 'Multiples':
            reasoning += "Compare to peer group and historical averages. "
            reasoning += "Adjust for growth, profitability, and risk differentials."
        
        if metrics:
            reasoning += f" Focus on {', '.join(metrics[:2])} for quality assessment."
        
        reasoning += " Consider industry dynamics and competitive moat sustainability."
        
        return reasoning


class TechnicalAnalystAgent(BaseAgent):
    """
    Renaissance Technologies-Level Technical Analyst
    Expert in: Chart patterns, indicators, market timing, price action
    """
    
    def __init__(self):
        super().__init__(
            name="TechnicalAnalyst",
            role="Renaissance Technologies Technical Analyst",
            expertise=[
                'price action', 'volume analysis', 'trend analysis', 'support/resistance',
                'momentum indicators', 'volatility analysis', 'intermarket analysis',
                'pattern recognition', 'market breadth', 'market internals'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Identify technical approach
        approach = self._identify_approach(query_lower)
        
        # Detect patterns
        patterns = self._detect_patterns(query_lower)
        
        reasoning = self._generate_technical_reasoning(approach, patterns)
        
        confidence = 0.85 if patterns else 0.78
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Approach: {approach}"] + patterns[:2]
        )
    
    def _identify_approach(self, query: str) -> str:
        """Identify technical approach"""
        if any(w in query for w in ['trend', 'moving average', 'macd']):
            return 'Trend following'
        if any(w in query for w in ['momentum', 'rsi', 'stochastic']):
            return 'Momentum'
        if any(w in query for w in ['volatility', 'bollinger', 'atr']):
            return 'Volatility'
        if any(w in query for w in ['volume', 'obv', 'vwap']):
            return 'Volume'
        return 'Multi-factor'
    
    def _detect_patterns(self, query: str) -> List[str]:
        """Detect chart patterns mentioned"""
        patterns = []
        pattern_list = [
            'head and shoulders', 'double top', 'double bottom', 'triangle',
            'flag', 'pennant', 'wedge', 'channel', 'breakout', 'reversal'
        ]
        for pattern in pattern_list:
            if pattern in query:
                patterns.append(pattern)
        return patterns
    
    def _generate_technical_reasoning(self, approach: str, patterns: List[str]) -> str:
        """Generate Renaissance-level technical reasoning"""
        reasoning = f"Technical analysis ({approach}): "
        
        if patterns:
            reasoning += f"Pattern detected: {patterns[0]}. Measure rule applies for price target. "
            reasoning += "Confirm with volume and momentum divergence."
        else:
            reasoning += "No clear pattern. Focus on trend structure and support/resistance levels."
        
        reasoning += " Multiple timeframe analysis improves signal quality."
        reasoning += " Risk management: position size based on ATR, stops at invalidation."
        
        return reasoning


class MacroStrategistAgent(BaseAgent):
    """
    Bridgewater-Level Macro Strategist
    Expert in: Economic cycles, policy analysis, global markets, regime detection
    """
    
    def __init__(self):
        super().__init__(
            name="MacroStrategist",
            role="Bridgewater Macro Strategist",
            expertise=[
                'economic cycles', 'monetary policy', 'fiscal policy', 'global macro',
                'currency analysis', 'interest rates', 'inflation', 'employment',
                'regime detection', 'risk parity', 'all-weather strategy'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Identify macro theme
        theme = self._identify_theme(query_lower)
        
        # Detect economic regime
        regime = self._detect_economic_regime(query_lower)
        
        reasoning = self._generate_macro_reasoning(theme, regime)
        
        confidence = 0.85
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Theme: {theme}", f"Regime: {regime}"]
        )
    
    def _identify_theme(self, query: str) -> str:
        """Identify macro theme"""
        themes = {
            'monetary_policy': ['fed', 'interest rate', 'qe', 'tightening', 'easing'],
            'inflation': ['inflation', 'cpi', 'deflation', 'hyperinflation', 'pce'],
            'growth': ['gdp', 'recession', 'expansion', 'growth', 'slowdown'],
            'geopolitical': ['war', 'election', 'trade war', 'sanctions', 'brexit'],
            'currency': ['dollar', 'euro', 'yen', 'currency', 'fx', 'exchange rate'],
        }
        
        for theme, keywords in themes.items():
            if any(kw in query for kw in keywords):
                return theme
        return 'general'
    
    def _detect_economic_regime(self, query: str) -> str:
        """Detect economic regime"""
        if any(w in query for w in ['recession', 'crisis', 'contraction', 'slowdown']):
            return 'contraction'
        if any(w in query for w in ['expansion', 'growth', 'boom', 'recovery']):
            return 'expansion'
        if any(w in query for w in ['stagflation', 'inflation', 'high rates']):
            return 'stagflation'
        return 'neutral'
    
    def _generate_macro_reasoning(self, theme: str, regime: str) -> str:
        """Generate Bridgewater-level macro reasoning"""
        reasoning = f"Macro analysis ({theme.replace('_', ' ')}): "
        
        if theme == 'monetary_policy':
            reasoning += "Central bank policy drives asset prices. Watch for forward guidance changes. "
            reasoning += "Rate cuts typically bullish for equities, bearish for currency."
        elif theme == 'inflation':
            reasoning += "Inflation regime determines asset correlations. "
            reasoning += "High inflation: commodities outperform, bonds underperform."
        elif theme == 'growth':
            reasoning += "Growth outlook affects cyclical vs defensive positioning. "
            reasoning += "Leading indicators: PMI, yield curve, credit spreads."
        
        reasoning += f" Current regime ({regime}) suggests portfolio adjustments."
        
        return reasoning


class RiskManagerAgent(BaseAgent):
    """
    Two Sigma-Level Risk Manager
    Expert in: Portfolio risk, hedging, drawdown control, stress testing
    """
    
    def __init__(self):
        super().__init__(
            name="RiskManager",
            role="Two Sigma Risk Manager",
            expertise=[
                'portfolio risk', 'value at risk', 'stress testing', 'scenario analysis',
                'hedging strategies', 'drawdown control', 'position sizing',
                'correlation risk', 'tail risk', 'liquidity risk'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Identify risk type
        risk_type = self._identify_risk_type(query_lower)
        
        # Check for portfolio context
        portfolio = self._check_portfolio_context(query_lower)
        
        reasoning = self._generate_risk_reasoning(risk_type, portfolio)
        
        confidence = 0.88
        
        return AgentPosition(
            agent_name=self.name,
            stance='critical' if risk_type in ['tail', 'liquidity'] else 'analytical',
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Risk: {risk_type}"] + (["Portfolio context"] if portfolio else [])
        )
    
    def _identify_risk_type(self, query: str) -> str:
        """Identify risk type"""
        if any(w in query for w in ['var', 'value at risk', 'volatility']):
            return 'market'
        if any(w in query for w in ['tail', 'black swan', 'extreme']):
            return 'tail'
        if any(w in query for w in ['liquidity', 'bid ask', 'slippage']):
            return 'liquidity'
        if any(w in query for w in ['correlation', 'diversification', 'concentration']):
            return 'correlation'
        return 'general'
    
    def _check_portfolio_context(self, query: str) -> bool:
        """Check for portfolio context"""
        return any(w in query for w in ['portfolio', 'allocation', 'position', 'exposure'])
    
    def _generate_risk_reasoning(self, risk_type: str, portfolio: bool) -> str:
        """Generate risk management reasoning"""
        reasoning = f"Risk assessment ({risk_type} risk): "
        
        if risk_type == 'market':
            reasoning += "VaR and Expected Shortfall key metrics. Historical vs parametric vs Monte Carlo. "
            reasoning += "95% VaR underestimates tail risk; use 99% or Expected Shortfall."
        elif risk_type == 'tail':
            reasoning += "Tail risk hedging: options, VIX, trend following, alternative risk premia. "
            reasoning += "Black swan events require active hedging, not diversification."
        elif risk_type == 'liquidity':
            reasoning += "Liquidity risk often underestimated. Stress test with 5x normal spreads. "
            reasoning += "Position sizing must consider exit horizon."
        
        if portfolio:
            reasoning += " Portfolio context: correlations increase in stress."
        
        return reasoning


class PortfolioManagerAgent(BaseAgent):
    """
    BlackRock-Level Portfolio Manager
    Expert in: Asset allocation, optimization, rebalancing, implementation
    """
    
    def __init__(self):
        super().__init__(
            name="PortfolioManager",
            role="BlackRock Portfolio Manager",
            expertise=[
                'asset allocation', 'portfolio optimization', 'rebalancing',
                'factor investing', 'smart beta', 'implementation',
                'tax efficiency', 'transaction costs', 'best execution'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Identify portfolio task
        task = self._identify_task(query_lower)
        
        # Check constraints
        constraints = self._identify_constraints(query_lower)
        
        reasoning = self._generate_portfolio_reasoning(task, constraints)
        
        confidence = 0.85
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Task: {task}"] + constraints[:2]
        )
    
    def _identify_task(self, query: str) -> str:
        """Identify portfolio task"""
        if any(w in query for w in ['allocate', 'allocation', 'weights']):
            return 'asset_allocation'
        if any(w in query for w in ['rebalance', 'rebalancing', 'drift']):
            return 'rebalancing'
        if any(w in query for w in ['optimize', 'optimization', 'efficient frontier']):
            return 'optimization'
        if any(w in query for w in ['factor', 'smart beta', 'tilt']):
            return 'factor_investing'
        return 'general'
    
    def _identify_constraints(self, query: str) -> List[str]:
        """Identify portfolio constraints"""
        constraints = []
        if any(w in query for w in ['long only', 'no short']):
            constraints.append('Long-only')
        if any(w in query for w in ['turnover', 'transaction cost']):
            constraints.append('Turnover limits')
        if any(w in query for w in ['tracking error', 'benchmark']):
            constraints.append('Tracking error budget')
        if any(w in query for w in ['tax', 'harvest', 'gain']):
            constraints.append('Tax considerations')
        return constraints
    
    def _generate_portfolio_reasoning(self, task: str, constraints: List[str]) -> str:
        """Generate portfolio management reasoning"""
        reasoning = f"Portfolio management ({task.replace('_', ' ')}): "
        
        if task == 'asset_allocation':
            reasoning += "Strategic vs tactical allocation. Consider risk tolerance, horizon, goals. "
            reasoning += "Mean-variance optimization with constraints."
        elif task == 'rebalancing':
            reasoning += "Rebalancing rules: calendar vs threshold vs hybrid. "
            reasoning += "Transaction costs vs tracking error tradeoff."
        elif task == 'optimization':
            reasoning += "Markowitz mean-variance or Black-Litterman for views. "
            reasoning += "Resampling or robust optimization for estimation error."
        elif task == 'factor_investing':
            reasoning += "Factor premia: value, momentum, quality, low vol, size. "
            reasoning += "Factor timing difficult; strategic allocation preferred."
        
        if constraints:
            reasoning += f" Constraints: {', '.join(constraints)}."
        
        return reasoning


class FinanceAI(MultiAgentSystem):
    """
    Citadel-Level Finance Intelligence System
    Multi-agent architecture for comprehensive financial analysis
    """
    
    def __init__(self):
        super().__init__(domain_name='Finance', max_rounds=4)
        
        # Register all specialized agents
        self.register_agent(QuantitativeAnalystAgent())
        self.register_agent(FundamentalAnalystAgent())
        self.register_agent(TechnicalAnalystAgent())
        self.register_agent(MacroStrategistAgent())
        self.register_agent(RiskManagerAgent())
        self.register_agent(PortfolioManagerAgent())
    
    def analyze_investment(self, ticker: str, context: Dict = None) -> str:
        """
        Comprehensive investment analysis
        Returns Citadel-level analysis
        """
        query = f"Investment analysis for {ticker}"
        context = context or {}
        
        session_id = self.start_debate(query, context)
        
        import time
        max_wait = 60
        waited = 0
        while waited < max_wait:
            status = self.get_session_status(session_id)
            if status['status'] == 'complete':
                break
            time.sleep(0.5)
            waited += 0.5
        
        result = self.get_result(session_id)
        if result:
            return self._format_citadel_analysis(result)
        return "Finance analysis in progress..."
    
    def _format_citadel_analysis(self, result: DebateResult) -> str:
        """Format analysis in Citadel style"""
        sections = []
        
        consensus = "STRATEGIC CONSENSUS" if result.consensus_reached else "MULTI-FACTOR ANALYSIS"
        confidence = int(result.confidence * 100)
        
        sections.append(f"## {consensus}")
        sections.append(f"**Confidence Level: {confidence}%**\n")
        sections.append(result.final_answer)
        sections.append("")
        
        sections.append("## Investment Committee Analysis")
        for pos in result.agent_positions:
            emoji = {
                'QuantitativeAnalyst': '📊',
                'FundamentalAnalyst': '📈',
                'TechnicalAnalyst': '📉',
                'MacroStrategist': '🌍',
                'RiskManager': '⚠️',
                'PortfolioManager': '💼'
            }.get(pos.agent, '💡')
            
            sections.append(f"### {emoji} {pos.agent.replace('Agent', '')} ({pos.confidence:.0%})")
            sections.append(f"**{pos.stance.upper()}** | {pos.reasoning}\n")
            
            if pos.key_points:
                sections.append("Key Factors:")
                for point in pos.key_points[:2]:
                    sections.append(f"- {point}")
                sections.append("")
        
        return "\n".join(sections)


# Singleton instance
finance_ai = FinanceAI()
