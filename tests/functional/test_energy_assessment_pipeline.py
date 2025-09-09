"""
Functional Testing Suite for Energy Assessment Pipeline
Tests core energy assessment functionality and business logic
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from src.core.domain.entities import Property, PropertyType, EnergyClass, ListingType, Location
from src.core.services.energy_assessment import EnergyAssessmentService, EnergyRecommendation
from src.core.analytics.energy_efficiency import EnergyEfficiencyCalculator


class TestEnergyAssessmentPipeline:
    """Test energy assessment pipeline functionality"""

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for energy assessment"""
        return {
            'property_id': 'energy_test_001',
            'property_type': PropertyType.APARTMENT,
            'sqm': 85.0,
            'year_built': 2005,
            'energy_class': EnergyClass.C,
            'heating_system': 'gas',
            'insulation_walls': False,
            'insulation_roof': True,
            'solar_panels': False,
            'windows_type': 'single_glazed',
            'location': {
                'neighborhood': 'Kolonaki',
                'climate_zone': 'Mediterranean'
            },
            'current_energy_cost': Decimal('1200'),  # Annual cost in EUR
            'floor': 3,
            'orientation': 'south'
        }

    @pytest.fixture
    def energy_calculator(self):
        """Energy efficiency calculator instance"""
        return EnergyEfficiencyCalculator()

    @pytest.fixture
    async def energy_assessment_service(self, mock_property_repository):
        """Energy assessment service with mocked dependencies"""
        service = EnergyAssessmentService(
            property_repo=mock_property_repository,
            calculator=EnergyEfficiencyCalculator()
        )
        return service

    async def test_energy_class_calculation(self, energy_calculator, sample_property_data):
        """Test accurate energy class calculation"""
        # Test various scenarios
        test_scenarios = [
            # (modifications, expected_class, description)
            ({}, EnergyClass.C, "Current state"),
            ({'insulation_walls': True, 'insulation_roof': True}, EnergyClass.B, "With insulation"),
            ({'solar_panels': True, 'windows_type': 'double_glazed'}, EnergyClass.B, "With solar and windows"),
            ({'energy_class': EnergyClass.A, 'solar_panels': True}, EnergyClass.A, "Already efficient"),
        ]

        for modifications, expected_class, description in test_scenarios:
            test_data = {**sample_property_data, **modifications}
            
            calculated_class = await energy_calculator.calculate_energy_class(test_data)
            
            assert calculated_class == expected_class, f"Energy class calculation failed for: {description}"

    async def test_energy_efficiency_scoring(self, energy_calculator, sample_property_data):
        """Test energy efficiency scoring algorithm"""
        base_score = await energy_calculator.calculate_efficiency_score(sample_property_data)
        
        # Base C-class apartment should have moderate score
        assert 40 <= base_score <= 70, f"Base efficiency score out of expected range: {base_score}"

        # Test improvements increase score
        improved_data = {
            **sample_property_data,
            'insulation_walls': True,
            'insulation_roof': True,
            'solar_panels': True,
            'windows_type': 'triple_glazed'
        }
        
        improved_score = await energy_calculator.calculate_efficiency_score(improved_data)
        assert improved_score > base_score, "Energy improvements should increase efficiency score"
        assert improved_score >= 80, f"Fully improved property should have high score: {improved_score}"

    async def test_energy_cost_estimation(self, energy_calculator, sample_property_data):
        """Test energy cost estimation accuracy"""
        current_cost = await energy_calculator.estimate_annual_energy_cost(sample_property_data)
        
        # Should be reasonable for 85m² apartment
        assert 800 <= current_cost <= 2000, f"Annual energy cost estimation unrealistic: €{current_cost}"

        # Test cost reduction with improvements
        efficient_data = {
            **sample_property_data,
            'energy_class': EnergyClass.A,
            'insulation_walls': True,
            'insulation_roof': True,
            'solar_panels': True,
            'heating_system': 'heat_pump'
        }
        
        efficient_cost = await energy_calculator.estimate_annual_energy_cost(efficient_data)
        
        # Should be significantly lower
        assert efficient_cost < current_cost * 0.6, "Energy efficiency improvements should reduce costs significantly"

    async def test_renovation_recommendations(self, energy_assessment_service, sample_property_data):
        """Test energy renovation recommendations"""
        recommendations = await energy_assessment_service.generate_renovation_recommendations(sample_property_data)
        
        assert isinstance(recommendations, list), "Recommendations should be a list"
        assert len(recommendations) > 0, "Should generate at least one recommendation"

        # Check recommendation structure
        for rec in recommendations:
            assert hasattr(rec, 'improvement_type'), "Recommendation should have improvement type"
            assert hasattr(rec, 'estimated_cost'), "Recommendation should have estimated cost"
            assert hasattr(rec, 'annual_savings'), "Recommendation should have annual savings"
            assert hasattr(rec, 'payback_period'), "Recommendation should have payback period"
            assert hasattr(rec, 'energy_class_improvement'), "Recommendation should show energy class improvement"

        # Verify logical recommendations for the sample property
        rec_types = [rec.improvement_type for rec in recommendations]
        
        # Should recommend wall insulation since it's currently missing
        assert 'wall_insulation' in rec_types, "Should recommend wall insulation for uninsulated property"

    async def test_payback_period_calculation(self, energy_assessment_service, sample_property_data):
        """Test payback period calculation for energy improvements"""
        recommendations = await energy_assessment_service.generate_renovation_recommendations(sample_property_data)
        
        for rec in recommendations:
            # Payback period should be reasonable (1-20 years)
            assert 1 <= rec.payback_period <= 20, f"Unrealistic payback period: {rec.payback_period} years for {rec.improvement_type}"
            
            # Cost should be positive
            assert rec.estimated_cost > 0, f"Improvement cost should be positive: €{rec.estimated_cost}"
            
            # Savings should be positive
            assert rec.annual_savings > 0, f"Annual savings should be positive: €{rec.annual_savings}"
            
            # Payback period should match calculation
            calculated_payback = rec.estimated_cost / rec.annual_savings
            assert abs(rec.payback_period - calculated_payback) < 0.5, "Payback period calculation mismatch"

    async def test_energy_certificate_generation(self, energy_assessment_service, sample_property_data):
        """Test energy certificate generation"""
        certificate = await energy_assessment_service.generate_energy_certificate(sample_property_data)
        
        # Certificate should have required fields
        required_fields = [
            'property_id', 'energy_class', 'efficiency_score', 'annual_energy_consumption',
            'co2_emissions', 'certificate_date', 'valid_until', 'assessor_id'
        ]
        
        for field in required_fields:
            assert hasattr(certificate, field), f"Energy certificate missing required field: {field}"

        # Energy class should match calculation
        assert certificate.energy_class == sample_property_data['energy_class']
        
        # Certificate should be valid for 10 years
        validity_period = certificate.valid_until - certificate.certificate_date
        assert 9.5 <= validity_period.days / 365.25 <= 10.5, "Certificate validity period should be ~10 years"

    async def test_climate_zone_adjustments(self, energy_calculator):
        """Test climate zone adjustments in energy calculations"""
        base_property = {
            'sqm': 100,
            'energy_class': EnergyClass.B,
            'heating_system': 'gas',
            'insulation_walls': True,
            'insulation_roof': True
        }

        climate_zones = [
            ('Mediterranean', 'warm climate'),
            ('Continental', 'cold winters'),
            ('Mountain', 'very cold'),
            ('Coastal', 'mild climate')
        ]

        base_cost = None
        
        for zone, description in climate_zones:
            property_data = {
                **base_property,
                'location': {'climate_zone': zone}
            }
            
            cost = await energy_calculator.estimate_annual_energy_cost(property_data)
            
            if base_cost is None:
                base_cost = cost
            
            # Different climate zones should produce different costs
            assert cost > 0, f"Energy cost should be positive for {zone} climate"
            
            # Mountain climate should have higher heating costs
            if zone == 'Mountain':
                assert cost > base_cost * 1.2, f"Mountain climate should have higher energy costs"

    async def test_heating_system_comparison(self, energy_calculator, sample_property_data):
        """Test energy calculations for different heating systems"""
        heating_systems = [
            ('gas', 'Natural gas'),
            ('oil', 'Oil heating'),
            ('electric', 'Electric heating'),
            ('heat_pump', 'Heat pump'),
            ('solar', 'Solar heating')
        ]

        costs_by_system = {}

        for system, description in heating_systems:
            property_data = {
                **sample_property_data,
                'heating_system': system
            }
            
            cost = await energy_calculator.estimate_annual_energy_cost(property_data)
            efficiency_score = await energy_calculator.calculate_efficiency_score(property_data)
            
            costs_by_system[system] = (cost, efficiency_score, description)
            
            assert cost > 0, f"Energy cost should be positive for {description}"
            assert 0 <= efficiency_score <= 100, f"Efficiency score should be 0-100 for {description}"

        # Heat pump should be more efficient than oil
        assert costs_by_system['heat_pump'][0] < costs_by_system['oil'][0], "Heat pump should be cheaper than oil"
        assert costs_by_system['heat_pump'][1] > costs_by_system['oil'][1], "Heat pump should be more efficient than oil"

        # Solar should be most efficient
        solar_efficiency = costs_by_system['solar'][1]
        other_efficiencies = [score for system, (cost, score, desc) in costs_by_system.items() if system != 'solar']
        assert solar_efficiency >= max(other_efficiencies), "Solar should be most efficient heating system"

    async def test_property_age_impact(self, energy_calculator, sample_property_data):
        """Test impact of property age on energy calculations"""
        age_scenarios = [
            (2020, 'New construction'),
            (2010, 'Recent construction'),
            (2000, 'Early 2000s'),
            (1990, '1990s construction'),
            (1980, '1980s construction'),
            (1970, 'Older construction')
        ]

        base_score = None

        for year_built, description in age_scenarios:
            property_data = {
                **sample_property_data,
                'year_built': year_built
            }
            
            efficiency_score = await energy_calculator.calculate_efficiency_score(property_data)
            
            if base_score is None:
                base_score = efficiency_score
            
            assert 0 <= efficiency_score <= 100, f"Efficiency score out of range for {description}"
            
            # Newer properties should generally be more efficient
            if year_built >= 2015:  # Recent construction with modern standards
                assert efficiency_score >= base_score, f"Newer property should be more efficient: {description}"

    async def test_solar_potential_calculation(self, energy_calculator, sample_property_data):
        """Test solar panel potential calculation"""
        orientations = ['north', 'south', 'east', 'west', 'southeast', 'southwest']
        
        solar_potentials = {}

        for orientation in orientations:
            property_data = {
                **sample_property_data,
                'orientation': orientation,
                'floor': 5  # Top floor for better solar access
            }
            
            solar_potential = await energy_calculator.calculate_solar_potential(property_data)
            solar_potentials[orientation] = solar_potential
            
            assert 0 <= solar_potential <= 100, f"Solar potential should be 0-100% for {orientation} orientation"

        # South-facing should have best solar potential
        assert solar_potentials['south'] >= max(solar_potentials.values()), "South orientation should have best solar potential"
        
        # North-facing should have lowest solar potential
        assert solar_potentials['north'] <= min(solar_potentials.values()), "North orientation should have lowest solar potential"

    async def test_energy_assessment_workflow(self, energy_assessment_service, sample_property_data):
        """Test complete energy assessment workflow"""
        # Step 1: Initial assessment
        initial_assessment = await energy_assessment_service.assess_property_energy(sample_property_data)
        
        assert initial_assessment is not None, "Initial assessment should not be None"
        assert hasattr(initial_assessment, 'current_energy_class'), "Assessment should have current energy class"
        assert hasattr(initial_assessment, 'efficiency_score'), "Assessment should have efficiency score"
        assert hasattr(initial_assessment, 'annual_cost'), "Assessment should have annual cost"

        # Step 2: Generate recommendations
        recommendations = await energy_assessment_service.generate_renovation_recommendations(sample_property_data)
        
        assert len(recommendations) > 0, "Should generate recommendations"

        # Step 3: Apply best recommendation and reassess
        best_recommendation = min(recommendations, key=lambda r: r.payback_period)
        
        improved_property_data = await energy_assessment_service.apply_improvement(
            sample_property_data, 
            best_recommendation
        )
        
        improved_assessment = await energy_assessment_service.assess_property_energy(improved_property_data)
        
        # Improvement should increase efficiency
        assert improved_assessment.efficiency_score > initial_assessment.efficiency_score, "Improvement should increase efficiency score"
        
        # Improvement should reduce annual cost
        assert improved_assessment.annual_cost < initial_assessment.annual_cost, "Improvement should reduce annual cost"

    async def test_bulk_property_assessment(self, energy_assessment_service, property_data_generator):
        """Test bulk assessment of multiple properties"""
        # Generate test properties with different characteristics
        properties = property_data_generator(count=20, energy_class=EnergyClass.C)
        
        # Add variation to properties
        for i, prop in enumerate(properties):
            prop.year_built = 1980 + (i * 2)  # Varying ages
            prop.sqm = 60 + (i * 3)  # Varying sizes
            prop.heating_system = ['gas', 'oil', 'electric', 'heat_pump'][i % 4]  # Varying systems

        # Assess all properties
        assessments = await energy_assessment_service.assess_multiple_properties([
            {
                'property_id': prop.property_id,
                'sqm': prop.sqm,
                'year_built': prop.year_built,
                'energy_class': prop.energy_class,
                'heating_system': getattr(prop, 'heating_system', 'gas')
            }
            for prop in properties
        ])
        
        assert len(assessments) == len(properties), "Should assess all properties"
        
        # All assessments should be valid
        for assessment in assessments:
            assert assessment.efficiency_score > 0, "All assessments should have positive efficiency score"
            assert assessment.annual_cost > 0, "All assessments should have positive annual cost"

    async def test_energy_improvement_prioritization(self, energy_assessment_service, sample_property_data):
        """Test prioritization of energy improvements"""
        recommendations = await energy_assessment_service.generate_renovation_recommendations(sample_property_data)
        
        # Should be sorted by priority (typically payback period or cost-effectiveness)
        payback_periods = [rec.payback_period for rec in recommendations]
        
        # Verify some logical ordering (not necessarily strict sorting due to other factors)
        high_priority = recommendations[:len(recommendations)//2]
        low_priority = recommendations[len(recommendations)//2:]
        
        avg_high_payback = sum(rec.payback_period for rec in high_priority) / len(high_priority)
        avg_low_payback = sum(rec.payback_period for rec in low_priority) / len(low_priority) if low_priority else float('inf')
        
        assert avg_high_payback <= avg_low_payback, "High priority improvements should have better payback periods on average"

    async def test_energy_class_transitions(self, energy_assessment_service, sample_property_data):
        """Test energy class transition scenarios"""
        # Test different starting energy classes
        starting_classes = [EnergyClass.G, EnergyClass.E, EnergyClass.C, EnergyClass.A]
        
        for starting_class in starting_classes:
            property_data = {
                **sample_property_data,
                'energy_class': starting_class
            }
            
            recommendations = await energy_assessment_service.generate_renovation_recommendations(property_data)
            
            # Should have recommendations for improvement (unless already A+ class)
            if starting_class != EnergyClass.A:
                assert len(recommendations) > 0, f"Should have recommendations for {starting_class} class property"
                
                # At least one recommendation should improve energy class
                improvements = [rec for rec in recommendations if rec.energy_class_improvement]
                assert len(improvements) > 0, f"Should have class-improving recommendations for {starting_class}"

    async def test_investment_roi_calculation(self, energy_assessment_service, sample_property_data):
        """Test ROI calculation for energy investments"""
        recommendations = await energy_assessment_service.generate_renovation_recommendations(sample_property_data)
        
        for rec in recommendations:
            # Calculate expected ROI
            annual_roi = (rec.annual_savings / rec.estimated_cost) * 100
            
            assert annual_roi > 0, f"Investment ROI should be positive for {rec.improvement_type}"
            
            # ROI should be reasonable (typically 5-50% annually)
            assert 2 <= annual_roi <= 100, f"Annual ROI seems unrealistic: {annual_roi}% for {rec.improvement_type}"
            
            # Property value increase should be considered
            if hasattr(rec, 'property_value_increase'):
                total_benefit = rec.annual_savings * 10 + rec.property_value_increase  # 10-year savings + value increase
                total_roi = (total_benefit / rec.estimated_cost - 1) * 100
                
                assert total_roi > annual_roi * 5, "Total ROI should consider property value increase"


class TestEnergyAssessmentAccuracy:
    """Test accuracy and reliability of energy assessments"""

    @pytest.fixture
    def reference_properties(self):
        """Reference properties with known energy characteristics"""
        return [
            {
                'id': 'efficient_modern',
                'year_built': 2018,
                'sqm': 80,
                'energy_class': EnergyClass.A,
                'heating_system': 'heat_pump',
                'insulation_walls': True,
                'insulation_roof': True,
                'solar_panels': True,
                'windows_type': 'triple_glazed',
                'expected_annual_cost': 600,  # Very efficient
                'expected_efficiency_score': 85
            },
            {
                'id': 'average_property',
                'year_built': 2005,
                'sqm': 85,
                'energy_class': EnergyClass.C,
                'heating_system': 'gas',
                'insulation_walls': False,
                'insulation_roof': True,
                'solar_panels': False,
                'windows_type': 'double_glazed',
                'expected_annual_cost': 1200,
                'expected_efficiency_score': 55
            },
            {
                'id': 'inefficient_old',
                'year_built': 1975,
                'sqm': 90,
                'energy_class': EnergyClass.F,
                'heating_system': 'oil',
                'insulation_walls': False,
                'insulation_roof': False,
                'solar_panels': False,
                'windows_type': 'single_glazed',
                'expected_annual_cost': 2000,
                'expected_efficiency_score': 25
            }
        ]

    async def test_assessment_accuracy(self, energy_assessment_service, reference_properties):
        """Test assessment accuracy against reference properties"""
        for ref_prop in reference_properties:
            assessment = await energy_assessment_service.assess_property_energy(ref_prop)
            
            # Test cost estimation accuracy (within ±20%)
            cost_tolerance = ref_prop['expected_annual_cost'] * 0.2
            cost_diff = abs(assessment.annual_cost - ref_prop['expected_annual_cost'])
            
            assert cost_diff <= cost_tolerance, f"Cost estimation inaccurate for {ref_prop['id']}: expected {ref_prop['expected_annual_cost']}, got {assessment.annual_cost}"
            
            # Test efficiency score accuracy (within ±10 points)
            score_diff = abs(assessment.efficiency_score - ref_prop['expected_efficiency_score'])
            
            assert score_diff <= 10, f"Efficiency score inaccurate for {ref_prop['id']}: expected {ref_prop['expected_efficiency_score']}, got {assessment.efficiency_score}"

    async def test_consistency_across_similar_properties(self, energy_assessment_service):
        """Test consistency of assessments across similar properties"""
        # Create similar properties with minor variations
        base_property = {
            'year_built': 2010,
            'sqm': 85,
            'energy_class': EnergyClass.B,
            'heating_system': 'gas',
            'insulation_walls': True,
            'insulation_roof': True
        }

        similar_properties = []
        for i in range(5):
            prop = base_property.copy()
            prop['property_id'] = f'similar_{i}'
            prop['sqm'] += i * 2  # Minor size variation (85-93 sqm)
            similar_properties.append(prop)

        # Assess all properties
        assessments = []
        for prop in similar_properties:
            assessment = await energy_assessment_service.assess_property_energy(prop)
            assessments.append(assessment)

        # Calculate coefficient of variation for efficiency scores
        scores = [a.efficiency_score for a in assessments]
        mean_score = sum(scores) / len(scores)
        std_dev = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5
        cv = (std_dev / mean_score) * 100 if mean_score > 0 else 0

        # Coefficient of variation should be low for similar properties
        assert cv < 15, f"High variability in similar properties: CV = {cv}%"

    async def test_edge_case_handling(self, energy_assessment_service):
        """Test handling of edge cases in energy assessment"""
        edge_cases = [
            {
                'description': 'Very small apartment',
                'data': {'sqm': 25, 'energy_class': EnergyClass.B, 'year_built': 2010}
            },
            {
                'description': 'Very large apartment', 
                'data': {'sqm': 300, 'energy_class': EnergyClass.C, 'year_built': 2000}
            },
            {
                'description': 'Very old property',
                'data': {'sqm': 80, 'energy_class': EnergyClass.G, 'year_built': 1950}
            },
            {
                'description': 'Very new property',
                'data': {'sqm': 85, 'energy_class': EnergyClass.A, 'year_built': 2023}
            }
        ]

        for case in edge_cases:
            try:
                assessment = await energy_assessment_service.assess_property_energy(case['data'])
                
                # Should produce valid results
                assert assessment is not None, f"Assessment failed for {case['description']}"
                assert assessment.efficiency_score >= 0, f"Invalid efficiency score for {case['description']}"
                assert assessment.annual_cost > 0, f"Invalid annual cost for {case['description']}"
                
            except Exception as e:
                pytest.fail(f"Edge case failed for {case['description']}: {e}")


class TestEnergyAssessmentIntegration:
    """Integration tests for energy assessment system"""

    async def test_property_to_assessment_integration(self, energy_assessment_service, sample_properties):
        """Test integration between property entities and energy assessment"""
        # Take first property from sample
        property_entity = sample_properties[0]
        
        # Convert to assessment format
        assessment_data = {
            'property_id': property_entity.property_id,
            'sqm': property_entity.sqm,
            'year_built': property_entity.year_built,
            'energy_class': property_entity.energy_class,
            'heating_system': getattr(property_entity, 'heating_system', 'gas')
        }
        
        # Should successfully assess
        assessment = await energy_assessment_service.assess_property_energy(assessment_data)
        
        assert assessment is not None
        assert assessment.property_id == property_entity.property_id

    async def test_batch_assessment_performance(self, energy_assessment_service, property_data_generator):
        """Test performance of batch energy assessments"""
        import time
        
        # Generate larger set of properties
        properties = property_data_generator(count=100)
        
        # Convert to assessment format
        assessment_data = []
        for prop in properties:
            assessment_data.append({
                'property_id': prop.property_id,
                'sqm': prop.sqm,
                'year_built': prop.year_built,
                'energy_class': prop.energy_class,
                'heating_system': getattr(prop, 'heating_system', 'gas')
            })
        
        # Time the batch assessment
        start_time = time.perf_counter()
        assessments = await energy_assessment_service.assess_multiple_properties(assessment_data)
        elapsed = time.perf_counter() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 10.0, f"Batch assessment took too long: {elapsed:.2f}s for 100 properties"
        
        # Should assess all properties
        assert len(assessments) == len(properties), "Should assess all properties in batch"
        
        # Calculate throughput
        throughput = len(properties) / elapsed
        assert throughput > 10, f"Low assessment throughput: {throughput:.1f} assessments/sec"

    @pytest.mark.slow
    async def test_assessment_consistency_over_time(self, energy_assessment_service, sample_property_data):
        """Test that energy assessments are consistent over multiple runs"""
        # Run assessment multiple times
        assessments = []
        for i in range(10):
            assessment = await energy_assessment_service.assess_property_energy(sample_property_data)
            assessments.append(assessment)
        
        # All assessments should be identical
        first_assessment = assessments[0]
        for i, assessment in enumerate(assessments[1:], 1):
            assert assessment.efficiency_score == first_assessment.efficiency_score, f"Inconsistent efficiency score in run {i}"
            assert assessment.annual_cost == first_assessment.annual_cost, f"Inconsistent annual cost in run {i}"
            assert assessment.energy_class == first_assessment.energy_class, f"Inconsistent energy class in run {i}"