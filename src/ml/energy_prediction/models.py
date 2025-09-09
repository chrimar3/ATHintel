"""
🤖 ML Models for Energy Prediction

Advanced machine learning models optimized for Greek energy market conditions.
Includes ensemble methods, deep learning, and specialized energy efficiency predictors.
"""

import joblib
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
import logging

from domains.energy.value_objects.energy_class import EnergyClass
from .features import BuildingFeatures, MarketFeatures, ClimateFeatures

logger = logging.getLogger(__name__)

# Optional ML dependencies - graceful fallbacks if not available
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import mean_absolute_error, accuracy_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available, using mock implementations")
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

class BaseEnergyModel(ABC):
    """Base class for all energy prediction models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.training_date = None
        self.feature_names = []
        self.model_version = "1.0"
        
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs):
        """Train the model"""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        pass
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_name': self.model_name,
            'training_date': self.training_date,
            'feature_names': self.feature_names,
            'model_version': self.model_version,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model {self.model_name} saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data.get('scaler')
            self.model_name = model_data['model_name']
            self.training_date = model_data.get('training_date')
            self.feature_names = model_data.get('feature_names', [])
            self.model_version = model_data.get('model_version', '1.0')
            self.is_trained = model_data.get('is_trained', True)
            
            logger.info(f"Model {self.model_name} loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load model from {filepath}: {e}")
            raise

class EnergyClassPredictor(BaseEnergyModel):
    """
    Multi-class classifier for predicting EU energy classes (A+ to G)
    Optimized for Greek building characteristics
    """
    
    def __init__(self):
        super().__init__("EnergyClassPredictor")
        self.label_encoder = LabelEncoder() if SKLEARN_AVAILABLE else None
        self.class_names = ['A+', 'A', 'B+', 'B', 'C', 'D', 'E', 'F', 'G']
        
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs):
        """Train energy class prediction model"""
        
        if not SKLEARN_AVAILABLE:
            self._train_mock(X, y)
            return
        
        # Encode target classes
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Create ensemble model optimized for energy class prediction
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',  # Handle class imbalance
            random_state=42
        )
        
        # Train model
        self.model.fit(X_scaled, y_encoded)
        
        # Validate with cross-validation
        cv_scores = cross_val_score(self.model, X_scaled, y_encoded, cv=5, scoring='accuracy')
        
        self.is_trained = True
        self.training_date = datetime.now()
        
        logger.info(f"Energy class model trained with {X.shape[0]} samples")
        logger.info(f"Cross-validation accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Feature importance analysis
        self._analyze_feature_importance(X)
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict energy classes with confidence scores
        Returns: (predicted_classes, prediction_probabilities)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if not SKLEARN_AVAILABLE:
            return self._predict_mock(X)
        
        X_scaled = self.scaler.transform(X)
        
        # Get predictions and probabilities
        y_pred_encoded = self.model.predict(X_scaled)
        y_pred_proba = self.model.predict_proba(X_scaled)
        
        # Decode predictions
        y_pred = self.label_encoder.inverse_transform(y_pred_encoded)
        
        # Convert to EnergyClass objects
        energy_classes = [EnergyClass(pred) for pred in y_pred]
        
        # Get confidence (max probability)
        confidences = np.max(y_pred_proba, axis=1)
        
        return energy_classes, confidences
    
    def predict_single(self, building_features: BuildingFeatures) -> Tuple[EnergyClass, float]:
        """Predict energy class for a single property"""
        X = building_features.to_array().reshape(1, -1)
        classes, confidences = self.predict(X)
        return classes[0], confidences[0]
    
    def _train_mock(self, X: np.ndarray, y: np.ndarray):
        """Mock training when sklearn is not available"""
        self.is_trained = True
        self.training_date = datetime.now()
        logger.info(f"Mock training completed for {self.model_name}")
    
    def _predict_mock(self, X: np.ndarray) -> Tuple[List[EnergyClass], np.ndarray]:
        """Mock prediction when sklearn is not available"""
        # Return reasonable mock predictions based on building age
        predictions = []
        confidences = []
        
        for i in range(X.shape[0]):
            # Use building age (index 2) as proxy
            building_age = X[i, 2] * 100  # Denormalize
            
            if building_age < 10:
                pred_class = EnergyClass.A
                confidence = 0.85
            elif building_age < 25:
                pred_class = EnergyClass.B
                confidence = 0.80
            elif building_age < 40:
                pred_class = EnergyClass.C
                confidence = 0.75
            else:
                pred_class = EnergyClass.D
                confidence = 0.70
            
            predictions.append(pred_class)
            confidences.append(confidence)
        
        return predictions, np.array(confidences)
    
    def _analyze_feature_importance(self, X: np.ndarray):
        """Analyze and log feature importance"""
        if not SKLEARN_AVAILABLE or not hasattr(self.model, 'feature_importances_'):
            return
        
        importances = self.model.feature_importances_
        feature_names = self.feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        # Sort features by importance
        indices = np.argsort(importances)[::-1]
        
        logger.info("Top 10 most important features:")
        for i in range(min(10, len(indices))):
            idx = indices[i]
            logger.info(f"  {feature_names[idx] if idx < len(feature_names) else f'Feature {idx}'}: {importances[idx]:.3f}")

class ConsumptionPredictor(BaseEnergyModel):
    """
    Regression model for predicting annual energy consumption (kWh/m²/year)
    """
    
    def __init__(self):
        super().__init__("ConsumptionPredictor")
        
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs):
        """Train consumption prediction model"""
        
        if not SKLEARN_AVAILABLE:
            self._train_mock(X, y)
            return
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Use gradient boosting for better non-linear relationships
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=300,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Evaluate with cross-validation
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5, scoring='neg_mean_absolute_error')
        mae = -cv_scores.mean()
        
        self.is_trained = True
        self.training_date = datetime.now()
        
        logger.info(f"Consumption model trained with {X.shape[0]} samples")
        logger.info(f"Cross-validation MAE: {mae:.2f} kWh/m²/year")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict annual energy consumption"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if not SKLEARN_AVAILABLE:
            return self._predict_mock(X)
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        # Ensure predictions are within reasonable bounds
        predictions = np.clip(predictions, 20, 500)  # 20-500 kWh/m²/year
        
        return predictions
    
    def predict_with_uncertainty(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with uncertainty estimates"""
        predictions = self.predict(X)
        
        # Estimate uncertainty based on model characteristics
        # For ensemble models, could use prediction variance
        uncertainty = predictions * 0.15  # ±15% uncertainty estimate
        
        return predictions, uncertainty
    
    def _train_mock(self, X: np.ndarray, y: np.ndarray):
        """Mock training when sklearn is not available"""
        self.is_trained = True
        self.training_date = datetime.now()
        
    def _predict_mock(self, X: np.ndarray) -> np.ndarray:
        """Mock prediction when sklearn is not available"""
        # Simple heuristic based on building age and area
        predictions = []
        
        for i in range(X.shape[0]):
            building_age = X[i, 2] * 100  # Denormalize age
            total_area = X[i, 0] * 1000    # Denormalize area
            
            # Base consumption increases with age
            base_consumption = 80 + (building_age * 2.5)
            
            # Adjust for building size (smaller buildings less efficient per m²)
            size_factor = 1.0 + (1.0 / max(total_area / 100, 1.0)) * 0.2
            
            consumption = base_consumption * size_factor
            consumption = max(30, min(400, consumption))  # Reasonable bounds
            
            predictions.append(consumption)
        
        return np.array(predictions)

class ROIPredictor(BaseEnergyModel):
    """
    Model for predicting Return on Investment for energy upgrades
    """
    
    def __init__(self):
        super().__init__("ROIPredictor")
        
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs):
        """Train ROI prediction model"""
        
        if not SKLEARN_AVAILABLE:
            self._train_mock(X, y)
            return
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # ROI prediction benefits from ensemble approach
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            min_samples_split=3,
            min_samples_leaf=1,
            random_state=42
        )
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Evaluate
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5, scoring='neg_mean_absolute_error')
        mae = -cv_scores.mean()
        
        self.is_trained = True
        self.training_date = datetime.now()
        
        logger.info(f"ROI model trained with {X.shape[0]} samples")
        logger.info(f"Cross-validation MAE: {mae:.2f}% ROI")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict ROI percentages for energy upgrades"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if not SKLEARN_AVAILABLE:
            return self._predict_mock(X)
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        # Ensure reasonable ROI bounds
        predictions = np.clip(predictions, -10, 50)  # -10% to 50% ROI
        
        return predictions
    
    def _train_mock(self, X: np.ndarray, y: np.ndarray):
        """Mock training when sklearn is not available"""
        self.is_trained = True
        self.training_date = datetime.now()
    
    def _predict_mock(self, X: np.ndarray) -> np.ndarray:
        """Mock prediction when sklearn is not available"""
        predictions = []
        
        for i in range(X.shape[0]):
            # ROI generally higher for older, less efficient buildings
            building_age = X[i, 2] * 100
            current_efficiency = X[i, 20:23].mean()  # Average insulation scores
            
            base_roi = 8.0  # Base 8% ROI
            
            # Age bonus (older buildings have more potential)
            age_bonus = min(building_age / 10, 15)  # Up to 15% bonus
            
            # Efficiency penalty (already efficient buildings have less potential)
            efficiency_penalty = current_efficiency * 20  # Up to 20% penalty
            
            roi = base_roi + age_bonus - efficiency_penalty
            roi = max(-5, min(35, roi))  # Reasonable bounds
            
            predictions.append(roi)
        
        return np.array(predictions)

class MarketTrendPredictor(BaseEnergyModel):
    """
    Time series model for predicting energy market trends and prices
    """
    
    def __init__(self):
        super().__init__("MarketTrendPredictor")
        self.trend_window = 12  # months
        
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs):
        """Train market trend prediction model"""
        
        if not SKLEARN_AVAILABLE:
            self._train_mock(X, y)
            return
        
        # Market data might not need scaling for some features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Use linear model for interpretable market trends
        self.model = Ridge(alpha=1.0)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        self.is_trained = True
        self.training_date = datetime.now()
        
        logger.info(f"Market trend model trained with {X.shape[0]} samples")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict market trends"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if not SKLEARN_AVAILABLE:
            return self._predict_mock(X)
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_energy_price_trend(self, market_features: MarketFeatures, months_ahead: int = 6) -> float:
        """Predict energy price trend for next N months"""
        # Simplified prediction based on current trends
        current_trend = market_features.electricity_price_trend
        
        # Apply momentum with decay
        decay_factor = 0.85 ** (months_ahead / 6)  # Trends decay over time
        predicted_trend = current_trend * decay_factor
        
        return min(max(predicted_trend, -20), 30)  # ±30% max change
    
    def _train_mock(self, X: np.ndarray, y: np.ndarray):
        """Mock training when sklearn is not available"""
        self.is_trained = True
        self.training_date = datetime.now()
    
    def _predict_mock(self, X: np.ndarray) -> np.ndarray:
        """Mock prediction when sklearn is not available"""
        # Return modest positive trend predictions
        return np.random.normal(2.5, 1.5, X.shape[0])  # 2.5% ± 1.5% trend

# Model Factory and Ensemble

class EnergyModelEnsemble:
    """
    Ensemble of energy prediction models for robust predictions
    """
    
    def __init__(self):
        self.models = {
            'energy_class': EnergyClassPredictor(),
            'consumption': ConsumptionPredictor(),
            'roi': ROIPredictor(),
            'market_trend': MarketTrendPredictor()
        }
        self.is_trained = False
    
    def train_all(self, training_data: Dict[str, Tuple[np.ndarray, np.ndarray]]):
        """Train all models in the ensemble"""
        for model_name, (X, y) in training_data.items():
            if model_name in self.models:
                logger.info(f"Training {model_name} model...")
                self.models[model_name].train(X, y)
        
        self.is_trained = True
        logger.info("Ensemble training completed")
    
    def predict_comprehensive(self, building_features: BuildingFeatures) -> Dict[str, Any]:
        """Make comprehensive predictions using all models"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before making predictions")
        
        X = building_features.to_array().reshape(1, -1)
        
        results = {}
        
        # Energy class prediction
        energy_class, confidence = self.models['energy_class'].predict_single(building_features)
        results['energy_class'] = {
            'predicted_class': energy_class,
            'confidence': confidence
        }
        
        # Consumption prediction
        consumption = self.models['consumption'].predict(X)[0]
        results['annual_consumption'] = {
            'kwh_per_m2': consumption,
            'total_kwh': consumption * float(building_features.total_area)
        }
        
        # ROI prediction (mock upgrade scenario)
        roi = self.models['roi'].predict(X)[0]
        results['upgrade_roi'] = {
            'expected_roi_percentage': roi,
            'investment_attractiveness': 'High' if roi > 15 else 'Medium' if roi > 8 else 'Low'
        }
        
        return results
    
    def save_ensemble(self, base_path: str):
        """Save all models in the ensemble"""
        for model_name, model in self.models.items():
            if model.is_trained:
                filepath = f"{base_path}_{model_name}_model.joblib"
                model.save_model(filepath)
    
    def load_ensemble(self, base_path: str):
        """Load all models in the ensemble"""
        for model_name, model in self.models.items():
            try:
                filepath = f"{base_path}_{model_name}_model.joblib"
                model.load_model(filepath)
            except Exception as e:
                logger.warning(f"Failed to load {model_name} model: {e}")

def create_default_ensemble() -> EnergyModelEnsemble:
    """Create ensemble with default Greek energy models"""
    ensemble = EnergyModelEnsemble()
    
    # In a production system, this would load pre-trained models
    logger.info("Created default energy model ensemble")
    
    return ensemble