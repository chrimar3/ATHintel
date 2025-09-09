"""
🏗️ Property Energy Domain Entity

Core domain entity representing the energy characteristics and assessment
of a real estate property, following Domain-Driven Design principles.

This entity encapsulates all energy-related business logic and rules,
ensuring consistency and providing a rich domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from decimal import Decimal
from enum import Enum
import uuid

from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.value_objects.upgrade_recommendation import UpgradeRecommendation
from domains.energy.value_objects.financial_metrics import FinancialMetrics
from domains.energy.events.domain_events import PropertyEnergyAssessed, UpgradeRecommendationGenerated

class BuildingType(Enum):
    """Greek building construction types with energy implications"""
    NEOCLASSICAL = "neoclassical"  # Pre-1960, poor insulation
    APARTMENT_BLOCK = "apartment_block"  # 1960-1980, basic insulation
    MODERN_BUILDING = "modern_building"  # 1980-2000, improved standards
    NEW_CONSTRUCTION = "new_construction"  # 2000+, EU standards
    DETACHED_HOUSE = "detached_house"  # Various periods, variable efficiency
    MAISONETTE = "maisonette"  # Multi-level, specific heating challenges

class HeatingSystem(Enum):
    """Heating system types with efficiency characteristics"""
    OIL_BOILER = "oil_boiler"  # Traditional, low efficiency
    GAS_BOILER = "gas_boiler"  # Common, medium efficiency  
    ELECTRIC_HEATING = "electric_heating"  # Expensive operation
    HEAT_PUMP = "heat_pump"  # High efficiency, modern
    SOLAR_THERMAL = "solar_thermal"  # Renewable, high efficiency
    GEOTHERMAL = "geothermal"  # Premium, very high efficiency
    DISTRICT_HEATING = "district_heating"  # Centralized system
    FIREPLACE = "fireplace"  # Traditional, low efficiency

@dataclass
class PropertyEnergyProfile:
    """Value object representing energy characteristics"""
    building_type: BuildingType
    construction_year: int
    total_area: Decimal
    heating_system: HeatingSystem
    current_energy_class: EnergyClass
    annual_energy_consumption: Optional[Decimal] = None  # kWh/year
    annual_energy_cost: Optional[Decimal] = None  # €/year
    has_solar_panels: bool = False
    insulation_walls: bool = False
    insulation_roof: bool = False
    double_glazed_windows: bool = False
    smart_thermostat: bool = False
    
    def __post_init__(self):
        """Validate energy profile consistency"""
        if self.construction_year < 1800 or self.construction_year > datetime.now().year:
            raise ValueError(f"Invalid construction year: {self.construction_year}")
        
        if self.total_area <= 0:
            raise ValueError(f"Invalid total area: {self.total_area}")
        
        # Business rule: New construction should have better energy classes
        if self.construction_year >= 2010 and self.current_energy_class.numeric_value > 4:
            # This might indicate data quality issues but shouldn't fail
            pass

@dataclass 
class PropertyEnergyEntity:
    """
    Core domain entity for property energy assessment
    
    This entity represents a property's energy characteristics, assessment history,
    and upgrade recommendations. It enforces business rules and maintains consistency.
    """
    
    # Identity
    property_id: str
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Energy profile
    energy_profile: PropertyEnergyProfile
    
    # Assessment data
    assessment_date: datetime = field(default_factory=datetime.now)
    predicted_energy_class: Optional[EnergyClass] = None
    prediction_confidence: Decimal = field(default=Decimal('0.0'))
    
    # Financial metrics
    financial_metrics: Optional[FinancialMetrics] = None
    
    # Upgrade recommendations
    upgrade_recommendations: List[UpgradeRecommendation] = field(default_factory=list)
    
    # Business metadata
    assessor_id: str = "system"
    version: int = 1
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Domain events (for event-driven architecture)
    _domain_events: List = field(default_factory=list, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize domain entity and validate business rules"""
        self._validate_business_rules()
        self._calculate_initial_metrics()
    
    def _validate_business_rules(self):
        """Enforce domain business rules"""
        
        # Rule 1: Property must have valid energy profile
        if not isinstance(self.energy_profile, PropertyEnergyProfile):
            raise ValueError("Property must have valid energy profile")
        
        # Rule 2: Assessment date cannot be in the future
        if self.assessment_date > datetime.now():
            raise ValueError("Assessment date cannot be in the future")
        
        # Rule 3: Prediction confidence must be between 0 and 1
        if not (Decimal('0') <= self.prediction_confidence <= Decimal('1')):
            raise ValueError("Prediction confidence must be between 0 and 1")
        
        # Rule 4: If predictions exist, they should be reasonable
        if (self.predicted_energy_class and 
            abs(self.predicted_energy_class.numeric_value - 
                self.energy_profile.current_energy_class.numeric_value) > 3):
            # Log warning but don't fail - ML predictions can be aggressive
            pass
    
    def _calculate_initial_metrics(self):
        """Calculate initial financial and energy metrics"""
        if not self.financial_metrics:
            # Basic metrics calculation - will be enhanced by domain services
            baseline_cost = self._estimate_baseline_energy_cost()
            self.financial_metrics = FinancialMetrics(
                baseline_annual_cost=baseline_cost,
                potential_annual_savings=Decimal('0'),
                upgrade_investment_required=Decimal('0'),
                simple_payback_years=Decimal('0'),
                net_present_value=Decimal('0'),
                internal_rate_of_return=Decimal('0')
            )
    
    def _estimate_baseline_energy_cost(self) -> Decimal:
        """Estimate baseline energy cost based on profile"""
        
        # Greek energy pricing (approximate 2025 rates)
        kwh_price = Decimal('0.25')  # €0.25/kWh average
        
        if self.energy_profile.annual_energy_consumption:
            return self.energy_profile.annual_energy_consumption * kwh_price
        
        # Estimate based on area and energy class
        area = self.energy_profile.total_area
        energy_class = self.energy_profile.current_energy_class
        
        # Energy consumption estimation (kWh/m²/year) by class
        consumption_per_m2 = {
            EnergyClass.A_PLUS: Decimal('40'),
            EnergyClass.A: Decimal('65'),
            EnergyClass.B_PLUS: Decimal('90'),
            EnergyClass.B: Decimal('115'),
            EnergyClass.C: Decimal('140'),
            EnergyClass.D: Decimal('175'),
            EnergyClass.E: Decimal('225'),
            EnergyClass.F: Decimal('275'),
            EnergyClass.G: Decimal('400')
        }
        
        estimated_consumption = area * consumption_per_m2.get(energy_class, Decimal('200'))
        return estimated_consumption * kwh_price
    
    # Domain methods for business operations
    
    def update_energy_prediction(self, predicted_class: EnergyClass, confidence: Decimal, 
                               assessor_id: str = "ml_system") -> None:
        """Update energy class prediction with confidence score"""
        
        if not (Decimal('0') <= confidence <= Decimal('1')):
            raise ValueError("Confidence must be between 0 and 1")
        
        old_prediction = self.predicted_energy_class
        self.predicted_energy_class = predicted_class
        self.prediction_confidence = confidence
        self.assessor_id = assessor_id
        self.last_updated = datetime.now()
        
        # Raise domain event
        event = PropertyEnergyAssessed(
            property_id=self.property_id,
            assessment_id=self.assessment_id,
            old_energy_class=old_prediction,
            new_energy_class=predicted_class,
            confidence=confidence,
            timestamp=datetime.now()
        )
        self._add_domain_event(event)
    
    def add_upgrade_recommendation(self, recommendation: UpgradeRecommendation) -> None:
        """Add an upgrade recommendation with business validation"""
        
        # Business rule: No duplicate recommendations for same upgrade type
        existing_types = {rec.upgrade_type for rec in self.upgrade_recommendations}
        if recommendation.upgrade_type in existing_types:
            # Update existing recommendation instead of adding duplicate
            self.upgrade_recommendations = [
                rec if rec.upgrade_type != recommendation.upgrade_type else recommendation
                for rec in self.upgrade_recommendations
            ]
        else:
            self.upgrade_recommendations.append(recommendation)
        
        self.last_updated = datetime.now()
        
        # Raise domain event
        event = UpgradeRecommendationGenerated(
            property_id=self.property_id,
            assessment_id=self.assessment_id,
            upgrade_type=recommendation.upgrade_type,
            estimated_cost=recommendation.cost,
            estimated_savings=recommendation.annual_savings,
            roi=recommendation.roi,
            timestamp=datetime.now()
        )
        self._add_domain_event(event)
    
    def calculate_portfolio_metrics(self, other_properties: List['PropertyEnergyEntity']) -> Dict[str, Decimal]:
        """Calculate metrics in the context of a property portfolio"""
        
        total_properties = len(other_properties) + 1
        all_properties = other_properties + [self]
        
        # Portfolio-level calculations
        total_baseline_cost = sum(prop.financial_metrics.baseline_annual_cost 
                                for prop in all_properties if prop.financial_metrics)
        
        total_potential_savings = sum(prop.financial_metrics.potential_annual_savings
                                    for prop in all_properties if prop.financial_metrics)
        
        total_investment_required = sum(prop.financial_metrics.upgrade_investment_required
                                      for prop in all_properties if prop.financial_metrics)
        
        # This property's contribution to portfolio
        my_cost_share = (self.financial_metrics.baseline_annual_cost / total_baseline_cost 
                        if total_baseline_cost > 0 else Decimal('0'))
        
        my_savings_potential = (self.financial_metrics.potential_annual_savings / total_potential_savings
                               if total_potential_savings > 0 else Decimal('0'))
        
        return {
            'portfolio_baseline_cost': total_baseline_cost,
            'portfolio_potential_savings': total_potential_savings,
            'portfolio_investment_required': total_investment_required,
            'my_cost_share_percentage': my_cost_share * 100,
            'my_savings_potential_percentage': my_savings_potential * 100,
            'portfolio_average_energy_class': self._calculate_average_energy_class(all_properties),
            'portfolio_roi': (total_potential_savings / total_investment_required * 100 
                            if total_investment_required > 0 else Decimal('0'))
        }
    
    def _calculate_average_energy_class(self, properties: List['PropertyEnergyEntity']) -> Decimal:
        """Calculate weighted average energy class for portfolio"""
        total_area = sum(prop.energy_profile.total_area for prop in properties)
        
        if total_area == 0:
            return Decimal('5')  # Default to class C
        
        weighted_sum = sum(
            prop.energy_profile.current_energy_class.numeric_value * prop.energy_profile.total_area
            for prop in properties
        )
        
        return weighted_sum / total_area
    
    def get_upgrade_priority_score(self) -> Decimal:
        """Calculate priority score for this property's upgrades (0-100)"""
        
        if not self.upgrade_recommendations or not self.financial_metrics:
            return Decimal('0')
        
        # Factors affecting priority:
        # 1. ROI potential (40%)
        # 2. Energy class improvement potential (30%) 
        # 3. Investment size (20% - smaller investments get higher priority)
        # 4. Confidence in predictions (10%)
        
        # ROI score (0-40 points)
        best_roi = max(rec.roi for rec in self.upgrade_recommendations)
        roi_score = min(best_roi * 2, Decimal('40'))  # Cap at 40 points
        
        # Energy improvement score (0-30 points)
        if self.predicted_energy_class:
            improvement = (self.energy_profile.current_energy_class.numeric_value - 
                          self.predicted_energy_class.numeric_value)
            improvement_score = min(improvement * 10, Decimal('30'))  # Cap at 30 points
        else:
            improvement_score = Decimal('0')
        
        # Investment size score (0-20 points) - inverse relationship
        total_investment = self.financial_metrics.upgrade_investment_required
        if total_investment > 0:
            # Give higher scores to smaller investments (easier to implement)
            investment_score = max(Decimal('20') - (total_investment / 1000), Decimal('0'))
        else:
            investment_score = Decimal('0')
        
        # Confidence score (0-10 points)
        confidence_score = self.prediction_confidence * 10
        
        total_score = roi_score + improvement_score + investment_score + confidence_score
        return min(total_score, Decimal('100'))  # Cap at 100
    
    def is_eligible_for_subsidies(self) -> Dict[str, bool]:
        """Check eligibility for various government subsidy programs"""
        
        # Greek government energy efficiency programs (2025)
        eligibility = {}
        
        # "Εξοικονομώ" program eligibility
        building_age = datetime.now().year - self.energy_profile.construction_year
        eligibility['exoikonomo'] = (
            building_age >= 15 and  # Building older than 15 years
            self.energy_profile.current_energy_class.numeric_value >= 4  # Class D or worse
        )
        
        # Solar panel subsidies
        eligibility['solar_subsidies'] = (
            not self.energy_profile.has_solar_panels and  # Don't already have solar
            self.energy_profile.building_type in [BuildingType.DETACHED_HOUSE, BuildingType.MAISONETTE]
        )
        
        # Heat pump subsidies
        eligibility['heat_pump_subsidies'] = (
            self.energy_profile.heating_system in [HeatingSystem.OIL_BOILER, HeatingSystem.ELECTRIC_HEATING] and
            self.energy_profile.current_energy_class.numeric_value >= 5  # Class E or worse
        )
        
        # Insulation subsidies
        eligibility['insulation_subsidies'] = (
            not (self.energy_profile.insulation_walls and self.energy_profile.insulation_roof) and
            building_age >= 10
        )
        
        return eligibility
    
    def _add_domain_event(self, event) -> None:
        """Add domain event for event-driven architecture"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List:
        """Get and clear domain events"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    def to_dict(self) -> Dict:
        """Convert entity to dictionary for serialization"""
        return {
            'property_id': self.property_id,
            'assessment_id': self.assessment_id,
            'energy_profile': {
                'building_type': self.energy_profile.building_type.value,
                'construction_year': self.energy_profile.construction_year,
                'total_area': float(self.energy_profile.total_area),
                'heating_system': self.energy_profile.heating_system.value,
                'current_energy_class': self.energy_profile.current_energy_class.value,
                'annual_energy_consumption': float(self.energy_profile.annual_energy_consumption) if self.energy_profile.annual_energy_consumption else None,
                'annual_energy_cost': float(self.energy_profile.annual_energy_cost) if self.energy_profile.annual_energy_cost else None,
                'has_solar_panels': self.energy_profile.has_solar_panels,
                'insulation_walls': self.energy_profile.insulation_walls,
                'insulation_roof': self.energy_profile.insulation_roof,
                'double_glazed_windows': self.energy_profile.double_glazed_windows,
                'smart_thermostat': self.energy_profile.smart_thermostat
            },
            'assessment_date': self.assessment_date.isoformat(),
            'predicted_energy_class': self.predicted_energy_class.value if self.predicted_energy_class else None,
            'prediction_confidence': float(self.prediction_confidence),
            'financial_metrics': self.financial_metrics.to_dict() if self.financial_metrics else None,
            'upgrade_recommendations': [rec.to_dict() for rec in self.upgrade_recommendations],
            'assessor_id': self.assessor_id,
            'version': self.version,
            'last_updated': self.last_updated.isoformat(),
            'upgrade_priority_score': float(self.get_upgrade_priority_score()),
            'subsidy_eligibility': self.is_eligible_for_subsidies()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PropertyEnergyEntity':
        """Create entity from dictionary"""
        # This would implement the reverse conversion
        # Implementation details omitted for brevity
        raise NotImplementedError("from_dict implementation needed")

# Factory function for creating property energy entities
def create_property_energy_entity(
    property_id: str,
    building_type: BuildingType,
    construction_year: int,
    total_area: Decimal,
    heating_system: HeatingSystem,
    current_energy_class: EnergyClass,
    **kwargs
) -> PropertyEnergyEntity:
    """Factory function to create property energy entity with validation"""
    
    energy_profile = PropertyEnergyProfile(
        building_type=building_type,
        construction_year=construction_year,
        total_area=total_area,
        heating_system=heating_system,
        current_energy_class=current_energy_class,
        **kwargs
    )
    
    return PropertyEnergyEntity(
        property_id=property_id,
        energy_profile=energy_profile
    )