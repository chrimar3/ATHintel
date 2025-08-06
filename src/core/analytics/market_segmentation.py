"""
Advanced Market Segmentation Analytics - Enterprise 2025

Implements state-of-the-art market segmentation using machine learning,
statistical modeling, and advanced clustering techniques for Athens real estate.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import logging
from collections import defaultdict

# Advanced Analytics Stack
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.ensemble import IsolationForest
from scipy import stats
from scipy.spatial.distance import pdist, linkage
from scipy.cluster.hierarchy import dendrogram, fcluster
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..domain.entities import Property, PropertyType, EnergyClass, MarketSegment
from ..ports.repositories import PropertyRepository

logger = logging.getLogger(__name__)


class SegmentationMethod(str, Enum):
    """Market segmentation methods available"""
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    HIERARCHICAL = "hierarchical"
    GAUSSIAN_MIXTURE = "gaussian_mixture"
    HYBRID = "hybrid"


class AnalyticsMetric(str, Enum):
    """Analytics metrics for evaluation"""
    SILHOUETTE_SCORE = "silhouette_score"
    CALINSKI_HARABASZ = "calinski_harabasz"
    DAVIES_BOULDIN = "davies_bouldin"
    INERTIA = "inertia"
    ADJUSTED_RAND_INDEX = "adjusted_rand_index"


@dataclass
class SegmentationConfig:
    """Configuration for market segmentation analysis"""
    # Clustering parameters
    method: SegmentationMethod = SegmentationMethod.HYBRID
    n_clusters_range: Tuple[int, int] = (3, 12)
    optimal_clusters_method: str = "elbow"  # "elbow", "silhouette", "gap"
    
    # Feature engineering
    include_price_features: bool = True
    include_location_features: bool = True
    include_property_features: bool = True
    include_market_features: bool = True
    include_temporal_features: bool = True
    
    # Data preprocessing
    scaling_method: str = "robust"  # "standard", "minmax", "robust"
    handle_outliers: bool = True
    outlier_method: str = "isolation_forest"  # "isolation_forest", "z_score", "iqr"
    
    # Analysis parameters
    min_segment_size: int = 5
    enable_dimensionality_reduction: bool = True
    reduction_method: str = "pca"  # "pca", "factor_analysis", "tsne"
    n_components: int = 5
    
    # Visualization
    create_visualizations: bool = True
    interactive_plots: bool = True
    save_plots: bool = True


@dataclass
class SegmentationResult:
    """Results from market segmentation analysis"""
    segments: Dict[str, MarketSegment]
    cluster_assignments: Dict[str, int]  # property_id -> cluster_id
    feature_importance: Dict[str, float]
    evaluation_metrics: Dict[str, float]
    
    # Advanced analytics
    segment_transitions: Dict[str, Dict[str, float]]  # Segment flow analysis
    price_elasticity: Dict[str, float]  # Price elasticity by segment
    market_maturity_scores: Dict[str, float]  # Maturity scoring
    investment_attractiveness: Dict[str, float]  # Investment scores
    
    # Metadata
    analysis_date: datetime = field(default_factory=datetime.now)
    config_used: Optional[SegmentationConfig] = None
    data_quality_score: float = 0.0
    confidence_interval: float = 0.95


class AdvancedFeatureEngineering:
    """
    Advanced feature engineering for real estate market segmentation
    """
    
    def __init__(self):
        self.feature_cache = {}
        self.scaler = None
    
    def create_features(self, properties: List[Property]) -> pd.DataFrame:
        """Create comprehensive feature set for segmentation"""
        
        features_list = []
        
        for prop in properties:
            features = {}
            
            # Basic property features
            features.update(self._create_basic_features(prop))
            
            # Price-related features
            features.update(self._create_price_features(prop))
            
            # Location features
            features.update(self._create_location_features(prop))
            
            # Property characteristics features
            features.update(self._create_property_features(prop))
            
            # Temporal features
            features.update(self._create_temporal_features(prop))
            
            # Quality and market features
            features.update(self._create_market_features(prop))
            
            features['property_id'] = prop.property_id
            features_list.append(features)
        
        df = pd.DataFrame(features_list)
        df = df.set_index('property_id')
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        return df
    
    def _create_basic_features(self, prop: Property) -> Dict[str, float]:
        """Create basic property features"""
        
        features = {
            'price': float(prop.price),
            'sqm': prop.sqm or 0,
            'rooms': prop.rooms or 0,
            'floor': prop.floor or 0,
        }
        
        # Price per square meter
        if prop.sqm and prop.sqm > 0:
            features['price_per_sqm'] = float(prop.price) / prop.sqm
        else:
            features['price_per_sqm'] = 0
        
        # Room density (rooms per sqm)
        if prop.sqm and prop.sqm > 0 and prop.rooms:
            features['room_density'] = prop.rooms / prop.sqm
        else:
            features['room_density'] = 0
        
        return features
    
    def _create_price_features(self, prop: Property) -> Dict[str, float]:
        """Create price-related features"""
        
        price = float(prop.price)
        
        features = {
            'log_price': np.log1p(price),
            'price_category': self._categorize_price(price),
        }
        
        # Price bands
        features['is_luxury'] = 1 if price > 500000 else 0
        features['is_premium'] = 1 if 300000 <= price <= 500000 else 0
        features['is_mid_range'] = 1 if 150000 <= price < 300000 else 0
        features['is_entry_level'] = 1 if price < 150000 else 0
        
        return features
    
    def _create_location_features(self, prop: Property) -> Dict[str, float]:
        """Create location-based features"""
        
        neighborhood = prop.location.neighborhood.lower()
        
        features = {}
        
        # Neighborhood desirability scoring (based on typical Athens areas)
        desirability_scores = {
            'kolonaki': 10, 'kifisia': 9, 'glyfada': 8, 'marousi': 7,
            'nea smyrni': 6, 'koukaki': 6, 'pagrati': 5, 'exarchia': 5,
            'kipseli': 4, 'patisia': 3, 'athens center': 5
        }
        
        features['neighborhood_desirability'] = desirability_scores.get(neighborhood, 5)
        
        # Central vs peripheral classification
        central_areas = {
            'kolonaki', 'syntagma', 'plaka', 'monastiraki', 'koukaki', 
            'pagrati', 'exarchia', 'athens center'
        }
        features['is_central'] = 1 if neighborhood in central_areas else 0
        
        # Coastal vs inland
        coastal_areas = {'glyfada', 'vouliagmeni', 'faliro', 'piraeus'}
        features['is_coastal'] = 1 if neighborhood in coastal_areas else 0
        
        # Northern suburbs (typically more expensive)
        northern_suburbs = {'kifisia', 'marousi', 'halandri', 'vrilissia', 'nea erythrea'}
        features['is_northern_suburb'] = 1 if neighborhood in northern_suburbs else 0
        
        return features
    
    def _create_property_features(self, prop: Property) -> Dict[str, float]:
        """Create property characteristics features"""
        
        features = {}
        
        # Property type encoding
        type_mapping = {
            PropertyType.APARTMENT: 1,
            PropertyType.STUDIO: 2,
            PropertyType.HOUSE: 3,
            PropertyType.PENTHOUSE: 4,
            PropertyType.MAISONETTE: 5
        }
        features['property_type_num'] = type_mapping.get(prop.property_type, 1)
        
        # Energy efficiency scoring
        energy_scores = {
            EnergyClass.A_PLUS: 10, EnergyClass.A: 9, EnergyClass.B_PLUS: 8,
            EnergyClass.B: 7, EnergyClass.C: 6, EnergyClass.D: 5,
            EnergyClass.E: 4, EnergyClass.F: 3, EnergyClass.G: 2
        }
        features['energy_score'] = energy_scores.get(prop.energy_class, 5)
        
        # Age-related features
        current_year = datetime.now().year
        if prop.year_built:
            age = current_year - prop.year_built
            features['property_age'] = age
            features['is_new'] = 1 if age <= 5 else 0
            features['is_modern'] = 1 if age <= 15 else 0
            features['is_old'] = 1 if age >= 40 else 0
        else:
            features['property_age'] = 30  # Default assumption
            features['is_new'] = 0
            features['is_modern'] = 0
            features['is_old'] = 0
        
        # Size categorization
        sqm = prop.sqm or 0
        features['is_studio'] = 1 if sqm < 35 else 0
        features['is_small'] = 1 if 35 <= sqm < 60 else 0
        features['is_medium'] = 1 if 60 <= sqm < 100 else 0
        features['is_large'] = 1 if 100 <= sqm < 150 else 0
        features['is_very_large'] = 1 if sqm >= 150 else 0
        
        # Floor features
        floor = prop.floor or 0
        features['is_ground_floor'] = 1 if floor == 0 else 0
        features['is_low_floor'] = 1 if 1 <= floor <= 2 else 0
        features['is_high_floor'] = 1 if floor >= 5 else 0
        
        return features
    
    def _create_temporal_features(self, prop: Property) -> Dict[str, float]:
        """Create time-based features"""
        
        features = {}
        
        if prop.timestamp:
            # Listing age (days since listed)
            listing_age = (datetime.now() - prop.timestamp).days
            features['listing_age_days'] = listing_age
            features['is_fresh_listing'] = 1 if listing_age <= 7 else 0
            features['is_stale_listing'] = 1 if listing_age >= 90 else 0
            
            # Seasonal features
            month = prop.timestamp.month
            features['listing_month'] = month
            features['is_spring_listing'] = 1 if 3 <= month <= 5 else 0
            features['is_summer_listing'] = 1 if 6 <= month <= 8 else 0
            features['is_autumn_listing'] = 1 if 9 <= month <= 11 else 0
            features['is_winter_listing'] = 1 if month in [12, 1, 2] else 0
        else:
            features['listing_age_days'] = 30
            features['is_fresh_listing'] = 0
            features['is_stale_listing'] = 0
            features['listing_month'] = datetime.now().month
            features['is_spring_listing'] = 0
            features['is_summer_listing'] = 0
            features['is_autumn_listing'] = 0
            features['is_winter_listing'] = 0
        
        return features
    
    def _create_market_features(self, prop: Property) -> Dict[str, float]:
        """Create market-related features"""
        
        features = {}
        
        # Data quality indicators
        features['extraction_confidence'] = prop.extraction_confidence
        features['has_complete_data'] = 1 if all([
            prop.sqm, prop.rooms, prop.energy_class, prop.year_built
        ]) else 0
        
        # Validation flags
        features['validation_score'] = len(prop.validation_flags) if prop.validation_flags else 0
        
        # Investment potential indicators
        features['investment_score'] = self._calculate_quick_investment_score(prop)
        
        return features
    
    def _categorize_price(self, price: float) -> float:
        """Categorize price into bands"""
        
        if price < 100000:
            return 1  # Very Low
        elif price < 200000:
            return 2  # Low
        elif price < 350000:
            return 3  # Medium
        elif price < 500000:
            return 4  # High
        else:
            return 5  # Very High
    
    def _calculate_quick_investment_score(self, prop: Property) -> float:
        """Quick investment score calculation"""
        
        score = 50  # Base score
        
        # Energy efficiency bonus
        energy_bonus = {
            EnergyClass.A_PLUS: 15, EnergyClass.A: 12, EnergyClass.B_PLUS: 8,
            EnergyClass.B: 5, EnergyClass.C: 2, EnergyClass.D: 0,
            EnergyClass.E: -5, EnergyClass.F: -10, EnergyClass.G: -15
        }
        score += energy_bonus.get(prop.energy_class, 0)
        
        # Size optimization
        if prop.sqm:
            if 50 <= prop.sqm <= 120:
                score += 10
            elif prop.sqm < 30:
                score -= 10
        
        # Age factor
        if prop.year_built:
            age = datetime.now().year - prop.year_built
            if age <= 10:
                score += 8
            elif age >= 50:
                score -= 8
        
        return max(0, min(100, score))
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in feature matrix"""
        
        # Fill missing values with appropriate defaults
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if df[col].isnull().sum() > 0:
                if 'price' in col.lower():
                    df[col].fillna(df[col].median(), inplace=True)
                elif 'sqm' in col.lower():
                    df[col].fillna(df[col].median(), inplace=True)
                elif 'age' in col.lower():
                    df[col].fillna(30, inplace=True)
                elif 'score' in col.lower():
                    df[col].fillna(df[col].mean(), inplace=True)
                else:
                    df[col].fillna(0, inplace=True)
        
        return df


class ClusteringOptimizer:
    """
    Advanced clustering optimization using multiple evaluation metrics
    """
    
    def __init__(self, config: SegmentationConfig):
        self.config = config
        self.evaluation_results = {}
    
    def find_optimal_clusters(
        self, 
        X: np.ndarray, 
        method: SegmentationMethod = SegmentationMethod.KMEANS
    ) -> Tuple[int, Dict[str, float]]:
        """Find optimal number of clusters using multiple methods"""
        
        min_k, max_k = self.config.n_clusters_range
        
        if method == SegmentationMethod.KMEANS:
            return self._optimize_kmeans(X, min_k, max_k)
        elif method == SegmentationMethod.HIERARCHICAL:
            return self._optimize_hierarchical(X, min_k, max_k)
        elif method == SegmentationMethod.DBSCAN:
            return self._optimize_dbscan(X)
        elif method == SegmentationMethod.HYBRID:
            return self._optimize_hybrid(X, min_k, max_k)
        else:
            raise ValueError(f"Unsupported method: {method}")
    
    def _optimize_kmeans(self, X: np.ndarray, min_k: int, max_k: int) -> Tuple[int, Dict[str, float]]:
        """Optimize K-Means clustering"""
        
        inertias = []
        silhouette_scores = []
        calinski_scores = []
        davies_bouldin_scores = []
        
        k_range = range(min_k, max_k + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            
            inertias.append(kmeans.inertia_)
            
            if len(set(labels)) > 1:  # Need at least 2 clusters for these metrics
                silhouette_scores.append(silhouette_score(X, labels))
                calinski_scores.append(calinski_harabasz_score(X, labels))
                davies_bouldin_scores.append(davies_bouldin_score(X, labels))
            else:
                silhouette_scores.append(-1)
                calinski_scores.append(0)
                davies_bouldin_scores.append(float('inf'))
        
        # Find optimal k using multiple criteria
        optimal_k_elbow = self._find_elbow_point(k_range, inertias)
        optimal_k_silhouette = k_range[np.argmax(silhouette_scores)]
        optimal_k_calinski = k_range[np.argmax(calinski_scores)]
        optimal_k_davies = k_range[np.argmin(davies_bouldin_scores)]
        
        # Weighted decision
        k_votes = {
            optimal_k_elbow: 0.3,
            optimal_k_silhouette: 0.3,
            optimal_k_calinski: 0.2,
            optimal_k_davies: 0.2
        }
        
        optimal_k = max(k_votes.keys(), key=k_votes.get)
        
        metrics = {
            'optimal_k_elbow': optimal_k_elbow,
            'optimal_k_silhouette': optimal_k_silhouette,
            'optimal_k_calinski': optimal_k_calinski,
            'optimal_k_davies': optimal_k_davies,
            'silhouette_scores': silhouette_scores,
            'calinski_scores': calinski_scores,
            'davies_bouldin_scores': davies_bouldin_scores,
            'inertias': inertias
        }
        
        return optimal_k, metrics
    
    def _optimize_hierarchical(self, X: np.ndarray, min_k: int, max_k: int) -> Tuple[int, Dict[str, float]]:
        """Optimize hierarchical clustering"""
        
        # Perform hierarchical clustering
        linkage_matrix = linkage(X, method='ward')
        
        silhouette_scores = []
        k_range = range(min_k, max_k + 1)
        
        for k in k_range:
            labels = fcluster(linkage_matrix, k, criterion='maxclust') - 1
            
            if len(set(labels)) > 1:
                silhouette_scores.append(silhouette_score(X, labels))
            else:
                silhouette_scores.append(-1)
        
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        metrics = {
            'silhouette_scores': silhouette_scores,
            'linkage_matrix': linkage_matrix
        }
        
        return optimal_k, metrics
    
    def _optimize_dbscan(self, X: np.ndarray) -> Tuple[int, Dict[str, float]]:
        """Optimize DBSCAN clustering"""
        
        # Try different eps values
        eps_range = np.linspace(0.1, 2.0, 20)
        min_samples_range = [3, 5, 10]
        
        best_score = -1
        best_params = None
        best_n_clusters = 0
        
        for eps in eps_range:
            for min_samples in min_samples_range:
                dbscan = DBSCAN(eps=eps, min_samples=min_samples)
                labels = dbscan.fit_predict(X)
                
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                if n_clusters > 1:
                    score = silhouette_score(X, labels)
                    if score > best_score:
                        best_score = score
                        best_params = {'eps': eps, 'min_samples': min_samples}
                        best_n_clusters = n_clusters
        
        metrics = {
            'best_params': best_params,
            'best_silhouette': best_score
        }
        
        return best_n_clusters, metrics
    
    def _optimize_hybrid(self, X: np.ndarray, min_k: int, max_k: int) -> Tuple[int, Dict[str, float]]:
        """Hybrid optimization using multiple methods"""
        
        # Get results from different methods
        kmeans_k, kmeans_metrics = self._optimize_kmeans(X, min_k, max_k)
        hier_k, hier_metrics = self._optimize_hierarchical(X, min_k, max_k)
        
        # Weighted decision
        final_k = int(np.round(0.6 * kmeans_k + 0.4 * hier_k))
        final_k = max(min_k, min(max_k, final_k))  # Ensure within bounds
        
        metrics = {
            'kmeans_optimal': kmeans_k,
            'hierarchical_optimal': hier_k,
            'final_k': final_k,
            **kmeans_metrics
        }
        
        return final_k, metrics
    
    def _find_elbow_point(self, k_range: range, inertias: List[float]) -> int:
        """Find elbow point in inertia curve"""
        
        if len(inertias) < 3:
            return k_range[0]
        
        # Calculate the rate of change
        diffs = np.diff(inertias)
        diff_ratios = []
        
        for i in range(len(diffs) - 1):
            if diffs[i+1] != 0:
                diff_ratios.append(diffs[i] / diffs[i+1])
            else:
                diff_ratios.append(1)
        
        # Find the point where the rate of change stabilizes
        if diff_ratios:
            elbow_idx = np.argmin(diff_ratios) + 1
            return list(k_range)[elbow_idx]
        else:
            return k_range[0]


class MarketSegmentationAnalytics:
    """
    Advanced market segmentation analytics for Athens real estate
    """
    
    def __init__(
        self,
        property_repo: PropertyRepository,
        config: Optional[SegmentationConfig] = None
    ):
        self.property_repo = property_repo
        self.config = config or SegmentationConfig()
        self.feature_engineer = AdvancedFeatureEngineering()
        self.optimizer = ClusteringOptimizer(self.config)
        
        # Analysis state
        self.feature_matrix = None
        self.scaled_features = None
        self.cluster_model = None
        self.scaler = None
        
        logger.info("MarketSegmentationAnalytics initialized")
    
    async def perform_segmentation(
        self, 
        properties: Optional[List[Property]] = None
    ) -> SegmentationResult:
        """
        Perform comprehensive market segmentation analysis
        """
        
        logger.info("Starting market segmentation analysis")
        
        # Get properties if not provided
        if properties is None:
            properties = await self.property_repo.find_all()
        
        if len(properties) < self.config.n_clusters_range[0]:
            raise ValueError(f"Not enough properties for segmentation: {len(properties)}")
        
        # Feature engineering
        logger.info("Creating feature matrix")
        self.feature_matrix = self.feature_engineer.create_features(properties)
        
        # Preprocessing
        self.scaled_features = self._preprocess_features(self.feature_matrix)
        
        # Outlier detection and handling
        if self.config.handle_outliers:
            self.scaled_features = self._handle_outliers(self.scaled_features)
        
        # Dimensionality reduction (optional)
        if self.config.enable_dimensionality_reduction:
            self.scaled_features = self._reduce_dimensions(self.scaled_features)
        
        # Find optimal number of clusters
        logger.info("Optimizing cluster count")
        optimal_k, optimization_metrics = self.optimizer.find_optimal_clusters(
            self.scaled_features, self.config.method
        )
        
        # Perform clustering
        logger.info(f"Performing clustering with k={optimal_k}")
        cluster_labels, cluster_model = self._perform_clustering(
            self.scaled_features, optimal_k, self.config.method
        )
        
        self.cluster_model = cluster_model
        
        # Create cluster assignments
        cluster_assignments = {}
        for i, prop in enumerate(properties):
            cluster_assignments[prop.property_id] = int(cluster_labels[i])
        
        # Generate market segments
        logger.info("Generating market segments")
        segments = await self._generate_market_segments(properties, cluster_labels)
        
        # Calculate feature importance
        feature_importance = self._calculate_feature_importance()
        
        # Evaluation metrics
        evaluation_metrics = self._calculate_evaluation_metrics(cluster_labels)
        evaluation_metrics.update(optimization_metrics)
        
        # Advanced analytics
        segment_transitions = self._analyze_segment_transitions(segments)
        price_elasticity = self._calculate_price_elasticity(properties, cluster_labels)
        maturity_scores = self._calculate_market_maturity(segments)
        attractiveness_scores = self._calculate_investment_attractiveness(segments)
        
        # Data quality assessment
        data_quality_score = self._assess_data_quality(properties)
        
        result = SegmentationResult(
            segments=segments,
            cluster_assignments=cluster_assignments,
            feature_importance=feature_importance,
            evaluation_metrics=evaluation_metrics,
            segment_transitions=segment_transitions,
            price_elasticity=price_elasticity,
            market_maturity_scores=maturity_scores,
            investment_attractiveness=attractiveness_scores,
            config_used=self.config,
            data_quality_score=data_quality_score
        )
        
        logger.info(f"Segmentation completed. Found {len(segments)} segments")
        
        return result
    
    def _preprocess_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """Preprocess features for clustering"""
        
        # Select numeric features only
        numeric_features = features_df.select_dtypes(include=[np.number])
        
        # Remove features with zero variance
        numeric_features = numeric_features.loc[:, numeric_features.var() > 0]
        
        # Scale features
        if self.config.scaling_method == "standard":
            self.scaler = StandardScaler()
        elif self.config.scaling_method == "minmax":
            self.scaler = MinMaxScaler()
        elif self.config.scaling_method == "robust":
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaling method: {self.config.scaling_method}")
        
        scaled_features = self.scaler.fit_transform(numeric_features)
        
        return scaled_features
    
    def _handle_outliers(self, X: np.ndarray) -> np.ndarray:
        """Detect and handle outliers"""
        
        if self.config.outlier_method == "isolation_forest":
            # Use Isolation Forest for outlier detection
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            outlier_labels = iso_forest.fit_predict(X)
            
            # Keep only inliers
            X_clean = X[outlier_labels == 1]
            
        elif self.config.outlier_method == "z_score":
            # Use Z-score method
            z_scores = np.abs(stats.zscore(X, axis=0))
            outlier_mask = (z_scores < 3).all(axis=1)
            X_clean = X[outlier_mask]
            
        elif self.config.outlier_method == "iqr":
            # Use IQR method
            Q1 = np.percentile(X, 25, axis=0)
            Q3 = np.percentile(X, 75, axis=0)
            IQR = Q3 - Q1
            
            outlier_mask = ~((X < (Q1 - 1.5 * IQR)) | (X > (Q3 + 1.5 * IQR))).any(axis=1)
            X_clean = X[outlier_mask]
        
        else:
            X_clean = X
        
        logger.info(f"Outlier handling: {X.shape[0]} -> {X_clean.shape[0]} properties")
        
        return X_clean
    
    def _reduce_dimensions(self, X: np.ndarray) -> np.ndarray:
        """Apply dimensionality reduction"""
        
        if self.config.reduction_method == "pca":
            reducer = PCA(n_components=self.config.n_components, random_state=42)
        elif self.config.reduction_method == "factor_analysis":
            reducer = FactorAnalysis(n_components=self.config.n_components, random_state=42)
        elif self.config.reduction_method == "tsne":
            reducer = TSNE(n_components=min(3, self.config.n_components), random_state=42)
        else:
            return X
        
        X_reduced = reducer.fit_transform(X)
        
        logger.info(f"Dimensionality reduction: {X.shape[1]} -> {X_reduced.shape[1]} features")
        
        return X_reduced
    
    def _perform_clustering(
        self, 
        X: np.ndarray, 
        n_clusters: int, 
        method: SegmentationMethod
    ) -> Tuple[np.ndarray, Any]:
        """Perform clustering with specified method"""
        
        if method == SegmentationMethod.KMEANS:
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif method == SegmentationMethod.HIERARCHICAL:
            model = AgglomerativeClustering(n_clusters=n_clusters)
        elif method == SegmentationMethod.DBSCAN:
            # Use parameters from optimization
            model = DBSCAN(eps=0.5, min_samples=5)
        else:
            # Default to K-Means
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        
        labels = model.fit_predict(X)
        
        return labels, model
    
    async def _generate_market_segments(
        self, 
        properties: List[Property], 
        cluster_labels: np.ndarray
    ) -> Dict[str, MarketSegment]:
        """Generate MarketSegment entities from clustering results"""
        
        segments = {}
        
        # Group properties by cluster
        cluster_properties = defaultdict(list)
        for i, prop in enumerate(properties):
            if i < len(cluster_labels):  # Handle potential size mismatch
                cluster_id = int(cluster_labels[i])
                cluster_properties[cluster_id].append(prop)
        
        # Create MarketSegment for each cluster
        for cluster_id, cluster_props in cluster_properties.items():
            if len(cluster_props) < self.config.min_segment_size:
                continue  # Skip small segments
            
            # Calculate segment statistics
            prices = [float(prop.price) for prop in cluster_props]
            sqm_values = [prop.sqm for prop in cluster_props if prop.sqm]
            
            # Neighborhood analysis
            neighborhoods = [prop.location.neighborhood for prop in cluster_props]
            dominant_neighborhood = max(set(neighborhoods), key=neighborhoods.count)
            
            # Property type analysis
            property_types = [prop.property_type for prop in cluster_props]
            dominant_type = max(set(property_types), key=property_types.count)
            
            # Energy efficiency analysis
            energy_classes = [prop.energy_class for prop in cluster_props if prop.energy_class]
            energy_scores = []
            energy_map = {
                EnergyClass.A_PLUS: 10, EnergyClass.A: 9, EnergyClass.B_PLUS: 8,
                EnergyClass.B: 7, EnergyClass.C: 6, EnergyClass.D: 5,
                EnergyClass.E: 4, EnergyClass.F: 3, EnergyClass.G: 2
            }
            
            for energy_class in energy_classes:
                energy_scores.append(energy_map.get(energy_class, 5))
            
            avg_energy_score = np.mean(energy_scores) if energy_scores else 5.0
            
            # Investment scoring
            investment_scores = []
            for prop in cluster_props:
                score = self.feature_engineer._calculate_quick_investment_score(prop)
                investment_scores.append(score)
            
            avg_investment_score = np.mean(investment_scores)
            
            # Yield estimation (simplified)
            estimated_yield = self._estimate_segment_yield(cluster_props)
            
            # Market activity and liquidity (simplified)
            market_activity = min(10, len(cluster_props) / 10)
            liquidity_score = min(1.0, len(cluster_props) / 50)
            
            # Price volatility
            price_volatility = np.std(prices) / np.mean(prices) if len(prices) > 1 else 0.1
            
            # Market maturity
            ages = []
            for prop in cluster_props:
                if prop.year_built:
                    ages.append(datetime.now().year - prop.year_built)
            
            avg_age = np.mean(ages) if ages else 30
            maturity = "mature" if avg_age > 20 else "developing"
            
            # Create MarketSegment
            segment = MarketSegment(
                segment_id=f"cluster_{cluster_id}",
                neighborhood=dominant_neighborhood,
                property_count=len(cluster_props),
                avg_price=Decimal(str(round(np.mean(prices)))),
                median_price=Decimal(str(round(np.median(prices)))),
                avg_price_per_sqm=Decimal(str(round(np.mean([
                    float(prop.price_per_sqm) for prop in cluster_props 
                    if prop.price_per_sqm
                ])))),
                price_std_dev=Decimal(str(round(np.std(prices)))),
                avg_sqm=float(np.mean(sqm_values)) if sqm_values else 0,
                dominant_property_type=dominant_type,
                energy_efficiency_score=avg_energy_score,
                avg_investment_score=avg_investment_score,
                estimated_avg_yield=estimated_yield,
                market_activity_score=market_activity,
                price_volatility=price_volatility,
                market_maturity=maturity,
                liquidity_score=liquidity_score
            )
            
            segments[f"segment_{cluster_id}"] = segment
        
        return segments
    
    def _estimate_segment_yield(self, properties: List[Property]) -> float:
        """Estimate rental yield for segment"""
        
        # Simplified yield estimation based on property characteristics
        base_yield = 4.0  # Base yield assumption
        
        # Adjust based on segment characteristics
        prices = [float(prop.price) for prop in properties]
        avg_price = np.mean(prices)
        
        # Lower prices typically have higher yields
        if avg_price < 150000:
            yield_adjustment = 0.5
        elif avg_price > 400000:
            yield_adjustment = -0.5
        else:
            yield_adjustment = 0
        
        # Energy efficiency adjustment
        energy_classes = [prop.energy_class for prop in properties if prop.energy_class]
        if energy_classes:
            high_efficiency_count = sum(
                1 for ec in energy_classes 
                if ec in [EnergyClass.A_PLUS, EnergyClass.A, EnergyClass.B_PLUS]
            )
            efficiency_ratio = high_efficiency_count / len(energy_classes)
            yield_adjustment += efficiency_ratio * 0.3
        
        return max(2.0, base_yield + yield_adjustment)
    
    def _calculate_feature_importance(self) -> Dict[str, float]:
        """Calculate feature importance for clustering"""
        
        if self.feature_matrix is None or self.cluster_model is None:
            return {}
        
        # For K-means, use cluster centers to determine importance
        if hasattr(self.cluster_model, 'cluster_centers_'):
            centers = self.cluster_model.cluster_centers_
            
            # Calculate variance across cluster centers for each feature
            feature_variances = np.var(centers, axis=0)
            
            # Normalize to get importance scores
            total_variance = np.sum(feature_variances)
            if total_variance > 0:
                importance_scores = feature_variances / total_variance
            else:
                importance_scores = np.ones(len(feature_variances)) / len(feature_variances)
            
            # Map back to feature names
            feature_names = self.feature_matrix.select_dtypes(include=[np.number]).columns
            feature_names = [name for name in feature_names if self.feature_matrix[name].var() > 0]
            
            feature_importance = {}
            for i, name in enumerate(feature_names[:len(importance_scores)]):
                feature_importance[name] = float(importance_scores[i])
            
            return feature_importance
        
        return {}
    
    def _calculate_evaluation_metrics(self, labels: np.ndarray) -> Dict[str, float]:
        """Calculate clustering evaluation metrics"""
        
        metrics = {}
        
        if len(set(labels)) > 1:
            metrics['silhouette_score'] = float(silhouette_score(self.scaled_features, labels))
            metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(self.scaled_features, labels))
            metrics['davies_bouldin_score'] = float(davies_bouldin_score(self.scaled_features, labels))
        
        metrics['n_clusters'] = len(set(labels))
        metrics['n_noise'] = int(np.sum(labels == -1)) if -1 in labels else 0
        
        return metrics
    
    def _analyze_segment_transitions(self, segments: Dict[str, MarketSegment]) -> Dict[str, Dict[str, float]]:
        """Analyze potential transitions between segments"""
        
        transitions = {}
        
        segment_list = list(segments.values())
        
        for i, seg1 in enumerate(segment_list):
            transitions[seg1.segment_id] = {}
            
            for j, seg2 in enumerate(segment_list):
                if i != j:
                    # Calculate similarity/transition probability
                    price_diff = abs(float(seg1.avg_price) - float(seg2.avg_price))
                    price_similarity = 1.0 / (1.0 + price_diff / 100000)  # Normalize by 100K
                    
                    transitions[seg1.segment_id][seg2.segment_id] = price_similarity
        
        return transitions
    
    def _calculate_price_elasticity(
        self, 
        properties: List[Property], 
        labels: np.ndarray
    ) -> Dict[str, float]:
        """Calculate price elasticity for each segment"""
        
        elasticity = {}
        
        # Group properties by cluster
        cluster_properties = defaultdict(list)
        for i, prop in enumerate(properties):
            if i < len(labels):
                cluster_id = int(labels[i])
                cluster_properties[cluster_id].append(prop)
        
        for cluster_id, cluster_props in cluster_properties.items():
            if len(cluster_props) < 5:
                elasticity[f"segment_{cluster_id}"] = 1.0  # Default elasticity
                continue
            
            # Simple elasticity calculation based on price variance
            prices = [float(prop.price) for prop in cluster_props]
            sqm_values = [prop.sqm for prop in cluster_props if prop.sqm and prop.sqm > 0]
            
            if len(sqm_values) > 3:
                # Calculate elasticity as correlation between price and size
                prices_with_sqm = [float(prop.price) for prop in cluster_props if prop.sqm and prop.sqm > 0]
                
                if len(prices_with_sqm) > 3:
                    correlation = np.corrcoef(prices_with_sqm, sqm_values)[0, 1]
                    elasticity[f"segment_{cluster_id}"] = abs(correlation) if not np.isnan(correlation) else 1.0
                else:
                    elasticity[f"segment_{cluster_id}"] = 1.0
            else:
                elasticity[f"segment_{cluster_id}"] = 1.0
        
        return elasticity
    
    def _calculate_market_maturity(self, segments: Dict[str, MarketSegment]) -> Dict[str, float]:
        """Calculate market maturity scores"""
        
        maturity_scores = {}
        
        for segment_id, segment in segments.items():
            score = 50  # Base score
            
            # Property count factor
            if segment.property_count > 50:
                score += 20
            elif segment.property_count > 20:
                score += 10
            
            # Market activity factor
            score += segment.market_activity_score * 3
            
            # Liquidity factor
            score += segment.liquidity_score * 20
            
            # Price volatility (lower is more mature)
            if segment.price_volatility < 0.2:
                score += 10
            elif segment.price_volatility > 0.5:
                score -= 10
            
            maturity_scores[segment_id] = max(0, min(100, score))
        
        return maturity_scores
    
    def _calculate_investment_attractiveness(
        self, 
        segments: Dict[str, MarketSegment]
    ) -> Dict[str, float]:
        """Calculate investment attractiveness scores"""
        
        attractiveness = {}
        
        for segment_id, segment in segments.items():
            score = segment.avg_investment_score
            
            # Yield bonus
            if segment.estimated_avg_yield > 4.5:
                score += 10
            elif segment.estimated_avg_yield < 3:
                score -= 10
            
            # Market activity bonus
            if segment.market_activity_score > 7:
                score += 5
            
            # Liquidity bonus
            score += segment.liquidity_score * 10
            
            # Energy efficiency bonus
            score += (segment.energy_efficiency_score - 5) * 2
            
            attractiveness[segment_id] = max(0, min(100, score))
        
        return attractiveness
    
    def _assess_data_quality(self, properties: List[Property]) -> float:
        """Assess overall data quality"""
        
        if not properties:
            return 0.0
        
        quality_scores = []
        
        for prop in properties:
            prop_score = 0.0
            
            # Required fields
            if prop.price and prop.price > 0:
                prop_score += 0.3
            
            if prop.sqm and prop.sqm > 0:
                prop_score += 0.2
            
            if prop.location and prop.location.neighborhood:
                prop_score += 0.15
            
            # Optional but valuable fields
            if prop.rooms:
                prop_score += 0.1
            
            if prop.energy_class:
                prop_score += 0.1
            
            if prop.year_built:
                prop_score += 0.1
            
            # Data consistency
            if prop.price_per_sqm and prop.sqm and prop.sqm > 0:
                calculated_price_per_sqm = float(prop.price) / prop.sqm
                actual_price_per_sqm = float(prop.price_per_sqm)
                
                if abs(calculated_price_per_sqm - actual_price_per_sqm) / calculated_price_per_sqm < 0.1:
                    prop_score += 0.05
            
            quality_scores.append(prop_score)
        
        return float(np.mean(quality_scores))


# Export for use in other modules
__all__ = [
    'MarketSegmentationAnalytics',
    'SegmentationConfig',
    'SegmentationResult',
    'SegmentationMethod',
    'AdvancedFeatureEngineering',
    'ClusteringOptimizer'
]