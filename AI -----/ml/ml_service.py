"""
MLService - Machine Learning ensemble for predictions
Phase 2 Implementation
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import asdict
from sklearn.linear_model import Ridge, ElasticNet, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

from core.data_structures import (
    FeatureVector, FeatureMatrix, ModelPrediction, ModelMetrics
)
from core.exceptions import MLError, ModelTrainingError, PredictionError

log = logging.getLogger(__name__)


class LinearModels:
    """Linear model implementations"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.ridge = Ridge(alpha=1.0)
        self.elastic = ElasticNet(alpha=0.1, l1_ratio=0.5)
        self.logistic = LogisticRegression(max_iter=1000)
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit linear models"""
        X_scaled = self.scaler.fit_transform(X)
        
        self.ridge.fit(X_scaled, y)
        self.elastic.fit(X_scaled, y)
        
        # Logistic for classification (up/down)
        y_binary = (y > 0).astype(int)
        if len(np.unique(y_binary)) > 1:
            self.logistic.fit(X_scaled, y_binary)
        
        self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict using linear models"""
        if not self.is_fitted:
            raise PredictionError("Models not fitted")
        
        X_scaled = self.scaler.transform(X)
        
        return {
            'ridge': self.ridge.predict(X_scaled),
            'elastic': self.elastic.predict(X_scaled),
            'logistic_proba': self.logistic.predict_proba(X_scaled)[:, 1] if hasattr(self.logistic, 'classes_') else np.ones(len(X)) * 0.5
        }


class TreeModels:
    """Tree-based model implementations (lightweight)"""
    
    def __init__(self):
        self.rf = RandomForestRegressor(
            n_estimators=50,  # Lightweight
            max_depth=10,
            min_samples_split=20,
            random_state=42,
            n_jobs=-1
        )
        self.gb = GradientBoostingRegressor(
            n_estimators=50,  # Lightweight
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit tree models"""
        self.rf.fit(X, y)
        self.gb.fit(X, y)
        self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict using tree models"""
        if not self.is_fitted:
            raise PredictionError("Models not fitted")
        
        return {
            'random_forest': self.rf.predict(X),
            'gradient_boost': self.gb.predict(X)
        }


class EnsembleWeighter:
    """Dynamic ensemble weighting based on performance"""
    
    def __init__(self, models: List[str], initial_weight: float = None):
        self.models = models
        if initial_weight is None:
            initial_weight = 1.0 / len(models)
        self.weights = {model: initial_weight for model in models}
        self.performance_history = {model: [] for model in models}
    
    def update_weights(self, recent_performance: Dict[str, float], learning_rate: float = 2.0):
        """
        Update weights based on recent performance
        
        Args:
            recent_performance: Dict of model -> accuracy/error score
            learning_rate: Temperature parameter for softmax
        """
        # Calculate raw weights using softmax
        raw_weights = {}
        for model in self.models:
            perf = recent_performance.get(model, 0.5)
            raw_weights[model] = np.exp(learning_rate * perf)
        
        # Normalize
        total = sum(raw_weights.values())
        new_weights = {model: w/total for model, w in raw_weights.items()}
        
        # Blend with old weights (momentum)
        momentum = 0.7
        for model in self.models:
            self.weights[model] = (
                momentum * self.weights[model] +
                (1 - momentum) * new_weights[model]
            )
        
        # Renormalize
        total = sum(self.weights.values())
        self.weights = {m: w/total for m, w in self.weights.items()}
        
        log.info(f"Updated weights: {self.weights}")
    
    def get_weights(self) -> Dict[str, float]:
        """Get current weights"""
        return self.weights.copy()


class MLService:
    """
    Machine Learning Service with ensemble of models
    """
    
    def __init__(self):
        self.linear_models = LinearModels()
        self.tree_models = TreeModels()
        self.ensemble_weighter = EnsembleWeighter([
            'ridge', 'elastic', 'random_forest', 'gradient_boost'
        ])
        
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []
        
        # Model performance tracking
        self.model_metrics = {}
        
        log.info("MLService initialized")
    
    def train(self, features: FeatureMatrix, returns: np.ndarray) -> Dict[str, Any]:
        """
        Train all models on feature data
        
        Args:
            features: FeatureMatrix with training data
            returns: Array of forward returns (target variable)
            
        Returns:
            Training results with cross-validation scores
        """
        if len(features.features) < 100:
            raise ModelTrainingError(f"Insufficient data: {len(features.features)} samples, need 100+")
        
        X = features.features
        y = returns
        
        # Remove any NaN/Inf
        valid_mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(X) < 50:
            raise ModelTrainingError(f"Too few valid samples after cleaning: {len(X)}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=3)
        cv_scores = {}
        
        for model_name in ['ridge', 'elastic', 'rf', 'gb']:
            scores = []
            for train_idx, val_idx in tscv.split(X_scaled):
                X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                try:
                    if model_name in ['ridge', 'elastic']:
                        if model_name == 'ridge':
                            model = Ridge(alpha=1.0)
                        else:
                            model = ElasticNet(alpha=0.1, l1_ratio=0.5)
                        model.fit(X_train, y_train)
                        pred = model.predict(X_val)
                    else:
                        if model_name == 'rf':
                            model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
                        else:
                            model = GradientBoostingRegressor(n_estimators=50, max_depth=5, random_state=42)
                        model.fit(X_train, y_train)
                        pred = model.predict(X_val)
                    
                    # Calculate R²
                    ss_res = np.sum((y_val - pred) ** 2)
                    ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
                    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    scores.append(r2)
                except Exception as e:
                    log.warning(f"CV failed for {model_name}: {e}")
                    scores.append(0)
            
            cv_scores[model_name] = np.mean(scores)
        
        # Fit final models on all data
        self.linear_models.fit(X_scaled, y)
        self.tree_models.fit(X_scaled, y)
        
        self.is_fitted = True
        self.feature_names = features.feature_names
        
        # Update weights based on CV performance
        perf_map = {
            'ridge': cv_scores['ridge'],
            'elastic': cv_scores['elastic'],
            'random_forest': cv_scores['rf'],
            'gradient_boost': cv_scores['gb']
        }
        self.ensemble_weighter.update_weights(perf_map)
        
        # Store metrics
        self.model_metrics = {
            name: ModelMetrics(
                model_name=name,
                accuracy=max(0, score),
                last_updated=datetime.now()
            )
            for name, score in perf_map.items()
        }
        
        log.info(f"Training complete. CV scores: {cv_scores}")
        
        return {
            'cv_scores': cv_scores,
            'ensemble_weights': self.ensemble_weighter.get_weights(),
            'n_samples': len(X),
            'n_features': X.shape[1]
        }
    
    def predict(self, features: FeatureVector) -> ModelPrediction:
        """
        Generate prediction for a single feature vector
        
        Args:
            features: FeatureVector with input features
            
        Returns:
            ModelPrediction with ensemble output
        """
        if not self.is_fitted:
            raise PredictionError("Models not trained. Call train() first.")
        
        # Prepare input
        X = features.values_array.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from all models
        linear_preds = self.linear_models.predict(X_scaled)
        tree_preds = self.tree_models.predict(X_scaled)
        
        # Combine all predictions
        all_preds = {
            'ridge': linear_preds['ridge'][0],
            'elastic': linear_preds['elastic'][0],
            'random_forest': tree_preds['random_forest'][0],
            'gradient_boost': tree_preds['gradient_boost'][0]
        }
        
        # Weighted ensemble
        weights = self.ensemble_weighter.get_weights()
        ensemble_pred = sum(
            all_preds[model] * weights.get(model, 0.25)
            for model in all_preds
        )
        
        # Calculate direction probabilities
        # Based on ensemble prediction distribution
        up_prob = 1 / (1 + np.exp(-ensemble_pred * 10))  # Sigmoid
        down_prob = 1 - up_prob
        
        # Adjust based on model agreement
        direction_signs = [1 if p > 0 else -1 for p in all_preds.values()]
        agreement = abs(sum(direction_signs)) / len(direction_signs)
        
        # Confidence based on agreement and prediction magnitude
        confidence = agreement * min(abs(ensemble_pred) * 5, 1.0)
        confidence = max(0.1, min(0.95, confidence))  # Clip to reasonable range
        
        # Model contributions
        model_contributions = {
            model: pred * weights.get(model, 0.25)
            for model, pred in all_preds.items()
        }
        
        return ModelPrediction(
            symbol=features.symbol,
            direction_prob={
                'up': up_prob,
                'down': down_prob,
                'flat': 1 - up_prob - down_prob if abs(ensemble_pred) < 0.01 else 0
            },
            expected_return=ensemble_pred,
            confidence=confidence,
            model_contributions=model_contributions,
            timestamp=datetime.now()
        )
    
    def predict_batch(self, features: FeatureMatrix) -> List[ModelPrediction]:
        """
        Generate predictions for multiple samples
        
        Args:
            features: FeatureMatrix with multiple samples
            
        Returns:
            List of ModelPrediction objects
        """
        predictions = []
        
        for i, symbol in enumerate(features.symbols):
            fv = FeatureVector(
                symbol=symbol,
                timestamp=features.timestamps[i],
                features=dict(zip(features.feature_names, features.features[i])),
                feature_names=features.feature_names
            )
            
            try:
                pred = self.predict(fv)
                predictions.append(pred)
            except Exception as e:
                log.error(f"Prediction failed for {symbol}: {e}")
                # Return neutral prediction on error
                predictions.append(ModelPrediction(
                    symbol=symbol,
                    direction_prob={'up': 0.33, 'down': 0.33, 'flat': 0.34},
                    expected_return=0.0,
                    confidence=0.33,
                    model_contributions={},
                    timestamp=datetime.now()
                ))
        
        return predictions
    
    def get_model_performance(self) -> Dict[str, ModelMetrics]:
        """Get performance metrics for all models"""
        return self.model_metrics.copy()
    
    def update_ensemble_weights(self, recent_performance: Dict[str, float]):
        """Manually update ensemble weights"""
        self.ensemble_weighter.update_weights(recent_performance)
        log.info(f"Updated ensemble weights: {self.ensemble_weighter.get_weights()}")


# Global instance
ml_service = MLService()
