"""
User Memory & Portfolio API Routes
Endpoints for user queries, trades, portfolio, and performance tracking.
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any

from quant_ecosystem.api_key_manager import require_user_or_admin, require_admin, Role, api_key_manager
from quant_ecosystem.user_memory import user_memory, TradeRecord, TradeDirection, TradeStatus, PortfolioPosition

user_routes = Blueprint('user_routes', __name__, url_prefix='/api')


def _get_user_id_from_token() -> str:
    """Extract user_id from current API key"""
    from flask import g
    # Use the API key ID as the user identifier
    if hasattr(g, 'api_key') and g.api_key:
        return g.api_key.id
    return "anonymous"


@user_routes.route('/user/queries', methods=['GET'])
@require_user_or_admin
def get_user_queries():
    """
    Get user's query history.
    
    Query params:
        - limit: int (default: 50)
    """
    user_id = _get_user_id_from_token()
    limit = request.args.get('limit', 50, type=int)
    
    queries = user_memory.get_user_queries(user_id, limit)
    
    return jsonify({
        "success": True,
        "count": len(queries),
        "queries": [
            {
                "queryId": q.query_id,
                "queryText": q.query_text,
                "timestamp": q.timestamp.isoformat(),
                "responseSummary": q.response_summary,
                "symbolsMentioned": q.symbols_mentioned,
                "queryType": q.query_type
            }
            for q in queries
        ]
    })


@user_routes.route('/user/trades', methods=['GET'])
@require_user_or_admin
def get_user_trades():
    """
    Get user's trade history.
    
    Query params:
        - status: str (pending, open, closed, cancelled)
        - limit: int (default: 100)
    """
    user_id = _get_user_id_from_token()
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    
    trades = user_memory.get_user_trades(user_id, status, limit)
    
    return jsonify({
        "success": True,
        "count": len(trades),
        "trades": [
            {
                "tradeId": t.trade_id,
                "symbol": t.symbol,
                "direction": t.direction.value,
                "entryPrice": t.entry_price,
                "exitPrice": t.exit_price,
                "shares": t.shares,
                "status": t.status.value,
                "entryTime": t.entry_time.isoformat() if t.entry_time else None,
                "exitTime": t.exit_time.isoformat() if t.exit_time else None,
                "pnl": t.pnl,
                "pnlPercent": t.pnl_percent,
                "strategy": t.strategy,
                "confidence": t.confidence,
                "exitReason": t.exit_reason
            }
            for t in trades
        ]
    })


@user_routes.route('/user/portfolio', methods=['GET'])
@require_user_or_admin
def get_user_portfolio():
    """
    Get user's current portfolio state including positions and PnL.
    """
    user_id = _get_user_id_from_token()
    
    # Get cash balance from request or use default
    cash_balance = request.args.get('cash', 100000.0, type=float)
    
    portfolio = user_memory.get_portfolio_state(user_id, cash_balance)
    
    return jsonify({
        "success": True,
        "portfolioState": {
            "userId": portfolio.user_id,
            "totalValue": portfolio.total_value,
            "cashBalance": portfolio.cash_balance,
            "positionsValue": portfolio.positions_value,
            "unrealizedPnl": portfolio.unrealized_pnl,
            "realizedPnl": portfolio.realized_pnl,
            "totalPnl": portfolio.total_pnl,
            "lastUpdated": portfolio.last_updated.isoformat(),
            "positions": [
                {
                    "positionId": p.position_id,
                    "symbol": p.symbol,
                    "direction": p.direction.value,
                    "shares": p.shares,
                    "avgEntryPrice": p.avg_entry_price,
                    "currentPrice": p.current_price,
                    "marketValue": p.market_value,
                    "unrealizedPnl": p.unrealized_pnl,
                    "unrealizedPnlPercent": p.unrealized_pnl_percent,
                    "entryTime": p.entry_time.isoformat(),
                    "stopLoss": p.stop_loss,
                    "takeProfit": p.take_profit,
                    "strategy": p.strategy
                }
                for p in portfolio.positions
            ],
            "allocation": portfolio.allocation
        }
    })


@user_routes.route('/user/performance', methods=['GET'])
@require_user_or_admin
def get_user_performance():
    """
    Get user's performance metrics including win rate, returns, etc.
    """
    user_id = _get_user_id_from_token()
    
    performance = user_memory.get_user_performance(user_id)
    
    if not performance:
        return jsonify({
            "success": True,
            "userPerformance": {
                "userId": user_id,
                "totalTrades": 0,
                "winRate": 0,
                "avgReturn": 0,
                "totalPnl": 0,
                "message": "No trading history found"
            }
        })
    
    return jsonify({
        "success": True,
        "userPerformance": {
            "userId": performance.user_id,
            "totalTrades": performance.total_trades,
            "winningTrades": performance.winning_trades,
            "losingTrades": performance.losing_trades,
            "winRate": performance.win_rate,
            "avgReturn": performance.avg_return,
            "avgWin": performance.avg_win,
            "avgLoss": performance.avg_loss,
            "profitFactor": performance.profit_factor,
            "sharpeRatio": performance.sharpe_ratio,
            "maxDrawdown": performance.max_drawdown,
            "totalPnl": performance.total_pnl,
            "bestTrade": performance.best_trade,
            "worstTrade": performance.worst_trade,
            "favoriteSymbol": performance.favorite_symbol,
            "preferredStrategy": performance.preferred_strategy,
            "lastUpdated": performance.last_updated.isoformat()
        }
    })


@user_routes.route('/user/summary', methods=['GET'])
@require_user_or_admin
def get_user_summary():
    """
    Get complete user summary including portfolio and performance.
    Output format: { userPerformance, portfolioState }
    """
    user_id = _get_user_id_from_token()
    cash_balance = request.args.get('cash', 100000.0, type=float)
    
    portfolio = user_memory.get_portfolio_state(user_id, cash_balance)
    performance = user_memory.get_user_performance(user_id)
    
    # Format portfolio state
    portfolio_data = {
        "userId": portfolio.user_id,
        "totalValue": portfolio.total_value,
        "cashBalance": portfolio.cash_balance,
        "positionsValue": portfolio.positions_value,
        "unrealizedPnl": portfolio.unrealized_pnl,
        "realizedPnl": portfolio.realized_pnl,
        "totalPnl": portfolio.total_pnl,
        "openPositions": len(portfolio.positions),
        "allocation": portfolio.allocation,
        "lastUpdated": portfolio.last_updated.isoformat()
    }
    
    # Format performance
    performance_data = {
        "userId": user_id,
        "totalTrades": performance.total_trades if performance else 0,
        "winRate": performance.win_rate if performance else 0,
        "avgReturn": performance.avg_return if performance else 0,
        "totalPnl": performance.total_pnl if performance else 0,
        "profitFactor": performance.profit_factor if performance else 0,
        "favoriteSymbol": performance.favorite_symbol if performance else None,
        "preferredStrategy": performance.preferred_strategy if performance else "ai_debate",
        "lastUpdated": performance.last_updated.isoformat() if performance else None
    }
    
    return jsonify({
        "success": True,
        "userPerformance": performance_data,
        "portfolioState": portfolio_data
    })


@user_routes.route('/user/personalization', methods=['GET'])
@require_user_or_admin
def get_personalization_context():
    """
    Get personalized context for recommendations.
    Includes user preferences, favorite symbols, trading style.
    """
    user_id = _get_user_id_from_token()
    
    context = user_memory.get_personalized_recommendations_context(user_id)
    
    return jsonify({
        "success": True,
        "personalization": context
    })


# ==================== ADMIN ENDPOINTS ====================

@user_routes.route('/admin/users/summary', methods=['GET'])
@require_admin
def get_all_users_summary():
    """
    Get summary of all users (Admin only).
    Returns actual user data from memory system.
    """
    try:
        # Get all user profiles from memory
        all_users = []
        for user_id in list(user_memory.user_data.keys())[:100]:  # Limit to 100 users
            profile = user_memory.get_user_profile(user_id)
            if profile:
                # Get user's portfolio value
                positions = user_memory.get_portfolio_positions(user_id)
                total_value = sum(p.market_value for p in positions) if positions else 0
                
                # Get trade stats
                trades = user_memory.get_user_trades(user_id, limit=1000)
                open_trades = sum(1 for t in trades if t.status.value == 'open')
                
                all_users.append({
                    'user_id': user_id[:8] + '...',  # Truncated for security
                    'risk_appetite': profile.risk_appetite.value,
                    'preferred_timeframe': profile.preferred_timeframe,
                    'total_positions': len(positions),
                    'portfolio_value': round(total_value, 2),
                    'total_trades': len(trades),
                    'open_trades': open_trades,
                    'last_active': profile.last_updated.isoformat() if profile.last_updated else None
                })
        
        return jsonify({
            "success": True,
            "user_count": len(all_users),
            "users": all_users
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve user summaries"
        }), 500


@user_routes.route('/admin/trades', methods=['GET'])
@require_admin
def get_all_trades():
    """
    Get all trades across all users (Admin only).
    Returns actual trade data from memory system.
    """
    try:
        all_trades = []
        
        # Get trades from all users (limit for performance)
        for user_id in list(user_memory.user_data.keys())[:50]:
            trades = user_memory.get_user_trades(user_id, limit=100)
            for trade in trades:
                all_trades.append({
                    'trade_id': trade.trade_id,
                    'user_id': user_id[:8] + '...',
                    'symbol': trade.symbol,
                    'direction': trade.direction.value,
                    'entry_price': trade.entry_price,
                    'shares': trade.shares,
                    'position_value': trade.position_value,
                    'status': trade.status.value,
                    'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                    'strategy': trade.strategy,
                    'confidence': trade.confidence,
                    'pnl': trade.pnl if trade.pnl else None
                })
        
        # Sort by entry time, most recent first
        all_trades.sort(key=lambda x: x.get('entry_time', ''), reverse=True)
        
        return jsonify({
            "success": True,
            "trade_count": len(all_trades),
            "trades": all_trades[:100]  # Limit to 100 most recent
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve trades"
        }), 500


# ==================== TRADE RECORDING ENDPOINTS ====================

@user_routes.route('/user/trades/record', methods=['POST'])
@require_user_or_admin
def record_trade():
    """
    Record a new trade for the user.
    
    Request body:
        - symbol: str
        - direction: str ('long' or 'short')
        - entry_price: float
        - shares: int
        - strategy: str (optional)
        - confidence: float (optional)
        - stop_loss: float (optional)
        - take_profit: float (optional)
    """
    user_id = _get_user_id_from_token()
    data = request.get_json() or {}
    
    required = ['symbol', 'direction', 'entry_price', 'shares']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    
    try:
        trade = TradeRecord(
            trade_id=f"trd_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:8]}",
            user_id=user_id,
            symbol=data['symbol'].upper(),
            direction=TradeDirection(data['direction'].lower()),
            entry_price=float(data['entry_price']),
            shares=int(data['shares']),
            position_value=float(data['entry_price']) * int(data['shares']),
            status=TradeStatus.OPEN,
            entry_time=datetime.now(),
            strategy=data.get('strategy', 'ai_debate'),
            confidence=data.get('confidence', 0.0),
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            metadata=data.get('metadata', {})
        )
        
        trade_id = user_memory.record_trade(trade)
        
        # Also add as portfolio position
        position = PortfolioPosition(
            position_id=f"pos_{trade_id}",
            user_id=user_id,
            symbol=trade.symbol,
            direction=trade.direction,
            shares=trade.shares,
            avg_entry_price=trade.entry_price,
            current_price=trade.entry_price,
            market_value=trade.position_value,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            entry_time=trade.entry_time,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            strategy=trade.strategy
        )
        user_memory.add_position(position)
        
        return jsonify({
            "success": True,
            "tradeId": trade_id,
            "message": "Trade recorded successfully"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@user_routes.route('/user/trades/<trade_id>/close', methods=['POST'])
@require_user_or_admin
def close_trade(trade_id: str):
    """
    Close an existing trade with exit details.
    
    Request body:
        - exit_price: float
        - exit_reason: str (optional)
    """
    user_id = _get_user_id_from_token()
    data = request.get_json() or {}
    
    if 'exit_price' not in data:
        return jsonify({"error": "exit_price is required"}), 400
    
    try:
        # Update trade exit
        trades = user_memory.get_user_trades(user_id, limit=1000)
        trade = next((t for t in trades if t.trade_id == trade_id), None)
        
        if not trade:
            return jsonify({"error": "Trade not found"}), 404
        
        # Calculate PnL
        exit_price = float(data['exit_price'])
        entry_price = trade.entry_price
        
        if trade.direction == TradeDirection.LONG:
            pnl = (exit_price - entry_price) * trade.shares
        else:
            pnl = (entry_price - exit_price) * trade.shares
        
        user_memory.update_trade_exit(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_time=datetime.now(),
            pnl=pnl,
            exit_reason=data.get('exit_reason', 'manual')
        )
        
        # Remove from portfolio positions
        user_memory.remove_position(user_id, trade.symbol, trade.direction)
        
        return jsonify({
            "success": True,
            "tradeId": trade_id,
            "pnl": pnl,
            "message": "Trade closed successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@user_routes.route('/user/positions/update', methods=['POST'])
@require_user_or_admin
def update_position_prices():
    """
    Update current prices for all positions (called periodically).
    
    Request body:
        - prices: dict {symbol: current_price}
    """
    user_id = _get_user_id_from_token()
    data = request.get_json() or {}
    prices = data.get('prices', {})
    
    if not prices:
        return jsonify({"error": "prices dict is required"}), 400
    
    positions = user_memory.get_portfolio_positions(user_id)
    updated = 0
    
    for pos in positions:
        if pos.symbol in prices:
            new_price = float(prices[pos.symbol])
            
            # Calculate new unrealized PnL
            if pos.direction == TradeDirection.LONG:
                unrealized_pnl = (new_price - pos.avg_entry_price) * pos.shares
            else:
                unrealized_pnl = (pos.avg_entry_price - new_price) * pos.shares
            
            unrealized_pnl_percent = (unrealized_pnl / (pos.avg_entry_price * pos.shares)) * 100 if pos.avg_entry_price > 0 else 0
            
            # Update position
            updated_pos = PortfolioPosition(
                position_id=pos.position_id,
                user_id=pos.user_id,
                symbol=pos.symbol,
                direction=pos.direction,
                shares=pos.shares,
                avg_entry_price=pos.avg_entry_price,
                current_price=new_price,
                market_value=new_price * pos.shares,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent,
                entry_time=pos.entry_time,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
                strategy=pos.strategy
            )
            
            user_memory.add_position(updated_pos)
            updated += 1
    
    return jsonify({
        "success": True,
        "updatedPositions": updated,
        "message": f"Updated {updated} positions"
    })


@user_routes.route('/user/query/record', methods=['POST'])
@require_user_or_admin
def record_query():
    """
    Record a user query.
    
    Request body:
        - query_text: str
        - symbols: list (optional)
        - query_type: str (optional)
    """
    user_id = _get_user_id_from_token()
    data = request.get_json() or {}
    
    if 'query_text' not in data:
        return jsonify({"error": "query_text is required"}), 400
    
    query_id = user_memory.record_query(
        user_id=user_id,
        query_text=data['query_text'],
        symbols=data.get('symbols', []),
        query_type=data.get('query_type', 'general')
    )
    
    return jsonify({
        "success": True,
        "queryId": query_id,
        "message": "Query recorded"
    })
