"""
Portfolio Strategies Engine
==========================

Pre-built investment portfolios and strategy recommendations based on:
- Investment budget levels ($100K, $500K, $1M, $2M+)
- Risk tolerance and investment objectives
- Geographic and property type diversification
- Energy efficiency arbitrage opportunities
- Market timing and cycle positioning
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import json


class PortfolioStrategiesEngine:
    """
    Create optimized investment portfolios based on budget, risk tolerance, and market opportunities.
    """
    
    def __init__(self):
        self.portfolio_templates = {
            'budget_100k': {
                'name': 'Entry Level Portfolio',
                'description': 'Single property focus with high growth potential',
                'min_budget': 80000,
                'max_budget': 150000,
                'strategy_type': 'single_property_growth',
                'risk_level': 'medium',
                'expected_annual_return': 0.18,
                'holding_period': 3
            },
            'budget_500k': {
                'name': 'Growth Portfolio',
                'description': 'Diversified portfolio with energy arbitrage focus',
                'min_budget': 400000,
                'max_budget': 700000,
                'strategy_type': 'diversified_growth',
                'risk_level': 'medium',
                'expected_annual_return': 0.22,
                'holding_period': 5
            },
            'budget_1m': {
                'name': 'Balanced Portfolio',
                'description': 'Multi-property balanced growth and income strategy',
                'min_budget': 800000,
                'max_budget': 1500000,
                'strategy_type': 'balanced_portfolio',
                'risk_level': 'medium-low',
                'expected_annual_return': 0.20,
                'holding_period': 7
            },
            'budget_2m': {
                'name': 'Premium Portfolio',
                'description': 'Luxury market positioning with premium locations',
                'min_budget': 1500000,
                'max_budget': 10000000,
                'strategy_type': 'premium_portfolio',
                'risk_level': 'low',
                'expected_annual_return': 0.16,
                'holding_period': 10
            }
        }
        
        self.strategy_frameworks = {
            'energy_arbitrage': {
                'description': 'Buy low-energy properties, retrofit, resell at premium',
                'target_energy_classes': ['C', 'D', 'E'],
                'retrofit_budget_percentage': 0.15,
                'expected_value_increase': 0.35,
                'timeline_months': 18,
                'risk_factors': ['renovation_cost_overruns', 'permit_delays', 'market_timing']
            },
            'rental_yield_focus': {
                'description': 'High rental yield properties for cash flow generation',
                'target_rental_yield': 0.065,
                'target_neighborhoods': ['Exarchia', 'Koukaki', 'Pangrati'],
                'tenant_focus': 'professionals_students',
                'management_strategy': 'professional_management',
                'risk_factors': ['vacancy_risk', 'tenant_quality', 'neighborhood_gentrification']
            },
            'luxury_appreciation': {
                'description': 'Premium properties in top locations for capital appreciation',
                'target_neighborhoods': ['Kolonaki', 'Plaka', 'Kifisia'],
                'property_types': ['luxury_apartment', 'penthouse', 'villa'],
                'minimum_energy_class': 'B',
                'expected_appreciation': 0.08,
                'risk_factors': ['market_cycles', 'luxury_market_volatility']
            },
            'mixed_use_development': {
                'description': 'Properties with commercial potential or conversion opportunities',
                'target_property_types': ['mixed_use', 'commercial', 'conversion_potential'],
                'development_timeline': 36,
                'expected_return_multiple': 2.5,
                'risk_factors': ['zoning_restrictions', 'development_costs', 'market_demand']
            }
        }
    
    def create_portfolios(self, property_data: List[Dict], investor_profile: Dict) -> Dict:
        """
        Create customized investment portfolios based on investor profile and available properties.
        
        Args:
            property_data: List of available properties
            investor_profile: Investor requirements and constraints
            
        Returns:
            Dict: Comprehensive portfolio recommendations
        """
        
        budget = investor_profile.get('budget', 500000)
        risk_tolerance = investor_profile.get('risk_tolerance', 'medium')
        investment_horizon = investor_profile.get('investment_horizon', 5)
        objectives = investor_profile.get('objectives', ['capital_appreciation'])
        
        # Convert to DataFrame for easier analysis
        if isinstance(property_data, list):
            df = pd.DataFrame(property_data)
        else:
            df = property_data.copy()
        
        # Determine appropriate portfolio template
        portfolio_template = self._select_portfolio_template(budget, risk_tolerance, investment_horizon)
        
        # Create specific portfolio recommendations
        portfolio_recommendations = self._create_portfolio_recommendations(
            df, portfolio_template, investor_profile
        )
        
        # Generate strategy-specific portfolios
        strategy_portfolios = self._create_strategy_portfolios(df, investor_profile)
        
        # Risk analysis for each portfolio
        risk_analysis = self._analyze_portfolio_risks(portfolio_recommendations, strategy_portfolios)
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'investor_profile': investor_profile,
            'selected_template': portfolio_template,
            'recommended_portfolios': portfolio_recommendations,
            'strategy_specific_portfolios': strategy_portfolios,
            'risk_analysis': risk_analysis,
            'implementation_guide': self._create_implementation_guide(portfolio_recommendations),
            'portfolio_comparison': self._compare_portfolios(portfolio_recommendations, strategy_portfolios)
        }
        
        return results
    
    def _select_portfolio_template(self, budget: float, risk_tolerance: str, investment_horizon: int) -> Dict:
        """Select appropriate portfolio template based on investor characteristics."""
        
        # Select by budget range
        for template_key, template in self.portfolio_templates.items():
            if template['min_budget'] <= budget <= template['max_budget']:
                selected_template = template.copy()
                
                # Adjust for risk tolerance
                if risk_tolerance == 'low':
                    selected_template['expected_annual_return'] *= 0.85
                    selected_template['risk_level'] = 'low'
                elif risk_tolerance == 'high':
                    selected_template['expected_annual_return'] *= 1.15
                    selected_template['risk_level'] = 'high'
                
                # Adjust for investment horizon
                if investment_horizon < 3:
                    selected_template['strategy_type'] = 'short_term_growth'
                    selected_template['expected_annual_return'] *= 1.1
                elif investment_horizon > 10:
                    selected_template['strategy_type'] = 'long_term_wealth'
                    selected_template['expected_annual_return'] *= 0.9
                
                return selected_template
        
        # Default to medium budget template if no match
        return self.portfolio_templates['budget_500k']
    
    def _create_portfolio_recommendations(self, df: pd.DataFrame, template: Dict, investor_profile: Dict) -> Dict:
        """Create specific portfolio recommendations based on template and available properties."""
        
        budget = investor_profile.get('budget', 500000)
        
        # Score properties for this portfolio strategy
        df_scored = self._score_properties_for_portfolio(df, template, investor_profile)
        
        # Create different portfolio options
        portfolios = {
            'conservative': self._create_conservative_portfolio(df_scored, budget * 0.8, template),
            'balanced': self._create_balanced_portfolio(df_scored, budget, template),
            'aggressive': self._create_aggressive_portfolio(df_scored, budget * 1.2, template)
        }
        
        return portfolios
    
    def _score_properties_for_portfolio(self, df: pd.DataFrame, template: Dict, investor_profile: Dict) -> pd.DataFrame:
        """Score properties based on portfolio strategy and investor preferences."""
        
        df_scored = df.copy()
        df_scored['portfolio_score'] = 0.0
        
        strategy_type = template.get('strategy_type', 'balanced_portfolio')
        
        for idx, property_data in df_scored.iterrows():
            score = 5.0  # Base score
            
            # Price affordability (within budget)
            property_price = property_data.get('price', 0)
            budget = investor_profile.get('budget', 500000)
            
            if property_price <= budget * 0.3:  # Single property shouldn't exceed 30% of budget
                score += 2.0
            elif property_price <= budget * 0.5:
                score += 1.0
            elif property_price > budget:
                score -= 3.0
            
            # Energy efficiency scoring based on strategy
            energy_class = property_data.get('energy_class', 'C')
            if strategy_type in ['energy_arbitrage', 'diversified_growth']:
                # Prefer lower energy classes for retrofit opportunities
                energy_scores = {'G': 2.0, 'F': 1.8, 'E': 1.5, 'D': 1.2, 'C': 1.0, 'B': 0.5, 'B+': 0.3, 'A': 0.1, 'A+': 0.0}
                score += energy_scores.get(energy_class, 1.0)
            else:
                # Prefer higher energy classes for premium positioning
                energy_scores = {'A+': 2.0, 'A': 1.8, 'B+': 1.5, 'B': 1.2, 'C': 1.0, 'D': 0.5, 'E': 0.3, 'F': 0.1, 'G': 0.0}
                score += energy_scores.get(energy_class, 1.0)
            
            # Neighborhood scoring
            neighborhood = property_data.get('neighborhood', 'Unknown')
            neighborhood_scores = self._get_neighborhood_scores(strategy_type)
            score += neighborhood_scores.get(neighborhood, 0.5)
            
            # Price per sqm efficiency
            price_per_sqm = property_data.get('price_per_sqm', 4000)
            if price_per_sqm < 3500:
                score += 1.5  # Good value
            elif price_per_sqm > 6000:
                score -= 1.0  # Expensive
            
            # Size appropriateness
            sqm = property_data.get('sqm', 70)
            if strategy_type == 'rental_yield_focus':
                # Prefer medium-sized properties for rental
                if 60 <= sqm <= 100:
                    score += 1.0
            elif strategy_type == 'luxury_appreciation':
                # Prefer larger properties for luxury market
                if sqm > 100:
                    score += 1.5
            
            df_scored.at[idx, 'portfolio_score'] = max(0, min(10, score))
        
        return df_scored.sort_values('portfolio_score', ascending=False)
    
    def _get_neighborhood_scores(self, strategy_type: str) -> Dict[str, float]:
        """Get neighborhood scores based on investment strategy."""
        
        if strategy_type == 'energy_arbitrage':
            return {
                'Exarchia': 1.5, 'Koukaki': 1.3, 'Pangrati': 1.2, 'Kolonaki': 1.0,
                'Plaka': 1.1, 'Kipseli': 1.4, 'Patisia': 1.3
            }
        elif strategy_type == 'luxury_appreciation':
            return {
                'Kolonaki': 2.0, 'Plaka': 1.8, 'Kifisia': 1.6, 'Koukaki': 1.3,
                'Thiseio': 1.4, 'Exarchia': 0.8
            }
        elif strategy_type == 'rental_yield_focus':
            return {
                'Exarchia': 1.8, 'Koukaki': 1.6, 'Pangrati': 1.4, 'Kipseli': 1.3,
                'Plaka': 1.5, 'Kolonaki': 1.0
            }
        else:
            return {'Kolonaki': 1.2, 'Plaka': 1.1, 'Koukaki': 1.0, 'Exarchia': 1.0}
    
    def _create_conservative_portfolio(self, df_scored: pd.DataFrame, budget: float, template: Dict) -> Dict:
        """Create conservative portfolio with lower risk properties."""
        
        # Filter for lower risk properties
        conservative_properties = df_scored[
            (df_scored['energy_class'].isin(['A+', 'A', 'B+', 'B', 'C'])) &
            (df_scored['price'] <= budget * 0.4)  # No single property over 40% of budget
        ].head(10)
        
        if len(conservative_properties) == 0:
            conservative_properties = df_scored.head(5)
        
        portfolio = self._build_portfolio_from_properties(
            conservative_properties, budget, template, 'conservative'
        )
        
        return portfolio
    
    def _create_balanced_portfolio(self, df_scored: pd.DataFrame, budget: float, template: Dict) -> Dict:
        """Create balanced portfolio mixing growth and stability."""
        
        # Mix of property types and energy classes
        balanced_properties = df_scored.head(15)  # Top 15 scored properties
        
        portfolio = self._build_portfolio_from_properties(
            balanced_properties, budget, template, 'balanced'
        )
        
        return portfolio
    
    def _create_aggressive_portfolio(self, df_scored: pd.DataFrame, budget: float, template: Dict) -> Dict:
        """Create aggressive portfolio focused on high returns."""
        
        # Focus on energy arbitrage opportunities and emerging areas
        aggressive_properties = df_scored[
            (df_scored['energy_class'].isin(['C', 'D', 'E', 'F'])) |
            (df_scored['portfolio_score'] >= 7.0)
        ].head(10)
        
        if len(aggressive_properties) == 0:
            aggressive_properties = df_scored.head(8)
        
        portfolio = self._build_portfolio_from_properties(
            aggressive_properties, budget, template, 'aggressive'
        )
        
        return portfolio
    
    def _build_portfolio_from_properties(self, properties: pd.DataFrame, budget: float, template: Dict, risk_level: str) -> Dict:
        """Build portfolio from selected properties within budget constraints."""
        
        selected_properties = []
        total_cost = 0
        remaining_budget = budget
        
        # Greedy selection algorithm - select highest scoring properties that fit budget
        for idx, property_data in properties.iterrows():
            property_price = property_data.get('price', 0)
            transaction_costs = property_price * 0.08  # 8% transaction costs
            total_property_cost = property_price + transaction_costs
            
            if total_property_cost <= remaining_budget:
                property_info = {
                    'property_id': property_data.get('property_id', f'prop_{idx}'),
                    'neighborhood': property_data.get('neighborhood', 'Unknown'),
                    'price': property_price,
                    'sqm': property_data.get('sqm', 0),
                    'energy_class': property_data.get('energy_class', 'C'),
                    'price_per_sqm': property_data.get('price_per_sqm', 0),
                    'portfolio_score': property_data.get('portfolio_score', 5.0),
                    'total_cost': total_property_cost,
                    'expected_annual_return': self._calculate_expected_return(property_data, template, risk_level)
                }
                
                selected_properties.append(property_info)
                total_cost += total_property_cost
                remaining_budget -= total_property_cost
                
                # Stop if we have enough properties for diversification
                if len(selected_properties) >= 5 or remaining_budget < 50000:
                    break
        
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(selected_properties, budget, template)
        
        portfolio = {
            'risk_level': risk_level,
            'total_budget': budget,
            'total_invested': total_cost,
            'remaining_budget': remaining_budget,
            'properties': selected_properties,
            'property_count': len(selected_properties),
            'portfolio_metrics': portfolio_metrics,
            'diversification_score': self._calculate_diversification_score(selected_properties),
            'implementation_timeline': self._create_implementation_timeline(selected_properties)
        }
        
        return portfolio
    
    def _calculate_expected_return(self, property_data: Dict, template: Dict, risk_level: str) -> float:
        """Calculate expected annual return for property based on strategy and risk level."""
        
        base_return = template.get('expected_annual_return', 0.18)
        
        # Adjust for energy class
        energy_class = property_data.get('energy_class', 'C')
        energy_adjustments = {
            'A+': 0.02, 'A': 0.01, 'B+': 0.005, 'B': 0.0, 'C': -0.01,
            'D': -0.02, 'E': -0.03, 'F': -0.04, 'G': -0.05
        }
        
        # For energy arbitrage strategies, lower energy classes have higher potential returns
        strategy_type = template.get('strategy_type', 'balanced')
        if 'energy' in strategy_type or 'growth' in strategy_type:
            energy_adjustments = {k: -v for k, v in energy_adjustments.items()}
        
        energy_adjustment = energy_adjustments.get(energy_class, 0)
        
        # Adjust for risk level
        risk_adjustments = {
            'conservative': -0.03,
            'balanced': 0.0,
            'aggressive': 0.04
        }
        risk_adjustment = risk_adjustments.get(risk_level, 0.0)
        
        # Neighborhood adjustment
        neighborhood = property_data.get('neighborhood', 'Unknown')
        neighborhood_adjustments = {
            'Kolonaki': 0.01, 'Plaka': 0.015, 'Koukaki': 0.02,
            'Exarchia': 0.025, 'Kifisia': 0.005
        }
        neighborhood_adjustment = neighborhood_adjustments.get(neighborhood, 0.0)
        
        final_return = base_return + energy_adjustment + risk_adjustment + neighborhood_adjustment
        
        return max(0.05, min(0.40, final_return))  # Cap between 5% and 40%
    
    def _calculate_portfolio_metrics(self, properties: List[Dict], budget: float, template: Dict) -> Dict:
        """Calculate comprehensive portfolio performance metrics."""
        
        if not properties:
            return {}
        
        total_invested = sum(p['total_cost'] for p in properties)
        weighted_returns = sum(p['total_cost'] * p['expected_annual_return'] for p in properties)
        portfolio_return = weighted_returns / total_invested if total_invested > 0 else 0
        
        # Calculate risk metrics
        property_returns = [p['expected_annual_return'] for p in properties]
        portfolio_volatility = np.std(property_returns) if len(property_returns) > 1 else 0
        
        # Calculate Sharpe ratio (simplified, assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Expected portfolio value after holding period
        holding_period = template.get('holding_period', 5)
        expected_portfolio_value = total_invested * (1 + portfolio_return) ** holding_period
        
        metrics = {
            'portfolio_expected_return': portfolio_return,
            'portfolio_volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_invested': total_invested,
            'budget_utilization': total_invested / budget if budget > 0 else 0,
            'holding_period': holding_period,
            'expected_portfolio_value': expected_portfolio_value,
            'expected_profit': expected_portfolio_value - total_invested,
            'expected_roi_total': (expected_portfolio_value - total_invested) / total_invested if total_invested > 0 else 0,
            'properties_count': len(properties),
            'average_property_value': total_invested / len(properties) if properties else 0
        }
        
        return metrics
    
    def _calculate_diversification_score(self, properties: List[Dict]) -> float:
        """Calculate portfolio diversification score (0-10)."""
        
        if not properties:
            return 0
        
        # Geographic diversification
        neighborhoods = set(p['neighborhood'] for p in properties)
        geo_diversity = min(len(neighborhoods) / 3, 1.0) * 3  # Max 3 points for neighborhood diversity
        
        # Energy class diversification
        energy_classes = set(p['energy_class'] for p in properties)
        energy_diversity = min(len(energy_classes) / 4, 1.0) * 2  # Max 2 points
        
        # Size diversification
        sizes = [p['sqm'] for p in properties]
        if sizes:
            size_cv = np.std(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 0
            size_diversity = min(size_cv / 0.3, 1.0) * 2  # Max 2 points for size variation
        else:
            size_diversity = 0
        
        # Price diversification
        prices = [p['price'] for p in properties]
        if prices:
            price_cv = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
            price_diversity = min(price_cv / 0.4, 1.0) * 3  # Max 3 points for price variation
        else:
            price_diversity = 0
        
        total_score = geo_diversity + energy_diversity + size_diversity + price_diversity
        
        return min(10, max(0, total_score))
    
    def _create_implementation_timeline(self, properties: List[Dict]) -> List[Dict]:
        """Create implementation timeline for portfolio acquisition."""
        
        timeline = []
        
        # Sort properties by priority (score and strategic importance)
        sorted_properties = sorted(properties, key=lambda x: x['portfolio_score'], reverse=True)
        
        for i, property_info in enumerate(sorted_properties):
            timeline_entry = {
                'sequence': i + 1,
                'property_id': property_info['property_id'],
                'timeline_weeks': (i + 1) * 2,  # 2 weeks between acquisitions
                'priority': 'High' if i < 2 else 'Medium' if i < 4 else 'Low',
                'acquisition_strategy': self._get_acquisition_strategy(property_info),
                'financing_approach': 'Cash' if property_info['price'] < 200000 else 'Mortgage',
                'due_diligence_items': self._get_due_diligence_items(property_info)
            }
            timeline.append(timeline_entry)
        
        return timeline
    
    def _get_acquisition_strategy(self, property_info: Dict) -> str:
        """Get specific acquisition strategy for property."""
        
        energy_class = property_info.get('energy_class', 'C')
        price = property_info.get('price', 0)
        
        if energy_class in ['D', 'E', 'F', 'G']:
            return "Energy Arbitrage - Negotiate based on retrofit potential"
        elif price > 500000:
            return "Premium Acquisition - Focus on location and condition"
        else:
            return "Value Investment - Negotiate on price and terms"
    
    def _get_due_diligence_items(self, property_info: Dict) -> List[str]:
        """Get due diligence checklist for property."""
        
        items = [
            "Legal title verification",
            "Building permit compliance",
            "Energy certificate validation",
            "Structural condition assessment",
            "Market comparable analysis"
        ]
        
        energy_class = property_info.get('energy_class', 'C')
        if energy_class in ['D', 'E', 'F', 'G']:
            items.extend([
                "Retrofit feasibility study",
                "Energy upgrade cost estimation",
                "Permit requirements for renovations"
            ])
        
        if property_info.get('sqm', 0) > 100:
            items.append("Commercial conversion potential assessment")
        
        return items
    
    def _create_strategy_portfolios(self, df: pd.DataFrame, investor_profile: Dict) -> Dict:
        """Create strategy-specific portfolio recommendations."""
        
        budget = investor_profile.get('budget', 500000)
        
        strategy_portfolios = {}
        
        for strategy_name, strategy_config in self.strategy_frameworks.items():
            portfolio = self._create_strategy_specific_portfolio(
                df, budget, strategy_name, strategy_config, investor_profile
            )
            strategy_portfolios[strategy_name] = portfolio
        
        return strategy_portfolios
    
    def _create_strategy_specific_portfolio(self, df: pd.DataFrame, budget: float, strategy_name: str, strategy_config: Dict, investor_profile: Dict) -> Dict:
        """Create portfolio for specific investment strategy."""
        
        filtered_properties = self._filter_properties_for_strategy(df, strategy_config)
        
        if len(filtered_properties) == 0:
            return {
                'strategy_name': strategy_name,
                'error': 'No suitable properties found for this strategy'
            }
        
        # Score and select properties
        selected_properties = []
        total_cost = 0
        remaining_budget = budget
        
        for idx, property_data in filtered_properties.head(10).iterrows():
            property_price = property_data.get('price', 0)
            strategy_cost = self._calculate_strategy_cost(property_price, strategy_config)
            
            if strategy_cost <= remaining_budget:
                property_info = {
                    'property_id': property_data.get('property_id', f'prop_{idx}'),
                    'neighborhood': property_data.get('neighborhood', 'Unknown'),
                    'price': property_price,
                    'sqm': property_data.get('sqm', 0),
                    'energy_class': property_data.get('energy_class', 'C'),
                    'strategy_cost': strategy_cost,
                    'expected_return': self._calculate_strategy_return(property_data, strategy_config),
                    'timeline_months': strategy_config.get('timeline_months', 12),
                    'strategy_specific_analysis': self._get_strategy_analysis(property_data, strategy_config)
                }
                
                selected_properties.append(property_info)
                total_cost += strategy_cost
                remaining_budget -= strategy_cost
                
                if len(selected_properties) >= 3 or remaining_budget < 100000:
                    break
        
        portfolio = {
            'strategy_name': strategy_name,
            'description': strategy_config['description'],
            'total_budget': budget,
            'total_invested': total_cost,
            'properties': selected_properties,
            'expected_portfolio_return': self._calculate_strategy_portfolio_return(selected_properties),
            'risk_factors': strategy_config.get('risk_factors', []),
            'implementation_plan': self._create_strategy_implementation_plan(selected_properties, strategy_config)
        }
        
        return portfolio
    
    def _filter_properties_for_strategy(self, df: pd.DataFrame, strategy_config: Dict) -> pd.DataFrame:
        """Filter properties suitable for specific investment strategy."""
        
        filtered_df = df.copy()
        
        # Filter by target energy classes
        if 'target_energy_classes' in strategy_config:
            target_classes = strategy_config['target_energy_classes']
            filtered_df = filtered_df[filtered_df['energy_class'].isin(target_classes)]
        
        # Filter by neighborhoods
        if 'target_neighborhoods' in strategy_config:
            target_neighborhoods = strategy_config['target_neighborhoods']
            filtered_df = filtered_df[filtered_df['neighborhood'].isin(target_neighborhoods)]
        
        # Filter by minimum energy class
        if 'minimum_energy_class' in strategy_config:
            min_energy = strategy_config['minimum_energy_class']
            energy_order = ['G', 'F', 'E', 'D', 'C', 'B', 'B+', 'A', 'A+']
            min_index = energy_order.index(min_energy)
            valid_classes = energy_order[min_index:]
            filtered_df = filtered_df[filtered_df['energy_class'].isin(valid_classes)]
        
        # Filter by property types
        if 'property_types' in strategy_config:
            target_types = strategy_config['property_types']
            if 'property_type' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['property_type'].isin(target_types)]
        
        return filtered_df
    
    def _calculate_strategy_cost(self, property_price: float, strategy_config: Dict) -> float:
        """Calculate total cost including strategy-specific costs."""
        
        transaction_cost = property_price * 0.08  # Standard transaction costs
        strategy_cost = 0
        
        # Add strategy-specific costs
        if 'retrofit_budget_percentage' in strategy_config:
            retrofit_cost = property_price * strategy_config['retrofit_budget_percentage']
            strategy_cost += retrofit_cost
        
        return property_price + transaction_cost + strategy_cost
    
    def _calculate_strategy_return(self, property_data: Dict, strategy_config: Dict) -> float:
        """Calculate expected return for strategy-specific property."""
        
        if 'expected_value_increase' in strategy_config:
            return strategy_config['expected_value_increase']
        elif 'expected_appreciation' in strategy_config:
            return strategy_config['expected_appreciation']
        elif 'expected_return_multiple' in strategy_config:
            return strategy_config['expected_return_multiple'] - 1.0  # Convert multiple to return
        else:
            return 0.20  # Default 20% return
    
    def _get_strategy_analysis(self, property_data: Dict, strategy_config: Dict) -> Dict:
        """Get strategy-specific analysis for property."""
        
        analysis = {
            'strategy_fit_score': 8.0,  # Base score
            'implementation_complexity': 'Medium',
            'timeline_risk': 'Low'
        }
        
        # Customize based on strategy type
        if 'retrofit_budget_percentage' in strategy_config:
            energy_class = property_data.get('energy_class', 'C')
            if energy_class in ['E', 'F', 'G']:
                analysis['retrofit_potential'] = 'High'
                analysis['value_uplift_potential'] = 'Significant'
            else:
                analysis['retrofit_potential'] = 'Medium'
                analysis['value_uplift_potential'] = 'Moderate'
        
        return analysis
    
    def _calculate_strategy_portfolio_return(self, properties: List[Dict]) -> float:
        """Calculate expected return for strategy portfolio."""
        
        if not properties:
            return 0
        
        weighted_returns = sum(p['strategy_cost'] * p['expected_return'] for p in properties)
        total_investment = sum(p['strategy_cost'] for p in properties)
        
        return weighted_returns / total_investment if total_investment > 0 else 0
    
    def _create_strategy_implementation_plan(self, properties: List[Dict], strategy_config: Dict) -> List[Dict]:
        """Create implementation plan for strategy."""
        
        plan = []
        
        for i, prop in enumerate(properties):
            step = {
                'sequence': i + 1,
                'property_id': prop['property_id'],
                'phase': 'Acquisition' if i < len(properties) / 2 else 'Implementation',
                'timeline_months': prop['timeline_months'],
                'key_milestones': self._get_strategy_milestones(prop, strategy_config),
                'success_metrics': self._get_success_metrics(prop, strategy_config)
            }
            plan.append(step)
        
        return plan
    
    def _get_strategy_milestones(self, property_info: Dict, strategy_config: Dict) -> List[str]:
        """Get key milestones for strategy implementation."""
        
        milestones = [
            "Property acquisition completed",
            "Due diligence finalized",
            "Financing secured"
        ]
        
        if 'retrofit_budget_percentage' in strategy_config:
            milestones.extend([
                "Retrofit design completed",
                "Permits obtained",
                "Construction completed",
                "Energy certificate updated"
            ])
        
        if 'target_rental_yield' in strategy_config:
            milestones.extend([
                "Property prepared for rental",
                "Tenant acquired",
                "Rental income stabilized"
            ])
        
        milestones.append("Exit strategy executed")
        
        return milestones
    
    def _get_success_metrics(self, property_info: Dict, strategy_config: Dict) -> Dict:
        """Get success metrics for strategy."""
        
        metrics = {
            'target_return': property_info['expected_return'],
            'timeline_target': property_info['timeline_months'],
            'budget_target': property_info['strategy_cost']
        }
        
        if 'target_rental_yield' in strategy_config:
            metrics['rental_yield_target'] = strategy_config['target_rental_yield']
        
        if 'expected_value_increase' in strategy_config:
            metrics['value_increase_target'] = strategy_config['expected_value_increase']
        
        return metrics
    
    def _analyze_portfolio_risks(self, portfolio_recommendations: Dict, strategy_portfolios: Dict) -> Dict:
        """Analyze risks across all portfolio recommendations."""
        
        risk_analysis = {
            'portfolio_risks': {},
            'strategy_risks': {},
            'overall_risk_assessment': {},
            'risk_mitigation_recommendations': []
        }
        
        # Analyze standard portfolio risks
        for risk_level, portfolio in portfolio_recommendations.items():
            if 'error' not in portfolio:
                risks = self._analyze_single_portfolio_risk(portfolio)
                risk_analysis['portfolio_risks'][risk_level] = risks
        
        # Analyze strategy-specific risks
        for strategy_name, portfolio in strategy_portfolios.items():
            if 'error' not in portfolio:
                risks = self._analyze_strategy_risk(portfolio)
                risk_analysis['strategy_risks'][strategy_name] = risks
        
        # Overall risk assessment
        risk_analysis['overall_risk_assessment'] = self._create_overall_risk_assessment(
            risk_analysis['portfolio_risks'], risk_analysis['strategy_risks']
        )
        
        # Risk mitigation recommendations
        risk_analysis['risk_mitigation_recommendations'] = self._create_risk_mitigation_recommendations()
        
        return risk_analysis
    
    def _analyze_single_portfolio_risk(self, portfolio: Dict) -> Dict:
        """Analyze risk factors for a single portfolio."""
        
        properties = portfolio.get('properties', [])
        
        # Geographic concentration risk
        neighborhoods = [p['neighborhood'] for p in properties]
        geo_concentration = max([neighborhoods.count(n) / len(neighborhoods) for n in set(neighborhoods)]) if neighborhoods else 0
        
        # Energy class concentration risk
        energy_classes = [p['energy_class'] for p in properties]
        energy_concentration = max([energy_classes.count(e) / len(energy_classes) for e in set(energy_classes)]) if energy_classes else 0
        
        # Portfolio size risk
        portfolio_size_risk = 'High' if len(properties) < 2 else 'Medium' if len(properties) < 4 else 'Low'
        
        # Budget utilization risk
        budget_util = portfolio.get('total_invested', 0) / portfolio.get('total_budget', 1)
        budget_risk = 'High' if budget_util > 0.95 else 'Medium' if budget_util > 0.8 else 'Low'
        
        return {
            'geographic_concentration_risk': 'High' if geo_concentration > 0.6 else 'Medium' if geo_concentration > 0.4 else 'Low',
            'energy_concentration_risk': 'High' if energy_concentration > 0.7 else 'Medium' if energy_concentration > 0.5 else 'Low',
            'portfolio_size_risk': portfolio_size_risk,
            'budget_utilization_risk': budget_risk,
            'diversification_score': portfolio.get('diversification_score', 5.0),
            'overall_risk_score': self._calculate_overall_risk_score(geo_concentration, energy_concentration, len(properties), budget_util)
        }
    
    def _analyze_strategy_risk(self, portfolio: Dict) -> Dict:
        """Analyze risks specific to investment strategy."""
        
        strategy_name = portfolio.get('strategy_name', 'unknown')
        risk_factors = portfolio.get('risk_factors', [])
        
        return {
            'strategy_specific_risks': risk_factors,
            'implementation_complexity': 'High' if 'retrofit' in strategy_name else 'Medium',
            'market_timing_sensitivity': 'High' if 'arbitrage' in strategy_name else 'Medium',
            'regulatory_risk': 'High' if 'development' in strategy_name else 'Low'
        }
    
    def _calculate_overall_risk_score(self, geo_conc: float, energy_conc: float, property_count: int, budget_util: float) -> float:
        """Calculate overall portfolio risk score (0-10, higher is riskier)."""
        
        risk_score = 0
        
        # Geographic concentration
        risk_score += geo_conc * 3
        
        # Energy concentration
        risk_score += energy_conc * 2
        
        # Portfolio size (fewer properties = higher risk)
        if property_count == 1:
            risk_score += 3
        elif property_count < 3:
            risk_score += 2
        elif property_count < 5:
            risk_score += 1
        
        # Budget utilization
        if budget_util > 0.95:
            risk_score += 2
        elif budget_util > 0.8:
            risk_score += 1
        
        return min(10, max(0, risk_score))
    
    def _create_overall_risk_assessment(self, portfolio_risks: Dict, strategy_risks: Dict) -> Dict:
        """Create overall risk assessment across all portfolios."""
        
        return {
            'recommended_risk_level': self._determine_recommended_risk_level(portfolio_risks),
            'key_risk_factors': self._identify_key_risk_factors(portfolio_risks, strategy_risks),
            'risk_reward_summary': self._create_risk_reward_summary(portfolio_risks)
        }
    
    def _determine_recommended_risk_level(self, portfolio_risks: Dict) -> str:
        """Determine recommended risk level based on analysis."""
        
        if not portfolio_risks:
            return 'balanced'
        
        # Evaluate risk scores
        risk_scores = []
        for risk_level, risks in portfolio_risks.items():
            if 'overall_risk_score' in risks:
                risk_scores.append((risk_level, risks['overall_risk_score']))
        
        if not risk_scores:
            return 'balanced'
        
        # Find the risk level with best risk-adjusted returns
        best_risk_level = min(risk_scores, key=lambda x: x[1])[0]
        
        return best_risk_level
    
    def _identify_key_risk_factors(self, portfolio_risks: Dict, strategy_risks: Dict) -> List[str]:
        """Identify key risk factors across all portfolios."""
        
        risk_factors = []
        
        # Common portfolio risks
        high_geo_concentration = any(
            risks.get('geographic_concentration_risk') == 'High' 
            for risks in portfolio_risks.values()
        )
        if high_geo_concentration:
            risk_factors.append("Geographic concentration in specific neighborhoods")
        
        high_energy_concentration = any(
            risks.get('energy_concentration_risk') == 'High' 
            for risks in portfolio_risks.values()
        )
        if high_energy_concentration:
            risk_factors.append("Energy class concentration risk")
        
        # Strategy-specific risks
        strategy_risk_factors = set()
        for strategy_portfolio in strategy_risks.values():
            strategy_risk_factors.update(strategy_portfolio.get('strategy_specific_risks', []))
        
        risk_factors.extend(list(strategy_risk_factors)[:3])  # Top 3 strategy risks
        
        return risk_factors
    
    def _create_risk_reward_summary(self, portfolio_risks: Dict) -> Dict:
        """Create risk-reward summary for portfolios."""
        
        summary = {}
        
        for risk_level, risks in portfolio_risks.items():
            summary[risk_level] = {
                'risk_score': risks.get('overall_risk_score', 5.0),
                'diversification_score': risks.get('diversification_score', 5.0),
                'recommendation': self._get_risk_level_recommendation(risks)
            }
        
        return summary
    
    def _get_risk_level_recommendation(self, risks: Dict) -> str:
        """Get recommendation for specific risk level."""
        
        risk_score = risks.get('overall_risk_score', 5.0)
        diversification = risks.get('diversification_score', 5.0)
        
        if risk_score < 3 and diversification > 7:
            return "Recommended - Good risk-reward balance"
        elif risk_score < 5 and diversification > 5:
            return "Suitable - Acceptable risk level"
        else:
            return "Consider with caution - Higher risk profile"
    
    def _create_risk_mitigation_recommendations(self) -> List[str]:
        """Create general risk mitigation recommendations."""
        
        return [
            "Diversify across at least 3 different neighborhoods",
            "Mix energy efficiency classes to balance retrofit and premium opportunities",
            "Maintain 20% cash buffer for unexpected costs and opportunities",
            "Consider staggered acquisition timeline to reduce market timing risk",
            "Obtain comprehensive insurance coverage for all properties",
            "Establish relationships with reliable contractors for energy retrofits",
            "Monitor regulatory changes affecting energy efficiency requirements",
            "Implement professional property management for rental properties",
            "Regular portfolio rebalancing and performance monitoring",
            "Exit strategy planning and market timing optimization"
        ]
    
    def _compare_portfolios(self, portfolio_recommendations: Dict, strategy_portfolios: Dict) -> Dict:
        """Compare all portfolio options and provide recommendations."""
        
        comparison = {
            'portfolio_ranking': [],
            'best_overall_portfolio': '',
            'best_risk_adjusted_portfolio': '',
            'comparison_matrix': {},
            'selection_guidance': {}
        }
        
        # Combine all portfolios for comparison
        all_portfolios = {}
        
        # Add standard portfolios
        for risk_level, portfolio in portfolio_recommendations.items():
            if 'error' not in portfolio:
                all_portfolios[f"standard_{risk_level}"] = portfolio
        
        # Add strategy portfolios
        for strategy_name, portfolio in strategy_portfolios.items():
            if 'error' not in portfolio:
                all_portfolios[f"strategy_{strategy_name}"] = portfolio
        
        # Rank portfolios
        portfolio_scores = []
        for name, portfolio in all_portfolios.items():
            score = self._calculate_portfolio_score(portfolio)
            portfolio_scores.append((name, score, portfolio))
        
        # Sort by score
        portfolio_scores.sort(key=lambda x: x[1], reverse=True)
        comparison['portfolio_ranking'] = [
            {
                'name': name,
                'score': score,
                'type': 'Standard Portfolio' if name.startswith('standard_') else 'Strategy Portfolio'
            }
            for name, score, _ in portfolio_scores
        ]
        
        if portfolio_scores:
            comparison['best_overall_portfolio'] = portfolio_scores[0][0]
        
        # Create comparison matrix
        comparison['comparison_matrix'] = self._create_comparison_matrix(all_portfolios)
        
        # Selection guidance
        comparison['selection_guidance'] = self._create_selection_guidance(all_portfolios)
        
        return comparison
    
    def _calculate_portfolio_score(self, portfolio: Dict) -> float:
        """Calculate composite score for portfolio comparison."""
        
        score = 0
        
        # Return potential
        if 'portfolio_metrics' in portfolio:
            expected_return = portfolio['portfolio_metrics'].get('portfolio_expected_return', 0)
            score += expected_return * 30  # Weight return heavily
        
        if 'expected_portfolio_return' in portfolio:
            expected_return = portfolio.get('expected_portfolio_return', 0)
            score += expected_return * 30
        
        # Risk adjustment
        diversification = portfolio.get('diversification_score', 5)
        score += diversification * 2
        
        # Budget utilization
        if 'total_budget' in portfolio and 'total_invested' in portfolio:
            budget_util = portfolio['total_invested'] / portfolio['total_budget']
            if 0.7 <= budget_util <= 0.9:  # Optimal range
                score += 5
        
        # Property count (diversification)
        property_count = len(portfolio.get('properties', []))
        if property_count >= 3:
            score += 3
        elif property_count >= 2:
            score += 1
        
        return min(100, max(0, score))
    
    def _create_comparison_matrix(self, all_portfolios: Dict) -> Dict:
        """Create comparison matrix of portfolio characteristics."""
        
        matrix = {}
        
        for name, portfolio in all_portfolios.items():
            properties = portfolio.get('properties', [])
            
            matrix[name] = {
                'property_count': len(properties),
                'total_investment': portfolio.get('total_invested', 0),
                'expected_return': portfolio.get('portfolio_metrics', {}).get('portfolio_expected_return', 
                                               portfolio.get('expected_portfolio_return', 0)),
                'diversification_score': portfolio.get('diversification_score', 0),
                'risk_level': portfolio.get('risk_level', 'medium'),
                'neighborhoods': len(set(p['neighborhood'] for p in properties)) if properties else 0,
                'energy_classes': len(set(p['energy_class'] for p in properties)) if properties else 0
            }
        
        return matrix
    
    def _create_selection_guidance(self, all_portfolios: Dict) -> Dict:
        """Create guidance for portfolio selection."""
        
        guidance = {
            'for_risk_averse_investors': self._find_best_for_risk_profile(all_portfolios, 'conservative'),
            'for_growth_investors': self._find_best_for_risk_profile(all_portfolios, 'aggressive'),
            'for_income_investors': self._find_best_for_objective(all_portfolios, 'rental_yield'),
            'for_first_time_investors': self._find_best_for_profile(all_portfolios, 'beginner'),
            'general_recommendations': [
                "Consider starting with balanced portfolio for first investment",
                "Energy arbitrage strategy offers highest returns but requires renovation expertise",
                "Premium portfolio suitable for investors seeking stable, long-term appreciation",
                "Diversify across multiple neighborhoods to reduce location-specific risks"
            ]
        }
        
        return guidance
    
    def _find_best_for_risk_profile(self, portfolios: Dict, risk_profile: str) -> str:
        """Find best portfolio for specific risk profile."""
        
        if risk_profile == 'conservative':
            # Prefer portfolios with high diversification and lower volatility
            best_portfolio = max(
                portfolios.keys(),
                key=lambda x: portfolios[x].get('diversification_score', 0)
            )
        else:  # aggressive
            # Prefer portfolios with high expected returns
            best_portfolio = max(
                portfolios.keys(),
                key=lambda x: portfolios[x].get('portfolio_metrics', {}).get('portfolio_expected_return', 
                                            portfolios[x].get('expected_portfolio_return', 0))
            )
        
        return best_portfolio
    
    def _find_best_for_objective(self, portfolios: Dict, objective: str) -> str:
        """Find best portfolio for specific investment objective."""
        
        if objective == 'rental_yield':
            # Look for strategy portfolios focused on rental yield
            rental_portfolios = [k for k in portfolios.keys() if 'rental_yield' in k]
            if rental_portfolios:
                return rental_portfolios[0]
        
        # Default to best overall
        return max(portfolios.keys(), key=lambda x: self._calculate_portfolio_score(portfolios[x]))
    
    def _find_best_for_profile(self, portfolios: Dict, profile: str) -> str:
        """Find best portfolio for specific investor profile."""
        
        if profile == 'beginner':
            # Prefer simpler, more diversified portfolios
            standard_portfolios = [k for k in portfolios.keys() if k.startswith('standard_')]
            if standard_portfolios:
                return max(standard_portfolios, key=lambda x: portfolios[x].get('diversification_score', 0))
        
        # Default to balanced
        balanced_options = [k for k in portfolios.keys() if 'balanced' in k]
        return balanced_options[0] if balanced_options else list(portfolios.keys())[0]
    
    def _create_implementation_guide(self, portfolio_recommendations: Dict) -> Dict:
        """Create implementation guide for selected portfolios."""
        
        guide = {
            'preparation_steps': [
                "Secure financing pre-approval for target budget",
                "Establish legal entity for property investments (if applicable)",
                "Set up property management infrastructure",
                "Identify reliable legal, technical, and financial advisors",
                "Create property acquisition checklist and due diligence process"
            ],
            'acquisition_process': [
                "Property identification and initial screening",
                "Financial analysis and ROI calculation",
                "Property inspection and technical due diligence",
                "Legal due diligence and title verification",
                "Negotiation and purchase agreement",
                "Financing finalization and closing process",
                "Property registration and insurance setup"
            ],
            'post_acquisition': [
                "Property condition assessment and immediate repairs",
                "Energy efficiency improvements (if applicable)",
                "Rental preparation and tenant acquisition (if rental strategy)",
                "Property management system setup",
                "Regular performance monitoring and reporting",
                "Market value tracking and exit strategy planning"
            ],
            'timeline_milestones': self._create_implementation_milestones(),
            'success_metrics': [
                "Portfolio assembly completion within target timeline",
                "Total investment within 5% of budget",
                "Minimum diversification score of 6.0",
                "First year rental yield above 5% (for rental properties)",
                "Energy retrofit completion within 6 months (if applicable)",
                "Portfolio value appreciation tracking above market average"
            ]
        }
        
        return guide
    
    def _create_implementation_milestones(self) -> List[Dict]:
        """Create implementation timeline milestones."""
        
        return [
            {
                'milestone': 'Planning and Preparation Complete',
                'target_timeline': 'Month 1',
                'key_activities': ['Financing secured', 'Team assembled', 'Market research completed']
            },
            {
                'milestone': 'First Property Acquired',
                'target_timeline': 'Month 2-3',
                'key_activities': ['Due diligence completed', 'Purchase finalized', 'Immediate improvements started']
            },
            {
                'milestone': 'Core Portfolio Assembled',
                'target_timeline': 'Month 6',
                'key_activities': ['3+ properties acquired', 'Diversification targets met', 'Management systems operational']
            },
            {
                'milestone': 'Value Enhancement Complete',
                'target_timeline': 'Month 12',
                'key_activities': ['Energy improvements completed', 'Rental operations optimized', 'Portfolio performance tracking established']
            },
            {
                'milestone': 'Portfolio Optimization',
                'target_timeline': 'Month 18-24',
                'key_activities': ['Performance review completed', 'Rebalancing decisions made', 'Exit strategies refined']
            }
        ]