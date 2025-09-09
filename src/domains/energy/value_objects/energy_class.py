"""
🏗️ Energy Class Value Object

Represents EU Energy Performance Certificate Classes as an immutable value object
following Domain-Driven Design principles.
"""

from enum import Enum
from typing import Tuple, Dict
from decimal import Decimal

class EnergyClass(Enum):
    """
    EU Energy Performance Certificate Classes with Greek context
    
    Each class represents a range of energy consumption in kWh/m²/year
    and includes typical characteristics of Greek buildings in each category.
    """
    
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
        """Convert energy class to numeric value for calculations (1=best, 9=worst)"""
        mapping = {
            "A+": 1, "A": 2, "B+": 3, "B": 4, "C": 5,
            "D": 6, "E": 7, "F": 8, "G": 9
        }
        return mapping[self.value]

    @property
    def kwh_per_m2_range(self) -> Tuple[Decimal, Decimal]:
        """Energy consumption range in kWh/m²/year"""
        ranges = {
            "A+": (Decimal('0'), Decimal('50')),
            "A": (Decimal('51'), Decimal('75')),
            "B+": (Decimal('76'), Decimal('100')),
            "B": (Decimal('101'), Decimal('125')),
            "C": (Decimal('126'), Decimal('150')),
            "D": (Decimal('151'), Decimal('200')),
            "E": (Decimal('201'), Decimal('250')),
            "F": (Decimal('251'), Decimal('300')),
            "G": (Decimal('301'), Decimal('500'))
        }
        return ranges[self.value]
    
    @property
    def avg_kwh_per_m2(self) -> Decimal:
        """Average energy consumption for this class"""
        min_val, max_val = self.kwh_per_m2_range
        return (min_val + max_val) / 2
    
    @property
    def color_code(self) -> str:
        """Color code for UI representation"""
        colors = {
            "A+": "#00A651", "A": "#4CBB17", "B+": "#9ACD32", "B": "#ADFF2F",
            "C": "#FFFF00", "D": "#FFA500", "E": "#FF6347", "F": "#FF4500", "G": "#DC143C"
        }
        return colors[self.value]
    
    @property
    def description(self) -> str:
        """Human-readable description of energy class"""
        descriptions = {
            "A+": "Excellent energy performance - Very low consumption",
            "A": "Very good energy performance - Low consumption", 
            "B+": "Good energy performance - Moderate consumption",
            "B": "Good energy performance - Above average efficiency",
            "C": "Average energy performance - Typical consumption",
            "D": "Below average energy performance - Higher consumption",
            "E": "Poor energy performance - High consumption",
            "F": "Very poor energy performance - Very high consumption",
            "G": "Extremely poor energy performance - Excessive consumption"
        }
        return descriptions[self.value]
    
    @property
    def greek_context(self) -> Dict[str, str]:
        """Context specific to Greek buildings and market"""
        contexts = {
            "A+": {
                "typical_buildings": "New passive houses, premium renovations with latest technology",
                "market_premium": "15-20% higher property value",
                "heating_cost": "Very low - €200-400/year for 80m²",
                "renovation_status": "Recently renovated or new construction"
            },
            "A": {
                "typical_buildings": "Modern buildings with good insulation, efficient heating",
                "market_premium": "10-15% higher property value",
                "heating_cost": "Low - €400-600/year for 80m²",
                "renovation_status": "Well-maintained, some upgrades"
            },
            "B+": {
                "typical_buildings": "Well-insulated buildings, decent heating systems",
                "market_premium": "5-10% higher property value",
                "heating_cost": "Moderate - €600-800/year for 80m²",
                "renovation_status": "Basic renovations, adequate maintenance"
            },
            "B": {
                "typical_buildings": "Average buildings with some insulation",
                "market_premium": "Neutral market position",
                "heating_cost": "Moderate - €800-1000/year for 80m²",
                "renovation_status": "Minimal renovations needed"
            },
            "C": {
                "typical_buildings": "Typical Greek apartment blocks, basic heating",
                "market_premium": "Standard market value",
                "heating_cost": "Average - €1000-1200/year for 80m²",
                "renovation_status": "Some renovations recommended"
            },
            "D": {
                "typical_buildings": "Older buildings, poor insulation, inefficient heating",
                "market_premium": "5-10% below market average",
                "heating_cost": "High - €1200-1600/year for 80m²",
                "renovation_status": "Renovations recommended"
            },
            "E": {
                "typical_buildings": "Old buildings, no insulation, outdated heating",
                "market_premium": "10-15% below market average",
                "heating_cost": "Very high - €1600-2000/year for 80m²",
                "renovation_status": "Significant renovations needed"
            },
            "F": {
                "typical_buildings": "Very old buildings, major energy inefficiencies",
                "market_premium": "15-20% below market average",
                "heating_cost": "Extremely high - €2000-2400/year for 80m²",
                "renovation_status": "Major renovations required"
            },
            "G": {
                "typical_buildings": "Buildings in poor condition, severe energy waste",
                "market_premium": "20%+ below market average",
                "heating_cost": "Excessive - €2400+/year for 80m²",
                "renovation_status": "Complete renovation necessary"
            }
        }
        return contexts[self.value]
    
    def improvement_potential(self, target_class: 'EnergyClass') -> Dict[str, Decimal]:
        """Calculate improvement potential to target class"""
        if target_class.numeric_value >= self.numeric_value:
            return {
                'improvement_levels': Decimal('0'),
                'consumption_reduction_percentage': Decimal('0'),
                'cost_savings_percentage': Decimal('0')
            }
        
        improvement_levels = Decimal(self.numeric_value - target_class.numeric_value)
        
        # Estimate consumption and cost reduction
        current_avg = self.avg_kwh_per_m2
        target_avg = target_class.avg_kwh_per_m2
        
        consumption_reduction = ((current_avg - target_avg) / current_avg) * 100
        # Cost savings typically higher than consumption reduction due to efficiency gains
        cost_savings = consumption_reduction * Decimal('1.1')  # 10% additional savings
        
        return {
            'improvement_levels': improvement_levels,
            'consumption_reduction_percentage': consumption_reduction,
            'cost_savings_percentage': min(cost_savings, Decimal('80'))  # Cap at 80% savings
        }
    
    def get_upgrade_path(self) -> Dict[str, 'EnergyClass']:
        """Get realistic upgrade path from current class"""
        paths = {
            "G": {"achievable": EnergyClass.D, "ambitious": EnergyClass.B},
            "F": {"achievable": EnergyClass.D, "ambitious": EnergyClass.B},
            "E": {"achievable": EnergyClass.C, "ambitious": EnergyClass.B},
            "D": {"achievable": EnergyClass.B, "ambitious": EnergyClass.A},
            "C": {"achievable": EnergyClass.B, "ambitious": EnergyClass.A},
            "B": {"achievable": EnergyClass.A, "ambitious": EnergyClass.A_PLUS},
            "B+": {"achievable": EnergyClass.A, "ambitious": EnergyClass.A_PLUS},
            "A": {"achievable": EnergyClass.A_PLUS, "ambitious": EnergyClass.A_PLUS},
            "A+": {"achievable": EnergyClass.A_PLUS, "ambitious": EnergyClass.A_PLUS}
        }
        return paths[self.value]
    
    @classmethod
    def from_consumption(cls, kwh_per_m2: Decimal) -> 'EnergyClass':
        """Determine energy class from consumption value"""
        for energy_class in cls:
            min_val, max_val = energy_class.kwh_per_m2_range
            if min_val <= kwh_per_m2 <= max_val:
                return energy_class
        
        # If consumption is extremely high, return G
        if kwh_per_m2 > Decimal('500'):
            return cls.G
        
        # If consumption is very low, return A+
        return cls.A_PLUS
    
    @classmethod
    def estimate_from_building_age(cls, construction_year: int, has_renovations: bool = False) -> 'EnergyClass':
        """Estimate energy class based on building age and renovation status"""
        from datetime import datetime
        
        building_age = datetime.now().year - construction_year
        
        if building_age <= 5:
            # New construction (2020+)
            return cls.A if has_renovations else cls.B_PLUS
        elif building_age <= 15:
            # Modern construction (2010-2020)
            return cls.B if has_renovations else cls.C
        elif building_age <= 25:
            # Recent construction (2000-2010)
            return cls.B_PLUS if has_renovations else cls.D
        elif building_age <= 40:
            # 1980s-2000s construction
            return cls.C if has_renovations else cls.E
        elif building_age <= 60:
            # 1960s-1980s construction  
            return cls.D if has_renovations else cls.F
        else:
            # Pre-1960s construction
            return cls.E if has_renovations else cls.G
    
    def __str__(self) -> str:
        return f"Energy Class {self.value}"
    
    def __repr__(self) -> str:
        return f"EnergyClass.{self.name}"