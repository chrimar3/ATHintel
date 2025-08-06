"""
Advanced Analytics Engine
========================

Comprehensive statistical modeling and market analysis capabilities.

Components:
- Market segmentation and clustering analysis
- Advanced statistical modeling and trend analysis
- Neighborhood-level market intelligence with heat maps
- Investment opportunity scoring with multiple algorithms
- Risk assessment and diversification analysis
- Performance benchmarking against Athens market indices
"""

from .market_segmentation import MarketSegmentationEngine
from .statistical_modeling import StatisticalModelingEngine
from .neighborhood_intelligence import NeighborhoodIntelligenceEngine
from .opportunity_scoring import Opportunityscoring
from .risk_assessment import RiskAssessmentEngine
from .performance_benchmarking import PerformanceBenchmarkingEngine

class AdvancedAnalyticsEngine:
    """
    Main analytics engine orchestrating all statistical analysis components.
    """
    
    def __init__(self):
        self.market_segmentation = MarketSegmentationEngine()
        self.statistical_modeling = StatisticalModelingEngine()
        self.neighborhood_intelligence = NeighborhoodIntelligenceEngine()
        self.opportunity_scoring = OpportunityScoring()
        self.risk_assessment = RiskAssessmentEngine()
        self.performance_benchmarking = PerformanceBenchmarkingEngine()
    
    def run_comprehensive_analysis(self, property_data):
        """Run full advanced analytics pipeline."""
        results = {
            'market_segments': self.market_segmentation.analyze(property_data),
            'statistical_models': self.statistical_modeling.build_models(property_data),
            'neighborhood_intelligence': self.neighborhood_intelligence.generate_intelligence(property_data),
            'opportunity_scores': self.opportunity_scoring.score_opportunities(property_data),
            'risk_assessment': self.risk_assessment.assess_risks(property_data),
            'performance_benchmarks': self.performance_benchmarking.benchmark_performance(property_data)
        }
        return results

__all__ = [
    'AdvancedAnalyticsEngine',
    'MarketSegmentationEngine',
    'StatisticalModelingEngine', 
    'NeighborhoodIntelligenceEngine',
    'OpportunityScoring',
    'RiskAssessmentEngine',
    'PerformanceBenchmarkingEngine'
]