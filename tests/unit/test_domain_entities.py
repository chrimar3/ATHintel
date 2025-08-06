"""
Unit Tests for Domain Entities

Comprehensive unit tests for the core domain entities,
ensuring business rules and validations work correctly.
"""

import pytest
from decimal import Decimal
from datetime import datetime
import numpy as np

from src.core.domain.entities import (
    Property, Investment, Portfolio, MarketSegment, Location,
    PropertyType, EnergyClass, ListingType, InvestmentRisk
)


class TestLocation:
    """Test Location entity"""
    
    def test_location_creation(self):
        """Test basic location creation"""
        location = Location(
            neighborhood="Kolonaki",
            district="Athens Center",
            municipality="Athens"
        )
        
        assert location.neighborhood == "Kolonaki"
        assert location.district == "Athens Center"
        assert location.municipality == "Athens"
        assert location.country == "Greece"  # Default value
    
    def test_location_with_coordinates(self):
        """Test location with GPS coordinates"""
        location = Location(
            neighborhood="Glyfada",
            latitude=37.8667,
            longitude=23.7667
        )
        
        assert location.latitude == 37.8667
        assert location.longitude == 23.7667
    
    def test_location_invalid_coordinates(self):
        """Test location with invalid coordinates"""
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(
                neighborhood="Test",
                latitude=100.0  # Invalid latitude > 90
            )
        
        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(
                neighborhood="Test", 
                longitude=200.0  # Invalid longitude > 180
            )


class TestProperty:
    """Test Property entity"""
    
    def test_property_creation_minimal(self, sample_location):
        """Test property creation with minimal required fields"""
        property = Property(
            property_id="test-123",
            title="Test Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=sample_location,
            price=Decimal("250000")
        )
        
        assert property.property_id == "test-123"
        assert property.title == "Test Property"
        assert property.property_type == PropertyType.APARTMENT
        assert property.price == Decimal("250000")
    
    def test_property_creation_full(self, sample_location):
        """Test property creation with all fields"""
        property = Property(
            property_id="test-456",
            url="https://example.com/property/456",
            title="Luxury Apartment",
            property_type=PropertyType.PENTHOUSE,
            listing_type=ListingType.SALE,
            location=sample_location,
            sqm=120.0,
            rooms=3,
            bedrooms=2,
            bathrooms=2,
            floor=8,
            total_floors=10,
            energy_class=EnergyClass.A,
            year_built=2015,
            price=Decimal("650000"),
            common_charges=Decimal("150"),
            source="test"
        )
        
        assert property.sqm == 120.0
        assert property.rooms == 3
        assert property.energy_class == EnergyClass.A
        assert property.year_built == 2015
    
    def test_price_per_sqm_calculation(self, sample_location):
        """Test price per square meter calculation"""
        property = Property(
            property_id="test-789",
            title="Test Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=sample_location,
            price=Decimal("300000"),
            sqm=100.0
        )
        
        assert property.price_per_sqm == Decimal("3000")
    
    def test_price_per_sqm_no_area(self, sample_location):
        """Test price per sqm when no area provided"""
        property = Property(
            property_id="test-no-area",
            title="No Area Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=sample_location,
            price=Decimal("250000")
            # No sqm provided
        )
        
        assert property.price_per_sqm is None
    
    def test_neighborhood_key_generation(self, sample_location):
        """Test neighborhood key normalization"""
        location = Location(neighborhood="Athens - Center")
        property = Property(
            property_id="test-key",
            title="Test Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=location,
            price=Decimal("200000")
        )
        
        assert property.neighborhood_key == "athens___center"
    
    def test_investment_score_calculation(self, sample_location):
        """Test investment score calculation"""
        property = Property(
            property_id="test-score",
            title="High Score Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=sample_location,
            price=Decimal("300000"),
            sqm=80.0,
            energy_class=EnergyClass.A_PLUS,
            year_built=2020
        )
        
        market_data = {
            property.neighborhood_key: {
                'avg_price_per_sqm': 4000,  # Property is below market
                'property_count': 100
            }
        }
        
        score = property.calculate_investment_score(market_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 50  # Should be above base with good characteristics
    
    def test_rental_yield_estimation(self, sample_location):
        """Test rental yield estimation"""
        property = Property(
            property_id="test-yield",
            title="Rental Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=sample_location,
            price=Decimal("250000"),
            sqm=75.0,
            energy_class=EnergyClass.B
        )
        
        market_data = {
            property.neighborhood_key: {
                'avg_rent_per_sqm': 12.0  # €12/m² monthly rent
            }
        }
        
        yield_pct = property.estimate_rental_yield(market_data)
        
        assert isinstance(yield_pct, float)
        assert yield_pct > 0
        assert yield_pct < 50  # Reasonable upper bound
    
    def test_property_validation_negative_price(self, sample_location):
        """Test property validation with negative price"""
        with pytest.raises(ValueError):
            Property(
                property_id="test-negative",
                title="Invalid Property",
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                location=sample_location,
                price=Decimal("-100000")  # Invalid negative price
            )
    
    def test_property_validation_invalid_year(self, sample_location):
        """Test property validation with invalid year"""
        with pytest.raises(ValueError):
            Property(
                property_id="test-year",
                title="Invalid Year Property", 
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                location=sample_location,
                price=Decimal("200000"),
                year_built=1500  # Too old
            )


class TestInvestment:
    """Test Investment entity"""
    
    def test_investment_creation(self, sample_property):
        """Test investment creation"""
        investment = Investment(
            property=sample_property,
            investment_score=78.5,
            estimated_rental_yield=4.2,
            roi_projection_5y=42.8,
            risk_level=InvestmentRisk.MEDIUM
        )
        
        assert investment.property == sample_property
        assert investment.investment_score == 78.5
        assert investment.estimated_rental_yield == 4.2
        assert investment.risk_level == InvestmentRisk.MEDIUM
    
    def test_investment_score_validation(self, sample_property):
        """Test investment score validation"""
        with pytest.raises(ValueError):
            Investment(
                property=sample_property,
                investment_score=150.0  # Invalid score > 100
            )
        
        with pytest.raises(ValueError):
            Investment(
                property=sample_property,
                investment_score=-10.0  # Invalid score < 0
            )
    
    def test_total_cost_calculation(self, sample_property):
        """Test total investment cost calculation"""
        investment = Investment(
            property=sample_property,
            investment_score=75.0
        )
        
        total_cost = investment.calculate_total_cost(transaction_costs_pct=12.0)
        expected_cost = sample_property.price * Decimal("1.12")
        
        assert total_cost == expected_cost
    
    def test_cash_flow_projection(self, sample_property):
        """Test cash flow projection calculation"""
        investment = Investment(
            property=sample_property,
            investment_score=75.0,
            estimated_rental_yield=4.0
        )
        
        cash_flows = investment.project_cash_flows(years=3)
        
        assert len(cash_flows) == 3
        
        for i, cf in enumerate(cash_flows):
            assert 'year' in cf
            assert 'rental_income' in cf
            assert 'property_value' in cf
            assert 'total_return' in cf
            assert cf['year'] == i + 1
            assert cf['rental_income'] > 0
            assert cf['property_value'] > float(sample_property.price)
    
    def test_cash_flow_no_yield(self, sample_property):
        """Test cash flow projection without rental yield"""
        investment = Investment(
            property=sample_property,
            investment_score=75.0
            # No estimated_rental_yield
        )
        
        cash_flows = investment.project_cash_flows()
        
        assert cash_flows == []


class TestPortfolio:
    """Test Portfolio entity"""
    
    def test_portfolio_creation_empty(self):
        """Test empty portfolio creation"""
        portfolio = Portfolio(
            name="Test Portfolio"
        )
        
        assert portfolio.name == "Test Portfolio"
        assert len(portfolio.investments) == 0
        assert portfolio.total_value == Decimal("0")
    
    def test_portfolio_with_investments(self, sample_investment):
        """Test portfolio with investments"""
        investments = [sample_investment]
        portfolio = Portfolio(
            name="Test Portfolio",
            investments=investments
        )
        
        assert len(portfolio.investments) == 1
        assert portfolio.total_value == sample_investment.property.price
    
    def test_portfolio_average_score(self, sample_properties):
        """Test portfolio average investment score"""
        investments = []
        scores = [70.0, 80.0, 90.0]
        
        for i, prop in enumerate(sample_properties[:3]):
            investment = Investment(
                property=prop,
                investment_score=scores[i]
            )
            investments.append(investment)
        
        portfolio = Portfolio(
            name="Score Test Portfolio",
            investments=investments
        )
        
        assert portfolio.average_investment_score == 80.0  # (70+80+90)/3
    
    def test_portfolio_geographic_diversification(self, sample_properties):
        """Test geographic diversification calculation"""
        investments = []
        
        # Create investments with different neighborhoods
        neighborhoods = ["Kolonaki", "Glyfada", "Kolonaki", "Kifisia"]
        
        for i, prop in enumerate(sample_properties[:4]):
            # Update property location
            prop.location.neighborhood = neighborhoods[i]
            
            investment = Investment(
                property=prop,
                investment_score=75.0
            )
            investments.append(investment)
        
        portfolio = Portfolio(
            name="Diversification Test",
            investments=investments
        )
        
        diversification = portfolio.geographic_diversification
        
        assert diversification["Kolonaki"] == 2
        assert diversification["Glyfada"] == 1
        assert diversification["Kifisia"] == 1
        assert len(diversification) == 3
    
    def test_portfolio_risk_distribution(self, sample_properties):
        """Test risk level distribution"""
        investments = []
        risk_levels = [
            InvestmentRisk.LOW, 
            InvestmentRisk.MEDIUM, 
            InvestmentRisk.HIGH,
            InvestmentRisk.MEDIUM
        ]
        
        for i, prop in enumerate(sample_properties[:4]):
            investment = Investment(
                property=prop,
                investment_score=75.0,
                risk_level=risk_levels[i]
            )
            investments.append(investment)
        
        portfolio = Portfolio(
            name="Risk Test Portfolio",
            investments=investments
        )
        
        risk_dist = portfolio.risk_distribution
        
        assert risk_dist[InvestmentRisk.LOW] == 1
        assert risk_dist[InvestmentRisk.MEDIUM] == 2
        assert risk_dist[InvestmentRisk.HIGH] == 1
    
    def test_portfolio_metrics_calculation(self, sample_properties):
        """Test comprehensive portfolio metrics"""
        investments = []
        
        for i, prop in enumerate(sample_properties[:5]):
            investment = Investment(
                property=prop,
                investment_score=70.0 + i * 5,  # Varying scores
                estimated_rental_yield=3.5 + i * 0.2  # Varying yields
            )
            investments.append(investment)
        
        portfolio = Portfolio(
            name="Metrics Test Portfolio",
            investments=investments
        )
        
        metrics = portfolio.calculate_portfolio_metrics()
        
        assert 'total_properties' in metrics
        assert 'total_value' in metrics
        assert 'average_price' in metrics
        assert 'average_yield' in metrics
        assert 'average_score' in metrics
        assert 'diversification_score' in metrics
        
        assert metrics['total_properties'] == 5
        assert metrics['total_value'] > 0
        assert metrics['average_score'] == 75.0  # (70+72.5+75+77.5+80)/5


class TestMarketSegment:
    """Test MarketSegment entity"""
    
    def test_market_segment_creation(self):
        """Test market segment creation"""
        segment = MarketSegment(
            segment_id="test-segment",
            neighborhood="Kolonaki",
            property_count=50,
            avg_price=Decimal("450000"),
            median_price=Decimal("420000"),
            avg_price_per_sqm=Decimal("5200"),
            price_std_dev=Decimal("85000"),
            avg_sqm=86.5,
            dominant_property_type=PropertyType.APARTMENT,
            energy_efficiency_score=7.8,
            avg_investment_score=82.5,
            estimated_avg_yield=3.9,
            market_activity_score=8.2,
            price_volatility=0.18,
            market_maturity="mature",
            liquidity_score=0.82
        )
        
        assert segment.segment_id == "test-segment"
        assert segment.property_count == 50
        assert segment.avg_investment_score == 82.5
    
    def test_investment_recommendation_generation(self):
        """Test investment recommendation generation"""
        segment = MarketSegment(
            segment_id="high-score-segment",
            neighborhood="Premium Area",
            property_count=25,
            avg_price=Decimal("600000"),
            median_price=Decimal("580000"),
            avg_price_per_sqm=Decimal("6000"),
            price_std_dev=Decimal("100000"),
            avg_sqm=100.0,
            dominant_property_type=PropertyType.PENTHOUSE,
            energy_efficiency_score=9.0,
            avg_investment_score=85.0,  # High score
            estimated_avg_yield=5.2,    # High yield
            market_activity_score=9.0,
            price_volatility=0.12,      # Low volatility
            market_maturity="mature",
            liquidity_score=0.9
        )
        
        recommendation = segment.generate_investment_recommendation()
        
        assert recommendation['segment'] == "Premium Area"
        assert recommendation['attractiveness'] == 'high'
        assert isinstance(recommendation['key_strengths'], list)
        assert isinstance(recommendation['risk_factors'], list)
        assert 'recommended_budget' in recommendation
    
    def test_target_investor_profile(self):
        """Test target investor profile identification"""
        # High yield, low volatility - conservative income investor
        segment1 = MarketSegment(
            segment_id="income-segment",
            neighborhood="Income Area",
            property_count=30,
            avg_price=Decimal("200000"),
            median_price=Decimal("195000"),
            avg_price_per_sqm=Decimal("2500"),
            price_std_dev=Decimal("25000"),
            avg_sqm=80.0,
            dominant_property_type=PropertyType.APARTMENT,
            energy_efficiency_score=6.0,
            avg_investment_score=70.0,
            estimated_avg_yield=5.5,    # High yield
            market_activity_score=6.0,
            price_volatility=0.15,      # Low volatility
            market_maturity="established",
            liquidity_score=0.7
        )
        
        profile = segment1.get_target_investor_profile()
        assert "Income-focused conservative investor" in profile
        
        # High score, high activity - aggressive growth investor
        segment2 = MarketSegment(
            segment_id="growth-segment",
            neighborhood="Growth Area",
            property_count=40,
            avg_price=Decimal("400000"),
            median_price=Decimal("385000"),
            avg_price_per_sqm=Decimal("4500"),
            price_std_dev=Decimal("75000"),
            avg_sqm=88.0,
            dominant_property_type=PropertyType.APARTMENT,
            energy_efficiency_score=8.0,
            avg_investment_score=85.0,  # High score
            estimated_avg_yield=3.8,
            market_activity_score=8.5,  # High activity
            price_volatility=0.25,
            market_maturity="developing",
            liquidity_score=0.8
        )
        
        profile2 = segment2.get_target_investor_profile()
        assert "Growth-focused aggressive investor" in profile2
    
    def test_key_strengths_identification(self):
        """Test key strengths identification"""
        segment = MarketSegment(
            segment_id="strong-segment",
            neighborhood="Strong Market",
            property_count=35,
            avg_price=Decimal("350000"),
            median_price=Decimal("340000"),
            avg_price_per_sqm=Decimal("4000"),
            price_std_dev=Decimal("60000"),
            avg_sqm=87.5,
            dominant_property_type=PropertyType.APARTMENT,
            energy_efficiency_score=8.5,  # High energy efficiency
            avg_investment_score=78.0,     # Strong fundamentals
            estimated_avg_yield=4.8,       # Above average yield
            market_activity_score=8.0,     # Active market
            price_volatility=0.20,
            market_maturity="mature",
            liquidity_score=0.75
        )
        
        strengths = segment.identify_key_strengths()
        
        assert "Above-average rental yields" in strengths
        assert "High energy efficiency" in strengths
        assert "Active market with good liquidity" in strengths
        assert "Strong investment fundamentals" in strengths
    
    def test_risk_factors_identification(self):
        """Test risk factors identification"""
        segment = MarketSegment(
            segment_id="risky-segment",
            neighborhood="Volatile Market",
            property_count=8,              # Low count
            avg_price=Decimal("280000"),
            median_price=Decimal("275000"),
            avg_price_per_sqm=Decimal("3500"),
            price_std_dev=Decimal("90000"),
            avg_sqm=80.0,
            dominant_property_type=PropertyType.APARTMENT,
            energy_efficiency_score=5.0,
            avg_investment_score=65.0,
            estimated_avg_yield=2.8,       # Low yield
            market_activity_score=4.0,
            price_volatility=0.35,         # High volatility
            market_maturity="emerging",
            liquidity_score=0.25           # Low liquidity
        )
        
        risks = segment.identify_risk_factors()
        
        assert "High price volatility" in risks
        assert "Limited market depth" in risks
        assert "Lower market liquidity" in risks
        assert "Below-average rental yields" in risks
    
    def test_budget_recommendations(self):
        """Test recommended budget range calculation"""
        segment = MarketSegment(
            segment_id="budget-segment",
            neighborhood="Budget Area",
            property_count=25,
            avg_price=Decimal("300000"),
            median_price=Decimal("290000"),  # Base for calculations
            avg_price_per_sqm=Decimal("3500"),
            price_std_dev=Decimal("50000"),
            avg_sqm=85.7,
            dominant_property_type=PropertyType.APARTMENT,
            energy_efficiency_score=6.5,
            avg_investment_score=72.0,
            estimated_avg_yield=4.1,
            market_activity_score=6.8,
            price_volatility=0.22,
            market_maturity="established",
            liquidity_score=0.68
        )
        
        budget_range = segment.get_recommended_budget_range()
        
        assert 'entry_level' in budget_range
        assert 'optimal_range_min' in budget_range
        assert 'optimal_range_max' in budget_range
        assert 'premium_level' in budget_range
        
        # Check logical ordering
        assert budget_range['entry_level'] < budget_range['optimal_range_min']
        assert budget_range['optimal_range_min'] < budget_range['optimal_range_max']
        assert budget_range['optimal_range_max'] < budget_range['premium_level']
        
        # Check relative to median price
        median_price = float(segment.median_price)
        assert budget_range['entry_level'] == int(median_price * 0.7)
        assert budget_range['premium_level'] == int(median_price * 1.5)