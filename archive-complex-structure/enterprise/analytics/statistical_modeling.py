"""
Statistical Modeling Engine
==========================

Advanced statistical modeling and trend analysis including:
- Multiple regression models for price prediction
- Time series analysis and forecasting
- Correlation analysis and feature importance
- Trend detection and seasonality analysis
- Statistical significance testing
- Model validation and performance metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import json
import warnings
warnings.filterwarnings('ignore')


class StatisticalModelingEngine:
    """
    Comprehensive statistical modeling for real estate price prediction and analysis.
    """
    
    def __init__(self):
        self.models = {}
        self.model_performance = {}
        self.feature_importance = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def build_models(self, property_data):
        """
        Build comprehensive statistical models for price prediction and analysis.
        
        Args:
            property_data: List of property dictionaries or DataFrame
            
        Returns:
            dict: Complete modeling results with predictions and insights
        """
        
        # Convert to DataFrame if needed
        if isinstance(property_data, list):
            df = pd.DataFrame(property_data)
        else:
            df = property_data.copy()
        
        if len(df) < 10:
            return {'error': 'Insufficient data for statistical modeling (minimum 10 properties required)'}
        
        # Prepare features for modeling
        features_df, target_df = self._prepare_modeling_data(df)
        
        if features_df is None or len(features_df) == 0:
            return {'error': 'Unable to prepare features for modeling'}
        
        # Build multiple models
        model_results = self._build_prediction_models(features_df, target_df)
        
        # Correlation analysis
        correlation_analysis = self._perform_correlation_analysis(df)
        
        # Feature importance analysis
        feature_importance = self._analyze_feature_importance(features_df, target_df)
        
        # Statistical tests
        statistical_tests = self._perform_statistical_tests(df)
        
        # Price trend analysis
        trend_analysis = self._analyze_price_trends(df)
        
        # Market efficiency tests
        efficiency_analysis = self._test_market_efficiency(df)
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'dataset_size': len(df),
            'model_performance': model_results,
            'correlation_analysis': correlation_analysis,
            'feature_importance': feature_importance,
            'statistical_tests': statistical_tests,
            'trend_analysis': trend_analysis,
            'efficiency_analysis': efficiency_analysis,
            'model_insights': self._generate_model_insights(model_results, correlation_analysis)
        }
        
        return results
    
    def _prepare_modeling_data(self, df):
        """Prepare features and target variables for modeling."""
        
        try:
            # Target variable
            if 'price' not in df.columns:
                return None, None
                
            # Remove outliers (properties beyond 3 standard deviations)
            price_mean = df['price'].mean()
            price_std = df['price'].std()
            df_clean = df[
                (df['price'] >= price_mean - 3 * price_std) & 
                (df['price'] <= price_mean + 3 * price_std)
            ].copy()
            
            if len(df_clean) < 10:
                df_clean = df.copy()  # Use original data if too many outliers removed
            
            # Prepare features
            features = []
            feature_names = []
            
            # Numerical features
            numerical_features = ['sqm', 'rooms', 'price_per_sqm']
            for feature in numerical_features:
                if feature in df_clean.columns:
                    values = pd.to_numeric(df_clean[feature], errors='coerce').fillna(df_clean[feature].median() if feature in df_clean.columns else 0)
                    features.append(values)
                    feature_names.append(feature)
            
            # Energy class (ordinal encoding)
            if 'energy_class' in df_clean.columns:
                energy_map = {'A+': 8, 'A': 7, 'B+': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1, 'G': 0}
                energy_encoded = df_clean['energy_class'].map(energy_map).fillna(4)  # Default to C
                features.append(energy_encoded)
                feature_names.append('energy_class_encoded')
            
            # Neighborhood encoding (frequency-based)
            if 'neighborhood' in df_clean.columns:
                neighborhood_counts = df_clean['neighborhood'].value_counts()
                neighborhood_freq = df_clean['neighborhood'].map(neighborhood_counts).fillna(0)
                features.append(neighborhood_freq)
                feature_names.append('neighborhood_frequency')
                
                # Create neighborhood dummies for top neighborhoods
                top_neighborhoods = neighborhood_counts.head(5).index
                for neighborhood in top_neighborhoods:
                    dummy = (df_clean['neighborhood'] == neighborhood).astype(int)
                    features.append(dummy)
                    feature_names.append(f'neighborhood_{neighborhood}')
            
            # Property type encoding
            if 'property_type' in df_clean.columns:
                if 'property_type' not in self.label_encoders:
                    self.label_encoders['property_type'] = LabelEncoder()
                    type_encoded = self.label_encoders['property_type'].fit_transform(df_clean['property_type'].fillna('apartment'))
                else:
                    type_encoded = self.label_encoders['property_type'].transform(df_clean['property_type'].fillna('apartment'))
                features.append(type_encoded)
                feature_names.append('property_type_encoded')
            
            # Floor feature (if available)
            if 'floor' in df_clean.columns:
                floor_values = pd.to_numeric(df_clean['floor'], errors='coerce').fillna(2)  # Default to 2nd floor
                features.append(floor_values)
                feature_names.append('floor')
            
            # Combine features
            if not features:
                return None, None
            
            features_array = np.column_stack(features)
            features_df = pd.DataFrame(features_array, columns=feature_names)
            
            # Remove any remaining NaN values
            features_df = features_df.fillna(features_df.median())
            
            # Target variable (log-transformed for better modeling)
            target_df = np.log1p(df_clean['price'])
            
            return features_df, target_df
            
        except Exception as e:
            print(f"Error preparing modeling data: {e}")
            return None, None
    
    def _build_prediction_models(self, features_df, target_df):
        """Build and evaluate multiple prediction models."""
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features_df, target_df, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        models_to_test = {
            'linear_regression': LinearRegression(),
            'ridge_regression': Ridge(alpha=1.0),
            'lasso_regression': Lasso(alpha=0.1),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        model_results = {}
        
        for model_name, model in models_to_test.items():
            try:
                # Use scaled data for linear models, original for tree models
                if 'regression' in model_name:
                    X_train_model = X_train_scaled
                    X_test_model = X_test_scaled
                else:
                    X_train_model = X_train
                    X_test_model = X_test
                
                # Train model
                model.fit(X_train_model, y_train)
                
                # Make predictions
                y_pred_train = model.predict(X_train_model)
                y_pred_test = model.predict(X_test_model)
                
                # Calculate metrics
                train_r2 = r2_score(y_train, y_pred_train)
                test_r2 = r2_score(y_test, y_pred_test)
                train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                train_mae = mean_absolute_error(y_train, y_pred_train)
                test_mae = mean_absolute_error(y_test, y_pred_test)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train_model, y_train, cv=5, scoring='r2')
                
                model_results[model_name] = {
                    'train_r2': float(train_r2),
                    'test_r2': float(test_r2),
                    'train_rmse': float(train_rmse),
                    'test_rmse': float(test_rmse),
                    'train_mae': float(train_mae),
                    'test_mae': float(test_mae),
                    'cv_mean_r2': float(cv_scores.mean()),
                    'cv_std_r2': float(cv_scores.std()),
                    'overfitting_score': float(train_r2 - test_r2),  # Positive indicates overfitting
                    'model_quality': self._assess_model_quality(test_r2, train_r2 - test_r2)
                }
                
                # Store the best model
                if model_name not in self.models or test_r2 > self.model_performance.get(model_name, {}).get('test_r2', 0):
                    self.models[model_name] = model
                    self.model_performance[model_name] = model_results[model_name]
                
            except Exception as e:
                model_results[model_name] = {'error': str(e)}
        
        # Identify best model
        valid_models = {k: v for k, v in model_results.items() if 'error' not in v}
        if valid_models:
            best_model = max(valid_models.keys(), key=lambda x: valid_models[x]['test_r2'])
            model_results['best_model'] = best_model
            model_results['model_recommendation'] = self._recommend_model_usage(valid_models)
        
        return model_results
    
    def _assess_model_quality(self, test_r2, overfitting_score):
        """Assess overall model quality."""
        if test_r2 > 0.8 and overfitting_score < 0.1:
            return "Excellent"
        elif test_r2 > 0.6 and overfitting_score < 0.2:
            return "Good"
        elif test_r2 > 0.4 and overfitting_score < 0.3:
            return "Fair"
        else:
            return "Poor"
    
    def _recommend_model_usage(self, valid_models):
        """Recommend which model to use for different purposes."""
        
        # Find best model by test R2
        best_accuracy = max(valid_models.keys(), key=lambda x: valid_models[x]['test_r2'])
        
        # Find most stable model (lowest overfitting)
        best_stability = min(valid_models.keys(), key=lambda x: valid_models[x]['overfitting_score'])
        
        # Find simplest interpretable model
        interpretable_models = ['linear_regression', 'ridge_regression', 'lasso_regression']
        best_interpretable = None
        for model in interpretable_models:
            if model in valid_models:
                if best_interpretable is None or valid_models[model]['test_r2'] > valid_models[best_interpretable]['test_r2']:
                    best_interpretable = model
        
        return {
            'highest_accuracy': best_accuracy,
            'most_stable': best_stability,
            'most_interpretable': best_interpretable,
            'recommendation': f"Use {best_accuracy} for highest accuracy, {best_interpretable or best_stability} for interpretability"
        }
    
    def _perform_correlation_analysis(self, df):
        """Perform comprehensive correlation analysis."""
        
        correlation_results = {}
        
        # Prepare numerical data
        numerical_cols = []
        numerical_data = []
        
        if 'price' in df.columns:
            numerical_cols.append('price')
            numerical_data.append(pd.to_numeric(df['price'], errors='coerce'))
        
        if 'price_per_sqm' in df.columns:
            numerical_cols.append('price_per_sqm')
            numerical_data.append(pd.to_numeric(df['price_per_sqm'], errors='coerce'))
        
        if 'sqm' in df.columns:
            numerical_cols.append('sqm')
            numerical_data.append(pd.to_numeric(df['sqm'], errors='coerce'))
        
        if 'rooms' in df.columns:
            numerical_cols.append('rooms')
            numerical_data.append(pd.to_numeric(df['rooms'], errors='coerce'))
        
        # Energy class correlation
        if 'energy_class' in df.columns:
            energy_map = {'A+': 8, 'A': 7, 'B+': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1, 'G': 0}
            energy_numeric = df['energy_class'].map(energy_map).fillna(4)
            numerical_cols.append('energy_class_numeric')
            numerical_data.append(energy_numeric)
        
        if len(numerical_data) >= 2:
            # Create correlation matrix
            corr_df = pd.DataFrame({col: data for col, data in zip(numerical_cols, numerical_data)})
            corr_df = corr_df.dropna()
            
            if len(corr_df) > 5:
                # Pearson correlation
                pearson_corr = corr_df.corr()
                
                # Spearman correlation (rank-based)
                spearman_corr = corr_df.corr(method='spearman')
                
                correlation_results = {
                    'pearson_correlations': pearson_corr.to_dict(),
                    'spearman_correlations': spearman_corr.to_dict(),
                    'key_insights': self._extract_correlation_insights(pearson_corr, corr_df)
                }
        
        return correlation_results
    
    def _extract_correlation_insights(self, corr_matrix, data):
        """Extract key insights from correlation analysis."""
        
        insights = []
        
        # Price correlations
        if 'price' in corr_matrix.columns:
            price_corrs = corr_matrix['price'].drop('price').abs().sort_values(ascending=False)
            
            for feature, corr_value in price_corrs.head(3).items():
                if corr_value > 0.3:
                    direction = "positive" if corr_matrix['price'][feature] > 0 else "negative"
                    insights.append(f"Strong {direction} correlation between price and {feature} (r={corr_matrix['price'][feature]:.3f})")
        
        # Size vs Energy efficiency
        if 'sqm' in corr_matrix.columns and 'energy_class_numeric' in corr_matrix.columns:
            size_energy_corr = corr_matrix['sqm']['energy_class_numeric']
            insights.append(f"Size-Energy efficiency correlation: {size_energy_corr:.3f} (weak)" if abs(size_energy_corr) < 0.3 else f"Size-Energy efficiency correlation: {size_energy_corr:.3f} (strong)")
        
        # Price per sqm insights
        if 'price_per_sqm' in corr_matrix.columns and 'sqm' in corr_matrix.columns:
            price_size_corr = corr_matrix['price_per_sqm']['sqm']
            if price_size_corr < -0.2:
                insights.append("Larger properties tend to have lower price per sqm (economy of scale)")
            elif price_size_corr > 0.2:
                insights.append("Larger properties command premium price per sqm")
        
        return insights
    
    def _analyze_feature_importance(self, features_df, target_df):
        """Analyze feature importance using tree-based models."""
        
        if features_df is None or len(features_df) == 0:
            return {}
        
        try:
            # Use Random Forest for feature importance
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(features_df, target_df)
            
            # Get feature importance
            importance_scores = rf_model.feature_importances_
            feature_names = features_df.columns
            
            # Create importance dictionary
            feature_importance = dict(zip(feature_names, importance_scores))
            
            # Sort by importance
            sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            self.feature_importance = {
                'feature_rankings': sorted_importance,
                'top_features': [item[0] for item in sorted_importance[:5]],
                'feature_importance_dict': feature_importance,
                'model_used': 'RandomForestRegressor'
            }
            
            return self.feature_importance
            
        except Exception as e:
            return {'error': f"Feature importance analysis failed: {str(e)}"}
    
    def _perform_statistical_tests(self, df):
        """Perform various statistical tests on the data."""
        
        tests_results = {}
        
        # Normality test for price
        if 'price' in df.columns:
            price_data = pd.to_numeric(df['price'], errors='coerce').dropna()
            if len(price_data) > 8:
                shapiro_stat, shapiro_p = stats.shapiro(price_data[:5000])  # Shapiro-Wilk limited to 5000 samples
                tests_results['price_normality'] = {
                    'test': 'Shapiro-Wilk',
                    'statistic': float(shapiro_stat),
                    'p_value': float(shapiro_p),
                    'is_normal': shapiro_p > 0.05,
                    'interpretation': 'Price distribution is normal' if shapiro_p > 0.05 else 'Price distribution is not normal'
                }
        
        # Energy class price differences (ANOVA)
        if 'energy_class' in df.columns and 'price' in df.columns:
            energy_groups = []
            energy_classes = df['energy_class'].unique()
            
            for energy_class in energy_classes:
                if pd.isna(energy_class):
                    continue
                group_prices = pd.to_numeric(df[df['energy_class'] == energy_class]['price'], errors='coerce').dropna()
                if len(group_prices) >= 3:
                    energy_groups.append(group_prices)
            
            if len(energy_groups) >= 2:
                try:
                    f_stat, p_value = stats.f_oneway(*energy_groups)
                    tests_results['energy_class_price_anova'] = {
                        'test': 'One-way ANOVA',
                        'f_statistic': float(f_stat),
                        'p_value': float(p_value),
                        'significant_difference': p_value < 0.05,
                        'interpretation': 'Energy classes have significantly different prices' if p_value < 0.05 else 'No significant price difference between energy classes'
                    }
                except:
                    pass
        
        # Neighborhood price differences
        if 'neighborhood' in df.columns and 'price' in df.columns:
            neighborhood_counts = df['neighborhood'].value_counts()
            top_neighborhoods = neighborhood_counts[neighborhood_counts >= 5].index[:5]  # Top 5 with at least 5 properties
            
            if len(top_neighborhoods) >= 2:
                neighborhood_groups = []
                for neighborhood in top_neighborhoods:
                    group_prices = pd.to_numeric(df[df['neighborhood'] == neighborhood]['price'], errors='coerce').dropna()
                    neighborhood_groups.append(group_prices)
                
                try:
                    f_stat, p_value = stats.f_oneway(*neighborhood_groups)
                    tests_results['neighborhood_price_anova'] = {
                        'test': 'One-way ANOVA',
                        'f_statistic': float(f_stat),
                        'p_value': float(p_value),
                        'significant_difference': p_value < 0.05,
                        'neighborhoods_tested': list(top_neighborhoods),
                        'interpretation': 'Neighborhoods have significantly different prices' if p_value < 0.05 else 'No significant price difference between top neighborhoods'
                    }
                except:
                    pass
        
        return tests_results
    
    def _analyze_price_trends(self, df):
        """Analyze price trends and patterns in the data."""
        
        trends = {}
        
        # Price distribution analysis
        if 'price' in df.columns:
            price_data = pd.to_numeric(df['price'], errors='coerce').dropna()
            
            trends['price_distribution'] = {
                'mean': float(price_data.mean()),
                'median': float(price_data.median()),
                'std': float(price_data.std()),
                'min': float(price_data.min()),
                'max': float(price_data.max()),
                'q25': float(price_data.quantile(0.25)),
                'q75': float(price_data.quantile(0.75)),
                'skewness': float(price_data.skew()),
                'kurtosis': float(price_data.kurtosis())
            }
        
        # Price per sqm trends by energy class
        if 'energy_class' in df.columns and 'price_per_sqm' in df.columns:
            energy_price_trends = {}
            
            for energy_class in df['energy_class'].unique():
                if pd.isna(energy_class):
                    continue
                    
                class_data = df[df['energy_class'] == energy_class]
                class_price_per_sqm = pd.to_numeric(class_data['price_per_sqm'], errors='coerce').dropna()
                
                if len(class_price_per_sqm) >= 3:
                    energy_price_trends[energy_class] = {
                        'count': len(class_price_per_sqm),
                        'mean_price_per_sqm': float(class_price_per_sqm.mean()),
                        'median_price_per_sqm': float(class_price_per_sqm.median()),
                        'std_price_per_sqm': float(class_price_per_sqm.std())
                    }
            
            trends['energy_class_pricing'] = energy_price_trends
        
        # Size category analysis
        if 'sqm' in df.columns and 'price' in df.columns:
            size_categories = []
            df_size = df.copy()
            df_size['sqm_numeric'] = pd.to_numeric(df_size['sqm'], errors='coerce')
            df_size = df_size.dropna(subset=['sqm_numeric'])
            
            # Define size categories
            df_size['size_category'] = pd.cut(df_size['sqm_numeric'], 
                                            bins=[0, 50, 80, 120, np.inf], 
                                            labels=['Compact (<50)', 'Medium (50-80)', 'Large (80-120)', 'Premium (>120)'])
            
            size_trends = {}
            for category in df_size['size_category'].unique():
                if pd.isna(category):
                    continue
                    
                category_data = df_size[df_size['size_category'] == category]
                category_prices = pd.to_numeric(category_data['price'], errors='coerce').dropna()
                category_price_per_sqm = pd.to_numeric(category_data['price_per_sqm'], errors='coerce').dropna()
                
                if len(category_prices) >= 3:
                    size_trends[str(category)] = {
                        'count': len(category_prices),
                        'mean_price': float(category_prices.mean()),
                        'mean_price_per_sqm': float(category_price_per_sqm.mean()) if len(category_price_per_sqm) > 0 else None,
                        'avg_size': float(category_data['sqm_numeric'].mean())
                    }
            
            trends['size_category_pricing'] = size_trends
        
        return trends
    
    def _test_market_efficiency(self, df):
        """Test for market efficiency and identify potential arbitrage opportunities."""
        
        efficiency_tests = {}
        
        # Price dispersion test
        if 'price_per_sqm' in df.columns and 'neighborhood' in df.columns:
            # Calculate coefficient of variation for price per sqm within neighborhoods
            neighborhood_cv = {}
            
            for neighborhood in df['neighborhood'].unique():
                if pd.isna(neighborhood):
                    continue
                    
                neighborhood_data = df[df['neighborhood'] == neighborhood]
                price_per_sqm = pd.to_numeric(neighborhood_data['price_per_sqm'], errors='coerce').dropna()
                
                if len(price_per_sqm) >= 3:
                    cv = price_per_sqm.std() / price_per_sqm.mean()
                    neighborhood_cv[neighborhood] = float(cv)
            
            efficiency_tests['price_dispersion'] = {
                'neighborhood_cv': neighborhood_cv,
                'high_dispersion_areas': [k for k, v in neighborhood_cv.items() if v > 0.3],  # CV > 30%
                'market_efficiency_score': 1.0 - (np.mean(list(neighborhood_cv.values())) if neighborhood_cv else 0.5),
                'interpretation': 'High price dispersion suggests arbitrage opportunities'
            }
        
        # Energy efficiency premium consistency
        if 'energy_class' in df.columns and 'price_per_sqm' in df.columns:
            energy_premiums = {}
            base_price = None
            
            # Calculate average price per sqm for each energy class
            for energy_class in ['G', 'F', 'E', 'D', 'C', 'B', 'B+', 'A', 'A+']:
                class_data = df[df['energy_class'] == energy_class]
                if len(class_data) >= 3:
                    avg_price = pd.to_numeric(class_data['price_per_sqm'], errors='coerce').dropna().mean()
                    energy_premiums[energy_class] = float(avg_price)
                    
                    if energy_class == 'C':  # Use C as baseline
                        base_price = avg_price
            
            if base_price:
                efficiency_premiums = {k: (v - base_price) / base_price for k, v in energy_premiums.items()}
                efficiency_tests['energy_efficiency_premium'] = {
                    'premiums_by_class': efficiency_premiums,
                    'baseline_class': 'C',
                    'arbitrage_opportunities': [k for k, v in efficiency_premiums.items() if v < -0.1 and k in ['A+', 'A', 'B+', 'B']],  # Undervalued efficient properties
                    'interpretation': 'Energy efficient properties trading below expected premium'
                }
        
        return efficiency_tests
    
    def _generate_model_insights(self, model_results, correlation_analysis):
        """Generate actionable insights from modeling results."""
        
        insights = []
        
        # Model performance insights
        valid_models = {k: v for k, v in model_results.items() if 'error' not in v and k not in ['best_model', 'model_recommendation']}
        
        if valid_models:
            best_r2 = max(v.get('test_r2', 0) for v in valid_models.values())
            
            if best_r2 > 0.8:
                insights.append("Excellent model predictability - market follows clear patterns")
            elif best_r2 > 0.6:
                insights.append("Good model predictability - most price variation explained by key factors")
            elif best_r2 > 0.4:
                insights.append("Moderate predictability - significant unexplained price variation suggests opportunities")
            else:
                insights.append("Low predictability - market may have significant inefficiencies")
        
        # Correlation insights
        if 'key_insights' in correlation_analysis:
            insights.extend(correlation_analysis['key_insights'])
        
        # Feature importance insights
        if hasattr(self, 'feature_importance') and 'top_features' in self.feature_importance:
            top_features = self.feature_importance['top_features'][:3]
            insights.append(f"Top price drivers: {', '.join(top_features)}")
        
        return insights

    def predict_property_price(self, property_features, model_name='best'):
        """Predict price for a single property using trained models."""
        
        if not self.models:
            return {'error': 'No trained models available'}
        
        model_to_use = model_name
        if model_name == 'best' and 'best_model' in self.model_performance:
            model_to_use = max(self.models.keys(), key=lambda x: self.model_performance.get(x, {}).get('test_r2', 0))
        
        if model_to_use not in self.models:
            return {'error': f'Model {model_to_use} not available'}
        
        try:
            # Prepare features (same way as training)
            # This is a simplified version - in practice, you'd need to handle feature preparation more carefully
            model = self.models[model_to_use]
            
            # Make prediction (log price)
            if 'regression' in model_to_use:
                features_scaled = self.scaler.transform([property_features])
                log_price_pred = model.predict(features_scaled)[0]
            else:
                log_price_pred = model.predict([property_features])[0]
            
            # Convert back from log scale
            predicted_price = np.expm1(log_price_pred)
            
            # Get prediction confidence interval (simplified)
            model_rmse = self.model_performance[model_to_use]['test_rmse']
            lower_bound = np.expm1(log_price_pred - 1.96 * model_rmse)
            upper_bound = np.expm1(log_price_pred + 1.96 * model_rmse)
            
            return {
                'predicted_price': float(predicted_price),
                'confidence_interval': {
                    'lower': float(lower_bound),
                    'upper': float(upper_bound)
                },
                'model_used': model_to_use,
                'model_r2': self.model_performance[model_to_use]['test_r2']
            }
            
        except Exception as e:
            return {'error': f'Prediction failed: {str(e)}'}
    
    def export_models(self, filepath):
        """Export trained models for use in production."""
        import pickle
        
        export_data = {
            'models': self.models,
            'model_performance': self.model_performance,
            'feature_importance': self.feature_importance,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(export_data, f)
        
        return f"Models exported to {filepath}"