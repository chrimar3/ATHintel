"""
🔧 Feature Engineering for Energy Prediction

Advanced feature extraction and engineering for ML energy prediction models.
Optimized for Greek building characteristics and energy market conditions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import math
import numpy as np

from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.entities.property_energy import BuildingType, HeatingSystem

@dataclass(frozen=True)
class BuildingFeatures:
    """
    Engineered features representing building characteristics
    optimized for Greek energy assessment models
    """
    
    # Basic building metrics
    total_area: float
    construction_year: int
    building_age: int
    floors_count: int
    
    # Building type encoding
    building_type_residential: int
    building_type_commercial: int
    building_type_mixed_use: int
    building_type_industrial: int
    
    # Geometric features
    surface_to_volume_ratio: float  # Heat loss indicator
    window_to_wall_ratio: float    # Solar gain/loss
    
    # Construction era features (Greek-specific periods)
    pre_1980_construction: int     # Pre-thermal regulations
    thermal_regulation_era: int    # 1980-2010 (first regulations)
    modern_construction: int       # Post-2010 (stricter standards)
    
    # Energy system features
    heating_system_efficiency: float
    has_central_heating: int
    has_individual_heating: int
    heating_fuel_gas: int
    heating_fuel_oil: int
    heating_fuel_electric: int
    heating_fuel_renewable: int
    
    # Insulation and efficiency features
    wall_insulation_score: float      # 0-1 scale
    roof_insulation_score: float
    window_efficiency_score: float
    
    # Renovation indicators
    has_recent_renovation: int         # Last 5 years
    renovation_age_years: int
    renovation_quality_score: float   # 0-1 scale
    
    # Geographic and climate factors
    climate_zone: int                  # Greek climate zones 1-4
    heating_degree_days: float        # Annual HDD for location
    cooling_degree_days: float        # Annual CDD for location
    solar_irradiance: float           # kWh/m²/year
    
    # Urban context
    urban_density: float              # Population per km²
    building_density: float           # Buildings per hectare
    proximity_to_city_center: float  # km to nearest major city
    
    @classmethod
    def extract_from_property(
        cls,
        property_data: Dict[str, Any],
        climate_data: Optional[Dict[str, Any]] = None
    ) -> 'BuildingFeatures':
        """Extract building features from property data"""
        
        current_year = datetime.now().year
        construction_year = property_data.get('construction_year', 1980)
        building_age = current_year - construction_year
        
        # Building type encoding
        building_type = property_data.get('building_type', 'apartment')
        building_type_encoding = {
            'residential': (1, 0, 0, 0),
            'apartment': (1, 0, 0, 0),
            'maisonette': (1, 0, 0, 0),
            'commercial': (0, 1, 0, 0),
            'office': (0, 1, 0, 0),
            'mixed_use': (0, 0, 1, 0),
            'industrial': (0, 0, 0, 1),
        }
        building_encoding = building_type_encoding.get(building_type, (1, 0, 0, 0))
        
        # Calculate geometric features
        total_area = float(property_data.get('total_area', 100))
        floors = property_data.get('floors_count', 3)
        
        # Estimate surface-to-volume ratio (proxy for heat loss)
        # Assuming square building with 3m ceiling height
        building_width = math.sqrt(total_area / floors)
        building_height = floors * 3.0
        surface_area = 2 * building_width * building_height + 2 * total_area  # walls + floors
        volume = total_area * building_height
        surface_to_volume = surface_area / volume if volume > 0 else 1.0
        
        # Window-to-wall ratio estimation
        window_area = property_data.get('window_area', total_area * 0.15)  # 15% default
        wall_area = surface_area - 2 * total_area  # Subtract floors
        window_to_wall = window_area / wall_area if wall_area > 0 else 0.15
        
        # Construction era classification
        pre_1980 = 1 if construction_year < 1980 else 0
        thermal_reg = 1 if 1980 <= construction_year <= 2010 else 0
        modern = 1 if construction_year > 2010 else 0
        
        # Heating system features
        heating_system = property_data.get('heating_system', 'individual_gas')
        heating_efficiency_map = {
            'central_gas': 0.85,
            'individual_gas': 0.80,
            'central_oil': 0.75,
            'individual_oil': 0.70,
            'electric': 0.95,
            'heat_pump': 0.90,
            'solar': 0.85,
            'fireplace': 0.30,
        }
        heating_efficiency = heating_efficiency_map.get(heating_system, 0.75)
        
        # Heating system type encoding
        has_central = 1 if 'central' in heating_system else 0
        has_individual = 1 if 'individual' in heating_system else 0
        fuel_gas = 1 if 'gas' in heating_system else 0
        fuel_oil = 1 if 'oil' in heating_system else 0
        fuel_electric = 1 if 'electric' in heating_system or 'heat_pump' in heating_system else 0
        fuel_renewable = 1 if 'solar' in heating_system or 'heat_pump' in heating_system else 0
        
        # Insulation scores (0-1 scale)
        insulation_data = property_data.get('insulation', {})\n        wall_insulation = cls._calculate_insulation_score(\n            insulation_data.get('walls', 'none'),\n            building_age\n        )\n        roof_insulation = cls._calculate_insulation_score(\n            insulation_data.get('roof', 'none'),\n            building_age\n        )\n        \n        # Window efficiency based on age and type\n        window_type = property_data.get('window_type', 'single_glazed')\n        window_efficiency = cls._calculate_window_efficiency(window_type, building_age)\n        \n        # Renovation features\n        renovation_year = property_data.get('last_renovation_year', construction_year)\n        renovation_age = current_year - renovation_year\n        has_recent_renovation = 1 if renovation_age <= 5 else 0\n        renovation_quality = cls._estimate_renovation_quality(\n            property_data.get('renovation_scope', []),\n            renovation_age\n        )\n        \n        # Climate features (use defaults if not provided)\n        climate = climate_data or cls._get_default_climate_data()\n        climate_zone = climate.get('zone', 2)  # Athens default\n        heating_dd = float(climate.get('heating_degree_days', 1200))\n        cooling_dd = float(climate.get('cooling_degree_days', 400))\n        solar_irr = float(climate.get('solar_irradiance', 1600))\n        \n        # Urban context\n        location_data = property_data.get('location', {})\n        urban_density = float(location_data.get('population_density', 5000))\n        building_density = float(location_data.get('building_density', 25))\n        city_distance = float(location_data.get('distance_to_center', 10))\n        \n        return cls(\n            total_area=total_area,\n            construction_year=construction_year,\n            building_age=building_age,\n            floors_count=floors,\n            \n            building_type_residential=building_encoding[0],\n            building_type_commercial=building_encoding[1],\n            building_type_mixed_use=building_encoding[2],\n            building_type_industrial=building_encoding[3],\n            \n            surface_to_volume_ratio=surface_to_volume,\n            window_to_wall_ratio=min(window_to_wall, 0.5),  # Cap at 50%\n            \n            pre_1980_construction=pre_1980,\n            thermal_regulation_era=thermal_reg,\n            modern_construction=modern,\n            \n            heating_system_efficiency=heating_efficiency,\n            has_central_heating=has_central,\n            has_individual_heating=has_individual,\n            heating_fuel_gas=fuel_gas,\n            heating_fuel_oil=fuel_oil,\n            heating_fuel_electric=fuel_electric,\n            heating_fuel_renewable=fuel_renewable,\n            \n            wall_insulation_score=wall_insulation,\n            roof_insulation_score=roof_insulation,\n            window_efficiency_score=window_efficiency,\n            \n            has_recent_renovation=has_recent_renovation,\n            renovation_age_years=min(renovation_age, 50),\n            renovation_quality_score=renovation_quality,\n            \n            climate_zone=climate_zone,\n            heating_degree_days=heating_dd,\n            cooling_degree_days=cooling_dd,\n            solar_irradiance=solar_irr,\n            \n            urban_density=min(urban_density, 20000),  # Cap outliers\n            building_density=min(building_density, 100),\n            proximity_to_city_center=min(city_distance, 100)\n        )\n    \n    @staticmethod\n    def _calculate_insulation_score(insulation_type: str, building_age: int) -> float:\n        \"\"\"Calculate insulation effectiveness score (0-1)\"\"\"\n        base_scores = {\n            'none': 0.0,\n            'minimal': 0.2,\n            'basic': 0.4,\n            'good': 0.7,\n            'excellent': 0.9,\n            'premium': 1.0\n        }\n        \n        base_score = base_scores.get(insulation_type, 0.3)\n        \n        # Degradation over time\n        if building_age > 20:\n            degradation = min(0.3, (building_age - 20) * 0.01)  # 1% per year after 20\n            base_score = max(0.0, base_score - degradation)\n        \n        return base_score\n    \n    @staticmethod\n    def _calculate_window_efficiency(window_type: str, building_age: int) -> float:\n        \"\"\"Calculate window efficiency score (0-1)\"\"\"\n        window_scores = {\n            'single_glazed': 0.2,\n            'double_glazed': 0.6,\n            'triple_glazed': 0.9,\n            'energy_efficient': 0.95\n        }\n        \n        score = window_scores.get(window_type, 0.4)\n        \n        # Age-based degradation\n        if building_age > 15:\n            degradation = min(0.2, (building_age - 15) * 0.005)\n            score = max(0.1, score - degradation)\n        \n        return score\n    \n    @staticmethod\n    def _estimate_renovation_quality(renovation_scope: List[str], renovation_age: int) -> float:\n        \"\"\"Estimate renovation quality score (0-1)\"\"\"\n        if not renovation_scope:\n            return 0.0\n        \n        scope_weights = {\n            'insulation': 0.3,\n            'heating_system': 0.25,\n            'windows': 0.2,\n            'roof': 0.15,\n            'electrical': 0.05,\n            'plumbing': 0.05\n        }\n        \n        quality_score = sum(scope_weights.get(item, 0.02) for item in renovation_scope)\n        quality_score = min(1.0, quality_score)\n        \n        # Recent renovations are more effective\n        if renovation_age <= 2:\n            quality_score *= 1.0\n        elif renovation_age <= 5:\n            quality_score *= 0.9\n        else:\n            quality_score *= max(0.5, 1.0 - (renovation_age - 5) * 0.05)\n        \n        return quality_score\n    \n    @staticmethod\n    def _get_default_climate_data() -> Dict[str, Any]:\n        \"\"\"Get default climate data for Athens, Greece\"\"\"\n        return {\n            'zone': 2,\n            'heating_degree_days': 1200,\n            'cooling_degree_days': 400,\n            'solar_irradiance': 1600\n        }\n    \n    def to_array(self) -> np.ndarray:\n        \"\"\"Convert features to numpy array for ML models\"\"\"\n        return np.array([\n            self.total_area / 1000,  # Normalize to 0-1 range (max 1000m²)\n            self.construction_year / 2025,  # Normalize to 0-1\n            self.building_age / 100,  # Normalize to 0-1 (max 100 years)\n            self.floors_count / 20,  # Normalize to 0-1 (max 20 floors)\n            \n            self.building_type_residential,\n            self.building_type_commercial,\n            self.building_type_mixed_use,\n            self.building_type_industrial,\n            \n            self.surface_to_volume_ratio,\n            self.window_to_wall_ratio,\n            \n            self.pre_1980_construction,\n            self.thermal_regulation_era,\n            self.modern_construction,\n            \n            self.heating_system_efficiency,\n            self.has_central_heating,\n            self.has_individual_heating,\n            self.heating_fuel_gas,\n            self.heating_fuel_oil,\n            self.heating_fuel_electric,\n            self.heating_fuel_renewable,\n            \n            self.wall_insulation_score,\n            self.roof_insulation_score,\n            self.window_efficiency_score,\n            \n            self.has_recent_renovation,\n            self.renovation_age_years / 50,  # Normalize\n            self.renovation_quality_score,\n            \n            self.climate_zone / 4,  # Normalize (4 zones in Greece)\n            self.heating_degree_days / 2000,  # Normalize\n            self.cooling_degree_days / 1000,  # Normalize\n            self.solar_irradiance / 2000,  # Normalize\n            \n            self.urban_density / 20000,  # Normalize\n            self.building_density / 100,  # Normalize\n            self.proximity_to_city_center / 100  # Normalize\n        ])\n\n@dataclass(frozen=True)\nclass MarketFeatures:\n    \"\"\"Market and economic features for energy prediction\"\"\"\n    \n    # Energy prices (€/kWh)\n    electricity_price: float\n    gas_price: float\n    oil_price: float\n    \n    # Market trends\n    electricity_price_trend: float  # % change over last year\n    gas_price_trend: float\n    oil_price_trend: float\n    \n    # Economic indicators\n    gdp_growth: float\n    unemployment_rate: float\n    construction_index: float\n    \n    # Policy and subsidies\n    subsidy_availability: float    # 0-1 scale of available subsidies\n    environmental_policy_strength: float  # 0-1 scale\n    building_regulation_strictness: float  # 0-1 scale\n    \n    # Market activity\n    renovation_activity_index: float  # Regional renovation activity\n    energy_certificate_demand: float  # Certificates issued per month\n    \n    @classmethod\n    def get_current_greek_market(cls) -> 'MarketFeatures':\n        \"\"\"Get current Greek energy market features\"\"\"\n        return cls(\n            electricity_price=0.15,  # €/kWh\n            gas_price=0.08,\n            oil_price=0.12,\n            \n            electricity_price_trend=8.5,  # % increase\n            gas_price_trend=12.3,\n            oil_price_trend=5.7,\n            \n            gdp_growth=2.1,\n            unemployment_rate=12.3,\n            construction_index=0.65,\n            \n            subsidy_availability=0.75,  # High availability\n            environmental_policy_strength=0.80,\n            building_regulation_strictness=0.70,\n            \n            renovation_activity_index=0.68,\n            energy_certificate_demand=1250  # Certificates per month\n        )\n\n@dataclass(frozen=True)\nclass ClimateFeatures:\n    \"\"\"Climate and environmental features\"\"\"\n    \n    # Temperature data\n    avg_annual_temperature: float\n    winter_avg_temperature: float\n    summer_avg_temperature: float\n    \n    # Degree days\n    heating_degree_days: float\n    cooling_degree_days: float\n    \n    # Solar and wind\n    annual_solar_irradiance: float  # kWh/m²/year\n    avg_wind_speed: float          # m/s\n    \n    # Regional climate factors\n    coastal_influence: int         # 0 or 1\n    elevation: float              # meters above sea level\n    climate_zone: int             # Greek climate zones 1-4\n\nclass FeatureExtractor:\n    \"\"\"Main feature extraction orchestrator\"\"\"\n    \n    def __init__(self):\n        self.market_features = MarketFeatures.get_current_greek_market()\n    \n    def extract_all_features(\n        self,\n        property_data: Dict[str, Any],\n        climate_data: Optional[Dict[str, Any]] = None,\n        market_data: Optional[Dict[str, Any]] = None\n    ) -> Tuple[BuildingFeatures, MarketFeatures, Optional[ClimateFeatures]]:\n        \"\"\"Extract all feature types for a property\"\"\"\n        \n        # Extract building features\n        building_features = BuildingFeatures.extract_from_property(\n            property_data, climate_data\n        )\n        \n        # Use provided market data or current defaults\n        market_features = self.market_features\n        if market_data:\n            # Update with provided market data\n            pass\n        \n        # Extract climate features if data provided\n        climate_features = None\n        if climate_data:\n            climate_features = self._extract_climate_features(climate_data)\n        \n        return building_features, market_features, climate_features\n    \n    def _extract_climate_features(self, climate_data: Dict[str, Any]) -> ClimateFeatures:\n        \"\"\"Extract climate features from climate data\"\"\"\n        return ClimateFeatures(\n            avg_annual_temperature=float(climate_data.get('avg_temp', 16.5)),\n            winter_avg_temperature=float(climate_data.get('winter_temp', 8.0)),\n            summer_avg_temperature=float(climate_data.get('summer_temp', 26.0)),\n            heating_degree_days=float(climate_data.get('hdd', 1200)),\n            cooling_degree_days=float(climate_data.get('cdd', 400)),\n            annual_solar_irradiance=float(climate_data.get('solar', 1600)),\n            avg_wind_speed=float(climate_data.get('wind_speed', 3.5)),\n            coastal_influence=int(climate_data.get('coastal', 0)),\n            elevation=float(climate_data.get('elevation', 100)),\n            climate_zone=int(climate_data.get('zone', 2))\n        )\n    \n    def combine_features(self, *feature_sets) -> np.ndarray:\n        \"\"\"Combine multiple feature sets into single array\"\"\"\n        arrays = []\n        \n        for features in feature_sets:\n            if features is None:\n                continue\n                \n            if hasattr(features, 'to_array'):\n                arrays.append(features.to_array())\n            elif isinstance(features, np.ndarray):\n                arrays.append(features)\n        \n        if not arrays:\n            raise ValueError(\"No valid feature arrays provided\")\n        \n        return np.concatenate(arrays) if len(arrays) > 1 else arrays[0]