"""
BacktestService - Realistic trading simulation with slippage
Phase 5 Implementation
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from core.data_structures import (
    OrderDecision, OrderType, TradeExecution, BacktestResult, PerformanceMetrics
)
from core.exceptions import BacktestError

log = logging.getLogger(__name__)


class FillProbability(Enum):
    """Likelihood of order fill"""
    GUARANTEED = 1.0
    HIGH = 0.95
    MEDIUM = 0.80
    LOW = 0.60


@dataclass
class MarketImpact:
    """Market impact model for large orders"""
    temporary_impact: float  # Immediate price impact
    permanent_impact: float  # Long-term drift
    decay_time: int  # Minutes to decay


@dataclass
class SlippageModel:
    """Slippage model configuration"""
    base_slippage_bps: float = 5.0  # 5 bps base
    volatility_multiplier: float = 2.0
    volume_discount: float = 0.5
    
    def calculate(self, price: float, volatility: float, 
                  volume_ratio: float, order_size: float) -> float:
        """Calculate slippage in price terms"""
        # Base slippage
        slippage = self.base_slippage_bps / 10000 * price
        
        # Volatility adjustment
        slippage *= (1 + volatility * self.volatility_multiplier)
        
        # Volume discount (higher volume = less slippage)
        slippage *= (1 - min(volume_ratio, 0.5) * self.volume_discount)
        
        # Size penalty (larger orders = more slippage)
        if order_size > 0.02:  # >2% of ADV
            slippage *= (1 + (order_size - 0.02) * 10)
        
        return slippage


@dataclass
class CommissionModel:
    """Commission and fee structure"""
    per_share: float = 0.005  # $0.005/share
    min_per_order: float = 1.0  # $1 minimum
    max_pct: float = 0.01  # 1% max
    
    def calculate(self, shares: int, price: float) -> float:
        """Calculate commission"""
        commission = shares * self.per_share
        notional = shares * price
        commission = max(commission, self.min_per_order)
        commission = min(commission, notional * self.max_pct)
        return commission


class BacktestService:
    """
    Realistic backtesting service with slippage and imperfect fills
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 slippage_model: Optional[SlippageModel] = None,
                 commission_model: Optional[CommissionModel] = None):
        
        self.initial_capital = initial_capital
        self.slippage = slippage_model or SlippageModel()
        self.commission = commission_model or CommissionModel()
        
        # State
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}  # symbol -> position info
        self.trade_history: List[TradeExecution] = []
        self.daily_values: List[Dict] = []
        
        log.info(f"BacktestService initialized with ${initial_capital:,.0f}")
    
    def simulate_execution(self, order: OrderDecision,
                          market_data: Dict) -> Optional[TradeExecution]:
        """
        Simulate realistic trade execution
        
        Args:
            order: Order to execute
            market_data: Dict with price, volume, volatility, spread
            
        Returns:
            TradeExecution or None if fill failed
        """
        symbol = order.symbol
        
        # Skip HOLD orders
        if order.order_type == OrderType.HOLD:
            return None
        
        # Determine fill probability
        fill_prob = self._calculate_fill_probability(order, market_data)
        
        # Random fill check
        if np.random.random() > fill_prob.value:
            log.info(f"Order {symbol} failed to fill (prob: {fill_prob.value:.1%})")
            return None
        
        # Get market price
        mid_price = market_data.get('price', 0)
        spread = market_data.get('spread', 0.001)  # 10 bps default
        
        # Apply slippage
        volatility = market_data.get('volatility', 0.20)
        volume_ratio = market_data.get('volume_ratio', 0.1)
        
        slippage = self.slippage.calculate(
            mid_price, volatility, volume_ratio, order.position_size_pct
        )
        
        # Direction: buy = pay more, sell = receive less
        if order.order_type in [OrderType.MARKET_BUY, OrderType.LIMIT_BUY]:
            execution_price = mid_price + slippage + (spread * mid_price / 2)
            side = 'buy'
        else:
            execution_price = mid_price - slippage - (spread * mid_price / 2)
            side = 'sell'
        
        # Calculate shares
        portfolio_value = self._get_portfolio_value(market_data)
        position_value = portfolio_value * order.position_size_pct
        shares = int(position_value / execution_price)
        
        if shares < 1:
            log.warning(f"Order {symbol} too small ({position_value:.2f})")
            return None
        
        # Calculate commission
        commission = self.commission.calculate(shares, execution_price)
        
        # Create execution
        execution = TradeExecution(
            symbol=symbol,
            side=side,
            shares=shares,
            price=execution_price,
            commission=commission,
            slippage=slippage,
            timestamp=datetime.now(),
            expected_price=mid_price,
            fill_quality='good' if slippage < 0.001 else 'fair'
        )
        
        # Update state
        self._update_state(execution, market_data)
        self.trade_history.append(execution)
        
        log.info(f"Executed {side} {shares} {symbol} @ ${execution_price:.2f} "
                f"(slippage: ${slippage:.3f}, comm: ${commission:.2f})")
        
        return execution
    
    def run_backtest(self, orders: List[OrderDecision],
                    price_data: Dict[str, List[Dict]]) -> BacktestResult:
        """
        Run full backtest simulation
        
        Args:
            orders: List of order decisions to execute
            price_data: Dict mapping symbol to list of price bars
            
        Returns:
            BacktestResult with full performance metrics
        """
        log.info(f"Starting backtest with {len(orders)} orders")
        
        # Reset state
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.daily_values = []
        
        # Execute orders chronologically
        for order in sorted(orders, key=lambda o: o.timestamp or datetime.min):
            symbol = order.symbol
            
            # Get price data for this symbol/date
            if symbol not in price_data:
                continue
            
            # Find relevant price bar
            price_bar = self._find_price_bar(price_data[symbol], order.timestamp)
            if not price_bar:
                continue
            
            # Simulate execution
            execution = self.simulate_execution(order, price_bar)
            
            if execution:
                # Record daily value
                self._record_daily_value(price_bar['date'])
        
        # Calculate final metrics
        final_value = self._get_portfolio_value(price_bar) if price_bar else self.cash
        
        return self._calculate_backtest_result(final_value)
    
    def _calculate_fill_probability(self, order: OrderDecision,
                                   market_data: Dict) -> FillProbability:
        """Calculate probability of fill based on market conditions"""
        # Base on order urgency
        urgency = order.constraints.get('urgency', 'normal')
        
        if urgency == 'high':
            return FillProbability.HIGH
        elif urgency == 'low':
            # Check liquidity
            volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', volume)
            
            if volume < avg_volume * 0.5:
                return FillProbability.LOW
            elif volume > avg_volume * 1.5:
                return FillProbability.HIGH
            else:
                return FillProbability.MEDIUM
        
        return FillProbability.HIGH
    
    def _update_state(self, execution: TradeExecution, market_data: Dict):
        """Update portfolio state after execution"""
        symbol = execution.symbol
        notional = execution.shares * execution.price + execution.commission
        
        if execution.side == 'buy':
            self.cash -= notional
            
            if symbol in self.positions:
                # Update existing position
                pos = self.positions[symbol]
                total_cost = pos['shares'] * pos['avg_price'] + execution.shares * execution.price
                total_shares = pos['shares'] + execution.shares
                pos['shares'] = total_shares
                pos['avg_price'] = total_cost / total_shares
            else:
                # New position
                self.positions[symbol] = {
                    'shares': execution.shares,
                    'avg_price': execution.price,
                    'entry_date': market_data.get('date', datetime.now())
                }
        else:  # sell
            self.cash += (execution.shares * execution.price - execution.commission)
            
            if symbol in self.positions:
                self.positions[symbol]['shares'] -= execution.shares
                if self.positions[symbol]['shares'] <= 0:
                    del self.positions[symbol]
    
    def _get_portfolio_value(self, market_data: Dict) -> float:
        """Calculate current portfolio value"""
        position_value = sum(
            pos['shares'] * market_data.get('price', pos['avg_price'])
            for pos in self.positions.values()
        )
        return self.cash + position_value
    
    def _record_daily_value(self, date):
        """Record daily portfolio value"""
        self.daily_values.append({
            'date': date,
            'cash': self.cash,
            'positions': len(self.positions)
        })
    
    def _find_price_bar(self, price_bars: List[Dict], timestamp) -> Optional[Dict]:
        """Find price bar closest to timestamp"""
        if not timestamp:
            return price_bars[0] if price_bars else None
        
        for bar in price_bars:
            if bar.get('date') >= timestamp:
                return bar
        
        return price_bars[-1] if price_bars else None
    
    def _calculate_backtest_result(self, final_value: float) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Calculate trade statistics
        if not self.trade_history:
            return BacktestResult(
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                num_trades=0,
                avg_trade_return=0.0,
                trades=[]
            )
        
        # PnL per trade
        trade_pnls = []
        for trade in self.trade_history:
            # Simplified PnL calculation
            pnl = trade.shares * (trade.price - trade.expected_price)
            pnl -= trade.commission
            trade_pnls.append(pnl)
        
        winning_trades = [p for p in trade_pnls if p > 0]
        losing_trades = [p for p in trade_pnls if p < 0]
        
        win_rate = len(winning_trades) / len(trade_pnls) if trade_pnls else 0
        
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0.001
        profit_factor = gross_profit / gross_loss
        
        # Approximate Sharpe (simplified)
        if len(self.daily_values) > 1:
            returns = []
            for i in range(1, len(self.daily_values)):
                prev = self.daily_values[i-1]['cash']
                curr = self.daily_values[i]['cash']
                if prev > 0:
                    returns.append((curr - prev) / prev)
            
            if returns and len(returns) > 1:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe = 0
        else:
            sharpe = 0
        
        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=self._calculate_max_drawdown(),
            win_rate=win_rate,
            profit_factor=profit_factor,
            num_trades=len(self.trade_history),
            avg_trade_return=np.mean(trade_pnls) if trade_pnls else 0,
            trades=self.trade_history
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not self.daily_values:
            return 0.0
        
        # Simplified - use cash as equity proxy
        values = [v['cash'] for v in self.daily_values]
        
        peak = values[0]
        max_dd = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def get_trade_report(self) -> str:
        """Generate trade report"""
        if not self.trade_history:
            return "No trades executed"
        
        lines = []
        lines.append("=" * 60)
        lines.append("TRADE EXECUTION REPORT")
        lines.append("=" * 60)
        
        for i, trade in enumerate(self.trade_history, 1):
            lines.append(f"\nTrade #{i}")
            lines.append(f"  Symbol: {trade.symbol}")
            lines.append(f"  Side: {trade.side.upper()}")
            lines.append(f"  Shares: {trade.shares:,}")
            lines.append(f"  Price: ${trade.price:.2f}")
            lines.append(f"  Slippage: ${trade.slippage:.3f}")
            lines.append(f"  Commission: ${trade.commission:.2f}")
            lines.append(f"  Fill Quality: {trade.fill_quality}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# Global instance
backtest_service = BacktestService()
