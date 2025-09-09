"""
⚡ Advanced Energy Assessment Pipeline

Real-time energy assessment pipeline with ML integration, data validation,
and comprehensive analysis capabilities optimized for Greek energy market.
"""

from .pipeline import (
    EnergyAssessmentPipeline,
    RealTimeAssessmentService,
    BatchAssessmentProcessor,
)

from .stages import (
    DataValidationStage,
    FeatureExtractionStage,
    MLPredictionStage,
    RecommendationGenerationStage,
    ReportGenerationStage,
)

from .processors import (
    PropertyDataProcessor,
    ClimateDataProcessor,
    MarketDataProcessor,
    SubsidyEligibilityProcessor,
)

__all__ = [
    # Core Pipeline
    "EnergyAssessmentPipeline",
    "RealTimeAssessmentService", 
    "BatchAssessmentProcessor",
    
    # Pipeline Stages
    "DataValidationStage",
    "FeatureExtractionStage",
    "MLPredictionStage",
    "RecommendationGenerationStage", 
    "ReportGenerationStage",
    
    # Specialized Processors
    "PropertyDataProcessor",
    "ClimateDataProcessor",
    "MarketDataProcessor",
    "SubsidyEligibilityProcessor",
]