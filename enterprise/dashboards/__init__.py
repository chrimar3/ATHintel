"""
Executive Dashboard Engine
=========================

Comprehensive executive dashboards and visualization tools including:
- Real-time investment opportunity dashboards
- Portfolio performance monitoring dashboards
- Market intelligence and trend analysis dashboards
- Risk management and compliance dashboards
- Interactive property analysis tools
- Executive summary and KPI dashboards
"""

from .executive_dashboard import ExecutiveDashboardEngine
from .investment_dashboard import InvestmentDashboardEngine
from .portfolio_dashboard import PortfolioDashboardEngine
from .market_intelligence_dashboard import MarketIntelligenceDashboardEngine
from .risk_dashboard import RiskDashboardEngine
from .property_analysis_dashboard import PropertyAnalysisDashboardEngine

class ExecutiveDashboardEngine:
    """
    Main orchestrator for all executive dashboards and visualization tools.
    """
    
    def __init__(self):
        self.executive_dashboard = ExecutiveDashboardEngine()
        self.investment_dashboard = InvestmentDashboardEngine()
        self.portfolio_dashboard = PortfolioDashboardEngine()
        self.market_intelligence_dashboard = MarketIntelligenceDashboardEngine()
        self.risk_dashboard = RiskDashboardEngine()
        self.property_analysis_dashboard = PropertyAnalysisDashboardEngine()
    
    def generate_all_dashboards(self, data_sources, dashboard_config):
        """Generate all executive dashboards with comprehensive visualizations."""
        
        results = {
            'executive_summary': self.executive_dashboard.create_executive_summary(data_sources, dashboard_config),
            'investment_opportunities': self.investment_dashboard.create_investment_dashboard(data_sources, dashboard_config),
            'portfolio_performance': self.portfolio_dashboard.create_portfolio_dashboard(data_sources, dashboard_config),
            'market_intelligence': self.market_intelligence_dashboard.create_market_dashboard(data_sources, dashboard_config),
            'risk_management': self.risk_dashboard.create_risk_dashboard(data_sources, dashboard_config),
            'property_analysis': self.property_analysis_dashboard.create_property_dashboard(data_sources, dashboard_config)
        }
        
        return results

__all__ = [
    'ExecutiveDashboardEngine',
    'InvestmentDashboardEngine',
    'PortfolioDashboardEngine',
    'MarketIntelligenceDashboardEngine',
    'RiskDashboardEngine',
    'PropertyAnalysisDashboardEngine'
]