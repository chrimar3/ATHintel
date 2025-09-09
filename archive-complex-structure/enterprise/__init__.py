"""
ATHintel Enterprise Platform
==========================

Comprehensive Athens Real Estate Intelligence Platform for Enterprise Investment Solutions.

This package provides:
- Advanced market analytics and statistical modeling
- Investment portfolio optimization with Monte Carlo simulations  
- Risk-adjusted return analysis and portfolio management
- Alternative data acquisition and quality assurance frameworks
- Executive dashboards and professional reporting
- Enterprise-grade security and compliance features

Author: ATHintel Development Team
Version: 1.0.0
License: Enterprise Commercial License
"""

__version__ = "1.0.0"
__author__ = "ATHintel Development Team"
__email__ = "enterprise@athintel.com"

# Enterprise Platform Components
from .analytics import AdvancedAnalyticsEngine
from .modeling import InvestmentModelingEngine  
from .strategies import InvestmentStrategiesEngine
from .data_acquisition import AlternativeDataEngine
from .dashboards import ExecutiveDashboardEngine
from .security import EnterpriseSecurityFramework

__all__ = [
    "AdvancedAnalyticsEngine",
    "InvestmentModelingEngine", 
    "InvestmentStrategiesEngine",
    "AlternativeDataEngine",
    "ExecutiveDashboardEngine",
    "EnterpriseSecurityFramework"
]