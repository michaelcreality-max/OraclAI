"""
AI Platform Orchestrator - Main integration point for all services
Phase 6 Implementation
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Import all services
from services.data_service import DataService
from services.feature_service import FeatureService
from ml.ml_service import MLService
from services.signal_service import SignalService
from services.agent_service import AgentService
from services.debate_service import DebateService
from services.judge_service import JudgeService
from services.risk_service import RiskService
from services.backtest_service import BacktestService
from services.adaptive_learning_service import AdaptiveLearningService

from core.edge_detector import EdgeDetector, edge_detector
from core.trade_filter import TradeFilter, trade_filter
from core.position_sizing import PositionSizer, position_sizer
from core.risk_management import RiskManager, risk_manager
from core.enhanced_backtest import WalkForwardTester, walk_forward_tester
from core.adaptive_strategy_manager import AdaptiveStrategyManager, adaptive_manager
from core.performance_tracker import PerformanceTracker, performance_tracker
from core.realistic_execution import RealisticTradeSimulator, realistic_simulator
from core.system_mode_controller import SystemModeController, system_mode_controller
from core.auth_system import AuthSystem, auth_system
from core.api_key_system import APIKeyManager, initialize_api_key_manager, api_key_manager
from services.pattern_recognition_service import PatternRecognitionService, pattern_service
from services.media_analysis_service import MediaAnalysisService, media_service

from core.data_structures import (
    MarketData, FeatureVector, ModelPrediction, TradingSignal, 
    AgentPosition, DebateSession, JudicialVerdict, OrderDecision, BacktestResult
)

log = logging.getLogger(__name__)


class AIPlatformOrchestrator:
    """
    Main orchestrator that coordinates all services in the AI Platform.
    Provides high-level API for end-to-end trading workflow.
    
    Pipeline:
    1. Data Ingestion (DataService)
    2. Feature Engineering (FeatureService)
    3. ML Prediction (MLService)
    4. Signal Generation (SignalService)
    5. Multi-Agent Analysis (AgentService)
    6. Debate & Consensus (DebateService)
    7. Judicial Verdict (JudgeService)
    8. Risk Check (RiskService)
    9. Trade Execution / Backtest (BacktestService)
    10. Adaptive Learning (AdaptiveLearningService)
    """
    
    def __init__(self):
        # Initialize all services
        self.data_service = DataService()
        self.feature_service = FeatureService()
        self.ml_service = MLService()
        self.signal_service = SignalService()
        self.agent_service = AgentService()
        self.debate_service = DebateService()
        self.judge_service = JudgeService()
        self.risk_service = RiskService()
        self.backtest_service = BacktestService()
        self.learning_service = AdaptiveLearningService()
        
        # Edge detection and trade filtering
        self.edge_detector = EdgeDetector()
        self.trade_filter = TradeFilter(
            edge_threshold=65,
            confidence_threshold=0.60,
            agreement_threshold=0.55,
            strict_mode=True
        )
        
        # Advanced position sizing
        self.position_sizer = PositionSizer(
            portfolio_value=100000.0,
            max_position_pct=0.10,
            max_risk_per_trade_pct=0.015
        )
        
        # Strict risk management
        self.risk_manager = RiskManager(initial_capital=100000.0)
        
        # Enhanced walk-forward backtesting
        self.walk_forward_tester = WalkForwardTester(
            n_periods=5,
            train_pct=0.6,
            min_trades_per_period=10
        )
        
        # Adaptive strategy management
        self.adaptive_manager = AdaptiveStrategyManager()
        
        # Performance-driven learning
        self.performance_tracker = PerformanceTracker()
        
        # Realistic trade execution simulator
        self.realistic_simulator = RealisticTradeSimulator()
        
        # System mode controller (training/execution)
        self.mode_controller = system_mode_controller
        
        # Multi-user authentication system
        self.auth_system = auth_system
        
        # API Key management system
        self.api_key_manager = initialize_api_key_manager(self.auth_system)
        
        # Pattern recognition service
        self.pattern_service = PatternRecognitionService()
        
        # Media & news analysis service
        self.media_service = MediaAnalysisService()
        
        log.info("AI Platform Orchestrator initialized with pattern recognition and media analysis")
    
    def run_full_pipeline(self, symbol: str, days: int = 60) -> Dict:
        """
        Run complete pipeline for a symbol
        
        Args:
            symbol: Stock symbol to analyze
            days: Historical data days
            
        Returns:
            Complete pipeline results
        """
        log.info(f"Running full pipeline for {symbol}")
        
        # Step 1: Get data
        market_data = self.data_service.get_ohlcv(symbol, days=days)
        if market_data is None or market_data.empty:
            return {'error': f'No data available for {symbol}'}
        
        # Step 1.5: ADAPT TO MARKET CONDITIONS
        # Detect regime and adjust system parameters
        adaptation = self.adaptive_manager.adapt(market_data, symbol)
        
        # Update trade filter with regime-specific thresholds
        self.trade_filter.edge_threshold = adaptation['config']['edge_threshold']
        self.trade_filter.confidence_threshold = adaptation['config']['confidence_threshold']
        self.trade_filter.agreement_threshold = adaptation['config']['agreement_threshold']
        
        # Update position sizer with regime-specific sizing
        self.position_sizer.max_risk_per_trade_pct = adaptation['config']['risk_per_trade_pct']
        
        # Update agent weights based on regime
        agent_weights = adaptation['agent_weights']
        for agent_type, weight in agent_weights.items():
            if agent_type in self.agent_service.agent_weights:
                self.agent_service.agent_weights[agent_type] = weight
        
        log.info(f"System adapted to {adaptation['regime']} regime for {symbol}")
        
        # Step 2: Generate features
        features = self.feature_service.compute_features(symbol, market_data)
        
        # Step 3: ML Prediction
        feature_vector = FeatureVector(
            symbol=symbol,
            timestamp=datetime.now(),
            features=features,
            feature_names=list(features.keys())
        )
        prediction = self.ml_service.predict(feature_vector)
        
        # Step 4: Generate signal
        signal = self.signal_service.generate_signal(prediction)
        
        # Step 5: Agent analysis
        positions = self.agent_service.analyze_signal(signal)
        
        # Step 6: Debate
        debate_session = self.agent_service.prepare_debate_session(signal, positions)
        debate_result = self.debate_service.conduct_debate(debate_session)
        
        # Step 7: Judicial verdict
        verdict = self.judge_service.render_verdict(debate_result)
        
        # Step 7.5: Edge Detection & Trade Filter
        # Only trade when strong edge exists
        ml_pred_dict = {
            'confidence': prediction.confidence,
            'direction': prediction.direction,
            'model_agreement': prediction.metadata.get('model_agreement', 0.5)
        } if hasattr(prediction, 'confidence') else None
        
        agent_pos_list = [
            {
                'agent_id': p.agent_id,
                'stance': p.stance.value if hasattr(p.stance, 'value') else str(p.stance),
                'confidence': p.confidence,
                'position_size': p.position_size_pct
            }
            for p in positions.values() if hasattr(p, 'agent_id')
        ]
        
        filter_result = self.trade_filter.evaluate(
            ml_prediction=ml_pred_dict,
            agent_positions=agent_pos_list,
            judicial_verdict={'winning_stance': verdict.winning_stance.value},
            current_regime='neutral',  # Would come from regime detector
            symbol=symbol
        )
        
        # Override verdict if trade not allowed
        if not filter_result.trade_allowed:
            log.info(f"Trade BLOCKED for {symbol}: {filter_result.blocking_reason}")
            verdict.order_decision.order_type = OrderType.HOLD
            verdict.order_decision.position_size_pct = 0.0
            position_sizing = None
        else:
            # Step 7.6: Advanced Position Sizing
            # Calculate volatility (ATR) from market data
            atr_percent = self._calculate_atr(market_data)
            
            # Get latest price
            entry_price = market_data['close'].iloc[-1] if 'close' in market_data else 100.0
            
            # Calculate dynamic position size
            position_sizing = self.position_sizer.calculate_position_size(
                edge_score=filter_result.edge_score,
                confidence=verdict.conviction_level,
                atr_percent=atr_percent,
                entry_price=entry_price,
                stop_loss_price=None,  # Will use 2x ATR
                symbol=symbol
            )
            
            # Update verdict with calculated position size
            verdict.order_decision.position_size_pct = position_sizing.position_size_percent / 100
            
            log.info(f"Position sized for {symbol}: {position_sizing.position_size_percent:.2f}% "
                    f"(edge={filter_result.edge_score}, vol={atr_percent:.2%})")
            
            # Step 7.7: Strict Risk Management - Stop Loss & Risk Assessment
            direction = 'long' if verdict.winning_stance.value == 'buy' else 'short' if verdict.winning_stance.value == 'sell' else 'neutral'
            
            if direction != 'neutral':
                # Calculate volatility-based stop loss
                stop_loss = self.risk_manager.calculate_stop_loss(
                    entry_price=entry_price,
                    atr_percent=atr_percent,
                    direction=direction,
                    volatility_regime='normal'  # Could be detected from ATR
                )
                
                # Get current portfolio heat
                portfolio_heat = self.risk_manager.get_portfolio_heat()
                
                # Assess trade risk
                risk_assessment = self.risk_manager.assess_trade_risk(
                    symbol=symbol,
                    entry_price=entry_price,
                    position_size_pct=position_sizing.position_size_percent / 100,
                    stop_loss=stop_loss,
                    portfolio_heat=portfolio_heat
                )
                
                # Apply risk reduction if required
                if risk_assessment.reduction_required:
                    log.warning(f"Risk reduction required for {symbol}: "
                              f"recommended size {risk_assessment.recommended_position_size:.2f}%")
                    # Update position size to recommended
                    verdict.order_decision.position_size_pct = risk_assessment.recommended_position_size / 100
                    position_sizing.position_size_percent = risk_assessment.recommended_position_size
                    position_sizing.capital_allocation = risk_assessment.recommended_position_size / 100 * self.position_sizer.portfolio_value
                
                log.info(f"Risk assessment for {symbol}: stop=${stop_loss.stop_price:.2f}, "
                        f"risk={risk_assessment.risk_percent:.2f}%, approved={risk_assessment.risk_approved}")
        # Step 8: Risk check (only if trade allowed)
        if filter_result.trade_allowed:
            risk_check = self.risk_service.check_order_risk(
                verdict.order_decision,
                list(positions.values())
            )
        else:
            risk_check = {'approved': False, 'reason': filter_result.blocking_reason}
        
        # Step 9: Record for learning
        self.learning_service.record_prediction(symbol, datetime.now(), verdict)
        
        result = {
            'symbol': symbol,
            'prediction': prediction,
            'signal': signal,
            'positions': positions,
            'debate_summary': self.debate_service.get_debate_summary(debate_result),
            'verdict': verdict,
            'edge_score': filter_result.edge_score,
            'trade_allowed': filter_result.trade_allowed,
            'edge_details': self.trade_filter.get_output(filter_result),
            'risk_check': risk_check,
            'approved': risk_check.get('approved', False) and filter_result.trade_allowed and verdict.order_decision.order_type.value != 'hold'
        }
        
        # Add position sizing details if trade allowed
        if position_sizing:
            result['position_sizing'] = self.position_sizer.get_output(position_sizing)
        
        # Add risk assessment details if available
        if risk_assessment:
            result['risk_management'] = self.risk_manager.get_risk_output(risk_assessment)
        
        # Add adaptation info
        result['adaptation'] = adaptation
        
        return result
    
    def run_batch_analysis(self, symbols: List[str], days: int = 60) -> List[Dict]:
        """
        Analyze multiple symbols
        
        Args:
            symbols: List of stock symbols
            days: Historical data days
            
        Returns:
            List of analysis results
        """
        results = []
        for symbol in symbols:
            try:
                result = self.run_full_pipeline(symbol, days)
                results.append(result)
            except Exception as e:
                log.error(f"Failed to analyze {symbol}: {e}")
                results.append({'symbol': symbol, 'error': str(e)})
        
        return results
    
    def walk_forward_backtest(self, 
                             symbol: str, 
                             start_date: datetime,
                             end_date: datetime,
                             strategy_fn = None) -> Dict:
        """
        Run walk-forward backtest to validate strategy robustness
        
        Args:
            symbol: Stock symbol to test
            start_date: Backtest start date
            end_date: Backtest end date
            strategy_fn: Optional custom strategy function
            
        Returns:
            Walk-forward backtest results
        """
        log.info(f"Running walk-forward backtest for {symbol}")
        
        # Get historical data
        market_data = self.data_service.get_ohlcv(
            symbol, 
            start_date=start_date,
            end_date=end_date
        )
        
        if market_data is None or len(market_data) < 100:
            return {'error': f'Insufficient data for {symbol}'}
        
        # Use default strategy if none provided
        if strategy_fn is None:
            strategy_fn = self._default_strategy
        
        # Run walk-forward analysis
        wf_result = self.walk_forward_tester.run_walk_forward_analysis(
            strategy_fn=strategy_fn,
            market_data=market_data,
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate report
        report = self.walk_forward_tester.generate_report(wf_result)
        log.info(f"\n{report}")
        
        # Return structured result
        return {
            'symbol': symbol,
            'is_robust': wf_result.is_robust,
            'overall_return': wf_result.overall_return,
            'overall_sharpe': wf_result.overall_sharpe,
            'overall_max_dd': wf_result.overall_max_dd,
            'consistency_score': wf_result.consistency_score,
            'degradation_ratio': wf_result.degradation_ratio,
            'in_sample_performance': wf_result.in_sample_performance,
            'out_of_sample_performance': wf_result.out_of_sample_performance,
            'periods_tested': len(wf_result.periods),
            'periods_passed': sum(1 for p in wf_result.periods if p.is_valid),
            'rejection_reasons': wf_result.rejection_reasons,
            'report': report
        }
    
    def _default_strategy(self, market_data: pd.DataFrame) -> List[Dict]:
        """
        Default strategy for walk-forward testing
        Uses the full AI pipeline to generate signals
        """
        signals = []
        
        # Walk through data day by day
        for i in range(50, len(market_data) - 5):  # Skip first 50 for indicators
            # Get data up to current point
            current_data = market_data.iloc[:i+1]
            
            # Run pipeline on this data
            try:
                features = self.feature_service.compute_features(
                    current_data.iloc[-1].get('symbol', 'SYM'), 
                    current_data
                )
                
                feature_vector = FeatureVector(
                    symbol=current_data.iloc[-1].get('symbol', 'SYM'),
                    timestamp=current_data.index[-1],
                    features=features,
                    feature_names=list(features.keys())
                )
                
                prediction = self.ml_service.predict(feature_vector)
                
                # Generate signal if strong enough
                if prediction.confidence > 0.65 and prediction.direction != 0:
                    signals.append({
                        'date': current_data.index[-1],
                        'index': i,
                        'entry_price': current_data['close'].iloc[-1],
                        'direction': 'long' if prediction.direction == 1 else 'short',
                        'confidence': prediction.confidence,
                        'size': 0.03,  # 3% position
                        'stop_price': current_data['close'].iloc[-1] * 0.95,  # 5% stop
                        'holding_days': 5
                    })
            except Exception as e:
                continue
        
        return signals
    
    def execute_trade(self, symbol: str, verdict: JudicialVerdict,
                     market_data: Dict) -> Optional[Dict]:
        """
        Execute a trade based on verdict (or simulate)
        
        Args:
            symbol: Stock symbol
            verdict: Judicial verdict with order decision
            market_data: Current market data for execution
            
        Returns:
            Trade execution result or None
        """
        if verdict.order_decision.order_type.value == 'hold':
            log.info(f"No trade for {symbol} - HOLD verdict")
            return None
        
        execution = self.backtest_service.simulate_execution(
            verdict.order_decision,
            market_data
        )
        
        if execution:
            return {
                'symbol': symbol,
                'execution': execution,
                'timestamp': datetime.now(),
                'verdict_confidence': verdict.conviction_level
            }
        
        return None
    
    def simulate_realistic_trade(self,
                                symbol: str,
                                verdict: JudicialVerdict,
                                market_data: pd.DataFrame,
                                future_data: Optional[pd.DataFrame] = None) -> Optional[Dict]:
        """
        Simulate realistic trade execution with entry delays, slippage, and exit logic
        
        Args:
            symbol: Stock symbol
            verdict: Judicial verdict with trade decision
            market_data: Current market data (up to entry point)
            future_data: Future price data for exit simulation (for backtesting)
            
        Returns:
            Realistic trade result with all execution details
        """
        if verdict.order_decision.order_type.value == 'hold':
            return None
        
        # Get entry price
        entry_price = market_data['close'].iloc[-1] if 'close' in market_data else 100.0
        
        # Get position sizing
        position_pct = verdict.order_decision.position_size_pct if verdict.order_decision else 0.03
        shares = int((100000 * position_pct) / entry_price)  # Assume $100k portfolio
        
        # Get stop loss and profit target
        atr_percent = self._calculate_atr(market_data)
        stop_distance = entry_price * atr_percent * 2
        
        if verdict.winning_stance.value == 'buy':
            direction = 'long'
            stop_loss_price = entry_price - stop_distance
            profit_target = entry_price * 1.05  # 5% profit target
        else:
            direction = 'short'
            stop_loss_price = entry_price + stop_distance
            profit_target = entry_price * 0.95  # 5% profit target
        
        # Get regime for context
        adaptation = self.adaptive_manager.adapt(market_data, symbol)
        regime = adaptation.get('regime', 'unknown')
        edge_score = adaptation.get('config', {}).get('edge_threshold', 65)
        
        # Prepare price history for exit simulation
        if future_data is not None and len(future_data) > 0:
            price_history = future_data['close'].tolist()
            high_prices = future_data['high'].tolist() if 'high' in future_data else price_history
            low_prices = future_data['low'].tolist() if 'low' in future_data else price_history
        else:
            # Use simulated path if no future data
            price_history = [entry_price] * 5
            high_prices = low_prices = price_history
        
        # Simulate realistic trade
        trade = self.realistic_simulator.simulate_trade(
            symbol=symbol,
            intended_entry_price=entry_price,
            intended_shares=shares,
            direction=direction,
            stop_loss_price=stop_loss_price,
            profit_target_price=profit_target,
            price_history=price_history,
            high_prices=high_prices,
            low_prices=low_prices,
            volatility_regime='normal',  # Could detect from ATR
            max_holding_days=5,
            edge_score=edge_score,
            entry_regime=regime
        )
        
        # Record for performance tracking
        if trade.net_pnl != 0:
            self.performance_tracker.record_trade_exit(
                f"{symbol}_{trade.entry_intent_time.isoformat()}",
                {
                    'exit_price': trade.exit_result.exit_price if trade.exit_result else entry_price,
                    'was_stop_hit': trade.exit_result.exit_reason.value == 'stop_loss' if trade.exit_result else False,
                    'holding_days': trade.exit_result.days_held if trade.exit_result else 1
                }
            )
        
        return {
            'symbol': symbol,
            'direction': direction,
            'entry_price': trade.entry_price,
            'entry_slippage': trade.entry_fill.slippage,
            'entry_delay': trade.entry_fill.delay_seconds,
            'shares': trade.shares,
            'exit_price': trade.exit_result.exit_price if trade.exit_result else entry_price,
            'exit_reason': trade.exit_result.exit_reason.value if trade.exit_result else 'unknown',
            'days_held': trade.exit_result.days_held if trade.exit_result else 0,
            'gross_pnl': trade.gross_pnl,
            'total_costs': trade.total_cost,
            'net_pnl': trade.net_pnl,
            'net_return': trade.net_return,
            'max_profit_seen': trade.exit_result.max_profit_seen if trade.exit_result else 0,
            'regime': regime
        }
    
    def update_learning(self, symbol: str, prediction_timestamp: datetime,
                       actual_return: float, holding_days: int = 5):
        """
        Update learning with actual outcome
        
        Args:
            symbol: Stock symbol
            prediction_timestamp: When prediction was made
            actual_return: Actual realized return
            holding_days: Days position was held
        """
        self.learning_service.evaluate_prediction(
            symbol, prediction_timestamp, actual_return, holding_days
        )
        
        # Update weights periodically
        self.learning_service.update_weights()
        
        # Update agent weights in agent service
        new_weights = self.learning_service.agent_weights
        for agent_type_str, weight in new_weights.items():
            self.agent_service.agent_weights[agent_type_str] = weight
        
        # Performance-driven learning updates
        # Record trade outcome for performance tracking
        if symbol in self.performance_tracker.pending_trades:
            self.performance_tracker.record_trade_exit(
                self.performance_tracker.pending_trades[symbol].get('trade_id'),
                {
                    'exit_price': actual_return,  # Simplified - would need actual price
                    'was_stop_hit': False,
                    'holding_days': holding_days
                }
            )
        
        # Update agent weights based on performance
        self.performance_tracker.update_agent_weights()
        
        # Calibrate confidence based on accuracy
        self.performance_tracker.calibrate_confidence()
        
        # Sync performance-based weights to agent service
        perf_weights = self.performance_tracker.agent_weights
        for agent_type, weight in perf_weights.items():
            if agent_type in self.agent_service.agent_weights:
                # Blend learning service weights with performance weights
                current = self.agent_service.agent_weights[agent_type]
                self.agent_service.agent_weights[agent_type] = 0.5 * current + 0.5 * weight
        
        log.info("Performance-driven learning updates applied")
    
    def _calculate_atr(self, market_data, period: int = 14) -> float:
        """Calculate Average True Range as percentage of price"""
        try:
            high = market_data['high']
            low = market_data['low']
            close = market_data['close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = true_range.rolling(period).mean().iloc[-1]
            
            # Convert to percentage
            current_price = close.iloc[-1]
            atr_percent = atr / current_price if current_price > 0 else 0.02
            
            return atr_percent
        except Exception:
            return 0.02  # Default 2% if calculation fails
    
    def get_platform_status(self) -> Dict:
        """Get complete platform status"""
        return {
            'services_status': {
                'data': 'active',
                'features': 'active',
                'ml': 'active',
                'agents': len(self.agent_service.agents),
                'debate': 'active',
                'judge': 'active',
                'risk': 'active',
                'backtest': 'active',
                'learning': 'active'
            },
            'learning_stats': self.learning_service.get_system_performance(),
            'agent_weights': self.agent_service.agent_weights,
            'risk_limits': self.risk_service.limits,
            'performance_metrics': self.get_performance_metrics()
        }
    
    def get_performance_metrics(self) -> Dict:
        """
        Get performance-driven learning metrics
        
        Returns:
            Dict with winRate, avgReturn, bestStrategy and more
        """
        return self.performance_tracker.get_performance_metrics('medium')
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate human-readable report from batch analysis"""
        lines = []
        lines.append("=" * 70)
        lines.append("AI PLATFORM ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        lines.append("")
        
        # Summary stats
        approved = sum(1 for r in results if r.get('approved'))
        rejected = len(results) - approved
        
        lines.append(f"Total Analyzed: {len(results)}")
        lines.append(f"Approved Trades: {approved}")
        lines.append(f"Rejected/Hold: {rejected}")
        
        # Edge filter stats
        trade_allowed = sum(1 for r in results if r.get('trade_allowed'))
        blocked_by_filter = rejected - (len(results) - trade_allowed)
        
        lines.append(f"Trade Filter: {trade_allowed} allowed, {blocked_by_filter} blocked")
        lines.append("")
        
        # Individual results
        for result in results:
            if 'error' in result:
                lines.append(f"❌ {result['symbol']}: ERROR - {result['error']}")
                continue
            
            symbol = result['symbol']
            verdict = result['verdict']
            risk = result['risk_check']
            edge_score = result.get('edge_score', 0)
            trade_allowed = result.get('trade_allowed', False)
            
            status_icon = "✅" if result['approved'] else "⏸️"
            edge_icon = "🔥" if edge_score >= 80 else "⚡" if edge_score >= 65 else "❄️"
            
            lines.append(f"{status_icon} {symbol} {edge_icon}")
            
            # Show regime if available
            adaptation_info = result.get('adaptation')
            if adaptation_info:
                regime = adaptation_info.get('regime', 'unknown')
                regime_icon = "📈" if 'uptrend' in regime else "📉" if 'downtrend' in regime else "➡️" if 'sideways' in regime else "⚡" if 'volatility' in regime else "❓"
                lines.append(f"   Regime: {regime_icon} {regime.upper().replace('_', ' ')}")
            
            lines.append(f"   Verdict: {verdict.winning_stance.value.upper()} "
                        f"(conf: {verdict.conviction_level:.1%})")
            lines.append(f"   Edge Score: {edge_score}/100 "
                        f"({'TRADE ALLOWED' if trade_allowed else 'BLOCKED'})")
            lines.append(f"   Agreement: {verdict.agreement_level:.1%}")
            
            # Position sizing details
            pos_size = result.get('position_sizing')
            if pos_size:
                lines.append(f"   Position: {pos_size['positionSizePercent']:.2f}% "
                            f"(${pos_size['capitalAllocation']:,.0f})")
                lines.append(f"   Risk: {pos_size['riskPercent']:.2f}% "
                            f"(${pos_size['riskAmount']:,.0f})")
                lines.append(f"   Sizing Factors: edge={pos_size['factors']['edgeFactor']:.2f}, "
                            f"conf={pos_size['factors']['confidenceFactor']:.2f}, "
                            f"vol={pos_size['factors']['volatilityFactor']:.2f}")
            else:
                lines.append(f"   Position Size: {verdict.order_decision.position_size_pct:.1%}")
            
            lines.append(f"   Risk Check: {'✓ Approved' if risk.get('approved') else '✗ Rejected'}")
            
            # Risk management details
            risk_mgmt = result.get('risk_management')
            if risk_mgmt and risk_mgmt.get('approved'):
                lines.append(f"   Stop Loss: ${risk_mgmt['stopLoss']['price']:.2f} "
                            f"({risk_mgmt['stopLoss']['distancePercent']:.2f}%)")
                lines.append(f"   Trade Risk: {risk_mgmt['maxRisk']['percent']:.2f}% "
                            f"(max allowed: {risk_mgmt['maxRisk']['maxAllowed']:.2f}%)")
                lines.append(f"   Expected DD: {risk_mgmt['expectedDrawdown']['percent']:.2f}%")
            
            if not trade_allowed and 'edge_details' in result:
                blocking = result['edge_details'].get('blockingReason', '')
                if blocking:
                    lines.append(f"   Blocked: {blocking[:60]}...")
            
            lines.append("")
        
        # Performance metrics section
        lines.append("-" * 70)
        lines.append("PERFORMANCE METRICS (Performance-Driven Learning)")
        lines.append("-" * 70)
        
        perf = self.get_performance_metrics()
        lines.append(f"  Win Rate: {perf.get('winRate', 0):.1f}%")
        lines.append(f"  Avg Return: {perf.get('avgReturn', 0):.2f}%")
        lines.append(f"  Best Strategy: {perf.get('bestStrategy', 'unknown')}")
        lines.append(f"  Total Trades: {perf.get('totalTrades', 0)}")
        lines.append(f"  Sharpe Ratio: {perf.get('sharpe', 0):.2f}")
        lines.append(f"  Max Drawdown: {perf.get('maxDrawdown', 0):.1f}%")
        
        # Agent weights summary
        lines.append("")
        lines.append("AGENT WEIGHTS (Performance-Adjusted)")
        lines.append(f"  {', '.join([f'{k}: {v:.2f}' for k, v in list(self.agent_service.agent_weights.items())[:4]])}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    # ==================== SYSTEM MODE CONTROL API ====================
    
    def get_system_mode(self) -> Dict:
        """
        Get current system mode status
        
        Returns:
            {
                'currentMode': 'training' | 'execution',
                'lastChangedBy': str,
                'timestamp': str,
                'modelValidationStatus': Dict,
                'canExecute': bool
            }
        """
        return self.mode_controller.get_current_mode()
    
    def switch_system_mode(self, mode: str, admin_token: str, reason: str = "") -> Dict:
        """
        Switch system mode (Admin only)
        
        Args:
            mode: 'training' or 'execution'
            admin_token: Valid admin session token
            reason: Reason for mode switch
            
        Returns:
            Result dict with success status and message
        """
        try:
            result = self.mode_controller.switch_mode(
                new_mode=mode,
                session_token=admin_token,
                reason=reason
            )
            return result
        except Exception as e:
            log.error(f"Mode switch failed: {e}")
            return {
                'success': False,
                'message': str(e),
                'currentMode': self.mode_controller.get_current_mode()['currentMode']
            }
    
    def admin_login(self, username: str, password: str) -> Dict:
        """
        Admin authentication
        
        Returns:
            {'success': bool, 'token': str | None, 'message': str}
        """
        token = self.mode_controller.authenticate_admin(username, password)
        if token:
            return {
                'success': True,
                'token': token,
                'message': 'Authentication successful'
            }
        return {
            'success': False,
            'token': None,
            'message': 'Authentication failed'
        }
    
    def admin_logout(self, token: str) -> bool:
        """Logout admin session"""
        return self.mode_controller.logout(token)
    
    def setup_admin(self, username: str, password: str) -> bool:
        """Setup initial admin credentials (call once)"""
        return self.mode_controller.setup_admin(username, password)
    
    def get_mode_audit_log(self, n_entries: int = 100) -> List[str]:
        """Get mode switch audit log"""
        return self.mode_controller.get_audit_log(n_entries)
    
    def get_mode_switch_history(self, n_entries: int = 20) -> List[Dict]:
        """Get mode switch history"""
        return self.mode_controller.get_switch_history(n_entries)
    
    def update_model_validation(self, 
                               is_validated: bool,
                               sharpe: float,
                               max_drawdown: float,
                               walk_forward_passed: bool,
                               validation_score: float):
        """Update model validation status after backtesting"""
        self.mode_controller.update_model_validation(
            is_validated=is_validated,
            sharpe=sharpe,
            max_drawdown=max_drawdown,
            walk_forward_passed=walk_forward_passed,
            validation_score=validation_score
        )
    
    def is_training_mode(self) -> bool:
        """Check if system is in training mode"""
        return self.mode_controller.get_current_mode()['currentMode'] == 'training'
    
    def is_execution_mode(self) -> bool:
        """Check if system is in execution mode and validated"""
        mode_status = self.mode_controller.get_current_mode()
        return mode_status['currentMode'] == 'execution' and mode_status['canExecute']
    
    # ==================== MULTI-USER AUTHENTICATION API ====================
    
    def auth_register(self, email: str, password: str, role: str = "user") -> Dict:
        """
        Register a new user account
        
        POST /api/auth/register
        
        Args:
            email: User email address
            password: User password (min 8 chars, upper, lower, digit)
            role: 'user' or 'admin' (default: user)
            
        Returns:
            {
                'success': bool,
                'user': {'userId', 'email', 'role', 'createdAt'} | None,
                'message': str
            }
        """
        return self.auth_system.register_user(email, password, role)
    
    def auth_login(self, 
                  email: str, 
                  password: str,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None) -> Dict:
        """
        Authenticate user and create session
        
        POST /api/auth/login
        
        Args:
            email: User email
            password: User password
            ip_address: Optional client IP
            user_agent: Optional client user agent
            
        Returns:
            {
                'success': bool,
                'token': str | None,
                'user': {'userId', 'email', 'role'} | None,
                'message': str
            }
        """
        return self.auth_system.login(email, password, ip_address, user_agent)
    
    def auth_logout(self, token: str) -> bool:
        """
        Logout user and invalidate session
        
        POST /api/auth/logout
        """
        return self.auth_system.logout(token)
    
    def auth_me(self, token: str) -> Optional[Dict]:
        """
        Get current authenticated user info
        
        GET /api/auth/me
        
        Returns:
            {'userId', 'email', 'role', 'createdAt', 'lastLogin', 'isActive'} | None
        """
        return self.auth_system.get_current_user(token)
    
    def auth_validate_token(self, token: str) -> bool:
        """Validate if session token is active"""
        return self.auth_system.validate_session(token)
    
    def auth_check_permission(self, token: str, permission: str) -> bool:
        """Check if user has specific permission"""
        return self.auth_system.check_permission(token, permission)
    
    def auth_require_permission(self, token: str, permission: str):
        """Require permission or raise AuthError"""
        self.auth_system.require_permission(token, permission)
    
    def auth_is_admin(self, token: str) -> bool:
        """Check if authenticated user is admin"""
        return self.auth_system.is_admin(token)
    
    def auth_is_user(self, token: str) -> bool:
        """Check if authenticated user is regular user"""
        return self.auth_system.is_user(token)
    
    def auth_list_users(self, admin_token: str) -> List[Dict]:
        """
        List all users (Admin only)
        
        GET /api/admin/users
        """
        return self.auth_system.list_users(admin_token)
    
    def auth_deactivate_user(self, admin_token: str, user_id: str) -> bool:
        """
        Deactivate a user account (Admin only)
        """
        return self.auth_system.deactivate_user(admin_token, user_id)
    
    def auth_change_user_role(self, admin_token: str, user_id: str, new_role: str) -> Dict:
        """
        Change user role (Admin only)
        """
        return self.auth_system.change_user_role(admin_token, user_id, new_role)
    
    def auth_delete_user(self, admin_token: str, user_id: str) -> bool:
        """
        Delete user permanently (Admin only)
        """
        return self.auth_system.delete_user(admin_token, user_id)
    
    def auth_get_audit_log(self, admin_token: str, n_entries: int = 100) -> List[str]:
        """
        Get authentication audit log (Admin only)
        """
        return self.auth_system.get_audit_log(admin_token, n_entries)
    
    def auth_create_initial_admin(self, email: str, password: str) -> Dict:
        """
        Create initial admin account (only when no users exist)
        Call this during first-time setup
        """
        return self.auth_system.create_initial_admin(email, password)
    
    # ==================== PATTERN RECOGNITION API ====================
    
    def analyze_patterns(self, symbol: str, days: int = 60) -> Dict:
        """
        Analyze technical patterns for a symbol
        
        POST /api/analysis/patterns
        
        Returns:
            {
                'patterns': List[Detected patterns],
                'support_resistance': List[S/R levels],
                'trend': Trend analysis,
                'volume_profile': Volume analysis,
                'summary': Human-readable summary
            }
        """
        try:
            # Get market data
            market_data = self.data_service.get_ohlcv(symbol, days=days)
            if market_data is None or market_data.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Run pattern analysis
            analysis = self.pattern_service.analyze(symbol, market_data)
            
            return {
                'symbol': symbol,
                'success': True,
                'patterns': [
                    {
                        'type': p.pattern_type.value,
                        'confidence': p.confidence,
                        'price_target': p.price_target,
                        'stop_loss': p.stop_loss,
                        'description': p.description,
                        'start_date': p.start_date.isoformat() if hasattr(p.start_date, 'isoformat') else str(p.start_date),
                        'end_date': p.end_date.isoformat() if hasattr(p.end_date, 'isoformat') else str(p.end_date)
                    }
                    for p in analysis.get('patterns', [])
                ],
                'support_resistance': [
                    {
                        'level': s.level,
                        'type': s.type,
                        'strength': s.strength,
                        'touches': s.touches,
                        'is_active': s.is_active
                    }
                    for s in analysis.get('support_resistance', [])
                ],
                'trend': analysis.get('trend', {}),
                'volume_profile': analysis.get('volume_profile', {}),
                'summary': analysis.get('summary', 'No patterns detected')
            }
            
        except Exception as e:
            log.error(f"Pattern analysis failed for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    # ==================== MEDIA ANALYSIS API ====================
    
    def analyze_media_sentiment(self, symbol: str, articles: Optional[List[Dict]] = None) -> Dict:
        """
        Analyze media sentiment for a symbol
        
        POST /api/analysis/sentiment
        
        Args:
            symbol: Stock symbol
            articles: Optional list of article dicts with 'title', 'content', 'source', 'published_at'
            
        Returns:
            {
                'overall_sentiment': str,
                'sentiment_score': float,
                'confidence': float,
                'article_count': int,
                'bullish_count': int,
                'bearish_count': int,
                'key_topics': List[str],
                'risk_indicators': List[str],
                'opportunity_indicators': List[str],
                'extreme_signals': Dict  # Contrarian signals at extremes
            }
        """
        try:
            # If no articles provided, return empty analysis
            # In production, this would fetch from news APIs
            analysis = self.media_service.analyze_sentiment(symbol, articles)
            
            # Get extreme signals
            extremes = self.media_service.detect_sentiment_extremes(symbol)
            
            return {
                'symbol': symbol,
                'success': True,
                'overall_sentiment': analysis.overall_sentiment,
                'sentiment_score': analysis.sentiment_score,
                'confidence': analysis.confidence,
                'article_count': analysis.article_count,
                'bullish_count': analysis.bullish_articles,
                'bearish_count': analysis.bearish_articles,
                'key_topics': analysis.key_topics,
                'risk_indicators': analysis.risk_indicators,
                'opportunity_indicators': analysis.opportunity_indicators,
                'extreme_signals': extremes,
                'last_updated': analysis.last_updated.isoformat()
            }
            
        except Exception as e:
            log.error(f"Media analysis failed for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    def get_sentiment_trend(self, symbol: str, days: int = 7) -> Dict:
        """
        Get sentiment trend over time
        
        GET /api/analysis/sentiment-trend
        """
        return self.media_service.get_sentiment_trend(symbol, days)


# Global instance
platform_orchestrator = AIPlatformOrchestrator()
