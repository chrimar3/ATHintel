"""
Market Segmentation Engine
=========================

Advanced clustering and segmentation analysis for Athens real estate market.
Uses multiple machine learning algorithms to identify market segments and opportunities.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json


class MarketSegmentationEngine:
    """
    Comprehensive market segmentation using advanced clustering algorithms.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.segments = {}
        self.segment_profiles = {}
        self.analysis_timestamp = None
    
    def analyze(self, property_data):
        """
        Run comprehensive market segmentation analysis.
        
        Args:
            property_data: List of property dictionaries or DataFrame
            
        Returns:
            dict: Comprehensive segmentation results with investment insights
        """
        self.analysis_timestamp = datetime.now()
        
        # Convert to DataFrame if needed
        if isinstance(property_data, list):
            df = pd.DataFrame(property_data)
        else:
            df = property_data.copy()
        
        # Prepare features for clustering
        features_df = self._prepare_clustering_features(df)
        
        # Run multiple clustering algorithms
        clustering_results = self._run_clustering_algorithms(features_df)
        
        # Generate segment profiles
        segment_profiles = self._generate_segment_profiles(df, clustering_results)
        
        # Identify investment opportunities by segment
        investment_opportunities = self._identify_segment_opportunities(df, segment_profiles)
        
        # Create visualizations
        visualizations = self._create_segment_visualizations(features_df, clustering_results)
        
        results = {
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'total_properties': len(df),
            'clustering_results': clustering_results,
            'segment_profiles': segment_profiles,
            'investment_opportunities': investment_opportunities,
            'visualizations': visualizations,
            'segment_summary': self._generate_segment_summary(segment_profiles)
        }
        
        self.segments = clustering_results
        self.segment_profiles = segment_profiles
        
        return results
    
    def _prepare_clustering_features(self, df):
        """Prepare and normalize features for clustering analysis."""
        
        # Core features for clustering
        features = []
        feature_names = []
        
        # Price features
        if 'price_per_sqm' in df.columns:
            features.append(df['price_per_sqm'].fillna(df['price_per_sqm'].median()))
            feature_names.append('price_per_sqm')
        
        if 'price' in df.columns:
            features.append(np.log1p(df['price'].fillna(df['price'].median())))
            feature_names.append('log_price')
        
        # Size features
        if 'sqm' in df.columns:
            features.append(df['sqm'].fillna(df['sqm'].median()))
            feature_names.append('sqm')
        
        # Energy efficiency (convert to numeric)
        if 'energy_class' in df.columns:
            energy_map = {'A+': 8, 'A': 7, 'B+': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1, 'G': 0}
            energy_numeric = df['energy_class'].map(energy_map).fillna(3)  # Default to C
            features.append(energy_numeric)
            feature_names.append('energy_numeric')
        
        # Rooms
        if 'rooms' in df.columns:
            features.append(df['rooms'].fillna(df['rooms'].median()))
            feature_names.append('rooms')
        
        # Create neighborhood encoding (frequency-based)
        if 'neighborhood' in df.columns:
            neighborhood_counts = df['neighborhood'].value_counts()
            neighborhood_freq = df['neighborhood'].map(neighborhood_counts).fillna(0)
            features.append(neighborhood_freq)
            feature_names.append('neighborhood_frequency')
        
        # Combine features
        features_array = np.column_stack(features)
        features_df = pd.DataFrame(features_array, columns=feature_names)
        
        # Remove any remaining NaN values
        features_df = features_df.fillna(features_df.median())
        
        return features_df
    
    def _run_clustering_algorithms(self, features_df):
        """Run multiple clustering algorithms and select best results."""
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features_df)
        
        clustering_results = {}
        
        # K-Means clustering (try different k values)
        best_kmeans_score = -1
        best_kmeans_k = 3
        best_kmeans_labels = None
        
        for k in range(3, 8):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features_scaled)
            score = silhouette_score(features_scaled, labels)
            
            if score > best_kmeans_score:
                best_kmeans_score = score
                best_kmeans_k = k
                best_kmeans_labels = labels
        
        clustering_results['kmeans'] = {
            'labels': best_kmeans_labels.tolist(),
            'n_clusters': best_kmeans_k,
            'silhouette_score': best_kmeans_score
        }
        
        # DBSCAN clustering
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        dbscan_labels = dbscan.fit_predict(features_scaled)
        n_clusters_dbscan = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
        
        if n_clusters_dbscan > 1:
            dbscan_score = silhouette_score(features_scaled, dbscan_labels)
        else:
            dbscan_score = -1
        
        clustering_results['dbscan'] = {
            'labels': dbscan_labels.tolist(),
            'n_clusters': n_clusters_dbscan,
            'silhouette_score': dbscan_score,
            'n_noise_points': list(dbscan_labels).count(-1)
        }
        
        # Hierarchical clustering
        hierarchical = AgglomerativeClustering(n_clusters=best_kmeans_k)
        hierarchical_labels = hierarchical.fit_predict(features_scaled)
        hierarchical_score = silhouette_score(features_scaled, hierarchical_labels)
        
        clustering_results['hierarchical'] = {
            'labels': hierarchical_labels.tolist(),
            'n_clusters': best_kmeans_k,
            'silhouette_score': hierarchical_score
        }
        
        # Select best clustering method
        best_method = max(clustering_results.keys(), 
                         key=lambda x: clustering_results[x]['silhouette_score'])
        
        clustering_results['best_method'] = best_method
        clustering_results['best_labels'] = clustering_results[best_method]['labels']
        
        return clustering_results
    
    def _generate_segment_profiles(self, df, clustering_results):
        """Generate detailed profiles for each market segment."""
        
        best_labels = clustering_results['best_labels']
        df_with_segments = df.copy()
        df_with_segments['segment'] = best_labels
        
        segment_profiles = {}
        unique_segments = set(best_labels)
        if -1 in unique_segments:  # Remove noise cluster from DBSCAN
            unique_segments.remove(-1)
        
        for segment_id in unique_segments:
            segment_data = df_with_segments[df_with_segments['segment'] == segment_id]
            
            profile = {
                'segment_id': int(segment_id),
                'property_count': len(segment_data),
                'percentage_of_market': len(segment_data) / len(df) * 100,
                'price_stats': {
                    'mean': float(segment_data['price'].mean()) if 'price' in segment_data.columns else None,
                    'median': float(segment_data['price'].median()) if 'price' in segment_data.columns else None,
                    'std': float(segment_data['price'].std()) if 'price' in segment_data.columns else None,
                    'min': float(segment_data['price'].min()) if 'price' in segment_data.columns else None,
                    'max': float(segment_data['price'].max()) if 'price' in segment_data.columns else None
                },
                'price_per_sqm_stats': {
                    'mean': float(segment_data['price_per_sqm'].mean()) if 'price_per_sqm' in segment_data.columns else None,
                    'median': float(segment_data['price_per_sqm'].median()) if 'price_per_sqm' in segment_data.columns else None,
                    'std': float(segment_data['price_per_sqm'].std()) if 'price_per_sqm' in segment_data.columns else None
                },
                'size_stats': {
                    'mean_sqm': float(segment_data['sqm'].mean()) if 'sqm' in segment_data.columns else None,
                    'median_sqm': float(segment_data['sqm'].median()) if 'sqm' in segment_data.columns else None,
                    'mean_rooms': float(segment_data['rooms'].mean()) if 'rooms' in segment_data.columns else None
                },
                'energy_distribution': segment_data['energy_class'].value_counts().to_dict() if 'energy_class' in segment_data.columns else {},
                'top_neighborhoods': segment_data['neighborhood'].value_counts().head(5).to_dict() if 'neighborhood' in segment_data.columns else {},
                'investment_characteristics': self._analyze_investment_characteristics(segment_data)
            }
            
            segment_profiles[f'segment_{segment_id}'] = profile
        
        return segment_profiles
    
    def _analyze_investment_characteristics(self, segment_data):
        """Analyze investment characteristics for a market segment."""
        
        characteristics = {
            'avg_price': float(segment_data['price'].mean()) if 'price' in segment_data.columns else None,
            'price_range': f"€{segment_data['price'].min():,.0f} - €{segment_data['price'].max():,.0f}" if 'price' in segment_data.columns else None,
            'dominant_energy_class': segment_data['energy_class'].mode().iloc[0] if 'energy_class' in segment_data.columns and not segment_data['energy_class'].empty else None,
            'size_category': self._categorize_size(segment_data['sqm'].mean() if 'sqm' in segment_data.columns else None),
            'investment_appeal': self._calculate_investment_appeal(segment_data)
        }
        
        return characteristics
    
    def _categorize_size(self, avg_sqm):
        """Categorize property size."""
        if avg_sqm is None:
            return "Unknown"
        elif avg_sqm < 50:
            return "Compact"
        elif avg_sqm < 80:
            return "Medium"
        elif avg_sqm < 120:
            return "Large"
        else:
            return "Premium"
    
    def _calculate_investment_appeal(self, segment_data):
        """Calculate investment appeal score for segment."""
        
        if 'price_per_sqm' not in segment_data.columns:
            return "Unknown"
        
        median_price_per_sqm = segment_data['price_per_sqm'].median()
        
        # Simple scoring based on price per sqm and energy efficiency
        if median_price_per_sqm < 3000:
            return "High Appeal - Budget Friendly"
        elif median_price_per_sqm < 5000:
            return "Medium Appeal - Balanced"
        else:
            return "Premium Segment"
    
    def _identify_segment_opportunities(self, df, segment_profiles):
        """Identify investment opportunities within each segment."""
        
        opportunities = {}
        
        for segment_key, profile in segment_profiles.items():
            segment_id = profile['segment_id']
            
            # Identify undervalued properties in this segment
            segment_data = df[df.index.isin(
                df.index[np.array(self.segments['best_labels']) == segment_id]
            )]
            
            if len(segment_data) == 0:
                continue
            
            # Find properties below segment median price
            median_price = profile['price_stats']['median'] if profile['price_stats']['median'] else 0
            undervalued = segment_data[
                segment_data['price'] < median_price * 0.9
            ] if 'price' in segment_data.columns else pd.DataFrame()
            
            # Find energy efficiency opportunities
            energy_opportunities = segment_data[
                segment_data['energy_class'].isin(['C', 'D', 'E', 'F', 'G'])
            ] if 'energy_class' in segment_data.columns else pd.DataFrame()
            
            opportunities[segment_key] = {
                'total_properties': len(segment_data),
                'undervalued_properties': len(undervalued),
                'undervalued_percentage': len(undervalued) / len(segment_data) * 100 if len(segment_data) > 0 else 0,
                'energy_retrofit_opportunities': len(energy_opportunities),
                'energy_opportunity_percentage': len(energy_opportunities) / len(segment_data) * 100 if len(segment_data) > 0 else 0,
                'investment_strategy': self._recommend_segment_strategy(profile),
                'top_opportunity_properties': self._identify_top_opportunities(segment_data)
            }
        
        return opportunities
    
    def _recommend_segment_strategy(self, profile):
        """Recommend investment strategy for segment based on characteristics."""
        
        avg_price = profile['price_stats']['mean'] if profile['price_stats']['mean'] else 0
        dominant_energy = profile['investment_characteristics']['dominant_energy_class']
        
        if avg_price < 200000 and dominant_energy in ['C', 'D', 'E']:
            return "Energy Arbitrage - Buy low-energy properties, retrofit, resell"
        elif avg_price < 300000:
            return "Entry-Level Investment - Rental yield focus"
        elif avg_price < 600000:
            return "Mid-Market Growth - Capital appreciation focus"
        else:
            return "Premium Investment - Luxury market positioning"
    
    def _identify_top_opportunities(self, segment_data, top_n=5):
        """Identify top investment opportunities in segment."""
        
        if len(segment_data) == 0 or 'price_per_sqm' not in segment_data.columns:
            return []
        
        # Score properties based on price efficiency and energy class
        opportunities = []
        
        for idx, property_data in segment_data.head(top_n).iterrows():
            opportunity = {
                'property_id': property_data.get('property_id', f'prop_{idx}'),
                'neighborhood': property_data.get('neighborhood', 'Unknown'),
                'price': float(property_data.get('price', 0)),
                'sqm': float(property_data.get('sqm', 0)),
                'price_per_sqm': float(property_data.get('price_per_sqm', 0)),
                'energy_class': property_data.get('energy_class', 'Unknown'),
                'opportunity_score': self._calculate_opportunity_score(property_data)
            }
            opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)
    
    def _calculate_opportunity_score(self, property_data):
        """Calculate opportunity score for individual property."""
        
        score = 5.0  # Base score
        
        # Adjust for energy efficiency
        energy_class = property_data.get('energy_class', 'C')
        energy_bonuses = {'A+': 1.0, 'A': 0.8, 'B+': 0.6, 'B': 0.4, 'C': 0.0, 'D': -0.2, 'E': -0.4}
        score += energy_bonuses.get(energy_class, 0)
        
        # Adjust for price per sqm (lower is better for investment)
        price_per_sqm = property_data.get('price_per_sqm', 4000)
        if price_per_sqm < 3000:
            score += 1.5
        elif price_per_sqm < 4000:
            score += 1.0
        elif price_per_sqm > 6000:
            score -= 1.0
        
        return max(1.0, min(10.0, score))
    
    def _create_segment_visualizations(self, features_df, clustering_results):
        """Create visualizations for market segmentation."""
        
        # PCA for 2D visualization
        pca = PCA(n_components=2)
        features_2d = pca.fit_transform(self.scaler.transform(features_df))
        
        visualizations = {
            'pca_components_explained_variance': pca.explained_variance_ratio_.tolist(),
            'clustering_method_comparison': {
                method: {
                    'n_clusters': results['n_clusters'],
                    'silhouette_score': results['silhouette_score']
                }
                for method, results in clustering_results.items()
                if method != 'best_method' and method != 'best_labels'
            }
        }
        
        return visualizations
    
    def _generate_segment_summary(self, segment_profiles):
        """Generate executive summary of market segmentation."""
        
        total_segments = len(segment_profiles)
        total_properties = sum(profile['property_count'] for profile in segment_profiles.values())
        
        # Find largest segment
        largest_segment = max(segment_profiles.values(), key=lambda x: x['property_count'])
        
        # Find most expensive segment
        most_expensive = max(
            segment_profiles.values(),
            key=lambda x: x['price_stats']['mean'] if x['price_stats']['mean'] else 0
        )
        
        summary = {
            'total_segments_identified': total_segments,
            'total_properties_analyzed': total_properties,
            'largest_segment': {
                'id': largest_segment['segment_id'],
                'properties': largest_segment['property_count'],
                'market_share': largest_segment['percentage_of_market']
            },
            'most_expensive_segment': {
                'id': most_expensive['segment_id'],
                'avg_price': most_expensive['price_stats']['mean'],
                'properties': most_expensive['property_count']
            },
            'investment_insights': [
                f"Market divided into {total_segments} distinct segments",
                f"Largest segment contains {largest_segment['property_count']} properties ({largest_segment['percentage_of_market']:.1f}% of market)",
                f"Premium segment averaging €{most_expensive['price_stats']['mean']:,.0f}" if most_expensive['price_stats']['mean'] else "Premium segment identified",
                "Energy efficiency varies significantly across segments"
            ]
        }
        
        return summary

    def export_segments_to_csv(self, df, output_path):
        """Export segmentation results to CSV for further analysis."""
        
        if not self.segments or 'best_labels' not in self.segments:
            raise ValueError("No segmentation results available. Run analyze() first.")
        
        df_export = df.copy()
        df_export['market_segment'] = self.segments['best_labels']
        df_export['segment_profile'] = df_export['market_segment'].apply(
            lambda x: f"segment_{x}" if x != -1 else "noise"
        )
        
        df_export.to_csv(output_path, index=False)
        return output_path