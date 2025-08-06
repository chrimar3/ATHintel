"""
ROI Calculator Engine
====================

Advanced ROI calculation with multiple scenarios including:
- Conservative, moderate, and aggressive scenarios
- Capital appreciation modeling
- Rental yield optimization
- Total return on investment calculations
- Sensitivity analysis and Monte Carlo simulations
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class ROICalculatorEngine:
    """
    Comprehensive ROI calculation engine with multiple scenarios and sensitivity analysis.
    """
    
    def __init__(self):
        self.scenario_parameters = {
            'conservative': {
                'annual_appreciation': 0.03,  # 3% per year
                'rental_yield': 0.04,         # 4% gross yield
                'vacancy_rate': 0.15,         # 15% vacancy
                'maintenance_cost': 0.02,     # 2% of property value
                'management_fee': 0.08,       # 8% of rental income
                'transaction_cost': 0.08      # 8% buying/selling costs
            },
            'moderate': {
                'annual_appreciation': 0.05,  # 5% per year
                'rental_yield': 0.055,        # 5.5% gross yield
                'vacancy_rate': 0.10,         # 10% vacancy
                'maintenance_cost': 0.015,    # 1.5% of property value
                'management_fee': 0.06,       # 6% of rental income
                'transaction_cost': 0.06      # 6% buying/selling costs
            },
            'aggressive': {
                'annual_appreciation': 0.08,  # 8% per year
                'rental_yield': 0.07,         # 7% gross yield
                'vacancy_rate': 0.05,         # 5% vacancy
                'maintenance_cost': 0.01,     # 1% of property value
                'management_fee': 0.04,       # 4% of rental income
                'transaction_cost': 0.04      # 4% buying/selling costs
            }
        }
        
        self.energy_efficiency_multipliers = {
            'A+': 1.15,  # 15% premium for A+ properties
            'A': 1.12,   # 12% premium
            'B+': 1.08,  # 8% premium
            'B': 1.05,   # 5% premium
            'C': 1.00,   # Baseline
            'D': 0.95,   # 5% discount
            'E': 0.88,   # 12% discount
            'F': 0.80,   # 20% discount
            'G': 0.75    # 25% discount
        }
    
    def calculate_scenarios(self, property_data: List[Dict], investment_params: Dict) -> Dict:
        """
        Calculate ROI for all scenarios across property portfolio.
        
        Args:
            property_data: List of property dictionaries
            investment_params: Investment parameters and constraints
            
        Returns:
            Dict: Comprehensive ROI analysis results
        """
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_properties': len(property_data),
            'investment_parameters': investment_params,
            'scenario_results': {},
            'portfolio_summary': {},
            'sensitivity_analysis': {},
            'monte_carlo_simulation': {}
        }
        
        # Calculate ROI for each scenario
        for scenario_name, params in self.scenario_parameters.items():
            scenario_results = self._calculate_scenario_roi(property_data, params, investment_params)
            results['scenario_results'][scenario_name] = scenario_results
        
        # Generate portfolio summary
        results['portfolio_summary'] = self._generate_portfolio_summary(results['scenario_results'])
        
        # Run sensitivity analysis
        results['sensitivity_analysis'] = self._run_sensitivity_analysis(property_data, investment_params)
        
        # Monte Carlo simulation
        results['monte_carlo_simulation'] = self._run_monte_carlo_simulation(property_data, investment_params)
        
        return results
    
    def _calculate_scenario_roi(self, property_data: List[Dict], scenario_params: Dict, investment_params: Dict) -> Dict:
        """Calculate ROI for a specific scenario across all properties."""
        
        holding_period = investment_params.get('holding_period', 5)  # Default 5 years
        
        property_rois = []
        total_investment = 0
        total_returns = 0
        
        for property_info in property_data:
            roi_result = self._calculate_property_roi(property_info, scenario_params, holding_period)
            property_rois.append(roi_result)
            total_investment += roi_result['initial_investment']
            total_returns += roi_result['total_return']
        
        # Portfolio-level metrics
        portfolio_roi = (total_returns - total_investment) / total_investment if total_investment > 0 else 0
        annual_roi = (1 + portfolio_roi) ** (1/holding_period) - 1
        
        return {
            'scenario_name': scenario_params,
            'holding_period_years': holding_period,
            'property_count': len(property_data),
            'total_investment': total_investment,
            'total_returns': total_returns,
            'net_profit': total_returns - total_investment,
            'portfolio_roi': portfolio_roi,
            'annual_roi': annual_roi,
            'individual_properties': property_rois,
            'summary_statistics': self._calculate_summary_statistics(property_rois)
        }
    
    def _calculate_property_roi(self, property_info: Dict, scenario_params: Dict, holding_period: int) -> Dict:
        """Calculate detailed ROI for individual property."""
        
        purchase_price = property_info.get('price', 0)
        sqm = property_info.get('sqm', 0)
        energy_class = property_info.get('energy_class', 'C')
        neighborhood = property_info.get('neighborhood', 'Unknown')
        
        # Apply energy efficiency multiplier to rental yield
        energy_multiplier = self.energy_efficiency_multipliers.get(energy_class, 1.0)
        adjusted_rental_yield = scenario_params['rental_yield'] * energy_multiplier
        
        # Calculate transaction costs
        transaction_costs = purchase_price * scenario_params['transaction_cost']
        initial_investment = purchase_price + transaction_costs
        
        # Annual calculations
        annual_rental_income = purchase_price * adjusted_rental_yield
        annual_vacancy_loss = annual_rental_income * scenario_params['vacancy_rate']
        net_annual_rental = annual_rental_income - annual_vacancy_loss
        
        # Annual expenses
        annual_maintenance = purchase_price * scenario_params['maintenance_cost']
        annual_management = net_annual_rental * scenario_params['management_fee']
        annual_expenses = annual_maintenance + annual_management
        
        # Net annual cash flow
        annual_cash_flow = net_annual_rental - annual_expenses
        
        # Capital appreciation
        final_value = purchase_price * (1 + scenario_params['annual_appreciation']) ** holding_period
        selling_costs = final_value * scenario_params['transaction_cost']
        net_selling_proceeds = final_value - selling_costs
        
        # Total returns
        total_rental_income = annual_cash_flow * holding_period
        capital_gain = net_selling_proceeds - purchase_price
        total_return = total_rental_income + capital_gain
        
        # ROI calculations
        total_roi = (total_return - initial_investment) / initial_investment if initial_investment > 0 else 0
        annual_roi = (1 + total_roi) ** (1/holding_period) - 1
        
        # Cash-on-cash return (annual rental yield)
        cash_on_cash = annual_cash_flow / initial_investment if initial_investment > 0 else 0
        
        return {
            'property_id': property_info.get('property_id', 'unknown'),
            'neighborhood': neighborhood,
            'energy_class': energy_class,
            'purchase_price': purchase_price,
            'sqm': sqm,
            'initial_investment': initial_investment,
            'annual_rental_income': annual_rental_income,
            'annual_cash_flow': annual_cash_flow,
            'capital_appreciation': final_value - purchase_price,
            'total_return': total_return,
            'total_roi': total_roi,
            'annual_roi': annual_roi,
            'cash_on_cash_return': cash_on_cash,
            'investment_multiple': total_return / initial_investment if initial_investment > 0 else 0,
            'break_even_years': self._calculate_break_even(initial_investment, annual_cash_flow),
            'energy_efficiency_bonus': energy_multiplier - 1.0,
            'risk_adjusted_return': self._calculate_risk_adjusted_return(annual_roi, energy_class, neighborhood)
        }
    
    def _calculate_break_even(self, initial_investment: float, annual_cash_flow: float) -> Optional[float]:
        """Calculate break-even point in years."""
        if annual_cash_flow <= 0:
            return None
        return initial_investment / annual_cash_flow
    
    def _calculate_risk_adjusted_return(self, annual_roi: float, energy_class: str, neighborhood: str) -> float:
        """Calculate risk-adjusted return using simplified risk factors."""
        
        # Risk adjustments based on energy class
        energy_risk_factors = {
            'A+': 0.95, 'A': 0.97, 'B+': 0.98, 'B': 0.99, 'C': 1.0,
            'D': 1.05, 'E': 1.10, 'F': 1.15, 'G': 1.20
        }
        
        # Neighborhood risk (simplified)
        premium_neighborhoods = ['Kolonaki', 'Plaka', 'Koukaki', 'Thiseio']
        neighborhood_risk = 0.95 if neighborhood in premium_neighborhoods else 1.0
        
        total_risk_factor = energy_risk_factors.get(energy_class, 1.0) * neighborhood_risk
        
        return annual_roi / total_risk_factor
    
    def _calculate_summary_statistics(self, property_rois: List[Dict]) -> Dict:
        """Calculate summary statistics for property ROI results."""
        
        if not property_rois:
            return {}
        
        roi_values = [p['total_roi'] for p in property_rois]
        annual_roi_values = [p['annual_roi'] for p in property_rois]
        cash_flow_values = [p['annual_cash_flow'] for p in property_rois]
        
        return {
            'roi_statistics': {
                'mean': np.mean(roi_values),
                'median': np.median(roi_values),
                'std': np.std(roi_values),
                'min': np.min(roi_values),
                'max': np.max(roi_values),
                'percentile_25': np.percentile(roi_values, 25),
                'percentile_75': np.percentile(roi_values, 75)
            },
            'annual_roi_statistics': {
                'mean': np.mean(annual_roi_values),
                'median': np.median(annual_roi_values),
                'std': np.std(annual_roi_values)
            },
            'cash_flow_statistics': {
                'mean': np.mean(cash_flow_values),
                'median': np.median(cash_flow_values),
                'total': np.sum(cash_flow_values)
            },
            'positive_roi_count': sum(1 for roi in roi_values if roi > 0),
            'negative_roi_count': sum(1 for roi in roi_values if roi <= 0),
            'success_rate': sum(1 for roi in roi_values if roi > 0) / len(roi_values) if roi_values else 0
        }
    
    def _generate_portfolio_summary(self, scenario_results: Dict) -> Dict:
        """Generate portfolio-level summary across all scenarios."""
        
        summary = {
            'scenario_comparison': {},
            'best_scenario': '',
            'worst_scenario': '',
            'average_performance': {},
            'risk_return_profile': {}
        }
        
        scenario_performance = {}
        
        for scenario_name, results in scenario_results.items():
            performance = {
                'annual_roi': results['annual_roi'],
                'total_roi': results['portfolio_roi'],
                'success_rate': results['summary_statistics'].get('success_rate', 0),
                'risk_score': results['summary_statistics']['roi_statistics']['std'] if results['summary_statistics'] else 0
            }
            scenario_performance[scenario_name] = performance
            summary['scenario_comparison'][scenario_name] = performance
        
        # Identify best and worst scenarios
        if scenario_performance:
            summary['best_scenario'] = max(scenario_performance.keys(), 
                                         key=lambda x: scenario_performance[x]['annual_roi'])
            summary['worst_scenario'] = min(scenario_performance.keys(), 
                                          key=lambda x: scenario_performance[x]['annual_roi'])
        
        # Average performance
        if scenario_performance:
            summary['average_performance'] = {
                'annual_roi': np.mean([p['annual_roi'] for p in scenario_performance.values()]),
                'total_roi': np.mean([p['total_roi'] for p in scenario_performance.values()]),
                'success_rate': np.mean([p['success_rate'] for p in scenario_performance.values()])
            }
        
        return summary
    
    def _run_sensitivity_analysis(self, property_data: List[Dict], investment_params: Dict) -> Dict:
        """Run sensitivity analysis on key parameters."""
        
        base_params = self.scenario_parameters['moderate'].copy()
        sensitivity_results = {}
        
        # Parameters to test
        sensitivity_params = {
            'annual_appreciation': [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08],
            'rental_yield': [0.03, 0.04, 0.05, 0.055, 0.06, 0.07, 0.08],
            'vacancy_rate': [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20],
            'transaction_cost': [0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10]
        }
        
        for param_name, param_values in sensitivity_params.items():
            param_results = []
            
            for param_value in param_values:
                test_params = base_params.copy()
                test_params[param_name] = param_value
                
                # Calculate ROI with modified parameter
                scenario_result = self._calculate_scenario_roi(property_data, test_params, investment_params)
                
                param_results.append({
                    'parameter_value': param_value,
                    'annual_roi': scenario_result['annual_roi'],
                    'portfolio_roi': scenario_result['portfolio_roi']
                })
            
            sensitivity_results[param_name] = param_results
        
        return sensitivity_results
    
    def _run_monte_carlo_simulation(self, property_data: List[Dict], investment_params: Dict, num_simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation for ROI uncertainty analysis."""
        
        base_params = self.scenario_parameters['moderate'].copy()
        simulation_results = []
        
        # Parameter distributions (normal distribution parameters)
        param_distributions = {
            'annual_appreciation': {'mean': 0.05, 'std': 0.02},
            'rental_yield': {'mean': 0.055, 'std': 0.015},
            'vacancy_rate': {'mean': 0.10, 'std': 0.03},
            'maintenance_cost': {'mean': 0.015, 'std': 0.005},
            'transaction_cost': {'mean': 0.06, 'std': 0.01}
        }
        
        # Run simulations
        for _ in range(num_simulations):
            # Sample parameters from distributions
            sim_params = base_params.copy()
            
            for param_name, distribution in param_distributions.items():
                sampled_value = np.random.normal(distribution['mean'], distribution['std'])
                # Ensure positive values and reasonable bounds
                sim_params[param_name] = max(0.001, min(0.5, sampled_value))
            
            # Calculate ROI for this simulation
            scenario_result = self._calculate_scenario_roi(property_data, sim_params, investment_params)
            
            simulation_results.append({
                'annual_roi': scenario_result['annual_roi'],
                'portfolio_roi': scenario_result['portfolio_roi'],
                'parameters': sim_params
            })
        
        # Analyze simulation results
        annual_rois = [r['annual_roi'] for r in simulation_results]
        portfolio_rois = [r['portfolio_roi'] for r in simulation_results]
        
        monte_carlo_analysis = {
            'num_simulations': num_simulations,
            'annual_roi_distribution': {
                'mean': np.mean(annual_rois),
                'median': np.median(annual_rois),
                'std': np.std(annual_rois),
                'percentile_5': np.percentile(annual_rois, 5),
                'percentile_25': np.percentile(annual_rois, 25),
                'percentile_75': np.percentile(annual_rois, 75),
                'percentile_95': np.percentile(annual_rois, 95),
                'min': np.min(annual_rois),
                'max': np.max(annual_rois)
            },
            'portfolio_roi_distribution': {
                'mean': np.mean(portfolio_rois),
                'median': np.median(portfolio_rois),
                'std': np.std(portfolio_rois),
                'percentile_5': np.percentile(portfolio_rois, 5),
                'percentile_95': np.percentile(portfolio_rois, 95)
            },
            'probability_positive_returns': sum(1 for roi in annual_rois if roi > 0) / len(annual_rois),
            'probability_high_returns': sum(1 for roi in annual_rois if roi > 0.15) / len(annual_rois),  # >15% annual return
            'value_at_risk_5': np.percentile(annual_rois, 5),  # 5% VaR
            'expected_shortfall': np.mean([roi for roi in annual_rois if roi <= np.percentile(annual_rois, 5)])
        }
        
        return monte_carlo_analysis

    def generate_investment_recommendations(self, roi_results: Dict, top_n: int = 10) -> Dict:
        """Generate top investment recommendations based on ROI analysis."""
        
        recommendations = {
            'analysis_timestamp': datetime.now().isoformat(),
            'methodology': 'Risk-adjusted ROI with scenario analysis',
            'top_opportunities': [],
            'portfolio_allocation': {},
            'risk_warnings': [],
            'market_timing': {}
        }
        
        # Extract all properties from scenario results
        all_properties = []
        
        for scenario_name, scenario_result in roi_results['scenario_results'].items():
            for prop in scenario_result['individual_properties']:
                prop_copy = prop.copy()
                prop_copy['scenario'] = scenario_name
                all_properties.append(prop_copy)
        
        # Score and rank properties
        scored_properties = []
        for prop in all_properties:
            score = self._calculate_investment_score(prop)
            prop['investment_score'] = score
            scored_properties.append(prop)
        
        # Get top opportunities
        top_properties = sorted(scored_properties, key=lambda x: x['investment_score'], reverse=True)[:top_n]
        
        recommendations['top_opportunities'] = [
            {
                'rank': i + 1,
                'property_id': prop['property_id'],
                'neighborhood': prop['neighborhood'],
                'energy_class': prop['energy_class'],
                'purchase_price': prop['purchase_price'],
                'expected_annual_roi': prop['annual_roi'],
                'investment_score': prop['investment_score'],
                'scenario': prop['scenario'],
                'key_strengths': self._identify_property_strengths(prop),
                'investment_thesis': self._generate_investment_thesis(prop)
            }
            for i, prop in enumerate(top_properties)
        ]
        
        return recommendations
    
    def _calculate_investment_score(self, property_data: Dict) -> float:
        """Calculate composite investment score for property."""
        
        # Base score from ROI
        roi_score = min(10, property_data['annual_roi'] * 20)  # Scale to 0-10
        
        # Adjust for risk
        risk_adjustment = 1.0 / (1.0 + property_data.get('energy_efficiency_bonus', 0))
        
        # Adjust for cash flow
        cash_flow_score = min(2, property_data['cash_on_cash_return'] * 10) if property_data['cash_on_cash_return'] > 0 else 0
        
        # Combine scores
        final_score = (roi_score * 0.6 + cash_flow_score * 0.3) * risk_adjustment
        
        return min(10, max(0, final_score))
    
    def _identify_property_strengths(self, property_data: Dict) -> List[str]:
        """Identify key investment strengths of property."""
        
        strengths = []
        
        if property_data['annual_roi'] > 0.15:
            strengths.append("High ROI potential (>15% annually)")
        
        if property_data['cash_on_cash_return'] > 0.06:
            strengths.append("Strong cash flow (>6% annual yield)")
        
        if property_data['energy_class'] in ['A+', 'A', 'B+']:
            strengths.append("High energy efficiency")
        
        if property_data.get('break_even_years') and property_data['break_even_years'] < 10:
            strengths.append(f"Quick payback ({property_data['break_even_years']:.1f} years)")
        
        if property_data['investment_multiple'] > 2.0:
            strengths.append("Strong total return multiple")
        
        return strengths[:3]  # Top 3 strengths
    
    def _generate_investment_thesis(self, property_data: Dict) -> str:
        """Generate investment thesis for property."""
        
        roi_pct = property_data['annual_roi'] * 100
        neighborhood = property_data['neighborhood']
        energy_class = property_data['energy_class']
        price = property_data['purchase_price']
        
        thesis = f"€{price:,.0f} {energy_class}-class property in {neighborhood} "
        thesis += f"offering {roi_pct:.1f}% expected annual returns. "
        
        if property_data['energy_efficiency_bonus'] > 0:
            thesis += "Benefits from energy efficiency premium. "
        
        if property_data['cash_on_cash_return'] > 0.05:
            thesis += "Strong rental yield fundamentals. "
        
        thesis += "Recommended for immediate acquisition."
        
        return thesis