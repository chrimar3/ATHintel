"""
🏗️ Domain Events for Energy Domain

Event-driven architecture implementation for the energy assessment domain.
Events represent significant business occurrences that other parts of the system
may need to react to.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
from abc import ABC, abstractmethod

from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.value_objects.upgrade_recommendation import UpgradeType

class DomainEvent(ABC):
    """Base class for all domain events"""
    
    def __init__(self):
        self.occurred_on = datetime.now()
        self.event_version = 1
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        pass

@dataclass
class PropertyEnergyAssessed(DomainEvent):
    """
    Event fired when a property's energy assessment is completed or updated
    """
    property_id: str
    assessment_id: str
    old_energy_class: Optional[EnergyClass]
    new_energy_class: EnergyClass
    confidence: Decimal
    assessor_type: str = "ml_system"  # ml_system, manual, certified_auditor
    timestamp: datetime = None
    
    def __post_init__(self):
        super().__init__()
        if self.timestamp is None:
            self.timestamp = self.occurred_on
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'PropertyEnergyAssessed',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'property_id': self.property_id,
            'assessment_id': self.assessment_id,
            'old_energy_class': self.old_energy_class.value if self.old_energy_class else None,
            'new_energy_class': self.new_energy_class.value,
            'confidence': float(self.confidence),
            'assessor_type': self.assessor_type,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class UpgradeRecommendationGenerated(DomainEvent):
    """
    Event fired when an upgrade recommendation is generated for a property
    """
    property_id: str
    assessment_id: str
    upgrade_type: UpgradeType
    estimated_cost: Decimal
    estimated_savings: Decimal
    roi: Decimal
    priority_score: Decimal = Decimal('0')
    timestamp: datetime = None
    
    def __post_init__(self):
        super().__init__()
        if self.timestamp is None:
            self.timestamp = self.occurred_on
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'UpgradeRecommendationGenerated',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'property_id': self.property_id,
            'assessment_id': self.assessment_id,
            'upgrade_type': self.upgrade_type.value,
            'estimated_cost': float(self.estimated_cost),
            'estimated_savings': float(self.estimated_savings),
            'roi': float(self.roi),
            'priority_score': float(self.priority_score),
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class EnergyMarketDataUpdated(DomainEvent):
    """
    Event fired when energy market data (pricing, subsidies) is updated
    """
    market_region: str  # e.g., "athens", "thessaloniki", "greece"
    data_type: str      # e.g., "electricity_price", "gas_price", "subsidies"
    old_value: Optional[Decimal]
    new_value: Decimal
    effective_date: datetime
    data_source: str
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'EnergyMarketDataUpdated',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'market_region': self.market_region,
            'data_type': self.data_type,
            'old_value': float(self.old_value) if self.old_value else None,
            'new_value': float(self.new_value),
            'effective_date': self.effective_date.isoformat(),
            'data_source': self.data_source
        }

@dataclass
class PortfolioAnalysisCompleted(DomainEvent):
    """
    Event fired when a portfolio-level energy analysis is completed
    """
    portfolio_id: str
    property_count: int
    total_baseline_cost: Decimal
    total_potential_savings: Decimal
    recommended_investment: Decimal
    portfolio_roi: Decimal
    analysis_type: str  # "full", "quick", "targeted"
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'PortfolioAnalysisCompleted',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'portfolio_id': self.portfolio_id,
            'property_count': self.property_count,
            'total_baseline_cost': float(self.total_baseline_cost),
            'total_potential_savings': float(self.total_potential_savings),
            'recommended_investment': float(self.recommended_investment),
            'portfolio_roi': float(self.portfolio_roi),
            'analysis_type': self.analysis_type
        }

@dataclass
class SubsidyEligibilityChanged(DomainEvent):
    """
    Event fired when a property's eligibility for subsidies changes
    """
    property_id: str
    subsidy_program: str
    old_eligibility: bool
    new_eligibility: bool
    eligibility_factors: Dict[str, Any]
    estimated_subsidy_amount: Optional[Decimal]
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'SubsidyEligibilityChanged',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'property_id': self.property_id,
            'subsidy_program': self.subsidy_program,
            'old_eligibility': self.old_eligibility,
            'new_eligibility': self.new_eligibility,
            'eligibility_factors': self.eligibility_factors,
            'estimated_subsidy_amount': float(self.estimated_subsidy_amount) if self.estimated_subsidy_amount else None
        }

@dataclass
class EnergyModelRetrained(DomainEvent):
    """
    Event fired when the ML energy prediction model is retrained
    """
    model_version: str
    training_data_size: int
    model_accuracy: Decimal
    validation_score: Decimal
    improvement_over_previous: Optional[Decimal]
    features_used: int
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'EnergyModelRetrained',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'model_version': self.model_version,
            'training_data_size': self.training_data_size,
            'model_accuracy': float(self.model_accuracy),
            'validation_score': float(self.validation_score),
            'improvement_over_previous': float(self.improvement_over_previous) if self.improvement_over_previous else None,
            'features_used': self.features_used
        }

@dataclass
class BatchAssessmentCompleted(DomainEvent):
    """
    Event fired when a batch of property assessments is completed
    """
    batch_id: str
    property_count: int
    successful_assessments: int
    failed_assessments: int
    processing_time_seconds: Decimal
    average_confidence: Decimal
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': 'BatchAssessmentCompleted',
            'event_version': self.event_version,
            'occurred_on': self.occurred_on.isoformat(),
            'batch_id': self.batch_id,
            'property_count': self.property_count,
            'successful_assessments': self.successful_assessments,
            'failed_assessments': self.failed_assessments,
            'processing_time_seconds': float(self.processing_time_seconds),
            'average_confidence': float(self.average_confidence)
        }

# Event Publisher Interface
class DomainEventPublisher:
    """
    Publisher for domain events - integrates with message broker
    """
    
    def __init__(self):
        self._subscribers = {}
    
    def subscribe(self, event_type: type, handler):
        """Subscribe to domain events"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        """Publish domain event to all subscribers"""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't fail the publish
                    print(f"Error handling event {event_type.__name__}: {e}")
    
    def publish_async(self, event: DomainEvent):
        """Publish event asynchronously (placeholder for message broker integration)"""
        # In production, this would integrate with Redis Pub/Sub, RabbitMQ, etc.
        self.publish(event)

# Global event publisher instance
_event_publisher = DomainEventPublisher()

def get_event_publisher() -> DomainEventPublisher:
    """Get global event publisher instance"""
    return _event_publisher

# Event Handler Examples
def log_energy_assessment_handler(event: PropertyEnergyAssessed):
    """Example handler for energy assessment events"""
    print(f"Energy assessment completed for property {event.property_id}: "
          f"{event.new_energy_class.value} (confidence: {event.confidence})")

def update_market_statistics_handler(event: UpgradeRecommendationGenerated):
    """Example handler for upgrade recommendation events"""
    print(f"New upgrade recommendation: {event.upgrade_type.value} for property {event.property_id} "
          f"(ROI: {event.roi}%)")

def notify_portfolio_completion_handler(event: PortfolioAnalysisCompleted):
    """Example handler for portfolio analysis completion"""
    print(f"Portfolio analysis completed: {event.property_count} properties, "
          f"ROI: {event.portfolio_roi}%")

# Register example handlers
def setup_default_handlers():
    """Set up default event handlers"""
    publisher = get_event_publisher()
    publisher.subscribe(PropertyEnergyAssessed, log_energy_assessment_handler)
    publisher.subscribe(UpgradeRecommendationGenerated, update_market_statistics_handler)
    publisher.subscribe(PortfolioAnalysisCompleted, notify_portfolio_completion_handler)