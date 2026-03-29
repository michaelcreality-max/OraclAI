"""
AgentService - Multi-agent management and orchestration
Phase 3 Implementation
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.conservative_agent import ConservativeAgent
from agents.aggressive_agent import AggressiveAgent
from agents.quantitative_agent import QuantitativeAgent
from agents.sentiment_agent import SentimentAgent
from agents.risk_manager_agent import RiskManagerAgent

from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, DebateSession, AgentArgument
)
from core.exceptions import AgentError

log = logging.getLogger(__name__)


class AgentService:
    """
    Service for managing and orchestrating multiple trading agents.
    Coordinates analysis across all agent types and prepares for debate.
    """
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self._initialize_agents()
        
        # Agent weight tracking for adaptive learning
        self.agent_weights = {
            AgentType.CONSERVATIVE: 0.15,
            AgentType.AGGRESSIVE: 0.20,
            AgentType.QUANTITATIVE: 0.20,
            AgentType.SENTIMENT: 0.15,
            AgentType.RISK_MANAGER: 0.30  # Risk manager has veto power
        }
        
        log.info("AgentService initialized with 5 agents")
    
    def _initialize_agents(self):
        """Initialize all 5 agent types"""
        self.agents[AgentType.CONSERVATIVE] = ConservativeAgent("conservative_001")
        self.agents[AgentType.AGGRESSIVE] = AggressiveAgent("aggressive_001")
        self.agents[AgentType.QUANTITATIVE] = QuantitativeAgent("quantitative_001")
        self.agents[AgentType.SENTIMENT] = SentimentAgent("sentiment_001")
        self.agents[AgentType.RISK_MANAGER] = RiskManagerAgent("risk_manager_001")
    
    def analyze_signal(self, signal: TradingSignal,
                      market_context: Optional[Dict] = None) -> Dict[AgentType, AgentPosition]:
        """
        Have all agents analyze a trading signal
        
        Args:
            signal: TradingSignal to analyze
            market_context: Additional market context
            
        Returns:
            Dict mapping agent types to their positions
        """
        positions = {}
        
        for agent_type, agent in self.agents.items():
            try:
                position = agent.analyze(signal, market_context)
                positions[agent_type] = position
                log.debug(f"{agent_type.value}: {position.stance.value} "
                         f"(conf: {position.confidence:.2f})")
            except Exception as e:
                log.error(f"Agent {agent_type.value} failed: {e}")
                # Return neutral position on error
                positions[agent_type] = AgentPosition(
                    agent_id=agent.agent_id,
                    agent_type=agent_type,
                    symbol=signal.symbol,
                    stance=PositionStance.HOLD,
                    confidence=0.0,
                    position_size_pct=0.0,
                    reasoning=f"Analysis error: {str(e)}",
                    timestamp=datetime.now()
                )
        
        return positions
    
    def analyze_batch(self, signals: List[TradingSignal],
                     market_context: Optional[Dict] = None) -> List[Dict[AgentType, AgentPosition]]:
        """
        Analyze multiple signals across all agents
        
        Args:
            signals: List of TradingSignals
            market_context: Shared market context
            
        Returns:
            List of position dicts, one per signal
        """
        return [
            self.analyze_signal(signal, market_context)
            for signal in signals
        ]
    
    def prepare_debate_session(self, signal: TradingSignal,
                               positions: Dict[AgentType, AgentPosition]) -> DebateSession:
        """
        Prepare a debate session from agent positions
        
        Args:
            signal: The trading signal being debated
            positions: All agent positions
            
        Returns:
            DebateSession ready for debate
        """
        arguments = []
        
        for agent_type, position in positions.items():
            # Skip risk manager from debate (it provides risk overlay)
            if agent_type == AgentType.RISK_MANAGER:
                continue
            
            argument = AgentArgument(
                agent_id=position.agent_id,
                agent_type=agent_type,
                stance=position.stance,
                confidence=position.confidence,
                reasoning=position.reasoning,
                supporting_factors=position.supporting_factors,
                opposing_factors=position.opposing_factors,
                expected_return=getattr(position, 'expected_return', 0.0),
                position_size_pct=position.position_size_pct
            )
            arguments.append(argument)
        
        # Check for risk manager veto
        risk_position = positions.get(AgentType.RISK_MANAGER)
        risk_override = risk_position.risk_override if risk_position else False
        
        return DebateSession(
            symbol=signal.symbol,
            topic=f"Investment decision for {signal.symbol}",
            signal=signal,
            arguments=arguments,
            risk_assessment=self._create_risk_assessment(positions),
            risk_override=risk_override,
            start_time=datetime.now()
        )
    
    def _create_risk_assessment(self, positions: Dict[AgentType, AgentPosition]) -> Dict:
        """Create risk assessment from positions"""
        risk_manager = self.agents.get(AgentType.RISK_MANAGER)
        
        if risk_manager:
            position_list = list(positions.values())
            return risk_manager.assess_portfolio_risk(position_list).__dict__
        
        return {
            'portfolio_heat': 0.0,
            'risk_level': 'unknown',
            'timestamp': datetime.now()
        }
    
    def get_agent_performance(self) -> Dict[str, Dict]:
        """Get performance summary for all agents"""
        return {
            agent_type.value: agent.get_performance_summary()
            for agent_type, agent in self.agents.items()
        }
    
    def update_agent_weights(self, performance_data: Dict[str, float]):
        """
        Update agent weights based on recent performance
        
        Args:
            performance_data: Dict of agent_type -> performance_score
        """
        # Simple exponential moving average update
        alpha = 0.3  # Learning rate
        
        for agent_type_str, score in performance_data.items():
            agent_type = AgentType(agent_type_str)
            current_weight = self.agent_weights[agent_type]
            new_weight = (1 - alpha) * current_weight + alpha * score
            self.agent_weights[agent_type] = max(0.05, min(0.50, new_weight))
        
        # Normalize to sum to 1
        total = sum(self.agent_weights.values())
        self.agent_weights = {k: v/total for k, v in self.agent_weights.items()}
        
        log.info(f"Updated agent weights: {self.agent_weights}")
    
    def get_consensus(self, positions: Dict[AgentType, AgentPosition],
                     risk_weight: float = 0.30) -> Dict:
        """
        Calculate consensus from all agent positions
        
        Args:
            positions: All agent positions
            risk_weight: Weight given to risk manager
            
        Returns:
            Consensus dict with stance, confidence, and sizing
        """
        # Count weighted votes
        buy_votes = 0.0
        sell_votes = 0.0
        hold_votes = 0.0
        
        for agent_type, position in positions.items():
            weight = self.agent_weights[agent_type]
            
            # Risk manager gets extra weight and can veto
            if agent_type == AgentType.RISK_MANAGER:
                if position.risk_override:
                    return {
                        'stance': 'HOLD',
                        'confidence': position.confidence,
                        'position_size_pct': 0.0,
                        'reasoning': 'Risk manager veto',
                        'agent_count': len(positions),
                        'buy_votes': 0,
                        'sell_votes': 0,
                        'hold_votes': len(positions)
                    }
                weight = risk_weight
            
            confidence = position.confidence * weight
            
            if position.stance.value == 'buy':
                buy_votes += confidence
            elif position.stance.value == 'sell':
                sell_votes += confidence
            else:
                hold_votes += confidence
        
        # Determine consensus
        total_votes = buy_votes + sell_votes + hold_votes
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            stance = 'BUY'
            confidence = buy_votes / total_votes if total_votes > 0 else 0
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            stance = 'SELL'
            confidence = sell_votes / total_votes if total_votes > 0 else 0
        else:
            stance = 'HOLD'
            confidence = hold_votes / total_votes if total_votes > 0 else 0
        
        # Calculate position size based on confidence and consensus
        # Weight average of position sizes from agents in consensus
        position_sizes = []
        for agent_type, position in positions.items():
            if position.stance.value.lower() == stance.lower():
                position_sizes.append(position.position_size_pct)
        
        avg_position_size = sum(position_sizes) / len(position_sizes) if position_sizes else 0
        
        return {
            'stance': stance,
            'confidence': confidence,
            'position_size_pct': avg_position_size * confidence,
            'reasoning': f"Weighted consensus: {buy_votes:.2f} buy, {sell_votes:.2f} sell, {hold_votes:.2f} hold",
            'agent_count': len(positions),
            'buy_votes': sum(1 for p in positions.values() if p.stance.value == 'buy'),
            'sell_votes': sum(1 for p in positions.values() if p.stance.value == 'sell'),
            'hold_votes': sum(1 for p in positions.values() if p.stance.value == 'hold')
        }
    
    def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs"""
        return [agent.agent_id for agent in self.agents.values()]
    
    def reset_agent_performance(self):
        """Reset all agent performance tracking"""
        for agent in self.agents.values():
            agent.performance_history = []
            agent.profile.win_rate = 0.5
            agent.profile.avg_return = 0.0
        
        log.info("Agent performance reset")


# Global instance
agent_service = AgentService()
