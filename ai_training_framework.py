"""
OraclAI Model Training & Self-Improvement Framework
Advanced training system for multi-agent AI models

Features:
- Performance tracking and analytics
- Feedback-based learning
- Knowledge base enhancement
- Confidence calibration
- Agent specialization training
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading


@dataclass
class AgentPerformance:
    """Tracks individual agent performance metrics"""
    agent_name: str
    total_queries: int = 0
    successful_predictions: int = 0
    consensus_accuracy: float = 0.0
    average_confidence: float = 0.0
    confidence_calibration: float = 0.0  # How well confidence matches accuracy
    expertise_areas: Dict[str, int] = field(default_factory=dict)
    response_times: List[float] = field(default_factory=list)
    feedback_scores: List[float] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TrainingSession:
    """Represents a training session for agents"""
    session_id: str
    agent_name: str
    training_type: str  # 'feedback', 'supervised', 'reinforcement', 'self_play'
    start_time: str
    end_time: Optional[str] = None
    samples_processed: int = 0
    accuracy_before: float = 0.0
    accuracy_after: float = 0.0
    improvements: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"  # running, completed, failed


class ModelTrainingEngine:
    """
    Central training engine for all AI models
    Implements various training strategies:
    - Feedback-based learning from user ratings
    - Self-play for debate improvement
    - Knowledge base expansion
    - Confidence calibration
    """
    
    def __init__(self, db_path: str = "ai_training.db"):
        self.db_path = db_path
        self.performance_data: Dict[str, AgentPerformance] = {}
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.knowledge_cache: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        
        self._init_database()
        self._load_performance_data()
    
    def _init_database(self):
        """Initialize training database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Agent performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_performance (
                agent_name TEXT PRIMARY KEY,
                total_queries INTEGER DEFAULT 0,
                successful_predictions INTEGER DEFAULT 0,
                consensus_accuracy REAL DEFAULT 0.0,
                average_confidence REAL DEFAULT 0.0,
                confidence_calibration REAL DEFAULT 0.0,
                expertise_areas TEXT DEFAULT '{}',
                last_updated TEXT
            )
        ''')
        
        # Training sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_sessions (
                session_id TEXT PRIMARY KEY,
                agent_name TEXT,
                training_type TEXT,
                start_time TEXT,
                end_time TEXT,
                samples_processed INTEGER DEFAULT 0,
                accuracy_before REAL DEFAULT 0.0,
                accuracy_after REAL DEFAULT 0.0,
                improvements TEXT DEFAULT '{}',
                status TEXT DEFAULT 'running'
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                agent_name TEXT,
                query_hash TEXT,
                user_rating INTEGER,  -- 1-5 scale
                feedback_text TEXT,
                predicted_stance TEXT,
                actual_outcome TEXT,
                timestamp TEXT
            )
        ''')
        
        # Knowledge expansions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_expansions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                category TEXT,
                new_knowledge TEXT,
                source TEXT,
                verified BOOLEAN DEFAULT 0,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_performance_data(self):
        """Load existing performance data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM agent_performance")
            rows = cursor.fetchall()
            
            for row in rows:
                self.performance_data[row[0]] = AgentPerformance(
                    agent_name=row[0],
                    total_queries=row[1],
                    successful_predictions=row[2],
                    consensus_accuracy=row[3],
                    average_confidence=row[4],
                    confidence_calibration=row[5],
                    expertise_areas=json.loads(row[6]),
                    last_updated=row[7]
                )
            
            conn.close()
        except Exception as e:
            print(f"[TrainingEngine] Error loading performance data: {e}")
    
    def record_query(self, agent_name: str, query: str, context: Dict, 
                     position: Any, consensus_reached: bool):
        """Record agent performance for a query"""
        with self.lock:
            if agent_name not in self.performance_data:
                self.performance_data[agent_name] = AgentPerformance(agent_name=agent_name)
            
            perf = self.performance_data[agent_name]
            perf.total_queries += 1
            
            # Update expertise areas
            query_lower = query.lower()
            for expertise in getattr(position, 'key_points', []):
                area = expertise.split(':')[0] if ':' in expertise else expertise
                perf.expertise_areas[area] = perf.expertise_areas.get(area, 0) + 1
            
            # Update confidence tracking
            if hasattr(position, 'confidence'):
                conf = position.confidence
                perf.average_confidence = (
                    (perf.average_confidence * (perf.total_queries - 1) + conf) / 
                    perf.total_queries
                )
            
            perf.last_updated = datetime.now().isoformat()
            
            # Save to database
            self._save_performance(agent_name)
    
    def record_feedback(self, session_id: str, agent_name: str, query: str,
                        user_rating: int, feedback_text: str = "",
                        predicted_stance: str = "", actual_outcome: str = ""):
        """Record user feedback for learning"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback 
            (session_id, agent_name, query_hash, user_rating, feedback_text,
             predicted_stance, actual_outcome, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, agent_name, query_hash, user_rating, feedback_text,
              predicted_stance, actual_outcome, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update agent performance with feedback
        with self.lock:
            if agent_name in self.performance_data:
                perf = self.performance_data[agent_name]
                perf.feedback_scores.append(user_rating)
                
                # Calculate moving average of feedback
                recent_scores = perf.feedback_scores[-20:]  # Last 20 feedbacks
                avg_feedback = sum(recent_scores) / len(recent_scores)
                
                # Adjust confidence calibration
                if avg_feedback >= 4.0:
                    perf.confidence_calibration = min(1.0, perf.confidence_calibration + 0.01)
                elif avg_feedback <= 2.0:
                    perf.confidence_calibration = max(0.0, perf.confidence_calibration - 0.02)
    
    def start_training_session(self, agent_name: str, training_type: str) -> str:
        """Start a new training session"""
        session_id = f"train_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TrainingSession(
            session_id=session_id,
            agent_name=agent_name,
            training_type=training_type,
            start_time=datetime.now().isoformat()
        )
        
        self.active_sessions[session_id] = session
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO training_sessions 
            (session_id, agent_name, training_type, start_time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, agent_name, training_type, session.start_time, 'running'))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def complete_training_session(self, session_id: str, improvements: Dict):
        """Mark training session as complete"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now().isoformat()
        session.status = "completed"
        session.improvements = improvements
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE training_sessions 
            SET end_time = ?, status = ?, improvements = ?
            WHERE session_id = ?
        ''', (session.end_time, 'completed', json.dumps(improvements), session_id))
        
        conn.commit()
        conn.close()
        
        del self.active_sessions[session_id]
    
    def get_agent_improvements(self, agent_name: str) -> Dict[str, Any]:
        """Get recommended improvements for an agent based on performance"""
        if agent_name not in self.performance_data:
            return {"error": "No performance data available"}
        
        perf = self.performance_data[agent_name]
        
        improvements = {
            "agent_name": agent_name,
            "current_metrics": {
                "total_queries": perf.total_queries,
                "average_confidence": round(perf.average_confidence, 3),
                "consensus_accuracy": round(perf.consensus_accuracy, 3),
                "calibration": round(perf.confidence_calibration, 3)
            },
            "recommendations": []
        }
        
        # Generate recommendations based on performance
        if perf.confidence_calibration < 0.5:
            improvements["recommendations"].append({
                "type": "confidence_calibration",
                "priority": "high",
                "description": "Confidence scores need calibration - consider adjusting based on accuracy",
                "action": "run_confidence_training"
            })
        
        if perf.total_queries < 100:
            improvements["recommendations"].append({
                "type": "more_data",
                "priority": "medium",
                "description": f"Limited query history ({perf.total_queries} queries). More data needed for reliable metrics.",
                "action": "continue_usage"
            })
        
        if perf.expertise_areas:
            # Find underrepresented areas
            sorted_areas = sorted(perf.expertise_areas.items(), key=lambda x: x[1])
            if sorted_areas and sorted_areas[0][1] < 5:
                improvements["recommendations"].append({
                    "type": "expertise_expansion",
                    "priority": "low",
                    "description": f"Expand knowledge in: {sorted_areas[0][0]} (only {sorted_areas[0][1]} queries)",
                    "action": "knowledge_base_expansion"
                })
        
        # Calculate recent feedback trend
        if len(perf.feedback_scores) >= 10:
            recent = perf.feedback_scores[-10:]
            older = perf.feedback_scores[-20:-10] if len(perf.feedback_scores) >= 20 else perf.feedback_scores[:10]
            
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            
            if recent_avg < older_avg - 0.5:
                improvements["recommendations"].append({
                    "type": "performance_decline",
                    "priority": "high",
                    "description": f"User satisfaction declining: {older_avg:.2f} -> {recent_avg:.2f}",
                    "action": "review_recent_changes"
                })
        
        return improvements
    
    def get_training_statistics(self) -> Dict:
        """Get overall training statistics"""
        total_queries = sum(p.total_queries for p in self.performance_data.values())
        avg_confidence = sum(p.average_confidence for p in self.performance_data.values()) / len(self.performance_data) if self.performance_data else 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total_feedback = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(user_rating) FROM feedback")
        avg_rating = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM training_sessions WHERE status = 'completed'")
        completed_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_agents": len(self.performance_data),
            "total_queries_processed": total_queries,
            "average_confidence": round(avg_confidence, 3),
            "total_user_feedback": total_feedback,
            "average_user_rating": round(avg_rating, 2),
            "completed_training_sessions": completed_sessions,
            "active_training_sessions": len(self.active_sessions),
            "agent_breakdown": {
                name: {
                    "queries": p.total_queries,
                    "confidence": round(p.average_confidence, 3)
                }
                for name, p in self.performance_data.items()
            }
        }
    
    def _save_performance(self, agent_name: str):
        """Save agent performance to database"""
        try:
            perf = self.performance_data[agent_name]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO agent_performance
                (agent_name, total_queries, successful_predictions, consensus_accuracy,
                 average_confidence, confidence_calibration, expertise_areas, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                perf.agent_name, perf.total_queries, perf.successful_predictions,
                perf.consensus_accuracy, perf.average_confidence, perf.confidence_calibration,
                json.dumps(perf.expertise_areas), perf.last_updated
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[TrainingEngine] Error saving performance: {e}")


class AgentSpecializationTrainer:
    """
    Trains agents to specialize in specific areas
    based on performance and feedback
    """
    
    def __init__(self, training_engine: ModelTrainingEngine):
        self.engine = training_engine
    
    def identify_specializations(self, agent_name: str) -> List[Dict]:
        """Identify what areas an agent should specialize in"""
        if agent_name not in self.engine.performance_data:
            return []
        
        perf = self.engine.performance_data[agent_name]
        
        # Sort expertise areas by frequency
        sorted_expertise = sorted(
            perf.expertise_areas.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        specializations = []
        for area, count in sorted_expertise[:5]:  # Top 5 areas
            if count >= 10:  # Minimum threshold
                specializations.append({
                    "area": area,
                    "experience_level": "expert" if count >= 50 else "proficient" if count >= 20 else "developing",
                    "query_count": count,
                    "confidence_in_area": self._calculate_area_confidence(agent_name, area)
                })
        
        return specializations
    
    def _calculate_area_confidence(self, agent_name: str, area: str) -> float:
        """Calculate agent's confidence in a specific area"""
        # This would analyze historical performance in this area
        # For now, return a placeholder based on query count
        perf = self.engine.performance_data.get(agent_name)
        if not perf:
            return 0.5
        
        count = perf.expertise_areas.get(area, 0)
        base_conf = perf.average_confidence
        
        # More queries = higher confidence in area
        area_boost = min(0.15, count / 100)
        return min(0.98, base_conf + area_boost)
    
    def generate_training_plan(self, agent_name: str) -> Dict:
        """Generate a personalized training plan for an agent"""
        specializations = self.identify_specializations(agent_name)
        
        plan = {
            "agent_name": agent_name,
            "current_specializations": specializations,
            "training_objectives": [],
            "recommended_sessions": []
        }
        
        # Add objectives based on current state
        if not specializations:
            plan["training_objectives"].append({
                "objective": "Establish core expertise",
                "priority": "high",
                "description": "Agent needs more queries to establish specialization areas"
            })
            plan["recommended_sessions"].append({
                "type": "diverse_practice",
                "description": "Process 100+ diverse queries to identify strengths"
            })
        else:
            # Strengthen top specialization
            top_area = specializations[0]["area"]
            plan["training_objectives"].append({
                "objective": f"Deepen expertise in {top_area}",
                "priority": "medium",
                "description": f"Become world-class expert in {top_area}"
            })
            
            # Add cross-training for other areas
            if len(specializations) < 3:
                plan["training_objectives"].append({
                    "objective": "Develop secondary expertise",
                    "priority": "low",
                    "description": "Expand knowledge to adjacent areas"
                })
        
        return plan


# Global training engine instance
training_engine = ModelTrainingEngine()
specialization_trainer = AgentSpecializationTrainer(training_engine)


def get_training_dashboard() -> Dict:
    """Get comprehensive training dashboard data"""
    stats = training_engine.get_training_statistics()
    
    # Add per-agent details
    agent_details = {}
    for agent_name in training_engine.performance_data:
        agent_details[agent_name] = {
            "performance": training_engine.get_agent_improvements(agent_name),
            "specializations": specialization_trainer.identify_specializations(agent_name),
            "training_plan": specialization_trainer.generate_training_plan(agent_name)
        }
    
    return {
        "overview": stats,
        "agents": agent_details,
        "system_status": "operational",
        "last_updated": datetime.now().isoformat()
    }
