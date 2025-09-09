"""
🏗️ Upgrade Recommendation Value Object

Immutable value object representing an energy upgrade recommendation
with cost, savings, and implementation details.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class UpgradeType(Enum):
    """Types of energy efficiency upgrades"""
    WALL_INSULATION = "wall_insulation"
    ROOF_INSULATION = "roof_insulation"
    FLOOR_INSULATION = "floor_insulation"
    WINDOW_REPLACEMENT = "window_replacement"
    DOOR_REPLACEMENT = "door_replacement"
    HEATING_SYSTEM_UPGRADE = "heating_system_upgrade"
    SOLAR_PANELS = "solar_panels"
    SOLAR_WATER_HEATER = "solar_water_heater"
    HEAT_PUMP = "heat_pump"
    SMART_THERMOSTAT = "smart_thermostat"
    LED_LIGHTING = "led_lighting"
    VENTILATION_SYSTEM = "ventilation_system"
    BUILDING_AUTOMATION = "building_automation"

class UpgradePriority(Enum):
    """Priority levels for upgrade recommendations"""
    CRITICAL = "critical"      # High ROI, easy implementation
    HIGH = "high"             # Good ROI, reasonable implementation
    MEDIUM = "medium"         # Moderate ROI, some complexity
    LOW = "low"               # Lower ROI, high complexity
    OPTIONAL = "optional"     # Nice to have, low priority

class ImplementationDifficulty(Enum):
    """Implementation difficulty levels"""
    EASY = "easy"           # DIY or single day professional work
    MODERATE = "moderate"   # Few days professional work
    COMPLEX = "complex"     # Weeks of work, permits required
    MAJOR = "major"         # Months of work, significant disruption

@dataclass(frozen=True)
class GovernmentSubsidy:
    """Government subsidy information"""
    program_name: str
    subsidy_percentage: Decimal  # 0-100
    max_subsidy_amount: Decimal  # Maximum € amount
    eligibility_criteria: List[str]
    application_url: Optional[str] = None
    deadline: Optional[datetime] = None

@dataclass(frozen=True)
class UpgradeRecommendation:
    """
    Immutable value object for energy upgrade recommendations
    
    Contains all information needed to evaluate and implement
    an energy efficiency upgrade.
    """
    
    # Core upgrade information
    upgrade_type: UpgradeType
    priority: UpgradePriority
    implementation_difficulty: ImplementationDifficulty
    
    # Financial metrics
    cost: Decimal  # Total implementation cost in €
    annual_savings: Decimal  # Annual energy cost savings in €
    roi: Decimal  # Return on investment as percentage (0-100)
    simple_payback_years: Decimal  # Years to break even
    
    # Technical details
    description: str
    technical_specifications: Dict[str, str]
    energy_class_improvement: int  # Number of energy classes improved
    
    # Implementation details
    implementation_time: str  # e.g., "2-3 days", "1 week"
    best_season: str  # When to implement for best results
    permits_required: List[str]  # Building permits needed
    
    # Government subsidies
    available_subsidies: List[GovernmentSubsidy]
    
    # Additional metadata
    confidence_level: Decimal = Decimal('0.8')  # Confidence in estimates (0-1)
    environmental_impact: Optional[str] = None  # CO2 savings description
    
    def __post_init__(self):
        """Validate upgrade recommendation data"""
        if self.cost < 0:
            raise ValueError("Cost cannot be negative")
        
        if self.annual_savings < 0:
            raise ValueError("Annual savings cannot be negative")
        
        if not (0 <= self.roi <= 200):  # Allow up to 200% ROI
            raise ValueError("ROI must be between 0 and 200%")
        
        if not (0 <= self.confidence_level <= 1):
            raise ValueError("Confidence level must be between 0 and 1")
    
    @property
    def net_cost_after_subsidies(self) -> Decimal:
        """Calculate net cost after applying all available subsidies"""
        total_subsidy = Decimal('0')
        
        for subsidy in self.available_subsidies:
            # Calculate subsidy amount (percentage of cost, capped at max amount)
            subsidy_amount = min(
                self.cost * (subsidy.subsidy_percentage / 100),
                subsidy.max_subsidy_amount
            )
            total_subsidy += subsidy_amount
        
        return max(self.cost - total_subsidy, Decimal('0'))
    
    @property
    def payback_after_subsidies(self) -> Decimal:
        """Calculate payback period after subsidies"""
        net_cost = self.net_cost_after_subsidies
        if self.annual_savings <= 0:
            return Decimal('999')  # Infinite payback
        
        return net_cost / self.annual_savings
    
    @property
    def roi_after_subsidies(self) -> Decimal:
        """Calculate ROI after subsidies"""
        net_cost = self.net_cost_after_subsidies
        if net_cost <= 0:
            return Decimal('100')  # 100% ROI if fully subsidized
        
        return (self.annual_savings / net_cost) * 100
    
    @property
    def priority_score(self) -> Decimal:
        """Calculate numerical priority score (0-100)"""
        # Base score from priority level
        priority_scores = {
            UpgradePriority.CRITICAL: Decimal('90'),
            UpgradePriority.HIGH: Decimal('75'),
            UpgradePriority.MEDIUM: Decimal('60'),
            UpgradePriority.LOW: Decimal('40'),
            UpgradePriority.OPTIONAL: Decimal('20')
        }
        base_score = priority_scores[self.priority]
        
        # Adjust based on ROI after subsidies
        roi_bonus = min(self.roi_after_subsidies / 10, Decimal('20'))  # Up to 20 points for ROI
        
        # Adjust based on implementation difficulty (easier = higher score)
        difficulty_adjustment = {
            ImplementationDifficulty.EASY: Decimal('10'),
            ImplementationDifficulty.MODERATE: Decimal('5'),
            ImplementationDifficulty.COMPLEX: Decimal('-5'),
            ImplementationDifficulty.MAJOR: Decimal('-10')
        }
        difficulty_score = difficulty_adjustment[self.implementation_difficulty]
        
        # Adjust based on confidence level
        confidence_bonus = (self.confidence_level - Decimal('0.5')) * 10  # -5 to +5 points
        
        total_score = base_score + roi_bonus + difficulty_score + confidence_bonus
        return max(min(total_score, Decimal('100')), Decimal('0'))  # Clamp to 0-100
    
    def get_implementation_timeline(self) -> Dict[str, datetime]:
        """Get recommended implementation timeline"""
        now = datetime.now()
        
        # Determine best start date based on season
        if self.best_season.lower() == "spring":
            start_date = datetime(now.year, 4, 1)
            if now.month > 6:  # If past spring, target next year
                start_date = datetime(now.year + 1, 4, 1)
        elif self.best_season.lower() == "summer":
            start_date = datetime(now.year, 6, 1)
            if now.month > 8:
                start_date = datetime(now.year + 1, 6, 1)
        elif self.best_season.lower() == "autumn":
            start_date = datetime(now.year, 9, 1)
            if now.month > 11:
                start_date = datetime(now.year + 1, 9, 1)
        else:  # Winter or any season
            start_date = now + timedelta(days=30)  # Start in 30 days
        
        # Estimate duration based on implementation difficulty
        duration_days = {
            ImplementationDifficulty.EASY: 3,
            ImplementationDifficulty.MODERATE: 14,
            ImplementationDifficulty.COMPLEX: 45,
            ImplementationDifficulty.MAJOR: 120
        }
        
        implementation_days = duration_days[self.implementation_difficulty]
        end_date = start_date + timedelta(days=implementation_days)
        
        return {
            'recommended_start': start_date,
            'estimated_completion': end_date,
            'preparation_start': start_date - timedelta(days=14),  # 2 weeks prep
            'permit_deadline': start_date - timedelta(days=30) if self.permits_required else None
        }
    
    def calculate_10_year_value(self) -> Dict[str, Decimal]:
        """Calculate 10-year financial value of the upgrade"""
        years = 10
        discount_rate = Decimal('0.03')  # 3% discount rate
        
        # Calculate NPV over 10 years
        npv = Decimal('0')
        for year in range(1, years + 1):
            discounted_savings = self.annual_savings / ((1 + discount_rate) ** year)
            npv += discounted_savings
        
        net_investment = self.net_cost_after_subsidies
        total_npv = npv - net_investment
        
        # Calculate cumulative savings
        cumulative_savings = self.annual_savings * years
        
        # Calculate energy savings (assuming 2% annual energy price increase)
        energy_price_growth = Decimal('0.02')
        total_energy_savings = Decimal('0')
        for year in range(1, years + 1):
            yearly_savings = self.annual_savings * ((1 + energy_price_growth) ** year)
            total_energy_savings += yearly_savings
        
        return {
            'net_present_value': total_npv,
            'cumulative_savings': cumulative_savings,
            'total_energy_savings': total_energy_savings,
            'roi_10_year': (total_energy_savings / net_investment * 100) if net_investment > 0 else Decimal('0'),
            'break_even_year': min(self.payback_after_subsidies, years)
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        timeline = self.get_implementation_timeline()
        value_analysis = self.calculate_10_year_value()
        
        return {
            'upgrade_type': self.upgrade_type.value,
            'priority': self.priority.value,
            'implementation_difficulty': self.implementation_difficulty.value,
            'cost': float(self.cost),
            'annual_savings': float(self.annual_savings),
            'roi': float(self.roi),
            'simple_payback_years': float(self.simple_payback_years),
            'description': self.description,
            'technical_specifications': self.technical_specifications,
            'energy_class_improvement': self.energy_class_improvement,
            'implementation_time': self.implementation_time,
            'best_season': self.best_season,
            'permits_required': self.permits_required,
            'available_subsidies': [
                {
                    'program_name': sub.program_name,
                    'subsidy_percentage': float(sub.subsidy_percentage),
                    'max_subsidy_amount': float(sub.max_subsidy_amount),
                    'eligibility_criteria': sub.eligibility_criteria,
                    'application_url': sub.application_url,
                    'deadline': sub.deadline.isoformat() if sub.deadline else None
                }
                for sub in self.available_subsidies
            ],
            'confidence_level': float(self.confidence_level),
            'environmental_impact': self.environmental_impact,
            'financial_analysis': {
                'net_cost_after_subsidies': float(self.net_cost_after_subsidies),
                'payback_after_subsidies': float(self.payback_after_subsidies),
                'roi_after_subsidies': float(self.roi_after_subsidies),
                'priority_score': float(self.priority_score),
                'ten_year_analysis': {
                    'net_present_value': float(value_analysis['net_present_value']),
                    'cumulative_savings': float(value_analysis['cumulative_savings']),
                    'total_energy_savings': float(value_analysis['total_energy_savings']),
                    'roi_10_year': float(value_analysis['roi_10_year']),
                    'break_even_year': float(value_analysis['break_even_year'])
                }
            },
            'implementation_timeline': {
                'recommended_start': timeline['recommended_start'].isoformat(),
                'estimated_completion': timeline['estimated_completion'].isoformat(),
                'preparation_start': timeline['preparation_start'].isoformat(),
                'permit_deadline': timeline['permit_deadline'].isoformat() if timeline['permit_deadline'] else None
            }
        }
    
    @classmethod
    def create_wall_insulation_recommendation(
        cls, 
        building_area: Decimal, 
        current_energy_class: 'EnergyClass',
        construction_year: int
    ) -> 'UpgradeRecommendation':
        """Factory method for wall insulation recommendations"""
        
        # Cost estimation: €25-40 per m² of wall area
        # Assume wall area is roughly 1.5x floor area for typical buildings
        wall_area = building_area * Decimal('1.5')
        cost = wall_area * Decimal('32')  # €32/m² average
        
        # Savings estimation based on current energy class
        from domains.energy.value_objects.energy_class import EnergyClass
        annual_savings = building_area * Decimal('15')  # €15/m²/year for insulation
        
        # ROI calculation
        roi = (annual_savings / cost) * 100 if cost > 0 else Decimal('0')
        payback = cost / annual_savings if annual_savings > 0 else Decimal('999')
        
        # Greek subsidies for insulation
        subsidies = [
            GovernmentSubsidy(
                program_name="Εξοικονομώ - Κατ' Οίκον",
                subsidy_percentage=Decimal('70'),
                max_subsidy_amount=Decimal('25000'),
                eligibility_criteria=[
                    "Building age > 15 years",
                    "Energy class D or lower", 
                    "Owner-occupied or rental property"
                ],
                application_url="https://exoikonomo.gov.gr"
            )
        ]
        
        return cls(
            upgrade_type=UpgradeType.WALL_INSULATION,
            priority=UpgradePriority.HIGH if current_energy_class.numeric_value >= 6 else UpgradePriority.MEDIUM,
            implementation_difficulty=ImplementationDifficulty.COMPLEX,
            cost=cost,
            annual_savings=annual_savings,
            roi=roi,
            simple_payback_years=payback,
            description=f"External wall insulation with 10cm thermal insulation system. "
                       f"Estimated {wall_area:.0f}m² wall area coverage.",
            technical_specifications={
                "insulation_type": "Expanded polystyrene (EPS) or mineral wool",
                "thickness": "10cm",
                "coverage_area": f"{wall_area:.0f}m²",
                "thermal_conductivity": "0.035 W/mK",
                "fire_rating": "Class B-s1,d0"
            },
            energy_class_improvement=1 if current_energy_class.numeric_value <= 7 else 2,
            implementation_time="3-4 weeks",
            best_season="spring",
            permits_required=["Building permit", "Fire safety certificate"],
            available_subsidies=subsidies,
            confidence_level=Decimal('0.85'),
            environmental_impact=f"Reduces CO2 emissions by ~{annual_savings * Decimal('0.4'):.0f}kg/year"
        )

# Factory functions for common upgrade types
def create_heating_system_upgrade(
    current_system: str,
    building_area: Decimal,
    target_efficiency_gain: Decimal = Decimal('30')
) -> UpgradeRecommendation:
    """Create heating system upgrade recommendation"""
    
    base_cost_per_m2 = Decimal('120')  # €120/m² for heat pump installation
    cost = building_area * base_cost_per_m2
    
    # Higher savings for worse current systems
    current_system_multiplier = {
        'oil_boiler': Decimal('1.5'),
        'electric_heating': Decimal('1.8'),
        'old_gas_boiler': Decimal('1.2'),
        'fireplace': Decimal('2.0')
    }.get(current_system, Decimal('1.0'))
    
    annual_savings = building_area * Decimal('20') * current_system_multiplier
    
    subsidies = [
        GovernmentSubsidy(
            program_name="Εξοικονομώ - Αντλίες Θερμότητας",
            subsidy_percentage=Decimal('50'),
            max_subsidy_amount=Decimal('15000'),
            eligibility_criteria=[
                "Replace old heating system",
                "Minimum COP 4.0 for heat pump"
            ]
        )
    ]
    
    return UpgradeRecommendation(
        upgrade_type=UpgradeType.HEAT_PUMP,
        priority=UpgradePriority.HIGH,
        implementation_difficulty=ImplementationDifficulty.MODERATE,
        cost=cost,
        annual_savings=annual_savings,
        roi=(annual_savings / cost) * 100,
        simple_payback_years=cost / annual_savings if annual_savings > 0 else Decimal('999'),
        description=f"Air-to-water heat pump system replacing {current_system}. "
                   f"High efficiency heating and cooling for {building_area:.0f}m².",
        technical_specifications={
            "system_type": "Air-to-water heat pump",
            "capacity": f"{building_area * Decimal('0.08'):.0f}kW",
            "cop_rating": "4.2",
            "coverage_area": f"{building_area:.0f}m²",
            "refrigerant": "R32"
        },
        energy_class_improvement=2,
        implementation_time="1-2 weeks",
        best_season="autumn",
        permits_required=["Building permit for outdoor unit"],
        available_subsidies=subsidies,
        confidence_level=Decimal('0.9'),
        environmental_impact=f"Reduces CO2 emissions by ~{annual_savings * Decimal('0.5'):.0f}kg/year"
    )