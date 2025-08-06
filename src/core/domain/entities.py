"""
Domain Entities - Core Business Objects

These represent the fundamental concepts in our real estate investment domain.
They contain business rules and invariants, but no external dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional, Set
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel, Field, ConfigDict, computed_field


class PropertyType(str, Enum):
    """Property type enumeration"""
    APARTMENT = "apartment"
    HOUSE = "house" 
    STUDIO = "studio"
    PENTHOUSE = "penthouse"
    MAISONETTE = "maisonette"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    WAREHOUSE = "warehouse"


class EnergyClass(str, Enum):
    """Energy efficiency class"""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    UNDER_PUBLICATION = "under_publication"


class ListingType(str, Enum):
    """Listing type enumeration"""
    SALE = "sale"
    RENT = "rent"


class InvestmentRisk(str, Enum):
    """Investment risk levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Location:
    """Geographic location with enhanced precision"""
    neighborhood: str
    district: Optional[str] = None
    municipality: Optional[str] = "Athens"
    region: Optional[str] = "Attica"
    country: str = "Greece"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    postal_code: Optional[str] = None
    
    def __post_init__(self):
        """Validate coordinates if provided"""
        if self.latitude and not (-90 <= self.latitude <= 90):
            raise ValueError("Invalid latitude")
        if self.longitude and not (-180 <= self.longitude <= 180):
            raise ValueError("Invalid longitude")


class Property(BaseModel):
    """
    Core Property entity with comprehensive real estate attributes
    
    This represents a real estate property with all its characteristics,
    market data, and derived investment metrics.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )
    
    # Core Identity
    property_id: str = Field(..., description="Unique property identifier")
    url: Optional[str] = Field(None, description="Source URL")
    
    # Property Characteristics
    title: str = Field(..., description="Property title/description")
    property_type: PropertyType = Field(..., description="Type of property")
    listing_type: ListingType = Field(..., description="Sale or rental listing")
    
    # Location
    location: Location = Field(..., description="Geographic location")
    
    # Physical Attributes
    sqm: Optional[float] = Field(None, ge=0, description="Square meters")
    rooms: Optional[int] = Field(None, ge=0, description="Number of rooms")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, ge=0, description="Number of bathrooms")
    floor: Optional[int] = Field(None, description="Floor number")
    total_floors: Optional[int] = Field(None, ge=0, description="Total building floors")
    
    # Energy & Technical
    energy_class: Optional[EnergyClass] = Field(None, description="Energy efficiency class")
    year_built: Optional[int] = Field(None, ge=1800, le=2030, description="Construction year")
    renovation_year: Optional[int] = Field(None, ge=1800, le=2030, description="Last renovation")
    
    # Financial
    price: Decimal = Field(..., ge=0, description="Property price in EUR")
    common_charges: Optional[Decimal] = Field(None, ge=0, description="Monthly common charges")
    heating_costs: Optional[Decimal] = Field(None, ge=0, description="Annual heating costs")
    
    # Market Data
    timestamp: datetime = Field(default_factory=datetime.now, description="Data collection timestamp")
    source: str = Field(default="spitogatos", description="Data source")
    extraction_confidence: float = Field(default=0.9, ge=0, le=1, description="Data extraction confidence")
    
    # Validation & Quality
    validation_flags: List[str] = Field(default_factory=list, description="Data validation flags")
    html_source_hash: Optional[str] = Field(None, description="Source HTML hash for change detection")
    
    # Additional Features
    features: Dict[str, bool] = Field(default_factory=dict, description="Property features (parking, pool, etc.)")
    description: Optional[str] = Field(None, description="Full property description")
    
    @computed_field
    @property
    def price_per_sqm(self) -> Optional[Decimal]:
        """Calculate price per square meter"""
        if self.sqm and self.sqm > 0:
            return self.price / Decimal(str(self.sqm))
        return None
    
    @computed_field
    @property
    def neighborhood_key(self) -> str:
        """Normalized neighborhood key for grouping"""
        return self.location.neighborhood.lower().replace(" ", "_").replace("-", "_")
    
    def calculate_investment_score(self, market_data: Dict) -> float:
        """
        Calculate investment attractiveness score (0-100)
        Based on multiple factors including price, location, condition, etc.
        """
        score = 50.0  # Base score
        
        # Price competitiveness (compare to neighborhood average)
        if self.price_per_sqm and self.neighborhood_key in market_data:
            neighborhood_avg = market_data[self.neighborhood_key].get('avg_price_per_sqm', 0)
            if neighborhood_avg > 0:
                price_ratio = float(self.price_per_sqm) / neighborhood_avg
                if price_ratio < 0.9:  # Below market
                    score += 15
                elif price_ratio > 1.1:  # Above market
                    score -= 10
        
        # Energy efficiency bonus
        energy_scores = {
            EnergyClass.A_PLUS: 10, EnergyClass.A: 8, EnergyClass.B_PLUS: 6,
            EnergyClass.B: 4, EnergyClass.C: 2, EnergyClass.D: 0,
            EnergyClass.E: -3, EnergyClass.F: -6, EnergyClass.G: -10
        }
        if self.energy_class:
            score += energy_scores.get(self.energy_class, 0)
        
        # Size efficiency (optimal range 50-120 sqm for apartments)
        if self.sqm:
            if 50 <= self.sqm <= 120:
                score += 5
            elif self.sqm < 30 or self.sqm > 200:
                score -= 5
        
        # Year built/renovation bonus
        current_year = datetime.now().year
        if self.renovation_year and current_year - self.renovation_year <= 10:
            score += 8
        elif self.year_built and current_year - self.year_built <= 15:
            score += 5
        elif self.year_built and current_year - self.year_built >= 50:
            score -= 5
        
        return max(0, min(100, score))
    
    def estimate_rental_yield(self, market_data: Dict) -> Optional[float]:
        """Estimate annual rental yield percentage"""
        if self.listing_type != ListingType.SALE:
            return None
            
        # Use market data to estimate rental income
        if self.neighborhood_key in market_data:
            avg_rent_per_sqm = market_data[self.neighborhood_key].get('avg_rent_per_sqm', 0)
            if avg_rent_per_sqm and self.sqm:
                annual_rent = avg_rent_per_sqm * self.sqm * 12
                yield_pct = (annual_rent / float(self.price)) * 100
                return round(yield_pct, 2)
        
        # Fallback estimate based on property type and location
        base_yields = {
            PropertyType.STUDIO: 4.5,
            PropertyType.APARTMENT: 4.0,
            PropertyType.HOUSE: 3.5,
            PropertyType.PENTHOUSE: 3.0,
        }
        return base_yields.get(self.property_type, 3.5)


class Investment(BaseModel):
    """Investment opportunity analysis"""
    model_config = ConfigDict(validate_assignment=True)
    
    investment_id: str = Field(default_factory=lambda: str(uuid4()))
    property: Property
    analysis_date: datetime = Field(default_factory=datetime.now)
    
    # Investment Metrics
    investment_score: float = Field(..., ge=0, le=100)
    estimated_rental_yield: Optional[float] = Field(None, ge=0, le=50)
    roi_projection_5y: Optional[float] = Field(None, description="5-year ROI projection")
    risk_level: InvestmentRisk = Field(default=InvestmentRisk.MEDIUM)
    
    # Market Analysis
    neighborhood_rank: Optional[int] = Field(None, ge=1, description="Neighborhood ranking")
    price_trend: Optional[str] = Field(None, description="Price trend indicator")
    market_liquidity: Optional[float] = Field(None, ge=0, le=1, description="Market liquidity score")
    
    # Investment Strategy
    holding_period_rec: Optional[int] = Field(None, ge=1, le=30, description="Recommended holding period (years)")
    financing_options: List[str] = Field(default_factory=list)
    total_investment_needed: Optional[Decimal] = Field(None, description="Total investment including costs")
    
    def calculate_total_cost(self, transaction_costs_pct: float = 10.0) -> Decimal:
        """Calculate total investment cost including transaction fees"""
        transaction_costs = self.property.price * Decimal(transaction_costs_pct / 100)
        return self.property.price + transaction_costs
    
    def project_cash_flows(self, years: int = 5) -> List[Dict]:
        """Project future cash flows"""
        if not self.estimated_rental_yield:
            return []
        
        annual_rent = float(self.property.price) * (self.estimated_rental_yield / 100)
        cash_flows = []
        
        for year in range(1, years + 1):
            # Assume 2% annual rent increase and 3% property appreciation
            yearly_rent = annual_rent * (1.02 ** year)
            property_value = float(self.property.price) * (1.03 ** year)
            
            cash_flows.append({
                'year': year,
                'rental_income': round(yearly_rent, 2),
                'property_value': round(property_value, 2),
                'total_return': round(yearly_rent + (property_value - float(self.property.price)) / year, 2)
            })
        
        return cash_flows


class Portfolio(BaseModel):
    """Real estate investment portfolio"""
    model_config = ConfigDict(validate_assignment=True)
    
    portfolio_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Portfolio name")
    investments: List[Investment] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=datetime.now)
    target_budget: Optional[Decimal] = Field(None, ge=0)
    
    @computed_field
    @property
    def total_value(self) -> Decimal:
        """Total portfolio value"""
        return sum(inv.property.price for inv in self.investments)
    
    @computed_field  
    @property
    def average_investment_score(self) -> float:
        """Average investment score across portfolio"""
        if not self.investments:
            return 0.0
        return sum(inv.investment_score for inv in self.investments) / len(self.investments)
    
    @computed_field
    @property
    def geographic_diversification(self) -> Dict[str, int]:
        """Count of properties by neighborhood"""
        neighborhoods = {}
        for inv in self.investments:
            neighborhood = inv.property.location.neighborhood
            neighborhoods[neighborhood] = neighborhoods.get(neighborhood, 0) + 1
        return neighborhoods
    
    @computed_field
    @property
    def risk_distribution(self) -> Dict[InvestmentRisk, int]:
        """Risk level distribution"""
        risks = {}
        for inv in self.investments:
            risks[inv.risk_level] = risks.get(inv.risk_level, 0) + 1
        return risks
    
    def calculate_portfolio_metrics(self) -> Dict:
        """Calculate comprehensive portfolio metrics"""
        if not self.investments:
            return {}
        
        prices = [float(inv.property.price) for inv in self.investments]
        yields = [inv.estimated_rental_yield or 0 for inv in self.investments]
        scores = [inv.investment_score for inv in self.investments]
        
        return {
            'total_properties': len(self.investments),
            'total_value': float(self.total_value),
            'average_price': np.mean(prices),
            'price_std_dev': np.std(prices),
            'average_yield': np.mean([y for y in yields if y > 0]) if any(yields) else 0,
            'average_score': np.mean(scores),
            'score_std_dev': np.std(scores),
            'diversification_score': len(self.geographic_diversification) / len(self.investments),
        }


class MarketSegment(BaseModel):
    """Market segment analysis"""
    model_config = ConfigDict(validate_assignment=True)
    
    segment_id: str
    neighborhood: str
    property_count: int = Field(ge=0)
    
    # Price Metrics
    avg_price: Decimal = Field(ge=0)
    median_price: Decimal = Field(ge=0) 
    avg_price_per_sqm: Decimal = Field(ge=0)
    price_std_dev: Decimal = Field(ge=0)
    
    # Market Characteristics
    avg_sqm: float = Field(ge=0)
    dominant_property_type: PropertyType
    energy_efficiency_score: float = Field(ge=0, le=10)
    
    # Investment Metrics
    avg_investment_score: float = Field(ge=0, le=100)
    estimated_avg_yield: float = Field(ge=0, le=50)
    market_activity_score: float = Field(ge=0, le=10)
    
    # Risk Assessment
    price_volatility: float = Field(ge=0, description="Price volatility measure")
    market_maturity: str = Field(description="Market maturity level")
    liquidity_score: float = Field(ge=0, le=1)
    
    analysis_date: datetime = Field(default_factory=datetime.now)
    
    def generate_investment_recommendation(self) -> Dict:
        """Generate investment recommendation for this segment"""
        recommendation = {
            'segment': self.neighborhood,
            'attractiveness': 'high' if self.avg_investment_score >= 75 else 'medium' if self.avg_investment_score >= 50 else 'low',
            'target_investor': self.get_target_investor_profile(),
            'key_strengths': self.identify_key_strengths(),
            'risk_factors': self.identify_risk_factors(),
            'recommended_budget': self.get_recommended_budget_range(),
        }
        return recommendation
    
    def get_target_investor_profile(self) -> str:
        """Identify target investor profile"""
        if self.estimated_avg_yield > 5 and self.price_volatility < 0.2:
            return "Income-focused conservative investor"
        elif self.avg_investment_score > 80 and self.market_activity_score > 7:
            return "Growth-focused aggressive investor"
        elif self.price_volatility < 0.15:
            return "Conservative wealth preservation investor"
        else:
            return "Balanced growth and income investor"
    
    def identify_key_strengths(self) -> List[str]:
        """Identify market segment strengths"""
        strengths = []
        if self.estimated_avg_yield > 4.5:
            strengths.append("Above-average rental yields")
        if self.energy_efficiency_score > 7:
            strengths.append("High energy efficiency")
        if self.market_activity_score > 7:
            strengths.append("Active market with good liquidity")
        if self.avg_investment_score > 75:
            strengths.append("Strong investment fundamentals")
        return strengths
    
    def identify_risk_factors(self) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        if self.price_volatility > 0.3:
            risks.append("High price volatility")
        if self.property_count < 10:
            risks.append("Limited market depth")
        if self.liquidity_score < 0.3:
            risks.append("Lower market liquidity")
        if self.estimated_avg_yield < 3:
            risks.append("Below-average rental yields")
        return risks
    
    def get_recommended_budget_range(self) -> Dict[str, int]:
        """Get recommended budget range for this segment"""
        median_price = float(self.median_price)
        return {
            'entry_level': int(median_price * 0.7),
            'optimal_range_min': int(median_price * 0.8),
            'optimal_range_max': int(median_price * 1.2),
            'premium_level': int(median_price * 1.5),
        }