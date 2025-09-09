"""
Investment Modeling Engine
=========================

Advanced investment modeling tools including:
- ROI calculators with multiple scenarios
- Cash flow projection models with rental yield optimization  
- Portfolio optimization algorithms (Monte Carlo simulation)
- Risk-adjusted return analysis (Sharpe ratio, Alpha, Beta)
- Market timing models and entry point optimization
- Tax optimization strategies for international investors
"""

from .roi_calculators import ROICalculatorEngine
from .cash_flow_models import CashFlowModelingEngine
from .portfolio_optimization import PortfolioOptimizationEngine
from .risk_analysis import RiskAnalysisEngine
from .market_timing import MarketTimingEngine
from .tax_optimization import TaxOptimizationEngine

class InvestmentModelingEngine:
    """
    Comprehensive investment modeling and analysis engine.
    """
    
    def __init__(self):
        self.roi_calculator = ROICalculatorEngine()
        self.cash_flow_modeler = CashFlowModelingEngine()
        self.portfolio_optimizer = PortfolioOptimizationEngine()
        self.risk_analyzer = RiskAnalysisEngine()
        self.market_timer = MarketTimingEngine()
        self.tax_optimizer = TaxOptimizationEngine()
    
    def run_comprehensive_modeling(self, property_data, investment_params):
        """Run comprehensive investment modeling analysis."""
        
        results = {
            'roi_analysis': self.roi_calculator.calculate_scenarios(property_data, investment_params),
            'cash_flow_projections': self.cash_flow_modeler.project_cash_flows(property_data, investment_params),
            'portfolio_optimization': self.portfolio_optimizer.optimize_portfolio(property_data, investment_params),
            'risk_analysis': self.risk_analyzer.analyze_risks(property_data, investment_params),
            'market_timing': self.market_timer.analyze_timing(property_data, investment_params),
            'tax_optimization': self.tax_optimizer.optimize_taxes(property_data, investment_params)
        }
        
        return results

__all__ = [
    'InvestmentModelingEngine',
    'ROICalculatorEngine',
    'CashFlowModelingEngine',
    'PortfolioOptimizationEngine', 
    'RiskAnalysisEngine',
    'MarketTimingEngine',
    'TaxOptimizationEngine'
]