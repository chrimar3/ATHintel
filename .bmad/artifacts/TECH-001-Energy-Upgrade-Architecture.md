# TECH-001: Energy Upgrade Analysis - Technical Architecture

## System Integration Overview

Building on ATHintel's existing robust architecture with enhanced energy analysis capabilities that leverage the current Property entity's EnergyClass foundation.

### Current Architecture Assets
- **Property Entity**: Comprehensive model with existing energy_class field
- **Investment Analysis**: Existing ROI calculation framework
- **Market Segmentation**: Established neighborhood analysis system
- **Validation Pipeline**: Proven data quality assurance framework

---

## Core Domain Extensions

### 1. Enhanced Energy Domain Models

```python
from enum import Enum
from typing import Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field
from datetime import datetime

class UpgradeType(str, Enum):
    """Energy upgrade categories"""
    INSULATION = "insulation"
    WINDOWS = "windows" 
    HEATING_SYSTEM = "heating_system"
    SOLAR_PANELS = "solar_panels"
    HEAT_PUMP = "heat_pump"
    SMART_THERMOSTAT = "smart_thermostat"
    LED_LIGHTING = "led_lighting"
    VENTILATION = "ventilation"

class UpgradePriority(str, Enum):
    """Upgrade implementation priority"""
    CRITICAL = "critical"        # Immediate ROI impact
    HIGH = "high"               # Strong ROI, recommended
    MEDIUM = "medium"           # Good ROI, optional
    LOW = "low"                 # Future consideration

class SubsidyType(str, Enum):
    """Government subsidy categories"""
    EXOIKONOMO = "exoikonomo"           # Main energy upgrade program
    PHOTOVOLTAICS = "photovoltaics"     # Solar panel subsidies
    HEAT_PUMP = "heat_pump"             # Heat pump specific subsidies
    INSULATION = "insulation"           # Insulation subsidies

class BuildingAge(str, Enum):
    """Building age categories for energy assessment"""
    PRE_1980 = "pre_1980"              # Poor insulation, high upgrade potential
    EIGHTIES_NINETIES = "1980_1999"    # Moderate insulation
    TWO_THOUSANDS = "2000_2010"        # Basic energy standards
    POST_2010 = "post_2010"            # Modern standards
    POST_2020 = "post_2020"            # Latest energy standards

@dataclass
class SubsidyInfo:
    """Government subsidy information"""
    subsidy_type: SubsidyType
    max_amount: Decimal
    percentage_coverage: float  # 0-100%
    eligibility_requirements: List[str]
    application_deadline: Optional[datetime]
    processing_time_weeks: int
    
@dataclass 
class UpgradeOpportunity:
    """Specific energy upgrade opportunity"""
    upgrade_type: UpgradeType
    priority: UpgradePriority
    estimated_cost: Decimal
    implementation_complexity: int  # 1-5 scale
    estimated_duration_days: int
    
    # ROI Metrics
    annual_energy_savings_kwh: float
    annual_cost_savings: Decimal
    property_value_increase_pct: float
    payback_period_years: float
    
    # Subsidy Information
    eligible_subsidies: List[SubsidyInfo]
    total_subsidy_amount: Decimal
    net_investment_cost: Decimal
    
    # Energy Rating Impact
    current_energy_rating: EnergyClass
    projected_energy_rating: EnergyClass
    energy_rating_improvement: int  # Number of grades improved

@dataclass
class BuildingProfile:
    """Comprehensive building characteristics for energy assessment"""
    building_age: BuildingAge
    construction_type: str  # reinforced_concrete, masonry, mixed
    insulation_status: str  # none, partial, full, unknown
    heating_system: str     # central_gas, central_oil, autonomous_gas, electric
    window_type: str        # single_glazed, double_glazed, triple_glazed
    roof_type: str         # flat, pitched, mixed
    solar_exposure: str     # excellent, good, moderate, poor
    building_orientation: Optional[str] = None
    
    @property
    def upgrade_potential_score(self) -> float:
        """Calculate upgrade potential (0-100)"""
        score = 0
        
        # Age factor (older = more potential)
        age_scores = {
            BuildingAge.PRE_1980: 40,
            BuildingAge.EIGHTIES_NINETIES: 25,
            BuildingAge.TWO_THOUSANDS: 15,
            BuildingAge.POST_2010: 8,
            BuildingAge.POST_2020: 3
        }
        score += age_scores.get(self.building_age, 20)
        
        # Insulation factor
        if self.insulation_status in ["none", "partial"]:
            score += 25
        
        # Heating system efficiency
        if self.heating_system in ["central_oil", "electric"]:
            score += 20
        
        # Window upgrade potential
        if self.window_type == "single_glazed":
            score += 15
        
        return min(score, 100)

class EnergyAssessment(BaseModel):
    """Complete energy efficiency assessment"""
    model_config = ConfigDict(validate_assignment=True)
    
    # Core Identity
    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    property_id: str = Field(..., description="Reference to Property entity")
    assessment_date: datetime = Field(default_factory=datetime.now)
    
    # Building Analysis
    building_profile: BuildingProfile
    current_energy_rating: EnergyClass
    estimated_annual_consumption_kwh: float
    estimated_annual_energy_cost: Decimal
    
    # Upgrade Opportunities (sorted by priority/ROI)
    upgrade_opportunities: List[UpgradeOpportunity] = Field(default_factory=list)
    recommended_package_budget_5k: List[UpgradeOpportunity] = Field(default_factory=list)
    recommended_package_budget_15k: List[UpgradeOpportunity] = Field(default_factory=list)
    recommended_package_budget_25k: List[UpgradeOpportunity] = Field(default_factory=list)
    
    # Assessment Confidence
    confidence_score: float = Field(ge=0, le=1, description="Assessment accuracy confidence")
    data_sources: List[str] = Field(default_factory=list)
    
    @computed_field
    @property
    def total_upgrade_potential(self) -> Decimal:
        """Total potential investment in all upgrades"""
        return sum(opp.estimated_cost for opp in self.upgrade_opportunities)
    
    @computed_field
    @property
    def maximum_annual_savings(self) -> Decimal:
        """Maximum possible annual energy savings"""
        return sum(opp.annual_cost_savings for opp in self.upgrade_opportunities)
    
    @computed_field
    @property
    def optimal_upgrade_sequence(self) -> List[UpgradeOpportunity]:
        """Upgrades ordered by ROI and implementation logic"""
        # Sort by payback period, then by priority
        return sorted(
            self.upgrade_opportunities, 
            key=lambda x: (x.payback_period_years, x.priority.value)
        )
    
    def calculate_package_roi(self, package: List[UpgradeOpportunity]) -> Dict:
        """Calculate comprehensive ROI for upgrade package"""
        total_cost = sum(opp.estimated_cost for opp in package)
        total_subsidies = sum(opp.total_subsidy_amount for opp in package)
        net_investment = total_cost - total_subsidies
        
        annual_savings = sum(opp.annual_cost_savings for opp in package)
        avg_property_increase = sum(opp.property_value_increase_pct for opp in package) / len(package)
        
        return {
            'total_investment': total_cost,
            'net_investment': net_investment,
            'subsidy_amount': total_subsidies,
            'annual_savings': annual_savings,
            'simple_payback_years': float(net_investment / annual_savings) if annual_savings > 0 else float('inf'),
            'property_value_increase_pct': avg_property_increase,
            '10_year_npv': self._calculate_npv(net_investment, annual_savings, avg_property_increase),
            'roi_10_year': self._calculate_total_roi(net_investment, annual_savings, avg_property_increase)
        }
    
    def _calculate_npv(self, investment: Decimal, annual_savings: Decimal, 
                      property_increase_pct: float, years: int = 10, discount_rate: float = 0.05) -> Decimal:
        """Calculate Net Present Value"""
        # Simplified NPV calculation
        present_value_savings = sum(
            float(annual_savings) / ((1 + discount_rate) ** year) 
            for year in range(1, years + 1)
        )
        
        # Add property value increase at end of period
        property_increase = float(investment) * (property_increase_pct / 100)
        present_value_property = property_increase / ((1 + discount_rate) ** years)
        
        return Decimal(present_value_savings + present_value_property - float(investment))
    
    def _calculate_total_roi(self, investment: Decimal, annual_savings: Decimal,
                            property_increase_pct: float, years: int = 10) -> float:
        """Calculate total ROI percentage over specified years"""
        total_savings = float(annual_savings) * years
        property_increase = float(investment) * (property_increase_pct / 100)
        total_return = total_savings + property_increase
        
        return (total_return / float(investment) - 1) * 100 if investment > 0 else 0

class EnergyMarketData(BaseModel):
    """Energy market and pricing data for calculations"""
    model_config = ConfigDict(validate_assignment=True)
    
    # Energy Pricing (EUR per kWh)
    electricity_price_kwh: Decimal = Field(default=Decimal('0.15'))
    gas_price_kwh: Decimal = Field(default=Decimal('0.08'))
    heating_oil_price_kwh: Decimal = Field(default=Decimal('0.10'))
    
    # Government Subsidy Programs (updated regularly)
    active_subsidies: Dict[SubsidyType, SubsidyInfo] = Field(default_factory=dict)
    
    # Market Benchmarks
    neighborhood_energy_benchmarks: Dict[str, Dict] = Field(default_factory=dict)
    upgrade_cost_database: Dict[UpgradeType, Dict] = Field(default_factory=dict)
    
    # Market Trends
    energy_price_trend_pct: float = Field(default=3.0)  # Annual increase %
    property_premium_energy_efficient_pct: float = Field(default=12.5)  # Market premium
    
    last_updated: datetime = Field(default_factory=datetime.now)
```

---

## Service Layer Architecture

### 1. Energy Assessment Service

```python
class EnergyAssessmentService:
    """Core service for property energy analysis"""
    
    def __init__(
        self,
        market_data_service: EnergyMarketDataService,
        subsidy_service: SubsidyCalculationService,
        building_analyzer: BuildingAnalysisService
    ):
        self.market_data = market_data_service
        self.subsidy_service = subsidy_service
        self.building_analyzer = building_analyzer
    
    async def assess_property_energy_potential(
        self, 
        property: Property
    ) -> EnergyAssessment:
        """
        Generate comprehensive energy assessment for property
        
        Test scenarios:
        - Complete property data -> full assessment with high confidence
        - Minimal data -> estimation-based assessment with confidence intervals
        - Invalid/missing energy class -> estimation based on building age/type
        """
        
        # 1. Analyze building characteristics
        building_profile = await self.building_analyzer.analyze_building(property)
        
        # 2. Estimate current energy performance
        current_rating, consumption = await self._estimate_current_performance(
            property, building_profile
        )
        
        # 3. Identify upgrade opportunities
        opportunities = await self._identify_upgrade_opportunities(
            building_profile, current_rating
        )
        
        # 4. Calculate ROI for each opportunity
        for opportunity in opportunities:
            await self._calculate_upgrade_roi(opportunity, property)
        
        # 5. Create budget-based packages
        packages = self._create_budget_packages(opportunities)
        
        # 6. Assess confidence level
        confidence = self._calculate_assessment_confidence(property, building_profile)
        
        return EnergyAssessment(
            property_id=property.property_id,
            building_profile=building_profile,
            current_energy_rating=current_rating,
            estimated_annual_consumption_kwh=consumption,
            estimated_annual_energy_cost=await self._calculate_annual_cost(consumption),
            upgrade_opportunities=opportunities,
            **packages,
            confidence_score=confidence,
            data_sources=["building_analysis", "market_data", "subsidy_database"]
        )
    
    async def _estimate_current_performance(
        self, 
        property: Property, 
        building_profile: BuildingProfile
    ) -> tuple[EnergyClass, float]:
        """Estimate current energy rating and consumption"""
        
        if property.energy_class and property.energy_class != EnergyClass.UNDER_PUBLICATION:
            estimated_rating = property.energy_class
        else:
            # Estimate based on building characteristics
            estimated_rating = self._estimate_energy_class_from_building(building_profile)
        
        # Calculate consumption based on sqm, rating, and building type
        base_consumption = self._calculate_base_consumption(property.sqm or 75)  # Default 75sqm
        rating_multiplier = self._get_consumption_multiplier(estimated_rating)
        building_multiplier = self._get_building_type_multiplier(building_profile)
        
        annual_consumption = base_consumption * rating_multiplier * building_multiplier
        
        return estimated_rating, annual_consumption
    
    def _create_budget_packages(self, opportunities: List[UpgradeOpportunity]) -> Dict:
        """Create optimized upgrade packages for different budgets"""
        
        # Sort opportunities by ROI (payback period)
        sorted_opps = sorted(opportunities, key=lambda x: x.payback_period_years)
        
        packages = {
            'recommended_package_budget_5k': [],
            'recommended_package_budget_15k': [],
            'recommended_package_budget_25k': []
        }
        
        # €5,000 package - highest ROI items first
        current_cost = Decimal('0')
        for opp in sorted_opps:
            if current_cost + opp.net_investment_cost <= Decimal('5000'):
                packages['recommended_package_budget_5k'].append(opp)
                current_cost += opp.net_investment_cost
        
        # €15,000 package - broader improvements
        current_cost = Decimal('0')
        for opp in sorted_opps:
            if current_cost + opp.net_investment_cost <= Decimal('15000'):
                packages['recommended_package_budget_15k'].append(opp)
                current_cost += opp.net_investment_cost
        
        # €25,000 package - comprehensive upgrade
        current_cost = Decimal('0')
        for opp in sorted_opps:
            if current_cost + opp.net_investment_cost <= Decimal('25000'):
                packages['recommended_package_budget_25k'].append(opp)
                current_cost += opp.net_investment_cost
        
        return packages

class EnergyROICalculatorService:
    """Advanced ROI calculations for energy upgrades"""
    
    def __init__(self, market_data: EnergyMarketDataService):
        self.market_data = market_data
    
    async def calculate_comprehensive_roi(
        self,
        property: Property,
        upgrades: List[UpgradeOpportunity],
        analysis_period_years: int = 10
    ) -> Dict:
        """
        Calculate comprehensive ROI including:
        - Energy cost savings
        - Property value increase
        - Government subsidies
        - Tax benefits
        - Market premium for energy efficiency
        """
        
        total_investment = sum(u.estimated_cost for u in upgrades)
        total_subsidies = sum(u.total_subsidy_amount for u in upgrades)
        net_investment = total_investment - total_subsidies
        
        # Annual savings calculation
        annual_energy_savings = sum(u.annual_cost_savings for u in upgrades)
        
        # Property value impact
        current_value = property.price
        energy_premium_pct = await self.market_data.get_energy_efficiency_premium(
            property.location.neighborhood
        )
        property_value_increase = current_value * Decimal(energy_premium_pct / 100)
        
        # Calculate year-by-year projections
        projections = []
        cumulative_savings = Decimal('0')
        
        for year in range(1, analysis_period_years + 1):
            # Account for energy price inflation
            yearly_savings = annual_energy_savings * (1 + self.market_data.energy_price_trend_pct / 100) ** year
            cumulative_savings += Decimal(yearly_savings)
            
            projections.append({
                'year': year,
                'annual_savings': yearly_savings,
                'cumulative_savings': float(cumulative_savings),
                'roi_to_date': float((cumulative_savings / net_investment - 1) * 100) if net_investment > 0 else 0
            })
        
        # Final calculations
        total_savings = cumulative_savings
        total_return = total_savings + property_value_increase
        final_roi = float((total_return / net_investment - 1) * 100) if net_investment > 0 else 0
        
        return {
            'investment_summary': {
                'total_investment': float(total_investment),
                'subsidies_received': float(total_subsidies),
                'net_investment': float(net_investment)
            },
            'returns': {
                'total_energy_savings': float(total_savings),
                'property_value_increase': float(property_value_increase),
                'total_return': float(total_return),
                'roi_percentage': final_roi
            },
            'payback_analysis': {
                'simple_payback_years': float(net_investment / annual_energy_savings) if annual_energy_savings > 0 else float('inf'),
                'discounted_payback_years': self._calculate_discounted_payback(net_investment, annual_energy_savings),
                'break_even_year': next((p['year'] for p in projections if p['roi_to_date'] > 0), analysis_period_years)
            },
            'yearly_projections': projections,
            'risk_factors': self._identify_roi_risks(upgrades, property),
            'sensitivity_analysis': self._perform_sensitivity_analysis(net_investment, annual_energy_savings, property_value_increase)
        }

class EnergyComparisonService:
    """Service for comparing properties based on energy efficiency"""
    
    async def compare_energy_efficiency_impact(
        self,
        target_property: Property,
        comparable_properties: List[Property],
        neighborhood: str
    ) -> Dict:
        """
        Compare target property against similar properties in terms of:
        - Current energy efficiency 
        - Upgrade potential
        - Market positioning after upgrades
        - Investment attractiveness
        """
        
        target_assessment = await self.energy_service.assess_property_energy_potential(target_property)
        
        # Analyze comparable properties
        comparable_assessments = []
        for prop in comparable_properties:
            assessment = await self.energy_service.assess_property_energy_potential(prop)
            comparable_assessments.append(assessment)
        
        # Market analysis
        neighborhood_stats = self._calculate_neighborhood_energy_stats(comparable_assessments)
        
        return {
            'target_property': {
                'current_rating': target_assessment.current_energy_rating.value,
                'upgrade_potential_score': target_assessment.building_profile.upgrade_potential_score,
                'max_annual_savings': float(target_assessment.maximum_annual_savings),
                'investment_required_optimal': float(sum(u.net_investment_cost for u in target_assessment.recommended_package_budget_15k))
            },
            'market_position': {
                'current_efficiency_percentile': self._calculate_efficiency_percentile(target_assessment, comparable_assessments),
                'post_upgrade_efficiency_percentile': self._calculate_post_upgrade_percentile(target_assessment, comparable_assessments),
                'upgrade_potential_rank': self._rank_upgrade_potential(target_assessment, comparable_assessments)
            },
            'neighborhood_benchmarks': neighborhood_stats,
            'competitive_advantage': {
                'energy_cost_advantage_annual': self._calculate_cost_advantage(target_assessment, neighborhood_stats),
                'market_premium_potential': self._calculate_market_premium_potential(target_assessment, neighborhood_stats),
                'rental_yield_boost': self._calculate_rental_yield_impact(target_assessment, target_property)
            },
            'investment_recommendation': self._generate_investment_recommendation(target_assessment, neighborhood_stats)
        }
```

---

## Data Layer & Integration

### 1. Energy Data Repository

```python
class EnergyAssessmentRepository:
    """Repository for energy assessment data persistence"""
    
    async def save_assessment(self, assessment: EnergyAssessment) -> str:
        """Save complete energy assessment with full audit trail"""
        
    async def get_assessment_by_property(self, property_id: str) -> Optional[EnergyAssessment]:
        """Retrieve latest assessment for property"""
        
    async def get_neighborhood_energy_stats(self, neighborhood: str) -> Dict:
        """Get aggregated energy statistics for neighborhood"""
        
    async def track_assessment_accuracy(self, assessment_id: str, actual_results: Dict):
        """Track accuracy of assessments against real implementation results"""

class SubsidyDataService:
    """External integration for government subsidy data"""
    
    async def get_current_subsidy_programs(self) -> Dict[SubsidyType, SubsidyInfo]:
        """Fetch current government subsidy programs and rates"""
        
    async def check_property_eligibility(self, property: Property, subsidy_type: SubsidyType) -> bool:
        """Check if property qualifies for specific subsidy"""
        
    async def estimate_application_timeline(self, subsidy_type: SubsidyType) -> Dict:
        """Get current processing times and application requirements"""

class EnergyPricingService:
    """Energy pricing and market data service"""
    
    async def get_current_energy_prices(self) -> Dict[str, Decimal]:
        """Get current energy prices by type (electricity, gas, oil)"""
        
    async def get_price_projections(self, years: int) -> Dict[str, List[Decimal]]:
        """Get energy price projections for ROI calculations"""
        
    async def get_neighborhood_energy_premiums(self, neighborhood: str) -> float:
        """Get market premium for energy-efficient properties in area"""
```

---

## API Layer Design

### 1. Energy Analysis Endpoints

```python
# FastAPI endpoint design
@app.post("/api/v1/properties/{property_id}/energy-assessment")
async def create_energy_assessment(
    property_id: str,
    background_tasks: BackgroundTasks,
    energy_service: EnergyAssessmentService = Depends(get_energy_service)
) -> EnergyAssessmentResponse:
    """Generate comprehensive energy assessment for property"""

@app.get("/api/v1/properties/{property_id}/upgrade-packages")
async def get_upgrade_packages(
    property_id: str,
    budget_max: Optional[int] = None,
    energy_service: EnergyAssessmentService = Depends(get_energy_service)
) -> UpgradePackagesResponse:
    """Get optimized upgrade packages within budget constraints"""

@app.post("/api/v1/properties/{property_id}/roi-analysis")
async def calculate_upgrade_roi(
    property_id: str,
    selected_upgrades: List[str],
    analysis_period: int = 10,
    roi_service: EnergyROICalculatorService = Depends(get_roi_service)
) -> ROIAnalysisResponse:
    """Calculate detailed ROI for selected upgrade combination"""

@app.get("/api/v1/neighborhoods/{neighborhood}/energy-comparison")
async def compare_neighborhood_energy(
    neighborhood: str,
    property_id: Optional[str] = None,
    comparison_service: EnergyComparisonService = Depends(get_comparison_service)
) -> EnergyComparisonResponse:
    """Compare energy efficiency across neighborhood properties"""
```

---

## Testing Strategy

### 1. TDD Test Structure

```python
class TestEnergyAssessmentService:
    """Comprehensive test suite for energy assessment core logic"""
    
    @pytest.fixture
    def sample_property(self):
        return Property(
            property_id="test-123",
            title="Test Apartment",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=Location(neighborhood="Kolonaki"),
            sqm=85,
            year_built=1985,
            energy_class=EnergyClass.D,
            price=Decimal("250000")
        )
    
    @pytest.mark.asyncio
    async def test_assess_property_complete_data(self, sample_property):
        """Test assessment with complete property data"""
        # Arrange
        service = EnergyAssessmentService(mock_market_data, mock_subsidy_service, mock_building_analyzer)
        
        # Act
        assessment = await service.assess_property_energy_potential(sample_property)
        
        # Assert
        assert assessment.property_id == "test-123"
        assert assessment.confidence_score > 0.8  # High confidence with complete data
        assert len(assessment.upgrade_opportunities) > 0
        assert assessment.building_profile.upgrade_potential_score > 0
        
    @pytest.mark.asyncio 
    async def test_assess_property_minimal_data(self):
        """Test assessment with minimal property data"""
        # Arrange - property with minimal information
        minimal_property = Property(
            property_id="minimal-123",
            title="Minimal Data Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=Location(neighborhood="Unknown"),
            price=Decimal("200000")
            # Missing: sqm, year_built, energy_class
        )
        
        # Act
        assessment = await service.assess_property_energy_potential(minimal_property)
        
        # Assert
        assert assessment.property_id == "minimal-123"
        assert 0.3 <= assessment.confidence_score <= 0.7  # Lower confidence
        assert len(assessment.upgrade_opportunities) > 0  # Still provides estimates
        
    @pytest.mark.asyncio
    async def test_roi_calculation_accuracy(self, sample_property):
        """Test ROI calculation accuracy"""
        # Arrange
        service = EnergyROICalculatorService(mock_market_data)
        upgrades = [
            create_mock_upgrade(UpgradeType.INSULATION, cost=8000, annual_savings=1200),
            create_mock_upgrade(UpgradeType.WINDOWS, cost=12000, annual_savings=800)
        ]
        
        # Act
        roi_analysis = await service.calculate_comprehensive_roi(sample_property, upgrades)
        
        # Assert
        assert roi_analysis['investment_summary']['total_investment'] == 20000
        assert roi_analysis['returns']['roi_percentage'] > 0
        assert roi_analysis['payback_analysis']['simple_payback_years'] < 15
        
    def test_budget_package_optimization(self):
        """Test upgrade package creation within budget constraints"""
        # Test that €5K package maximizes ROI
        # Test that €15K package includes complementary upgrades
        # Test that €25K package provides comprehensive improvements
        pass

class TestEnergyComparisonService:
    """Test suite for property energy comparison functionality"""
    
    @pytest.mark.asyncio
    async def test_neighborhood_energy_comparison(self):
        """Test energy efficiency comparison within neighborhood"""
        # Test ranking properties by energy efficiency
        # Test upgrade potential comparison
        # Test market positioning analysis
        pass
        
    @pytest.mark.asyncio
    async def test_market_premium_calculation(self):
        """Test calculation of energy efficiency market premium"""
        # Test premium calculation based on neighborhood data
        # Test impact of different energy ratings on market value
        pass

class TestDataIntegration:
    """Integration tests for external data services"""
    
    @pytest.mark.asyncio
    async def test_subsidy_data_integration(self):
        """Test government subsidy data integration"""
        # Test fetching current subsidy rates
        # Test eligibility checking
        # Test handling of subsidy program changes
        pass
        
    @pytest.mark.asyncio  
    async def test_energy_pricing_integration(self):
        """Test energy pricing data accuracy"""
        # Test current price fetching
        # Test price trend projections
        # Test regional price variations
        pass
```

---

## Implementation Plan

### Phase 1: Core Assessment Engine (Weeks 1-2)
- **Sprint 1**: Domain model extensions + basic assessment logic
- **Sprint 2**: ROI calculation engine + upgrade identification

### Phase 2: Package Optimization (Weeks 3-4) 
- **Sprint 3**: Budget-based package creation + subsidy integration
- **Sprint 4**: Market comparison tools + neighborhood benchmarking

### Phase 3: Integration & UI (Weeks 5-6)
- **Sprint 5**: API layer + existing system integration
- **Sprint 6**: Dashboard components + testing + documentation

### Development Priorities
1. **Foundation First**: Build on existing Property entity and energy_class field
2. **Data Quality**: Leverage existing validation pipeline for energy data
3. **Incremental Enhancement**: Add energy features without disrupting existing functionality
4. **Performance**: Maintain existing system performance standards

---

## Risk Mitigation & Fallbacks

### Data Quality Risks
- **Missing Energy Data**: Use building age/type estimation algorithms
- **Outdated Subsidy Info**: Configurable fallback rates + manual override capability
- **Market Data Gaps**: Use broader regional averages with confidence scoring

### Technical Risks
- **Performance Impact**: Async processing + caching for complex calculations
- **Integration Complexity**: Phased rollout with feature flags
- **External API Failures**: Local data caching + graceful degradation

### Business Risks  
- **Accuracy Concerns**: Comprehensive testing + feedback loop for accuracy tracking
- **Subsidy Changes**: Regular data updates + transparent assumption disclosure
- **Market Validation**: A/B testing + user feedback integration

---

## Success Metrics & Monitoring

### Technical KPIs
- **Assessment Accuracy**: >85% accuracy vs actual implementations
- **Response Time**: <2 seconds for assessment generation
- **System Integration**: Zero impact on existing functionality performance
- **Data Quality**: >90% confidence scores on assessments

### Business KPIs
- **Feature Adoption**: 60% of property viewers use energy analysis within 3 months
- **User Engagement**: Average 5+ minutes spent in energy analysis features
- **Conversion Impact**: 25% increase in premium subscription conversions
- **Revenue Attribution**: €50,000+ annual revenue attributed to energy features

*Created: 2025-09-06*  
*Architecture Lead: Technical Product Manager*  
*Integration Target: ATHintel Core Platform*  
*Implementation Method: TDD with existing system enhancement*