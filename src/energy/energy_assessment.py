"""
Energy Assessment Algorithm
ATHintel Energy Upgrade Analysis System
Calculates energy efficiency ratings and upgrade potential for Greek properties
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EnergyClass(Enum):
    """EU Energy Performance Certificate Classes"""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

    @property
    def numeric_value(self) -> int:
        """Convert energy class to numeric value for calculations"""
        mapping = {
            "A+": 1, "A": 2, "B+": 3, "B": 4, "C": 5,
            "D": 6, "E": 7, "F": 8, "G": 9
        }
        return mapping[self.value]

    @property
    def kwh_per_m2_range(self) -> Tuple[float, float]:
        """Energy consumption range in kWh/m²/year"""
        ranges = {
            "A+": (0, 50), "A": (51, 75), "B+": (76, 100), "B": (101, 125),
            "C": (126, 150), "D": (151, 200), "E": (201, 250),
            "F": (251, 300), "G": (301, 500)
        }
        return ranges[self.value]


class ConstructionType(Enum):
    """Greek building construction types"""
    MODERN_INSULATED = "modern_insulated"      # Post-2010, thermal regulations
    MODERN_BASIC = "modern_basic"              # 1990-2010, basic insulation
    TRADITIONAL_RENOVATED = "traditional_renovated"  # Pre-1990, renovated
    TRADITIONAL_ORIGINAL = "traditional_original"    # Pre-1990, original
    NEOCLASSICAL = "neoclassical"             # Historic buildings
    APARTMENT_BLOCK = "apartment_block"        # Multi-story residential


@dataclass
class BuildingCharacteristics:
    """Physical building characteristics affecting energy performance"""
    year_built: int
    size_m2: float
    floors: int
    floor_level: int  # Which floor the property is on
    construction_type: ConstructionType
    orientation: Optional[str] = None  # N, S, E, W, NE, etc.
    balconies: int = 0
    windows_type: str = "single"  # single, double, triple
    heating_system: str = "oil"   # oil, gas, electric, heat_pump, solar
    cooling_system: str = "ac"    # ac, none, central
    insulation_walls: bool = False
    insulation_roof: bool = False
    solar_panels: bool = False


@dataclass
class EnergyAssessment:
    """Complete energy assessment result"""
    property_id: str
    current_energy_class: EnergyClass
    estimated_consumption_kwh_m2: float
    annual_energy_cost_eur: float
    co2_emissions_kg_year: float
    assessment_confidence: float  # 0.0 to 1.0
    factors_analysis: Dict[str, float]
    upgrade_potential: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UpgradeOption:
    """Individual energy upgrade option"""
    name: str
    description: str
    cost_eur: float
    annual_savings_kwh: float
    annual_savings_eur: float
    energy_class_improvement: int  # How many classes it improves
    implementation_time_days: int
    government_subsidy_eur: float
    roi_years: float
    priority_score: float


class EnergyAssessmentEngine:
    """
    Core energy assessment engine for Greek properties
    Based on Greek building regulations and EU energy standards
    """
    
    def __init__(self):
        """Initialize energy assessment engine"""
        # Greek energy cost per kWh (average 2024)
        self.electricity_cost_kwh = 0.15  # €0.15/kWh
        self.heating_oil_cost_liter = 1.20  # €1.20/liter
        self.natural_gas_cost_kwh = 0.08   # €0.08/kWh equivalent
        
        # CO2 emission factors (kg CO2/kWh)
        self.co2_factor_electricity = 0.7  # Greek grid mix
        self.co2_factor_oil = 0.27
        self.co2_factor_gas = 0.2
        
        # Greek climate data (Athens region)
        self.heating_degree_days = 1200
        self.cooling_degree_days = 800
        
        # Government subsidy rates (2024)
        self.subsidy_rates = {
            "insulation": 0.7,        # 70% subsidy
            "windows": 0.6,           # 60% subsidy
            "heat_pump": 0.5,         # 50% subsidy
            "solar_panels": 0.4,      # 40% subsidy
            "smart_thermostat": 0.8   # 80% subsidy
        }
        
        logger.info("Energy assessment engine initialized")
    
    def assess_property(self, property_data: Dict[str, Any]) -> EnergyAssessment:
        """
        Main energy assessment function
        
        Args:
            property_data: Property information dictionary
            
        Returns:
            Complete energy assessment
        """
        # Extract building characteristics
        building = self._extract_building_characteristics(property_data)
        
        # Calculate current energy performance
        energy_class, consumption_kwh_m2 = self._calculate_current_energy_class(building)
        
        # Calculate energy costs
        annual_cost = self._calculate_annual_energy_cost(building, consumption_kwh_m2)
        
        # Calculate CO2 emissions
        co2_emissions = self._calculate_co2_emissions(building, consumption_kwh_m2)
        
        # Analyze factors affecting energy performance
        factors = self._analyze_energy_factors(building)
        
        # Assess upgrade potential
        upgrade_potential = self._assess_upgrade_potential(building, energy_class)
        
        # Calculate assessment confidence
        confidence = self._calculate_confidence(property_data)
        
        return EnergyAssessment(
            property_id=property_data.get('id', 'unknown'),
            current_energy_class=energy_class,
            estimated_consumption_kwh_m2=consumption_kwh_m2,
            annual_energy_cost_eur=annual_cost,
            co2_emissions_kg_year=co2_emissions,
            assessment_confidence=confidence,
            factors_analysis=factors,
            upgrade_potential=upgrade_potential
        )
    
    def _extract_building_characteristics(self, property_data: Dict[str, Any]) -> BuildingCharacteristics:
        """Extract building characteristics from property data"""
        year_built = property_data.get('year_built', 1980)
        size_m2 = property_data.get('size', 80.0)
        floor_level = property_data.get('floor', 2)
        
        # Determine construction type based on year and other factors
        construction_type = self._determine_construction_type(year_built, property_data)
        
        # Extract or estimate other characteristics
        return BuildingCharacteristics(
            year_built=year_built,
            size_m2=size_m2,
            floors=property_data.get('floors', 1),
            floor_level=floor_level,
            construction_type=construction_type,
            orientation=property_data.get('orientation'),
            balconies=property_data.get('balconies', 1),
            windows_type=self._estimate_windows_type(year_built),
            heating_system=property_data.get('heating_system', self._estimate_heating_system(year_built)),
            cooling_system=property_data.get('cooling_system', 'ac'),
            insulation_walls=property_data.get('insulation_walls', year_built > 2010),
            insulation_roof=property_data.get('insulation_roof', year_built > 2010),
            solar_panels=property_data.get('solar_panels', False)
        )
    
    def _determine_construction_type(self, year_built: int, property_data: Dict[str, Any]) -> ConstructionType:
        """Determine construction type based on building year and characteristics"""
        if year_built >= 2010:
            return ConstructionType.MODERN_INSULATED
        elif year_built >= 1990:
            return ConstructionType.MODERN_BASIC
        elif year_built >= 1950:
            # Check if it's an apartment block
            if property_data.get('building_type') == 'apartment' or property_data.get('floor', 0) > 0:
                return ConstructionType.APARTMENT_BLOCK
            else:
                return ConstructionType.TRADITIONAL_RENOVATED
        else:
            return ConstructionType.NEOCLASSICAL
    
    def _estimate_windows_type(self, year_built: int) -> str:
        """Estimate window type based on construction year"""
        if year_built >= 2010:
            return "double"
        elif year_built >= 2000:
            return "single"  # May have been upgraded
        else:
            return "single"
    
    def _estimate_heating_system(self, year_built: int) -> str:
        """Estimate heating system based on construction year"""
        if year_built >= 2015:
            return "gas"  # More modern systems
        elif year_built >= 2000:
            return "gas"
        else:
            return "oil"  # Traditional heating
    
    def _calculate_current_energy_class(self, building: BuildingCharacteristics) -> Tuple[EnergyClass, float]:
        """
        Calculate current energy class and consumption
        Based on Greek building energy regulations
        """
        # Base consumption by construction type (kWh/m²/year)
        base_consumption = {
            ConstructionType.MODERN_INSULATED: 80,
            ConstructionType.MODERN_BASIC: 120,
            ConstructionType.TRADITIONAL_RENOVATED: 150,
            ConstructionType.TRADITIONAL_ORIGINAL: 200,
            ConstructionType.NEOCLASSICAL: 250,
            ConstructionType.APARTMENT_BLOCK: 160
        }
        
        consumption = base_consumption[building.construction_type]
        
        # Adjust for building characteristics
        
        # Age factor (newer is more efficient)
        age_factor = max(0.8, 1 - (2024 - building.year_built) * 0.005)
        consumption *= age_factor
        
        # Size factor (smaller properties are less efficient)
        if building.size_m2 < 50:
            consumption *= 1.2
        elif building.size_m2 > 150:
            consumption *= 0.9
        
        # Floor level factor (middle floors are more efficient)
        if building.floor_level == 0:  # Ground floor
            consumption *= 1.1  # More heat loss
        elif building.floor_level >= 5:  # Top floors
            consumption *= 1.15  # Heat loss through roof
        
        # Windows factor
        if building.windows_type == "double":
            consumption *= 0.8
        elif building.windows_type == "triple":
            consumption *= 0.7
        
        # Insulation factors
        if building.insulation_walls:
            consumption *= 0.7
        if building.insulation_roof:
            consumption *= 0.8
        
        # Heating system efficiency
        heating_efficiency = {
            "heat_pump": 0.6,    # Most efficient
            "gas": 0.8,          # Efficient
            "oil": 1.0,          # Base efficiency
            "electric": 1.2,     # Less efficient
            "solar": 0.4         # Very efficient (with backup)
        }
        consumption *= heating_efficiency.get(building.heating_system, 1.0)
        
        # Solar panels bonus
        if building.solar_panels:
            consumption *= 0.7
        
        # Determine energy class from consumption
        for energy_class in EnergyClass:
            min_kwh, max_kwh = energy_class.kwh_per_m2_range
            if min_kwh <= consumption <= max_kwh:
                return energy_class, consumption
        
        # If consumption is very high, assign worst class
        return EnergyClass.G, consumption
    
    def _calculate_annual_energy_cost(self, building: BuildingCharacteristics, 
                                     consumption_kwh_m2: float) -> float:
        """Calculate annual energy cost in EUR"""
        total_consumption_kwh = consumption_kwh_m2 * building.size_m2
        
        # Cost depends on heating system
        if building.heating_system == "electric":
            annual_cost = total_consumption_kwh * self.electricity_cost_kwh
        elif building.heating_system == "gas":
            annual_cost = total_consumption_kwh * self.natural_gas_cost_kwh
        elif building.heating_system == "oil":
            # Convert kWh to liters (roughly 10 kWh per liter)
            liters_needed = total_consumption_kwh / 10
            annual_cost = liters_needed * self.heating_oil_cost_liter
        elif building.heating_system == "heat_pump":
            # Heat pumps are more efficient
            annual_cost = total_consumption_kwh * self.electricity_cost_kwh * 0.6
        else:
            # Default to electricity
            annual_cost = total_consumption_kwh * self.electricity_cost_kwh
        
        return round(annual_cost, 2)
    
    def _calculate_co2_emissions(self, building: BuildingCharacteristics, 
                                consumption_kwh_m2: float) -> float:
        """Calculate annual CO2 emissions in kg"""
        total_consumption_kwh = consumption_kwh_m2 * building.size_m2
        
        # CO2 factor depends on energy source
        if building.heating_system in ["electric", "heat_pump"]:
            co2_factor = self.co2_factor_electricity
        elif building.heating_system == "gas":
            co2_factor = self.co2_factor_gas
        elif building.heating_system == "oil":
            co2_factor = self.co2_factor_oil
        else:
            co2_factor = self.co2_factor_electricity
        
        annual_emissions = total_consumption_kwh * co2_factor
        
        # Solar panels reduce emissions
        if building.solar_panels:
            annual_emissions *= 0.6
        
        return round(annual_emissions, 1)
    
    def _analyze_energy_factors(self, building: BuildingCharacteristics) -> Dict[str, float]:
        """
        Analyze factors contributing to energy performance
        Returns scores from 0 (poor) to 1 (excellent)
        """
        factors = {}
        
        # Insulation factor
        insulation_score = 0
        if building.insulation_walls:
            insulation_score += 0.5
        if building.insulation_roof:
            insulation_score += 0.5
        factors['insulation'] = insulation_score
        
        # Windows factor
        windows_score = {
            "single": 0.3,
            "double": 0.7,
            "triple": 1.0
        }.get(building.windows_type, 0.3)
        factors['windows'] = windows_score
        
        # Heating system factor
        heating_score = {
            "solar": 1.0,
            "heat_pump": 0.9,
            "gas": 0.7,
            "oil": 0.4,
            "electric": 0.3
        }.get(building.heating_system, 0.5)
        factors['heating_system'] = heating_score
        
        # Building age factor
        age = 2024 - building.year_built
        if age <= 10:
            age_score = 1.0
        elif age <= 20:
            age_score = 0.8
        elif age <= 40:
            age_score = 0.6
        else:
            age_score = 0.3
        factors['building_age'] = age_score
        
        # Size efficiency factor
        if building.size_m2 >= 80 and building.size_m2 <= 120:
            size_score = 1.0  # Optimal size
        elif building.size_m2 >= 60 and building.size_m2 <= 150:
            size_score = 0.8
        else:
            size_score = 0.6  # Very small or very large
        factors['size_efficiency'] = size_score
        
        # Renewable energy factor
        renewable_score = 1.0 if building.solar_panels else 0.0
        factors['renewable_energy'] = renewable_score
        
        return factors
    
    def _assess_upgrade_potential(self, building: BuildingCharacteristics, 
                                 current_class: EnergyClass) -> Dict[str, Any]:
        """Assess potential energy upgrades and their impact"""
        upgrades = []
        
        # Wall insulation upgrade
        if not building.insulation_walls:
            cost = building.size_m2 * 45  # €45/m² for external insulation
            savings_kwh_m2 = 40  # Typical savings
            subsidy = cost * self.subsidy_rates["insulation"]
            
            upgrades.append({
                "name": "Wall Insulation",
                "cost_eur": cost,
                "subsidy_eur": subsidy,
                "net_cost_eur": cost - subsidy,
                "annual_savings_kwh_m2": savings_kwh_m2,
                "annual_savings_eur": savings_kwh_m2 * building.size_m2 * self.electricity_cost_kwh,
                "energy_class_improvement": 1,
                "payback_years": (cost - subsidy) / (savings_kwh_m2 * building.size_m2 * self.electricity_cost_kwh),
                "priority": "high"
            })
        
        # Window replacement
        if building.windows_type == "single":
            # Estimate 1 window per 15m²
            num_windows = math.ceil(building.size_m2 / 15)
            cost = num_windows * 400  # €400 per double-glazed window
            savings_kwh_m2 = 25
            subsidy = cost * self.subsidy_rates["windows"]
            
            upgrades.append({
                "name": "Double-Glazed Windows",
                "cost_eur": cost,
                "subsidy_eur": subsidy,
                "net_cost_eur": cost - subsidy,
                "annual_savings_kwh_m2": savings_kwh_m2,
                "annual_savings_eur": savings_kwh_m2 * building.size_m2 * self.electricity_cost_kwh,
                "energy_class_improvement": 1,
                "payback_years": (cost - subsidy) / (savings_kwh_m2 * building.size_m2 * self.electricity_cost_kwh),
                "priority": "medium"
            })
        
        # Heat pump upgrade
        if building.heating_system in ["oil", "electric"]:
            cost = 8000  # Average heat pump installation
            savings_kwh_m2 = 50  # Significant savings from oil/electric
            subsidy = cost * self.subsidy_rates["heat_pump"]
            
            upgrades.append({
                "name": "Heat Pump System",
                "cost_eur": cost,
                "subsidy_eur": subsidy,
                "net_cost_eur": cost - subsidy,
                "annual_savings_kwh_m2": savings_kwh_m2,
                "annual_savings_eur": savings_kwh_m2 * building.size_m2 * self.electricity_cost_kwh,
                "energy_class_improvement": 2,
                "payback_years": (cost - subsidy) / (savings_kwh_m2 * building.size_m2 * self.electricity_cost_kwh),
                "priority": "high"
            })
        
        # Solar panels
        if not building.solar_panels and building.floor_level >= 3:  # Higher floors suitable for solar
            # 1 kW per 10m² of property
            kw_capacity = building.size_m2 / 10
            cost = kw_capacity * 1500  # €1500 per kW installed
            annual_generation_kwh = kw_capacity * 1300  # Athens solar potential
            savings_eur = annual_generation_kwh * self.electricity_cost_kwh
            subsidy = cost * self.subsidy_rates["solar_panels"]
            
            upgrades.append({
                "name": "Solar Panels",
                "cost_eur": cost,
                "subsidy_eur": subsidy,
                "net_cost_eur": cost - subsidy,
                "annual_savings_kwh": annual_generation_kwh,
                "annual_savings_eur": savings_eur,
                "energy_class_improvement": 1,
                "payback_years": (cost - subsidy) / savings_eur,
                "priority": "medium"
            })
        
        # Calculate potential energy class after all upgrades
        potential_improvement = sum(u["energy_class_improvement"] for u in upgrades)
        max_potential_class = max(1, current_class.numeric_value - potential_improvement)
        
        # Convert back to energy class
        class_mapping = {v.numeric_value: v for v in EnergyClass}
        potential_class = class_mapping.get(max_potential_class, EnergyClass.A_PLUS)
        
        return {
            "upgrades": upgrades,
            "total_investment_eur": sum(u["cost_eur"] for u in upgrades),
            "total_subsidies_eur": sum(u["subsidy_eur"] for u in upgrades),
            "total_net_cost_eur": sum(u["net_cost_eur"] for u in upgrades),
            "total_annual_savings_eur": sum(u["annual_savings_eur"] for u in upgrades),
            "potential_energy_class": potential_class.value,
            "energy_class_improvement": potential_improvement,
            "average_payback_years": sum(u["payback_years"] for u in upgrades) / len(upgrades) if upgrades else 0
        }
    
    def _calculate_confidence(self, property_data: Dict[str, Any]) -> float:
        """Calculate confidence level of the assessment"""
        confidence = 1.0
        
        # Reduce confidence for missing data
        required_fields = ['year_built', 'size', 'floor']
        for field in required_fields:
            if field not in property_data or property_data[field] is None:
                confidence -= 0.2
        
        # Bonus for additional data
        bonus_fields = ['heating_system', 'insulation_walls', 'windows_type']
        for field in bonus_fields:
            if field in property_data and property_data[field] is not None:
                confidence += 0.05
        
        return max(0.5, min(1.0, confidence))  # Keep between 0.5 and 1.0


# Helper functions for integration

def assess_property_energy(property_data: Dict[str, Any]) -> EnergyAssessment:
    """
    Convenient function to assess property energy performance
    
    Args:
        property_data: Property information dictionary
        
    Returns:
        Complete energy assessment
    """
    engine = EnergyAssessmentEngine()
    return engine.assess_property(property_data)


def get_upgrade_recommendations(property_data: Dict[str, Any], 
                              budget_eur: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Get prioritized upgrade recommendations within budget
    
    Args:
        property_data: Property information
        budget_eur: Maximum budget for upgrades
        
    Returns:
        List of recommended upgrades
    """
    assessment = assess_property_energy(property_data)
    upgrades = assessment.upgrade_potential["upgrades"]
    
    # Sort by payback period (ROI)
    sorted_upgrades = sorted(upgrades, key=lambda x: x["payback_years"])
    
    if budget_eur is None:
        return sorted_upgrades
    
    # Filter by budget
    affordable_upgrades = []
    remaining_budget = budget_eur
    
    for upgrade in sorted_upgrades:
        if upgrade["net_cost_eur"] <= remaining_budget:
            affordable_upgrades.append(upgrade)
            remaining_budget -= upgrade["net_cost_eur"]
    
    return affordable_upgrades