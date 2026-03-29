"""
Base Agent Class
Abstract base for all trading agents
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime

from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, AgentProfile
)


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    Each agent interprets signals differently based on their personality.
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.profile = self._create_profile()
        self.performance_history = []
        self.active_positions = {}
    
    @abstractmethod
    def _create_profile(self) -> AgentProfile:
        """Create agent-specific profile"""
        pass
    
    @abstractmethod
    def analyze(self, signal: TradingSignal, 
                market_context: Optional[Dict] = None) -> AgentPosition:
        """
        Analyze a trading signal and produce a position stance.
        
        Args:
            signal: TradingSignal to analyze
            market_context: Additional market context (optional)
            
        Returns:
            AgentPosition with stance and reasoning
        """
        pass
    
    def update_performance(self, realized_return: float, 
                          predicted_signal: str, actual_outcome: str):
        """Track agent performance for adaptive learning"""
        self.performance_history.append({
            'timestamp': datetime.now(),
            'realized_return': realized_return,
            'predicted': predicted_signal,
            'actual': actual_outcome,
            'correct': predicted_signal == actual_outcome
        })
        
        # Update profile metrics
        if len(self.performance_history) > 0:
            recent = self.performance_history[-20:]  # Last 20 trades
            self.profile.win_rate = sum(1 for p in recent if p['correct']) / len(recent)
            self.profile.avg_return = sum(p['realized_return'] for p in recent) / len(recent)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for this agent"""
        if not self.performance_history:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_return': 0.0
            }
        
        recent = self.performance_history[-50:]  # Last 50 trades
        return {
            'total_trades': len(self.performance_history),
            'recent_trades': len(recent),
            'win_rate': sum(1 for p in recent if p['correct']) / len(recent) if recent else 0,
            'avg_return': sum(p['realized_return'] for p in recent) / len(recent) if recent else 0,
            'agent_type': self.agent_type.value,
            'risk_tolerance': self.profile.risk_tolerance
        }
