"""
Execution Realism System
Trade simulation with slippage, delayed execution, position management,
risk constraints, and performance tracking. NO FAKING - Real trading conditions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random
import numpy as np

log = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class TradeOrder:
    """Represents a trade order"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    
    # Execution details (filled when order executes)
    fill_price: Optional[float] = None
    fill_quantity: float = 0.0
    fill_timestamp: Optional[datetime] = None
    slippage: float = 0.0
    commission: float = 0.0
    
    # Rejection reason
    rejection_reason: Optional[str] = None


@dataclass
class Position:
    """Represents a position in a stock"""
    symbol: str
    quantity: float = 0.0
    average_entry_price: float = 0.0
    current_price: float = 0.0
    
    # Entry tracking
    entry_date: Optional[datetime] = None
    entry_orders: List[str] = field(default_factory=list)
    
    # Exit tracking
    exit_date: Optional[datetime] = None
    exit_orders: List[str] = field(default_factory=list)
    is_closed: bool = False
    
    # Stop-loss tracking
    stop_loss_price: Optional[float] = None
    stop_loss_triggered: bool = False
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        if self.quantity == 0:
            return 0.0
        return self.quantity * (self.current_price - self.average_entry_price)
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.average_entry_price == 0:
            return 0.0
        return (self.current_price - self.average_entry_price) / self.average_entry_price


@dataclass
class Trade:
    """Represents a completed trade"""
    trade_id: str
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    exit_price: float
    entry_date: datetime
    exit_date: datetime
    
    # PnL
    realized_pnl: float = 0.0
    realized_pnl_pct: float = 0.0
    
    # Costs
    total_commission: float = 0.0
    total_slippage: float = 0.0
    
    # Exit reason
    exit_reason: str = ""  # 'manual', 'stop_loss', 'take_profit', 'system'


class SlippageModel:
    """
    Models realistic slippage based on market conditions.
    Slippage increases with:
    - Higher volatility
    - Larger order size relative to average volume
    - Market orders vs limit orders
    - Lower liquidity stocks
    """
    
    BASE_SLIPPAGE_PCT = 0.0005  # 5 basis points base
    
    def __init__(self):
        self.volatility_regime = "normal"  # normal, high, extreme
    
    def calculate_slippage(self, 
                          order: TradeOrder,
                          current_price: float,
                          avg_volume_30d: float,
                          volatility_20d: float) -> float:
        """Calculate expected slippage for an order"""
        
        # Base slippage
        slippage = self.BASE_SLIPPAGE_PCT
        
        # Volatility adjustment (annualized vol)
        if volatility_20d > 0.5:  # > 50% annualized
            slippage *= 3.0  # 3x slippage in high vol
        elif volatility_20d > 0.3:  # > 30% annualized
            slippage *= 1.5  # 1.5x slippage in elevated vol
        
        # Order size impact (if order > 1% of daily volume, more slippage)
        if avg_volume_30d > 0:
            volume_pct = order.quantity / avg_volume_30d
            if volume_pct > 0.10:  # Order > 10% of daily volume
                slippage *= 2.0
            elif volume_pct > 0.05:  # Order > 5% of daily volume
                slippage *= 1.5
            elif volume_pct > 0.01:  # Order > 1% of daily volume
                slippage *= 1.2
        
        # Order type adjustment
        if order.order_type == OrderType.MARKET:
            slippage *= 1.0  # Base
        elif order.order_type == OrderType.LIMIT:
            slippage *= 0.3  # Less slippage with limit orders
        
        # Add randomness (slippage varies)
        random_factor = random.uniform(0.8, 1.2)
        slippage *= random_factor
        
        # Calculate dollar slippage
        dollar_slippage = current_price * slippage
        
        log.debug(f"Slippage for {order.symbol}: {slippage:.4%} (${dollar_slippage:.4f})")
        
        return dollar_slippage


class ExecutionSimulator:
    """
    Simulates real trade execution with:
    - Slippage
    - Delayed fills
    - Partial fills
    - Rejections for risk violations
    """
    
    def __init__(self):
        self.slippage_model = SlippageModel()
        self.commission_per_share = 0.005  # $0.005 per share (typical retail)
        self.min_commission = 1.0  # $1 minimum
        self.max_commission = 0.01  # 1% of trade value cap
        
        # Execution delay (seconds)
        self.base_delay = 1.0  # 1 second base
        self.market_hours_only = True
    
    def simulate_execution(self, 
                          order: TradeOrder,
                          current_price: float,
                          avg_volume_30d: float = 1000000,
                          volatility_20d: float = 0.25) -> TradeOrder:
        """Simulate order execution with realistic conditions"""
        
        # Simulate execution delay
        import time
        delay = self.base_delay * random.uniform(0.5, 2.0)
        time.sleep(min(delay, 0.1))  # Cap at 100ms for sim speed
        
        # Calculate fill timestamp
        order.fill_timestamp = datetime.now()
        
        # Calculate slippage
        slippage = self.slippage_model.calculate_slippage(
            order, current_price, avg_volume_30d, volatility_20d
        )
        
        # Apply slippage to fill price (always against the trader)
        if order.side == OrderSide.BUY:
            order.fill_price = current_price + slippage
        else:  # SELL
            order.fill_price = current_price - slippage
        
        order.slippage = slippage
        
        # Calculate commission
        commission = max(
            self.min_commission,
            min(
                order.quantity * self.commission_per_share,
                order.fill_price * order.quantity * self.max_commission
            )
        )
        order.commission = commission
        
        # Simulate partial fills for large orders
        if avg_volume_30d > 0:
            volume_pct = order.quantity / avg_volume_30d
            if volume_pct > 0.20:  # Very large order
                fill_ratio = random.uniform(0.7, 0.95)
                order.fill_quantity = order.quantity * fill_ratio
                order.status = OrderStatus.PARTIAL
            else:
                order.fill_quantity = order.quantity
                order.status = OrderStatus.FILLED
        else:
            order.fill_quantity = order.quantity
            order.status = OrderStatus.FILLED
        
        log.info(f"Order {order.order_id} executed: {order.side.value} {order.fill_quantity} "
                f"{order.symbol} @ ${order.fill_price:.2f} "
                f"(slippage: ${order.slippage:.2f}, comm: ${order.commission:.2f})")
        
        return order


class RiskManager:
    """
    Risk management with:
    - Max position size limits
    - Stop-loss logic
    - Daily loss limits
    - Concentration limits
    """
    
    def __init__(self, portfolio_value: float = 100000.0):
        self.portfolio_value = portfolio_value
        
        # Risk parameters
        self.max_position_pct = 0.10  # Max 10% in single position
        self.max_position_value = portfolio_value * self.max_position_pct
        
        self.max_single_trade_pct = 0.05  # Max 5% in single trade
        self.max_single_trade_value = portfolio_value * self.max_single_trade_pct
        
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.trailing_stop_pct = 0.08  # 8% trailing stop
        
        self.max_daily_loss_pct = 0.02  # 2% daily loss limit
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Track violations
        self.violations: List[Dict[str, Any]] = []
    
    def check_order_risk(self, order: TradeOrder, 
                         current_positions: Dict[str, Position]) -> Tuple[bool, Optional[str]]:
        """Check if order passes risk checks"""
        
        # Reset daily PnL if new day
        if datetime.now().date() != self.last_reset_date:
            self.daily_pnl = 0.0
            self.last_reset_date = datetime.now().date()
        
        # Check daily loss limit
        if self.daily_pnl < -self.portfolio_value * self.max_daily_loss_pct:
            return False, "Daily loss limit reached - trading halted"
        
        # Check position size limit
        position_value = order.quantity * (order.limit_price or 100)  # Estimate
        if position_value > self.max_position_value:
            return False, f"Position size ${position_value:.2f} exceeds max ${self.max_position_value:.2f}"
        
        # Check single trade limit
        trade_value = order.quantity * (order.limit_price or 100)
        if trade_value > self.max_single_trade_value:
            return False, f"Trade size ${trade_value:.2f} exceeds max ${self.max_single_trade_value:.2f}"
        
        # Check if we already have max position in this symbol
        existing_position = current_positions.get(order.symbol)
        if existing_position:
            if order.side == OrderSide.BUY:
                new_quantity = existing_position.quantity + order.quantity
                new_value = new_quantity * (order.limit_price or existing_position.current_price)
                if new_value > self.max_position_value:
                    return False, f"Adding to position would exceed max size"
        
        # Check concentration (total positions)
        total_position_value = sum(p.market_value for p in current_positions.values())
        if total_position_value > self.portfolio_value * 0.80:  # 80% invested
            # Still allow closes, but not new opens
            if order.side == OrderSide.BUY and not existing_position:
                return False, "Portfolio at 80% capacity - close positions before opening new ones"
        
        return True, None
    
    def check_stop_loss(self, position: Position, current_price: float) -> bool:
        """Check if stop loss should be triggered"""
        if position.quantity == 0 or position.average_entry_price == 0:
            return False
        
        # Fixed stop loss
        stop_price = position.average_entry_price * (1 - self.stop_loss_pct)
        
        if current_price <= stop_price:
            position.stop_loss_triggered = True
            position.stop_loss_price = stop_price
            log.warning(f"Stop loss triggered for {position.symbol}: "
                       f"price ${current_price:.2f} <= stop ${stop_price:.2f}")
            return True
        
        return False
    
    def update_daily_pnl(self, pnl: float):
        """Update daily PnL"""
        self.daily_pnl += pnl
        log.info(f"Daily PnL updated: ${self.daily_pnl:.2f}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk status"""
        return {
            'portfolio_value': self.portfolio_value,
            'daily_pnl': self.daily_pnl,
            'daily_loss_limit': -self.portfolio_value * self.max_daily_loss_pct,
            'max_position_pct': self.max_position_pct,
            'max_position_value': self.max_position_value,
            'stop_loss_pct': self.stop_loss_pct,
            'trailing_stop_pct': self.trailing_stop_pct,
            'violations_24h': len([v for v in self.violations 
                                  if datetime.now() - v['timestamp'] < timedelta(hours=24)]),
            'risk_status': 'green' if self.daily_pnl > -self.portfolio_value * self.max_daily_loss_pct * 0.5 else 'yellow' if self.daily_pnl > -self.portfolio_value * self.max_daily_loss_pct else 'red'
        }


class PerformanceTracker:
    """
    Tracks portfolio performance:
    - PnL (realized and unrealized)
    - Drawdown
    - Win rate
    - Sharpe ratio
    - Trade statistics
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Track trades
        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Position] = {}
        
        # Performance history
        self.daily_returns: List[float] = []
        self.equity_curve: List[Tuple[datetime, float]] = [(datetime.now(), initial_capital)]
        
        # Peak for drawdown calculation
        self.peak_capital = initial_capital
        self.max_drawdown = 0.0
        self.max_drawdown_date: Optional[datetime] = None
    
    def record_trade(self, trade: Trade):
        """Record a completed trade"""
        self.trades.append(trade)
        
        # Update capital
        if trade.side == OrderSide.BUY:
            self.current_capital -= (trade.entry_price * trade.quantity + trade.total_commission)
        else:  # SELL
            self.current_capital += (trade.exit_price * trade.quantity - trade.total_commission)
        
        # Update equity curve
        self.equity_curve.append((datetime.now(), self.current_capital))
        
        # Update drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        else:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
                self.max_drawdown_date = datetime.now()
        
        log.info(f"Trade recorded: {trade.symbol} {trade.side.value} PnL: ${trade.realized_pnl:.2f}")
    
    def update_position(self, position: Position):
        """Update an open position"""
        self.open_positions[position.symbol] = position
    
    def close_position(self, symbol: str, close_price: float, 
                      close_date: datetime, exit_reason: str = "manual"):
        """Close a position and record the trade"""
        if symbol not in self.open_positions:
            return
        
        position = self.open_positions[symbol]
        
        # Calculate realized PnL
        if position.quantity > 0:
            realized_pnl = position.quantity * (close_price - position.average_entry_price)
            realized_pnl_pct = (close_price - position.average_entry_price) / position.average_entry_price
        else:
            realized_pnl = 0
            realized_pnl_pct = 0
        
        # Create trade record
        trade = Trade(
            trade_id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}",
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=position.quantity,
            entry_price=position.average_entry_price,
            exit_price=close_price,
            entry_date=position.entry_date or datetime.now(),
            exit_date=close_date,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            total_commission=0.0,  # Would be calculated
            total_slippage=0.0,
            exit_reason=exit_reason
        )
        
        # Mark position as closed
        position.is_closed = True
        position.exit_date = close_date
        
        # Record trade
        self.record_trade(trade)
        
        # Remove from open positions
        del self.open_positions[symbol]
        
        return trade
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.trades:
            return {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_return': 0.0,
                'total_trades': 0,
                'status': 'No trades yet'
            }
        
        # Calculate statistics
        winning_trades = [t for t in self.trades if t.realized_pnl > 0]
        losing_trades = [t for t in self.trades if t.realized_pnl <= 0]
        
        total_pnl = sum(t.realized_pnl for t in self.trades)
        gross_profit = sum(t.realized_pnl for t in winning_trades)
        gross_loss = sum(t.realized_pnl for t in losing_trades)
        
        # Average trade metrics
        avg_win = gross_profit / len(winning_trades) if winning_trades else 0
        avg_loss = gross_loss / len(losing_trades) if losing_trades else 0
        
        # Calculate Sharpe-like ratio (simplified)
        if len(self.daily_returns) > 1:
            avg_return = np.mean(self.daily_returns)
            std_return = np.std(self.daily_returns)
            sharpe = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe = 0
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return_pct': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100 if self.trades else 0,
            'profit_factor': abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf'),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown_pct': self.max_drawdown * 100,
            'max_drawdown_date': self.max_drawdown_date.isoformat() if self.max_drawdown_date else None,
            'sharpe_ratio': sharpe,
            'open_positions': len(self.open_positions),
            'unrealized_pnl': sum(p.unrealized_pnl for p in self.open_positions.values()),
            'current_equity': self.current_capital + sum(p.market_value for p in self.open_positions.values())
        }
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history"""
        recent = self.trades[-limit:]
        return [
            {
                'trade_id': t.trade_id,
                'symbol': t.symbol,
                'side': t.side.value,
                'quantity': t.quantity,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'realized_pnl': t.realized_pnl,
                'realized_pnl_pct': t.realized_pnl_pct * 100,
                'exit_reason': t.exit_reason,
                'entry_date': t.entry_date.isoformat(),
                'exit_date': t.exit_date.isoformat()
            }
            for t in reversed(recent)
        ]


class RealisticExecutionEngine:
    """
    Main execution engine that combines all realism components:
    - Simulates real trading conditions
    - Manages positions
    - Enforces risk constraints
    - Tracks performance
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        
        # Components
        self.simulator = ExecutionSimulator()
        self.risk_manager = RiskManager(initial_capital)
        self.performance_tracker = PerformanceTracker(initial_capital)
        
        # Order tracking
        self.orders: Dict[str, TradeOrder] = {}
        self.order_counter = 0
        
        # Market data cache
        self.market_data: Dict[str, Dict[str, Any]] = {}
        
        log.info(f"Realistic Execution Engine initialized with ${initial_capital:,.2f} capital")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self.order_counter += 1
        return f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_counter}"
    
    def submit_order(self, symbol: str, side: OrderSide, quantity: float,
                    order_type: OrderType = OrderType.MARKET,
                    limit_price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> TradeOrder:
        """Submit an order for execution"""
        
        # Create order
        order = TradeOrder(
            order_id=self._generate_order_id(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price
        )
        
        # Risk check
        passed, reason = self.risk_manager.check_order_risk(
            order, self.performance_tracker.open_positions
        )
        
        if not passed:
            order.status = OrderStatus.REJECTED
            order.rejection_reason = reason
            log.warning(f"Order rejected: {reason}")
            self.orders[order.order_id] = order
            return order
        
        # Get market data for execution
        current_price = self._get_current_price(symbol)
        avg_volume = self._get_avg_volume(symbol)
        volatility = self._get_volatility(symbol)
        
        # Simulate execution
        filled_order = self.simulator.simulate_execution(
            order, current_price, avg_volume, volatility
        )
        
        # Update positions
        self._update_position(filled_order)
        
        # Store order
        self.orders[order.order_id] = filled_order
        
        return filled_order
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price (would fetch from data source in production)"""
        # Simplified - would use data ingestion layer
        if symbol in self.market_data:
            return self.market_data[symbol].get('price', 100.0)
        return 100.0  # Default
    
    def _get_avg_volume(self, symbol: str) -> float:
        """Get 30-day average volume"""
        if symbol in self.market_data:
            return self.market_data[symbol].get('avg_volume', 1000000)
        return 1000000  # Default
    
    def _get_volatility(self, symbol: str) -> float:
        """Get 20-day volatility"""
        if symbol in self.market_data:
            return self.market_data[symbol].get('volatility', 0.25)
        return 0.25  # Default 25%
    
    def _update_position(self, order: TradeOrder):
        """Update position based on filled order"""
        symbol = order.symbol
        
        if symbol not in self.performance_tracker.open_positions:
            # New position
            position = Position(
                symbol=symbol,
                quantity=order.fill_quantity if order.side == OrderSide.BUY else -order.fill_quantity,
                average_entry_price=order.fill_price or 0,
                current_price=order.fill_price or 0,
                entry_date=order.fill_timestamp,
                entry_orders=[order.order_id]
            )
            self.performance_tracker.update_position(position)
        else:
            # Update existing position
            position = self.performance_tracker.open_positions[symbol]
            
            if order.side == OrderSide.BUY:
                # Adding to long position
                total_cost = (position.quantity * position.average_entry_price + 
                            order.fill_quantity * order.fill_price)
                position.quantity += order.fill_quantity
                position.average_entry_price = total_cost / position.quantity
            else:
                # Reducing/closing position
                position.quantity -= order.fill_quantity
                
                if position.quantity <= 0:
                    # Close position
                    self.performance_tracker.close_position(
                        symbol, order.fill_price or 0, 
                        order.fill_timestamp or datetime.now(),
                        'manual'
                    )
                else:
                    position.exit_orders.append(order.order_id)
    
    def check_stop_losses(self):
        """Check all positions for stop loss triggers"""
        for symbol, position in list(self.performance_tracker.open_positions.items()):
            current_price = self._get_current_price(symbol)
            
            if self.risk_manager.check_stop_loss(position, current_price):
                # Trigger stop loss order
                self.submit_order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
    
    def update_market_data(self, symbol: str, price: float, 
                          volume: float = 0, volatility: float = 0.25):
        """Update market data cache"""
        self.market_data[symbol] = {
            'price': price,
            'volume': volume,
            'avg_volume': volume,  # Simplified
            'volatility': volatility,
            'timestamp': datetime.now()
        }
        
        # Update positions with new price
        if symbol in self.performance_tracker.open_positions:
            self.performance_tracker.open_positions[symbol].current_price = price
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get complete portfolio summary"""
        performance = self.performance_tracker.get_performance_summary()
        risk = self.risk_manager.get_risk_summary()
        
        return {
            'performance': performance,
            'risk': risk,
            'open_orders': len([o for o in self.orders.values() if o.status == OrderStatus.PENDING]),
            'filled_orders': len([o for o in self.orders.values() if o.status == OrderStatus.FILLED]),
            'rejected_orders': len([o for o in self.orders.values() if o.status == OrderStatus.REJECTED]),
            'timestamp': datetime.now().isoformat()
        }
    
    def reset(self):
        """Reset the engine (for testing)"""
        self.orders.clear()
        self.order_counter = 0
        self.performance_tracker = PerformanceTracker(self.initial_capital)
        self.risk_manager = RiskManager(self.initial_capital)
        log.info("Execution engine reset")


# Global instance
execution_engine = RealisticExecutionEngine()


if __name__ == "__main__":
    # Test the realistic execution engine
    print("Testing Realistic Execution Engine...")
    
    engine = RealisticExecutionEngine(initial_capital=100000.0)
    
    # Simulate market data
    engine.update_market_data("AAPL", price=150.0, volume=50000000, volatility=0.25)
    engine.update_market_data("MSFT", price=300.0, volume=30000000, volatility=0.20)
    
    print("\n1. Submitting buy order for AAPL...")
    order1 = engine.submit_order("AAPL", OrderSide.BUY, quantity=100)
    print(f"Order status: {order1.status.value}")
    if order1.fill_price:
        print(f"Filled at: ${order1.fill_price:.2f} (slippage: ${order1.slippage:.2f})")
    
    print("\n2. Submitting buy order for MSFT...")
    order2 = engine.submit_order("MSFT", OrderSide.BUY, quantity=50)
    print(f"Order status: {order2.status.value}")
    if order2.fill_price:
        print(f"Filled at: ${order2.fill_price:.2f}")
    
    print("\n3. Portfolio Summary:")
    summary = engine.get_portfolio_summary()
    print(f"Performance: {summary['performance']}")
    print(f"Risk: {summary['risk']}")
    
    print("\n4. Trade history:")
    trades = engine.performance_tracker.get_trade_history()
    for trade in trades:
        print(f"  {trade['symbol']}: PnL ${trade['realized_pnl']:.2f}")
    
    print("\n5. Risk Summary:")
    risk = engine.risk_manager.get_risk_summary()
    print(f"  Max position value: ${risk['max_position_value']:,.2f}")
    print(f"  Stop loss: {risk['stop_loss_pct']:.1%}")
    print(f"  Status: {risk['risk_status']}")
