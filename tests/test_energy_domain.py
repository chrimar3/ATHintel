"""
🧪 Comprehensive Unit Tests for Energy Domain

Test suite covering domain entities, value objects, and business logic
for the energy assessment system with Greek market specifics.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any

# Import domain objects to test
from domains.energy.entities.property_energy import (
    PropertyEnergyEntity, PropertyEnergyProfile, BuildingType, HeatingSystem
)
from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.value_objects.financial_metrics import FinancialMetrics
from domains.energy.value_objects.upgrade_recommendation import (
    UpgradeRecommendation, UpgradeType, UpgradePriority, 
    ImplementationDifficulty, GovernmentSubsidy,
    create_heating_system_upgrade
)
from domains.energy.events.domain_events import (
    PropertyEnergyAssessed, UpgradeRecommendationGenerated, 
    EnergyMarketDataUpdated, get_event_publisher
)

class TestEnergyClass:
    """Test EU Energy Class value object functionality"""
    
    def test_energy_class_numeric_values(self):
        """Test energy class to numeric conversion"""
        assert EnergyClass.A_PLUS.numeric_value == 1
        assert EnergyClass.A.numeric_value == 2
        assert EnergyClass.G.numeric_value == 9
    
    def test_energy_consumption_ranges(self):
        """Test kWh/m²/year consumption ranges"""
        a_plus_range = EnergyClass.A_PLUS.kwh_per_m2_range
        assert a_plus_range == (Decimal('0'), Decimal('50'))
        
        g_range = EnergyClass.G.kwh_per_m2_range
        assert g_range == (Decimal('301'), Decimal('500'))
    
    def test_energy_class_from_consumption(self):
        """Test energy class determination from consumption"""
        assert EnergyClass.from_consumption(Decimal('25')) == EnergyClass.A_PLUS
        assert EnergyClass.from_consumption(Decimal('60')) == EnergyClass.A
        assert EnergyClass.from_consumption(Decimal('175')) == EnergyClass.D
        assert EnergyClass.from_consumption(Decimal('400')) == EnergyClass.G
        assert EnergyClass.from_consumption(Decimal('600')) == EnergyClass.G  # Cap at G
    
    def test_greek_market_context(self):
        """Test Greek-specific market context information"""
        c_class_context = EnergyClass.C.greek_context
        
        assert 'typical_buildings' in c_class_context
        assert 'heating_cost' in c_class_context
        assert 'market_premium' in c_class_context
        assert 'renovation_status' in c_class_context
        
        # Test typical Greek apartment characteristics
        assert 'apartment blocks' in c_class_context['typical_buildings'].lower()
    
    def test_improvement_potential(self):
        """Test improvement potential calculations"""
        improvement = EnergyClass.E.improvement_potential(EnergyClass.B)
        
        assert improvement['improvement_levels'] == Decimal('5')  # E(7) to B(4) = 3 levels
        assert improvement['consumption_reduction_percentage'] > 0
        assert improvement['cost_savings_percentage'] > 0
    
    def test_upgrade_path_recommendations(self):
        """Test realistic upgrade path suggestions"""
        g_class_paths = EnergyClass.G.get_upgrade_path()
        
        assert g_class_paths['achievable'] == EnergyClass.D
        assert g_class_paths['ambitious'] == EnergyClass.B
        
        a_class_paths = EnergyClass.A.get_upgrade_path()
        assert a_class_paths['achievable'] == EnergyClass.A_PLUS

class TestFinancialMetrics:
    """Test financial analysis calculations"""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample financial metrics for testing"""
        return FinancialMetrics(
            baseline_annual_cost=Decimal('1200'),
            potential_annual_savings=Decimal('360'),
            upgrade_investment_required=Decimal('15000'),
            simple_payback_years=Decimal('4.17'),
            net_present_value=Decimal('2500'),
            internal_rate_of_return=Decimal('18.5')
        )
    
    def test_roi_calculation(self, sample_metrics):
        """Test ROI percentage calculation"""
        expected_roi = (Decimal('360') / Decimal('15000')) * 100
        assert abs(sample_metrics.roi_percentage - expected_roi) < Decimal('0.01')
    
    def test_savings_percentage(self, sample_metrics):
        """Test savings as percentage of baseline"""
        expected_savings_pct = (Decimal('360') / Decimal('1200')) * 100
        assert abs(sample_metrics.savings_percentage - expected_savings_pct) < Decimal('0.01')
    
    def test_npv_detailed_calculation(self, sample_metrics):
        """Test detailed NPV calculation over time"""
        npv_analysis = sample_metrics.calculate_npv_detailed(years=10)
        
        assert 'gross_present_value' in npv_analysis
        assert 'net_present_value' in npv_analysis
        assert 'profitability_index' in npv_analysis
        assert 'annual_cash_flows' in npv_analysis
        
        # Check that we have 10 years of cash flows
        assert len(npv_analysis['annual_cash_flows']) == 10
        
        # NPV should be positive for good investment
        assert npv_analysis['net_present_value'] > 0
    
    def test_irr_calculation(self, sample_metrics):
        """Test Internal Rate of Return calculation"""
        irr = sample_metrics.calculate_irr()
        
        # IRR should be reasonable for energy upgrades (5-30%)
        assert 5 <= irr <= 30
    
    def test_payback_analysis(self, sample_metrics):
        """Test payback period calculations"""
        payback = sample_metrics.calculate_payback_analysis()
        
        assert 'simple_payback' in payback
        assert 'discounted_payback' in payback
        assert 'break_even_year' in payback
        
        # Simple payback should match our input
        assert abs(payback['simple_payback'] - sample_metrics.simple_payback_years) < Decimal('0.1')
        
        # Discounted payback should be longer than simple
        assert payback['discounted_payback'] >= payback['simple_payback']
    
    def test_sensitivity_analysis(self, sample_metrics):
        """Test sensitivity analysis with different scenarios"""
        sensitivity = sample_metrics.sensitivity_analysis()
        
        scenarios = ['pessimistic', 'realistic', 'optimistic']
        assert all(scenario in sensitivity for scenario in scenarios)
        
        # Realistic scenario should match base metrics
        realistic = sensitivity['realistic']
        assert abs(realistic['roi_percentage'] - sample_metrics.roi_percentage) < Decimal('1')
        
        # Optimistic should be better than pessimistic
        assert sensitivity['optimistic']['roi_percentage'] > sensitivity['pessimistic']['roi_percentage']
    
    def test_risk_assessment(self, sample_metrics):
        """Test investment risk assessment"""
        risk = sample_metrics.risk_assessment()
        
        assert 'risk_level' in risk
        assert 'risk_factors' in risk
        assert 'recommendation' in risk
        
        assert risk['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']
        assert isinstance(risk['risk_factors'], list)
    
    def test_greek_market_comparison(self, sample_metrics):
        """Test comparison to Greek investment alternatives"""
        comparison = sample_metrics.compare_to_alternative_investments()
        
        expected_alternatives = ['bank_deposit', 'government_bonds', 'real_estate_market', 'stock_market_index']
        assert all(alt in comparison for alt in expected_alternatives)
        
        # Each comparison should have required fields
        for alt_data in comparison.values():
            assert 'alternative_return' in alt_data
            assert 'energy_upgrade_advantage' in alt_data
            assert 'recommendation' in alt_data

class TestUpgradeRecommendation:
    """Test upgrade recommendation functionality"""
    
    @pytest.fixture
    def sample_subsidy(self):
        """Create sample Greek government subsidy"""
        return GovernmentSubsidy(
            program_name="Εξοικονομώ - Κατ' Οίκον",
            subsidy_percentage=Decimal('70'),
            max_subsidy_amount=Decimal('25000'),
            eligibility_criteria=["Building age > 15 years", "Energy class D or lower"]
        )
    
    @pytest.fixture
    def sample_recommendation(self, sample_subsidy):
        """Create sample upgrade recommendation"""
        return UpgradeRecommendation(
            upgrade_type=UpgradeType.WALL_INSULATION,
            priority=UpgradePriority.HIGH,
            implementation_difficulty=ImplementationDifficulty.MODERATE,
            cost=Decimal('12000'),
            annual_savings=Decimal('480'),
            roi=Decimal('20'),
            simple_payback_years=Decimal('5'),
            description="External wall insulation upgrade",
            technical_specifications={
                "insulation_type": "EPS",
                "thickness": "10cm",
                "coverage_area": "120m²"
            },
            energy_class_improvement=1,
            implementation_time="3 weeks",
            best_season="spring",
            permits_required=["Building permit"],
            available_subsidies=[sample_subsidy],
            confidence_level=Decimal('0.85')
        )
    
    def test_net_cost_after_subsidies(self, sample_recommendation):
        """Test cost calculation after applying subsidies"""
        net_cost = sample_recommendation.net_cost_after_subsidies
        
        # With 70% subsidy, net cost should be 30% of original
        expected_net_cost = sample_recommendation.cost * Decimal('0.3')
        assert abs(net_cost - expected_net_cost) < Decimal('1')
    
    def test_payback_after_subsidies(self, sample_recommendation):
        """Test payback calculation including subsidies"""
        payback = sample_recommendation.payback_after_subsidies
        
        # Should be much shorter than simple payback due to subsidy
        assert payback < sample_recommendation.simple_payback_years
    
    def test_priority_score_calculation(self, sample_recommendation):
        """Test priority score algorithm"""
        priority_score = sample_recommendation.priority_score
        
        # Should be between 0-100
        assert 0 <= priority_score <= 100
        
        # High priority with good ROI should score well
        assert priority_score >= 70
    
    def test_implementation_timeline(self, sample_recommendation):
        """Test implementation timeline calculation"""
        timeline = sample_recommendation.get_implementation_timeline()
        
        required_keys = ['recommended_start', 'estimated_completion', 'preparation_start']
        assert all(key in timeline for key in required_keys)
        
        # Completion should be after start
        assert timeline['estimated_completion'] > timeline['recommended_start']
        
        # Preparation should be before start
        assert timeline['preparation_start'] < timeline['recommended_start']
    
    def test_ten_year_value_analysis(self, sample_recommendation):
        """Test 10-year financial value calculation"""
        value_analysis = sample_recommendation.calculate_10_year_value()
        
        required_keys = ['net_present_value', 'cumulative_savings', 'total_energy_savings', 'roi_10_year']
        assert all(key in value_analysis for key in required_keys)
        
        # 10-year savings should be substantial
        assert value_analysis['total_energy_savings'] > sample_recommendation.annual_savings * 5
    
    def test_factory_method_heating_upgrade(self):
        """Test factory method for heating system upgrades"""
        heating_upgrade = create_heating_system_upgrade(
            current_system='oil_boiler',
            building_area=Decimal('100'),
            target_efficiency_gain=Decimal('30')
        )
        
        assert heating_upgrade.upgrade_type == UpgradeType.HEAT_PUMP
        assert heating_upgrade.cost > 0
        assert heating_upgrade.annual_savings > 0
        assert heating_upgrade.roi > 0

class TestPropertyEnergyEntity:
    """Test property energy entity business logic"""
    
    @pytest.fixture
    def sample_property(self):
        """Create sample property energy entity"""
        profile = PropertyEnergyProfile(
            current_energy_class=EnergyClass.D,
            annual_consumption_kwh_per_m2=Decimal('180'),
            annual_energy_cost=Decimal('1500'),
            heating_system=HeatingSystem.INDIVIDUAL_GAS,
            has_recent_renovation=False
        )
        
        return PropertyEnergyEntity(
            property_id="PROP_TEST_001",
            energy_profile=profile,
            building_type=BuildingType.APARTMENT,
            construction_year=1985,
            total_area=Decimal('95'),
            location={'region': 'attiki', 'city': 'athens'}
        )
    
    def test_subsidy_eligibility(self, sample_property):
        """Test Greek subsidy eligibility calculation"""
        eligibility = sample_property.is_eligible_for_subsidies()
        
        # Should be eligible for major programs
        assert eligibility['exoikonomo'] is True  # Old building, poor energy class
        assert eligibility['local_municipality'] is True  # Athens region
        
        expected_programs = ['exoikonomo', 'local_municipality', 'eu_renovation_wave']
        assert all(program in eligibility for program in expected_programs)
    
    def test_upgrade_priority_calculation(self, sample_property):
        """Test upgrade priority determination"""
        priorities = sample_property.calculate_upgrade_priorities()
        
        # Should identify key upgrade areas
        expected_upgrades = ['heating_system', 'insulation', 'windows']
        assert all(upgrade in priorities for upgrade in expected_upgrades)
        
        # Each priority should have score and rationale
        for upgrade_data in priorities.values():
            assert 'priority_score' in upgrade_data
            assert 'rationale' in upgrade_data
            assert 0 <= upgrade_data['priority_score'] <= 100
    
    def test_investment_analysis(self, sample_property):
        """Test comprehensive investment analysis"""
        analysis = sample_property.analyze_investment_potential(
            available_budget=Decimal('25000')
        )
        
        required_keys = [
            'recommended_upgrades', 'total_investment', 'expected_annual_savings',
            'portfolio_roi', 'payback_period', 'risk_assessment'
        ]
        assert all(key in analysis for key in required_keys)
        
        # Should not exceed available budget
        assert analysis['total_investment'] <= Decimal('25000')
        
        # ROI should be reasonable
        assert analysis['portfolio_roi'] >= 5  # At least 5% ROI

class TestDomainEvents:
    """Test domain event functionality"""
    
    def test_property_energy_assessed_event(self):
        """Test property energy assessment event"""
        event = PropertyEnergyAssessed(
            property_id="PROP_001",
            assessment_id="ASSESS_001",
            old_energy_class=EnergyClass.E,
            new_energy_class=EnergyClass.C,
            confidence=Decimal('0.88')
        )
        
        assert event.property_id == "PROP_001"
        assert event.old_energy_class == EnergyClass.E
        assert event.new_energy_class == EnergyClass.C
        assert event.confidence == Decimal('0.88')
        
        # Test serialization
        event_dict = event.to_dict()
        assert event_dict['event_type'] == 'PropertyEnergyAssessed'
        assert event_dict['old_energy_class'] == 'E'
        assert event_dict['new_energy_class'] == 'C'
    
    def test_upgrade_recommendation_generated_event(self):
        """Test upgrade recommendation event"""
        event = UpgradeRecommendationGenerated(
            property_id="PROP_001",
            assessment_id="ASSESS_001",
            upgrade_type=UpgradeType.SOLAR_PANELS,
            estimated_cost=Decimal('18000'),
            estimated_savings=Decimal('650'),
            roi=Decimal('22.5')
        )
        
        assert event.upgrade_type == UpgradeType.SOLAR_PANELS
        assert event.estimated_cost == Decimal('18000')
        
        # Test serialization
        event_dict = event.to_dict()
        assert event_dict['upgrade_type'] == 'solar_panels'
        assert event_dict['estimated_cost'] == 18000.0
    
    def test_event_publisher(self):
        """Test event publisher functionality"""
        publisher = get_event_publisher()
        
        # Test event subscription
        received_events = []
        
        def test_handler(event):
            received_events.append(event)
        
        publisher.subscribe(PropertyEnergyAssessed, test_handler)
        
        # Publish test event
        test_event = PropertyEnergyAssessed(
            property_id="TEST_001",
            assessment_id="ASSESS_TEST",
            old_energy_class=None,
            new_energy_class=EnergyClass.B,
            confidence=Decimal('0.9')
        )
        
        publisher.publish(test_event)
        
        # Verify handler was called
        assert len(received_events) == 1
        assert received_events[0].property_id == "TEST_001"

class TestInputValidation:
    """Test input validation and edge cases"""
    
    def test_invalid_financial_metrics(self):
        """Test financial metrics validation"""
        with pytest.raises(ValueError, match="Baseline annual cost cannot be negative"):
            FinancialMetrics(
                baseline_annual_cost=Decimal('-100'),
                potential_annual_savings=Decimal('50'),
                upgrade_investment_required=Decimal('1000'),
                simple_payback_years=Decimal('20'),
                net_present_value=Decimal('100'),
                internal_rate_of_return=Decimal('5')
            )
    
    def test_invalid_upgrade_recommendation(self):
        """Test upgrade recommendation validation"""
        with pytest.raises(ValueError, match="Cost cannot be negative"):
            UpgradeRecommendation(
                upgrade_type=UpgradeType.WALL_INSULATION,
                priority=UpgradePriority.HIGH,
                implementation_difficulty=ImplementationDifficulty.MODERATE,
                cost=Decimal('-5000'),  # Invalid negative cost
                annual_savings=Decimal('500'),
                roi=Decimal('10'),
                simple_payback_years=Decimal('10'),
                description="Test upgrade",
                technical_specifications={},
                energy_class_improvement=1,
                implementation_time="1 week",
                best_season="spring",
                permits_required=[],
                available_subsidies=[]
            )
    
    def test_edge_case_energy_consumption(self):
        """Test edge cases in energy consumption calculations"""
        # Very high consumption
        high_consumption_class = EnergyClass.from_consumption(Decimal('1000'))
        assert high_consumption_class == EnergyClass.G
        
        # Zero consumption (theoretical)
        zero_consumption_class = EnergyClass.from_consumption(Decimal('0'))
        assert zero_consumption_class == EnergyClass.A_PLUS

if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])