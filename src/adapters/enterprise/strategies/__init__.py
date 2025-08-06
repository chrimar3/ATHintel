"""
Investment Strategies Engine
===========================

Comprehensive investment strategy implementation including:
- Pre-built investment portfolios by budget ($100K, $500K, $1M, $2M+)
- Diversification strategies across neighborhoods and property types
- Entry timing recommendations with market cycle analysis
- Exit strategies and holding period optimization
- Financing optimization and leverage strategies
- Legal framework and acquisition process guidance
"""

from .portfolio_strategies import PortfolioStrategiesEngine
from .timing_strategies import TimingStrategiesEngine
from .financing_strategies import FinancingStrategiesEngine
from .diversification_strategies import DiversificationStrategiesEngine
from .legal_framework import LegalFrameworkEngine

class InvestmentStrategiesEngine:
    """
    Main orchestrator for all investment strategies and recommendations.
    """
    
    def __init__(self):
        self.portfolio_strategies = PortfolioStrategiesEngine()
        self.timing_strategies = TimingStrategiesEngine()
        self.financing_strategies = FinancingStrategiesEngine()
        self.diversification_strategies = DiversificationStrategiesEngine()
        self.legal_framework = LegalFrameworkEngine()
    
    def generate_comprehensive_strategies(self, property_data, investor_profile):
        """Generate comprehensive investment strategies for investor."""
        
        results = {
            'portfolio_strategies': self.portfolio_strategies.create_portfolios(property_data, investor_profile),
            'timing_strategies': self.timing_strategies.analyze_timing(property_data, investor_profile),
            'financing_strategies': self.financing_strategies.optimize_financing(property_data, investor_profile),
            'diversification_strategies': self.diversification_strategies.create_diversification_plan(property_data, investor_profile),
            'legal_framework': self.legal_framework.provide_legal_guidance(investor_profile)
        }
        
        return results

__all__ = [
    'InvestmentStrategiesEngine',
    'PortfolioStrategiesEngine',
    'TimingStrategiesEngine', 
    'FinancingStrategiesEngine',
    'DiversificationStrategiesEngine',
    'LegalFrameworkEngine'
]