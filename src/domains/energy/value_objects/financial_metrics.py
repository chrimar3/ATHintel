"""
🏗️ Financial Metrics Value Object

Immutable value object for energy upgrade financial calculations
including ROI, NPV, IRR, and payback analysis.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
import math

@dataclass(frozen=True)
class FinancialMetrics:
    """
    Immutable financial metrics for energy upgrades
    
    Contains comprehensive financial analysis including:
    - Basic payback calculations
    - Net Present Value (NPV) analysis
    - Internal Rate of Return (IRR)
    - Risk-adjusted returns
    - Sensitivity analysis
    """
    
    # Basic financial metrics
    baseline_annual_cost: Decimal  # Current annual energy cost
    potential_annual_savings: Decimal  # Annual savings from upgrades
    upgrade_investment_required: Decimal  # Total investment needed
    simple_payback_years: Decimal  # Simple payback period
    
    # Advanced financial metrics
    net_present_value: Decimal  # NPV over 10 years at 3% discount
    internal_rate_of_return: Decimal  # IRR as percentage
    
    # Risk and sensitivity metrics
    discount_rate: Decimal = Decimal('0.03')  # 3% default discount rate
    analysis_period_years: int = 10  # 10-year analysis period
    energy_price_inflation: Decimal = Decimal('0.02')  # 2% annual energy price growth
    
    def __post_init__(self):
        """Validate financial metrics"""
        if self.baseline_annual_cost < 0:
            raise ValueError("Baseline annual cost cannot be negative")
        
        if self.potential_annual_savings < 0:
            raise ValueError("Potential annual savings cannot be negative")
        
        if self.upgrade_investment_required < 0:
            raise ValueError("Investment required cannot be negative")
    
    @property
    def roi_percentage(self) -> Decimal:
        """Simple ROI as percentage"""
        if self.upgrade_investment_required == 0:
            return Decimal('0')
        return (self.potential_annual_savings / self.upgrade_investment_required) * 100
    
    @property
    def savings_percentage(self) -> Decimal:
        """Savings as percentage of baseline cost"""
        if self.baseline_annual_cost == 0:
            return Decimal('0')
        return (self.potential_annual_savings / self.baseline_annual_cost) * 100
    
    def calculate_npv_detailed(self, years: int = None, discount_rate: Decimal = None) -> Dict[str, Decimal]:
        """Calculate detailed NPV analysis"""
        years = years or self.analysis_period_years
        discount_rate = discount_rate or self.discount_rate
        
        annual_cash_flows = []
        cumulative_npv = Decimal('0')
        
        for year in range(1, years + 1):
            # Apply energy price inflation to savings
            inflated_savings = self.potential_annual_savings * (
                (1 + self.energy_price_inflation) ** year
            )
            
            # Discount to present value
            discount_factor = (1 + discount_rate) ** year
            present_value = inflated_savings / discount_factor
            
            annual_cash_flows.append({
                'year': year,
                'nominal_savings': inflated_savings,
                'present_value': present_value,
                'discount_factor': discount_factor
            })
            
            cumulative_npv += present_value
        
        # Subtract initial investment
        net_npv = cumulative_npv - self.upgrade_investment_required
        
        return {
            'gross_present_value': cumulative_npv,
            'initial_investment': self.upgrade_investment_required,
            'net_present_value': net_npv,
            'profitability_index': cumulative_npv / self.upgrade_investment_required if self.upgrade_investment_required > 0 else Decimal('0'),
            'annual_cash_flows': annual_cash_flows
        }
    
    def calculate_irr(self) -> Decimal:
        """Calculate Internal Rate of Return using Newton's method"""
        if self.upgrade_investment_required == 0 or self.potential_annual_savings == 0:
            return Decimal('0')
        
        # Initial guess for IRR
        irr = Decimal('0.1')  # 10% starting guess
        tolerance = Decimal('0.0001')
        max_iterations = 100
        
        for _ in range(max_iterations):
            # Calculate NPV and its derivative at current IRR
            npv = -self.upgrade_investment_required
            npv_derivative = Decimal('0')
            
            for year in range(1, self.analysis_period_years + 1):
                # Apply energy price inflation
                inflated_savings = self.potential_annual_savings * (
                    (1 + self.energy_price_inflation) ** year
                )
                
                # Calculate cash flow present value and derivative
                discount_factor = (1 + irr) ** year
                npv += inflated_savings / discount_factor
                npv_derivative -= inflated_savings * year / ((1 + irr) ** (year + 1))
            
            # Newton's method iteration
            if abs(npv_derivative) < tolerance:
                break
                
            irr_new = irr - (npv / npv_derivative)
            
            if abs(irr_new - irr) < tolerance:
                return irr_new * 100  # Return as percentage
            
            irr = irr_new
        
        # If IRR calculation fails, return simple ROI estimate
        return self.roi_percentage
    
    def calculate_payback_analysis(self) -> Dict[str, Decimal]:
        """Calculate detailed payback analysis"""
        if self.potential_annual_savings == 0:
            return {
                'simple_payback': Decimal('999'),
                'discounted_payback': Decimal('999'),
                'break_even_year': Decimal('999')
            }
        
        # Simple payback
        simple_payback = self.upgrade_investment_required / self.potential_annual_savings
        
        # Discounted payback calculation
        remaining_investment = self.upgrade_investment_required
        discounted_payback = Decimal('0')
        
        for year in range(1, 21):  # Check up to 20 years
            # Apply inflation to savings
            inflated_savings = self.potential_annual_savings * (
                (1 + self.energy_price_inflation) ** year
            )
            
            # Discount to present value
            pv_savings = inflated_savings / ((1 + self.discount_rate) ** year)
            
            remaining_investment -= pv_savings
            
            if remaining_investment <= 0:
                # Linear interpolation for fractional year
                excess = -remaining_investment
                discounted_payback = year - (excess / pv_savings)
                break
        else:
            discounted_payback = Decimal('999')  # More than 20 years
        
        return {
            'simple_payback': simple_payback,
            'discounted_payback': discounted_payback,
            'break_even_year': min(simple_payback, discounted_payback)
        }
    
    def sensitivity_analysis(self) -> Dict[str, Dict[str, Decimal]]:
        """Perform sensitivity analysis on key variables"""
        scenarios = {
            'pessimistic': Decimal('-0.2'),  # 20% worse
            'realistic': Decimal('0.0'),     # Base case
            'optimistic': Decimal('0.2')     # 20% better
        }
        
        results = {}
        
        for scenario_name, adjustment in scenarios.items():
            # Adjust savings (costs can vary, efficiency gains can differ)
            adjusted_savings = self.potential_annual_savings * (1 + adjustment)
            
            # Adjust investment (construction costs can vary)
            adjusted_investment = self.upgrade_investment_required * (1 + adjustment * Decimal('0.5'))
            
            # Create temporary metrics for analysis
            adjusted_metrics = FinancialMetrics(
                baseline_annual_cost=self.baseline_annual_cost,
                potential_annual_savings=adjusted_savings,
                upgrade_investment_required=adjusted_investment,
                simple_payback_years=adjusted_investment / adjusted_savings if adjusted_savings > 0 else Decimal('999'),
                net_present_value=Decimal('0'),  # Will be calculated
                internal_rate_of_return=Decimal('0')  # Will be calculated
            )
            
            npv_analysis = adjusted_metrics.calculate_npv_detailed()
            payback_analysis = adjusted_metrics.calculate_payback_analysis()
            
            results[scenario_name] = {
                'annual_savings': adjusted_savings,
                'investment_required': adjusted_investment,
                'roi_percentage': adjusted_metrics.roi_percentage,
                'net_present_value': npv_analysis['net_present_value'],
                'simple_payback': payback_analysis['simple_payback'],
                'discounted_payback': payback_analysis['discounted_payback']
            }
        
        return results
    
    def risk_assessment(self) -> Dict[str, str]:
        """Assess investment risk level"""
        risk_factors = []
        risk_level = "LOW"
        
        # Payback period risk
        if self.simple_payback_years > 15:
            risk_factors.append("Long payback period")
            risk_level = "HIGH"
        elif self.simple_payback_years > 10:
            risk_factors.append("Moderate payback period")
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
        
        # ROI risk
        if self.roi_percentage < 5:
            risk_factors.append("Low return on investment")
            risk_level = "HIGH"
        elif self.roi_percentage < 10:
            risk_factors.append("Moderate return on investment")
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
        
        # Investment size risk (relative to savings)
        if self.upgrade_investment_required > self.baseline_annual_cost * 20:
            risk_factors.append("High investment relative to annual costs")
            risk_level = "HIGH"
        elif self.upgrade_investment_required > self.baseline_annual_cost * 10:
            risk_factors.append("Moderate investment relative to annual costs")
            risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
        
        # NPV risk
        if self.net_present_value < 0:
            risk_factors.append("Negative net present value")
            risk_level = "HIGH"
        
        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get investment recommendation based on risk level"""
        recommendations = {
            'LOW': "Excellent investment opportunity with low risk and strong returns",
            'MEDIUM': "Good investment with moderate risk - consider as part of phased approach",
            'HIGH': "High risk investment - careful evaluation and possibly smaller scope recommended"
        }
        return recommendations.get(risk_level, "Unable to assess risk")
    
    def compare_to_alternative_investments(self) -> Dict[str, Dict[str, Decimal]]:
        """Compare energy upgrade returns to alternative investments"""
        
        # Greek market alternatives (2025 estimates)
        alternatives = {
            'bank_deposit': {
                'annual_return_percentage': Decimal('2.5'),
                'risk_level': 'Very Low'
            },
            'government_bonds': {
                'annual_return_percentage': Decimal('3.2'),
                'risk_level': 'Low'
            },
            'real_estate_market': {
                'annual_return_percentage': Decimal('6.5'),
                'risk_level': 'Medium'
            },
            'stock_market_index': {
                'annual_return_percentage': Decimal('8.5'),
                'risk_level': 'High'
            }
        }
        
        comparison = {}
        energy_upgrade_return = self.roi_percentage
        
        for investment, data in alternatives.items():
            alt_return = data['annual_return_percentage']
            
            comparison[investment] = {
                'alternative_return': alt_return,
                'energy_upgrade_advantage': energy_upgrade_return - alt_return,
                'risk_level': data['risk_level'],
                'recommendation': (
                    "Energy upgrade preferred" if energy_upgrade_return > alt_return
                    else "Alternative investment preferred"
                )
            }
        
        return comparison
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        npv_analysis = self.calculate_npv_detailed()
        payback_analysis = self.calculate_payback_analysis()
        sensitivity = self.sensitivity_analysis()
        risk_assessment = self.risk_assessment()
        alternatives_comparison = self.compare_to_alternative_investments()
        
        return {
            'basic_metrics': {
                'baseline_annual_cost': float(self.baseline_annual_cost),
                'potential_annual_savings': float(self.potential_annual_savings),
                'upgrade_investment_required': float(self.upgrade_investment_required),
                'simple_payback_years': float(self.simple_payback_years),
                'roi_percentage': float(self.roi_percentage),
                'savings_percentage': float(self.savings_percentage)
            },
            'advanced_metrics': {
                'net_present_value': float(self.net_present_value),
                'internal_rate_of_return': float(self.internal_rate_of_return),
                'discount_rate': float(self.discount_rate),
                'analysis_period_years': self.analysis_period_years
            },
            'detailed_analysis': {
                'npv_analysis': {
                    'gross_present_value': float(npv_analysis['gross_present_value']),
                    'net_present_value': float(npv_analysis['net_present_value']),
                    'profitability_index': float(npv_analysis['profitability_index'])
                },
                'payback_analysis': {
                    'simple_payback': float(payback_analysis['simple_payback']),
                    'discounted_payback': float(payback_analysis['discounted_payback']),
                    'break_even_year': float(payback_analysis['break_even_year'])
                },
                'sensitivity_analysis': {
                    scenario: {k: float(v) for k, v in metrics.items()}
                    for scenario, metrics in sensitivity.items()
                }
            },
            'risk_assessment': risk_assessment,
            'investment_comparison': {
                investment: {
                    'alternative_return': float(data['alternative_return']),
                    'energy_upgrade_advantage': float(data['energy_upgrade_advantage']),
                    'risk_level': data['risk_level'],
                    'recommendation': data['recommendation']
                }
                for investment, data in alternatives_comparison.items()
            }
        }