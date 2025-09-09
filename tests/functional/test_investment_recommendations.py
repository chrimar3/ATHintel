"""
Functional Testing Suite for Investment Recommendation System
Tests investment analysis, scoring, and recommendation accuracy
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

from src.core.domain.entities import (
    Property, Investment, Portfolio, PropertyType, EnergyClass, 
    ListingType, Location, InvestmentRisk
)
from src.core.services.investment_analysis import InvestmentAnalysisService
from src.core.analytics.investment_scoring import InvestmentScorer
from src.core.analytics.market_analysis import MarketAnalyzer


class TestInvestmentScoring:
    """Test investment scoring algorithm accuracy"""

    @pytest.fixture
    def investment_scorer(self):
        """Investment scorer instance"""
        return InvestmentScorer()

    @pytest.fixture
    def market_analyzer(self):
        """Market analyzer instance"""
        return MarketAnalyzer()

    @pytest.fixture
    def sample_properties_with_metrics(self):
        """Sample properties with different investment characteristics"""
        return [
            {
                'property_id': 'high_yield_property',
                'price': Decimal('200000'),
                'sqm': 70,
                'rooms': 2,
                'neighborhood': 'Exarchia',
                'energy_class': EnergyClass.B,
                'year_built': 2010,
                'estimated_rental': Decimal('800'),  # 4.8% yield
                'neighborhood_growth_rate': 0.08,
                'walkability_score': 85,
                'transport_score': 90,
                'expected_score_range': (75, 85)  # Should be high scoring
            },
            {
                'property_id': 'moderate_investment',
                'price': Decimal('350000'),
                'sqm': 85,
                'rooms': 3,
                'neighborhood': 'Nea Smyrni',
                'energy_class': EnergyClass.C,
                'year_built': 2005,
                'estimated_rental': Decimal('1200'),  # 4.1% yield
                'neighborhood_growth_rate': 0.04,
                'walkability_score': 70,
                'transport_score': 75,
                'expected_score_range': (60, 70)  # Should be moderate scoring
            },
            {
                'property_id': 'low_yield_property',
                'price': Decimal('500000'),
                'sqm': 90,
                'rooms': 3,
                'neighborhood': 'Kolonaki',
                'energy_class': EnergyClass.D,
                'year_built': 1985,
                'estimated_rental': Decimal('1400'),  # 3.4% yield
                'neighborhood_growth_rate': 0.02,
                'walkability_score': 95,
                'transport_score': 85,
                'expected_score_range': (45, 55)  # Should be lower scoring due to low yield
            },
            {
                'property_id': 'value_play_property',
                'price': Decimal('180000'),
                'sqm': 65,
                'rooms': 2,
                'neighborhood': 'Petralona',
                'energy_class': EnergyClass.C,
                'year_built': 2000,
                'estimated_rental': Decimal('700'),  # 4.7% yield
                'neighborhood_growth_rate': 0.12,  # Emerging area
                'walkability_score': 75,
                'transport_score': 80,
                'expected_score_range': (70, 80)  # Should score well due to growth potential
            }
        ]

    async def test_rental_yield_calculation(self, investment_scorer, sample_properties_with_metrics):
        """Test accurate rental yield calculation"""
        for prop_data in sample_properties_with_metrics:
            calculated_yield = await investment_scorer.calculate_rental_yield(
                annual_rent=prop_data['estimated_rental'] * 12,
                property_price=prop_data['price']
            )
            
            # Calculate expected yield
            expected_yield = (prop_data['estimated_rental'] * 12 / prop_data['price']) * 100
            
            # Should be within 0.1% of expected
            assert abs(calculated_yield - expected_yield) < 0.1, f"Yield calculation error for {prop_data['property_id']}"
            
            # Yield should be reasonable (1-15%)
            assert 1.0 <= calculated_yield <= 15.0, f"Unrealistic yield: {calculated_yield}% for {prop_data['property_id']}"

    async def test_investment_score_accuracy(self, investment_scorer, sample_properties_with_metrics):
        """Test investment score accuracy and ranges"""
        for prop_data in sample_properties_with_metrics:
            score = await investment_scorer.calculate_investment_score(prop_data)
            
            min_expected, max_expected = prop_data['expected_score_range']
            
            assert isinstance(score, float), "Investment score should be a float"
            assert 0 <= score <= 100, f"Investment score out of range: {score}"
            
            # Check if score is within expected range (with some tolerance)
            tolerance = 10  # Allow 10-point tolerance for testing
            assert (min_expected - tolerance) <= score <= (max_expected + tolerance), \
                f"Investment score {score} outside expected range {min_expected}-{max_expected} for {prop_data['property_id']}"

    async def test_neighborhood_impact_on_score(self, investment_scorer):
        """Test neighborhood characteristics impact on investment score"""
        base_property = {
            'price': Decimal('300000'),
            'sqm': 80,
            'estimated_rental': Decimal('1200'),
            'energy_class': EnergyClass.B,
            'year_built': 2010
        }

        # Test different neighborhood characteristics
        neighborhood_scenarios = [
            {
                'name': 'Prime location',
                'walkability_score': 95,
                'transport_score': 90,
                'neighborhood_growth_rate': 0.06,
                'crime_rate': 0.02,
                'expected_higher_score': True
            },
            {
                'name': 'Emerging area',
                'walkability_score': 70,
                'transport_score': 75,
                'neighborhood_growth_rate': 0.15,  # High growth
                'crime_rate': 0.05,
                'expected_higher_score': True
            },
            {
                'name': 'Declining area',
                'walkability_score': 50,
                'transport_score': 45,
                'neighborhood_growth_rate': -0.02,  # Negative growth
                'crime_rate': 0.12,
                'expected_higher_score': False
            }
        ]

        base_score = await investment_scorer.calculate_investment_score({
            **base_property,
            'walkability_score': 70,
            'transport_score': 70,
            'neighborhood_growth_rate': 0.04,
            'crime_rate': 0.06
        })

        for scenario in neighborhood_scenarios:
            scenario_property = {
                **base_property,
                **{k: v for k, v in scenario.items() if k not in ['name', 'expected_higher_score']}
            }
            
            scenario_score = await investment_scorer.calculate_investment_score(scenario_property)
            
            if scenario['expected_higher_score']:
                assert scenario_score >= base_score, f"{scenario['name']} should score higher than base case"
            else:
                assert scenario_score < base_score, f"{scenario['name']} should score lower than base case"

    async def test_property_characteristics_impact(self, investment_scorer):
        """Test property characteristics impact on investment score"""
        base_property = {
            'price': Decimal('300000'),
            'sqm': 80,
            'estimated_rental': Decimal('1100'),
            'neighborhood_growth_rate': 0.05,
            'walkability_score': 75,
            'transport_score': 75
        }

        # Test different property characteristics
        property_variations = [
            ('energy_class', EnergyClass.A, EnergyClass.F, 'Higher energy class should improve score'),
            ('year_built', 2018, 1975, 'Newer property should score better'),
            ('sqm', 100, 45, 'Larger property should generally score better'),
            ('rooms', 3, 1, 'More rooms should generally score better')
        ]

        for field, good_value, poor_value, description in property_variations:
            # Test good value
            good_property = {**base_property, field: good_value}
            good_score = await investment_scorer.calculate_investment_score(good_property)
            
            # Test poor value
            poor_property = {**base_property, field: poor_value}
            poor_score = await investment_scorer.calculate_investment_score(poor_property)
            
            assert good_score >= poor_score, f"{description}. Good: {good_score}, Poor: {poor_score}"

    async def test_price_to_value_ratio_impact(self, investment_scorer):
        """Test price-to-value ratio impact on investment scoring"""
        # Same property with different prices
        base_property = {
            'sqm': 80,
            'estimated_rental': Decimal('1000'),
            'energy_class': EnergyClass.B,
            'year_built': 2010,
            'neighborhood_growth_rate': 0.05,
            'walkability_score': 75,
            'transport_score': 75
        }

        prices = [Decimal('200000'), Decimal('300000'), Decimal('400000')]
        scores = []

        for price in prices:
            property_data = {**base_property, 'price': price}
            score = await investment_scorer.calculate_investment_score(property_data)
            scores.append((price, score))

        # Lower price should generally lead to higher score (better value)
        for i in range(len(scores) - 1):
            current_price, current_score = scores[i]
            next_price, next_score = scores[i + 1]
            
            # Allow for some exceptions but generally lower price = higher score
            if next_price > current_price * 1.3:  # Significant price increase
                assert current_score >= next_score * 0.9, f"Significantly cheaper property should score better: {current_price}€ vs {next_price}€"

    async def test_market_timing_impact(self, investment_scorer):
        """Test market timing impact on investment scoring"""
        property_data = {
            'price': Decimal('300000'),
            'sqm': 80,
            'estimated_rental': Decimal('1100'),
            'energy_class': EnergyClass.B,
            'year_built': 2010,
            'walkability_score': 75,
            'transport_score': 75
        }

        # Test different market conditions
        market_conditions = [
            {'name': 'Bull market', 'market_trend': 0.08, 'expected_higher': True},
            {'name': 'Stable market', 'market_trend': 0.02, 'expected_higher': False},
            {'name': 'Bear market', 'market_trend': -0.05, 'expected_higher': False}
        ]

        base_score = await investment_scorer.calculate_investment_score({
            **property_data,
            'market_trend': 0.03
        })

        for condition in market_conditions:
            test_property = {
                **property_data,
                'market_trend': condition['market_trend']
            }
            
            score = await investment_scorer.calculate_investment_score(test_property)
            
            if condition['expected_higher']:
                assert score >= base_score, f"{condition['name']} should result in higher score"


class TestInvestmentAnalysisService:
    """Test investment analysis service functionality"""

    @pytest.fixture
    async def investment_analysis_service(self, mock_property_repository, mock_market_data_service):
        """Investment analysis service with mocked dependencies"""
        return InvestmentAnalysisService(
            property_repo=mock_property_repository,
            market_service=mock_market_data_service,
            scorer=InvestmentScorer()
        )

    @pytest.fixture
    def mock_market_conditions(self):
        """Mock market conditions for testing"""
        return {
            'athens_center': {
                'avg_price_per_sqm': Decimal('3500'),
                'rental_yield_avg': 4.2,
                'price_growth_annual': 0.05,
                'liquidity_score': 0.8,
                'market_health': 'good'
            },
            'suburbs': {
                'avg_price_per_sqm': Decimal('2200'),
                'rental_yield_avg': 5.1,
                'price_growth_annual': 0.07,
                'liquidity_score': 0.6,
                'market_health': 'very_good'
            }
        }

    async def test_property_investment_analysis(self, investment_analysis_service, sample_property):
        """Test comprehensive property investment analysis"""
        analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
        
        # Verify analysis completeness
        required_fields = [
            'investment_score', 'estimated_rental_yield', 'roi_projection_5y',
            'risk_level', 'total_investment_needed', 'cash_flow_projection',
            'market_comparables', 'strengths', 'weaknesses', 'recommendations'
        ]
        
        for field in required_fields:
            assert hasattr(analysis, field), f"Analysis missing required field: {field}"

        # Verify data reasonableness
        assert 0 <= analysis.investment_score <= 100, f"Invalid investment score: {analysis.investment_score}"
        assert 0 <= analysis.estimated_rental_yield <= 15, f"Unrealistic rental yield: {analysis.estimated_rental_yield}%"
        assert analysis.total_investment_needed > analysis.property.price, "Total investment should include additional costs"

    async def test_roi_projection_accuracy(self, investment_analysis_service, sample_properties):
        """Test ROI projection accuracy and reasonableness"""
        for property in sample_properties[:5]:  # Test first 5 properties
            analysis = await investment_analysis_service.analyze_investment_potential(property)
            
            # ROI projections should be reasonable
            assert -20 <= analysis.roi_projection_5y <= 100, f"Unrealistic 5-year ROI: {analysis.roi_projection_5y}% for {property.property_id}"
            
            # Verify ROI calculation logic
            if hasattr(analysis, 'cash_flow_projection') and analysis.cash_flow_projection:
                total_cash_flow = sum(analysis.cash_flow_projection[:5])  # 5-year total
                initial_investment = float(analysis.total_investment_needed)
                
                calculated_roi = (total_cash_flow / initial_investment) * 100
                
                # Should be within reasonable range of projected ROI
                roi_difference = abs(analysis.roi_projection_5y - calculated_roi)
                assert roi_difference < 20, f"ROI projection inconsistent with cash flow for {property.property_id}"

    async def test_risk_assessment_accuracy(self, investment_analysis_service, sample_properties_with_metrics):
        """Test investment risk assessment accuracy"""
        # Create properties with known risk characteristics
        risk_test_properties = [
            {
                **sample_properties_with_metrics[0],  # High yield property
                'neighborhood_volatility': 0.05,
                'market_liquidity': 0.9,
                'expected_risk': InvestmentRisk.LOW
            },
            {
                **sample_properties_with_metrics[2],  # Low yield property
                'neighborhood_volatility': 0.15,
                'market_liquidity': 0.7,
                'expected_risk': InvestmentRisk.MEDIUM
            }
        ]

        for prop_data in risk_test_properties:
            # Convert to Property entity (simplified)
            property_entity = Property(
                property_id=prop_data['property_id'],
                price=prop_data['price'],
                sqm=prop_data['sqm'],
                rooms=prop_data['rooms'],
                location=Location(neighborhood=prop_data['neighborhood']),
                energy_class=prop_data['energy_class'],
                year_built=prop_data['year_built'],
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                url="https://example.com/test",
                title="Test Property",
                timestamp=datetime.now(),
                source="test"
            )
            
            analysis = await investment_analysis_service.analyze_investment_potential(property_entity)
            
            # Risk level should match expectations (with some tolerance)
            expected_risk = prop_data['expected_risk']
            actual_risk = analysis.risk_level
            
            # Allow one level of tolerance (e.g., LOW can be MEDIUM, but not HIGH)
            risk_levels = [InvestmentRisk.LOW, InvestmentRisk.MEDIUM, InvestmentRisk.HIGH]
            expected_index = risk_levels.index(expected_risk)
            actual_index = risk_levels.index(actual_risk)
            
            assert abs(actual_index - expected_index) <= 1, f"Risk assessment mismatch for {prop_data['property_id']}: expected {expected_risk}, got {actual_risk}"

    async def test_market_comparable_analysis(self, investment_analysis_service, sample_property, mock_market_data_service):
        """Test market comparable analysis"""
        # Mock comparable properties
        mock_comparables = [
            {
                'property_id': 'comp_1',
                'price': Decimal('340000'),
                'sqm': 82,
                'price_per_sqm': Decimal('4146'),
                'similarity_score': 0.9
            },
            {
                'property_id': 'comp_2', 
                'price': Decimal('360000'),
                'sqm': 88,
                'price_per_sqm': Decimal('4090'),
                'similarity_score': 0.85
            }
        ]
        
        mock_market_data_service.get_comparable_sales.return_value = mock_comparables
        
        analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
        
        assert len(analysis.market_comparables) > 0, "Should find market comparables"
        
        # Comparables should be reasonably similar
        for comp in analysis.market_comparables:
            assert hasattr(comp, 'similarity_score'), "Comparable should have similarity score"
            assert comp.similarity_score > 0.7, f"Low similarity comparable: {comp.similarity_score}"

    async def test_investment_strengths_weaknesses(self, investment_analysis_service, sample_properties_with_metrics):
        """Test identification of investment strengths and weaknesses"""
        for prop_data in sample_properties_with_metrics[:2]:  # Test first 2 properties
            # Convert to Property entity
            property_entity = Property(
                property_id=prop_data['property_id'],
                price=prop_data['price'],
                sqm=prop_data['sqm'],
                rooms=prop_data['rooms'],
                location=Location(neighborhood=prop_data['neighborhood']),
                energy_class=prop_data['energy_class'],
                year_built=prop_data['year_built'],
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                url="https://example.com/test",
                title="Test Property",
                timestamp=datetime.now(),
                source="test"
            )
            
            analysis = await investment_analysis_service.analyze_investment_potential(property_entity)
            
            # Should identify at least some strengths and weaknesses
            assert len(analysis.strengths) > 0, f"Should identify investment strengths for {prop_data['property_id']}"
            assert len(analysis.weaknesses) >= 0, f"Investment weaknesses should be identified if any exist for {prop_data['property_id']}"
            
            # Strengths and weaknesses should be meaningful
            for strength in analysis.strengths:
                assert isinstance(strength, str), "Strength should be a string description"
                assert len(strength) > 10, "Strength description should be meaningful"
            
            for weakness in analysis.weaknesses:
                assert isinstance(weakness, str), "Weakness should be a string description"
                assert len(weakness) > 10, "Weakness description should be meaningful"

    async def test_cash_flow_projection(self, investment_analysis_service, sample_property):
        """Test cash flow projection calculation"""
        analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
        
        assert hasattr(analysis, 'cash_flow_projection'), "Analysis should include cash flow projection"
        assert len(analysis.cash_flow_projection) >= 5, "Should project at least 5 years of cash flow"
        
        # Cash flow should be reasonable
        for year, cash_flow in enumerate(analysis.cash_flow_projection[:5]):
            assert isinstance(cash_flow, (int, float, Decimal)), f"Cash flow for year {year+1} should be numeric"
            
            # Cash flow should be within reasonable range
            assert -20000 <= cash_flow <= 50000, f"Unrealistic cash flow for year {year+1}: {cash_flow}"

    async def test_total_investment_calculation(self, investment_analysis_service, sample_property):
        """Test total investment calculation including all costs"""
        analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
        
        # Total investment should be greater than property price
        assert analysis.total_investment_needed > sample_property.price, "Total investment should include additional costs"
        
        # Should not be excessively higher (typically 10-25% more)
        ratio = float(analysis.total_investment_needed) / float(sample_property.price)
        assert 1.05 <= ratio <= 1.5, f"Total investment ratio seems unrealistic: {ratio:.2f}"

    async def test_recommendation_generation(self, investment_analysis_service, sample_properties_with_metrics):
        """Test investment recommendation generation"""
        for prop_data in sample_properties_with_metrics:
            # Convert to Property entity
            property_entity = Property(
                property_id=prop_data['property_id'],
                price=prop_data['price'],
                sqm=prop_data['sqm'],
                rooms=prop_data['rooms'],
                location=Location(neighborhood=prop_data['neighborhood']),
                energy_class=prop_data['energy_class'],
                year_built=prop_data['year_built'],
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                url="https://example.com/test",
                title="Test Property",
                timestamp=datetime.now(),
                source="test"
            )
            
            analysis = await investment_analysis_service.analyze_investment_potential(property_entity)
            
            # Should provide recommendations
            assert len(analysis.recommendations) > 0, f"Should provide investment recommendations for {prop_data['property_id']}"
            
            # Recommendations should be relevant to the investment score
            min_expected, max_expected = prop_data['expected_score_range']
            
            if analysis.investment_score >= 70:  # High scoring property
                buy_recommendations = [r for r in analysis.recommendations if 'buy' in r.lower() or 'invest' in r.lower()]
                assert len(buy_recommendations) > 0, "High-scoring property should have positive recommendations"
            
            elif analysis.investment_score < 50:  # Low scoring property  
                caution_recommendations = [r for r in analysis.recommendations if 'caution' in r.lower() or 'avoid' in r.lower() or 'consider' in r.lower()]
                assert len(caution_recommendations) > 0, "Low-scoring property should have cautionary recommendations"


class TestPortfolioOptimization:
    """Test investment portfolio optimization functionality"""

    @pytest.fixture
    async def portfolio_optimizer(self, investment_analysis_service):
        """Portfolio optimization service"""
        from src.core.services.portfolio_optimization import PortfolioOptimizer
        return PortfolioOptimizer(investment_service=investment_analysis_service)

    async def test_portfolio_diversification(self, portfolio_optimizer, sample_properties):
        """Test portfolio diversification optimization"""
        # Set budget and optimization criteria
        budget = Decimal('1000000')
        max_properties = 5
        
        optimized_portfolio = await portfolio_optimizer.optimize_portfolio(
            available_properties=sample_properties[:20],  # Use first 20 properties
            budget=budget,
            max_properties=max_properties,
            diversification_target=0.8  # High diversification
        )
        
        # Should not exceed budget
        total_cost = sum(inv.total_investment_needed for inv in optimized_portfolio.investments)
        assert total_cost <= budget, f"Portfolio exceeds budget: {total_cost} > {budget}"
        
        # Should not exceed property count
        assert len(optimized_portfolio.investments) <= max_properties, f"Too many properties in portfolio: {len(optimized_portfolio.investments)}"
        
        # Should be diversified across neighborhoods
        neighborhoods = [inv.property.location.neighborhood for inv in optimized_portfolio.investments]
        unique_neighborhoods = len(set(neighborhoods))
        
        if len(optimized_portfolio.investments) >= 3:
            assert unique_neighborhoods >= 2, "Portfolio should be diversified across neighborhoods"

    async def test_risk_adjusted_returns(self, portfolio_optimizer, sample_properties):
        """Test risk-adjusted return optimization"""
        budget = Decimal('800000')
        
        # Optimize for conservative strategy
        conservative_portfolio = await portfolio_optimizer.optimize_portfolio(
            available_properties=sample_properties[:15],
            budget=budget,
            risk_tolerance='conservative',
            target_return=6.0  # 6% target return
        )
        
        # Conservative portfolio should have mostly low-risk investments
        high_risk_count = sum(1 for inv in conservative_portfolio.investments if inv.risk_level == InvestmentRisk.HIGH)
        assert high_risk_count <= len(conservative_portfolio.investments) * 0.3, "Conservative portfolio has too many high-risk investments"

        # Optimize for aggressive strategy
        aggressive_portfolio = await portfolio_optimizer.optimize_portfolio(
            available_properties=sample_properties[:15],
            budget=budget,
            risk_tolerance='aggressive',
            target_return=12.0  # 12% target return
        )
        
        # Aggressive portfolio should have higher expected returns
        conservative_avg_roi = sum(inv.roi_projection_5y for inv in conservative_portfolio.investments) / len(conservative_portfolio.investments)
        aggressive_avg_roi = sum(inv.roi_projection_5y for inv in aggressive_portfolio.investments) / len(aggressive_portfolio.investments)
        
        assert aggressive_avg_roi >= conservative_avg_roi, "Aggressive portfolio should have higher expected returns"

    async def test_yield_optimization(self, portfolio_optimizer, sample_properties):
        """Test yield-focused portfolio optimization"""
        budget = Decimal('600000')
        
        yield_optimized = await portfolio_optimizer.optimize_portfolio(
            available_properties=sample_properties[:15],
            budget=budget,
            optimization_target='yield',
            min_yield=4.0  # Minimum 4% yield requirement
        )
        
        # All investments should meet minimum yield requirement
        for investment in yield_optimized.investments:
            assert investment.estimated_rental_yield >= 4.0, f"Investment below minimum yield: {investment.estimated_rental_yield}%"
        
        # Portfolio should have good average yield
        avg_yield = sum(inv.estimated_rental_yield for inv in yield_optimized.investments) / len(yield_optimized.investments)
        assert avg_yield >= 4.5, f"Portfolio average yield too low: {avg_yield}%"

    async def test_portfolio_performance_metrics(self, portfolio_optimizer, sample_properties):
        """Test portfolio performance metrics calculation"""
        budget = Decimal('750000')
        
        portfolio = await portfolio_optimizer.optimize_portfolio(
            available_properties=sample_properties[:10],
            budget=budget
        )
        
        metrics = await portfolio_optimizer.calculate_portfolio_metrics(portfolio)
        
        # Verify metric completeness
        required_metrics = [
            'total_value', 'weighted_avg_yield', 'portfolio_risk_score',
            'diversification_score', 'expected_annual_return', 'sharpe_ratio'
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Portfolio metrics missing: {metric}"
        
        # Verify metric reasonableness
        assert metrics['total_value'] > 0, "Portfolio total value should be positive"
        assert 0 <= metrics['diversification_score'] <= 1, "Diversification score should be 0-1"
        assert metrics['weighted_avg_yield'] > 0, "Weighted average yield should be positive"
        assert 0 <= metrics['portfolio_risk_score'] <= 100, "Portfolio risk score should be 0-100"


class TestInvestmentRecommendationIntegration:
    """Integration tests for investment recommendation system"""

    async def test_end_to_end_investment_workflow(self, investment_analysis_service, sample_property):
        """Test complete investment analysis workflow"""
        # Step 1: Analyze individual property
        analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
        
        assert analysis is not None, "Investment analysis should complete successfully"
        
        # Step 2: If analysis is positive, generate detailed recommendations
        if analysis.investment_score >= 60:
            detailed_analysis = await investment_analysis_service.generate_detailed_report(sample_property)
            
            assert detailed_analysis is not None, "Detailed analysis should be generated for good investments"
            assert hasattr(detailed_analysis, 'executive_summary'), "Detailed analysis should include executive summary"
            assert hasattr(detailed_analysis, 'financial_projections'), "Detailed analysis should include financial projections"
            assert hasattr(detailed_analysis, 'risk_analysis'), "Detailed analysis should include risk analysis"

    async def test_batch_investment_analysis(self, investment_analysis_service, sample_properties):
        """Test batch analysis of multiple properties"""
        # Analyze multiple properties
        analyses = []
        for prop in sample_properties[:10]:
            analysis = await investment_analysis_service.analyze_investment_potential(prop)
            analyses.append(analysis)
        
        # Should complete all analyses
        assert len(analyses) == 10, "Should analyze all properties"
        
        # Should rank properties by investment score
        sorted_analyses = sorted(analyses, key=lambda a: a.investment_score, reverse=True)
        
        # Top properties should have higher scores
        top_3_avg = sum(a.investment_score for a in sorted_analyses[:3]) / 3
        bottom_3_avg = sum(a.investment_score for a in sorted_analyses[-3:]) / 3
        
        assert top_3_avg >= bottom_3_avg, "Top-ranked properties should have higher average scores"

    async def test_investment_comparison_system(self, investment_analysis_service, sample_properties):
        """Test investment comparison functionality"""
        # Compare first two properties
        prop1, prop2 = sample_properties[0], sample_properties[1]
        
        comparison = await investment_analysis_service.compare_investments(prop1, prop2)
        
        # Should provide structured comparison
        assert hasattr(comparison, 'property_1_analysis'), "Comparison should include property 1 analysis"
        assert hasattr(comparison, 'property_2_analysis'), "Comparison should include property 2 analysis"
        assert hasattr(comparison, 'recommendation'), "Comparison should include recommendation"
        assert hasattr(comparison, 'key_differences'), "Comparison should highlight key differences"
        
        # Recommendation should favor the better investment
        better_property = comparison.property_1_analysis if comparison.property_1_analysis.investment_score > comparison.property_2_analysis.investment_score else comparison.property_2_analysis
        
        assert better_property.property.property_id in comparison.recommendation, "Recommendation should favor better investment"

    @pytest.mark.slow
    async def test_investment_analysis_performance(self, investment_analysis_service, property_data_generator):
        """Test performance of investment analysis system"""
        import time
        
        # Generate larger set of properties for performance testing
        properties = property_data_generator(count=50)
        
        start_time = time.perf_counter()
        
        # Analyze all properties
        analyses = []
        for prop in properties:
            analysis = await investment_analysis_service.analyze_investment_potential(prop)
            analyses.append(analysis)
        
        elapsed = time.perf_counter() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 30.0, f"Investment analysis took too long: {elapsed:.2f}s for 50 properties"
        
        # Calculate throughput
        throughput = len(properties) / elapsed
        assert throughput > 1.0, f"Low investment analysis throughput: {throughput:.1f} analyses/sec"
        
        # All analyses should be complete
        assert len(analyses) == len(properties), "Should complete all investment analyses"

    async def test_investment_data_consistency(self, investment_analysis_service, sample_property):
        """Test consistency of investment analysis data"""
        # Run analysis multiple times
        analyses = []
        for i in range(5):
            analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
            analyses.append(analysis)
        
        # All analyses should be consistent
        first_analysis = analyses[0]
        for i, analysis in enumerate(analyses[1:], 1):
            assert analysis.investment_score == first_analysis.investment_score, f"Inconsistent investment score in run {i}"
            assert analysis.estimated_rental_yield == first_analysis.estimated_rental_yield, f"Inconsistent rental yield in run {i}"
            assert analysis.risk_level == first_analysis.risk_level, f"Inconsistent risk level in run {i}"

    async def test_market_condition_integration(self, investment_analysis_service, sample_property, mock_market_data_service):
        """Test integration with market conditions"""
        # Mock different market conditions
        market_scenarios = [
            {
                'name': 'Bull market',
                'market_health': 'excellent',
                'price_trend': 'rising',
                'liquidity': 'high'
            },
            {
                'name': 'Bear market',
                'market_health': 'poor',
                'price_trend': 'falling',
                'liquidity': 'low'
            }
        ]

        analyses = {}
        
        for scenario in market_scenarios:
            # Configure mock market service
            mock_market_data_service.get_market_indicators.return_value = scenario
            
            analysis = await investment_analysis_service.analyze_investment_potential(sample_property)
            analyses[scenario['name']] = analysis

        # Bull market should generally result in higher scores
        bull_score = analyses['Bull market'].investment_score
        bear_score = analyses['Bear market'].investment_score
        
        # Allow for some exceptions but generally expect bull > bear
        assert bull_score >= bear_score * 0.8, f"Bull market should generally score better: Bull={bull_score}, Bear={bear_score}"