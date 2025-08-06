"""
Test Configuration and Fixtures - Enterprise Testing Suite

Comprehensive pytest configuration with fixtures for testing
the ATHintel Enterprise Platform with 95%+ coverage.
"""

import asyncio
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, AsyncGenerator, Any
from unittest.mock import AsyncMock, MagicMock
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

# Core domain entities
from src.core.domain.entities import (
    Property, Investment, Portfolio, MarketSegment, Location, 
    PropertyType, EnergyClass, ListingType, InvestmentRisk
)

# Services and repositories
from src.core.services.investment_analysis import InvestmentAnalysisService
from src.core.analytics.market_segmentation import MarketSegmentationAnalytics
from src.core.analytics.monte_carlo_modeling import MonteCarloSimulator
from src.core.ports.repositories import (
    PropertyRepository, InvestmentRepository, CacheRepository
)
from src.core.ports.services import (
    WebScrapingService, MarketDataService, AnalyticsService
)

# Adapters
from src.adapters.scrapers.crawlee_scraper import CrawleePropertyScraper


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "scraping: Web scraping tests"
    )
    config.addinivalue_line(
        "markers", "analytics: Analytics and ML tests"
    )
    config.addinivalue_line(
        "markers", "database: Database integration tests"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    
    for item in items:
        # Add markers based on file path
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add specific markers
        if "scraper" in str(item.fspath):
            item.add_marker(pytest.mark.scraping)
        elif "analytics" in str(item.fspath):
            item.add_marker(pytest.mark.analytics)
        elif "database" in str(item.fspath) or "repository" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        elif "api" in str(item.fspath) or "endpoint" in str(item.fspath):
            item.add_marker(pytest.mark.api)


# ============================================================================
# Test Environment Setup
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        'DATABASE_URL': 'sqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379/15',  # Test database
        'TEST_DATA_DIR': Path(__file__).parent / 'data',
        'LOG_LEVEL': 'DEBUG',
        'SCRAPING_DELAY': 0.1,  # Faster for tests
        'MONTE_CARLO_SIMULATIONS': 100,  # Smaller for tests
    }


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Mock Services and Repositories
# ============================================================================

@pytest.fixture
def mock_property_repository():
    """Mock PropertyRepository for testing"""
    
    repo = AsyncMock(spec=PropertyRepository)
    
    # Configure default return values
    repo.find_all.return_value = []
    repo.find_by_id.return_value = None
    repo.count_total.return_value = 0
    repo.save.return_value = None
    repo.bulk_save.return_value = []
    
    return repo


@pytest.fixture
def mock_investment_repository():
    """Mock InvestmentRepository for testing"""
    
    repo = AsyncMock(spec=InvestmentRepository)
    
    # Configure default return values
    repo.find_by_id.return_value = None
    repo.find_top_opportunities.return_value = []
    repo.save.return_value = None
    
    return repo


@pytest.fixture
def mock_cache_repository():
    """Mock CacheRepository for testing"""
    
    repo = AsyncMock(spec=CacheRepository)
    
    # Configure default return values
    repo.get.return_value = None
    repo.set.return_value = True
    repo.exists.return_value = False
    repo.delete.return_value = True
    
    return repo


@pytest.fixture
def mock_web_scraping_service():
    """Mock WebScrapingService for testing"""
    
    service = AsyncMock(spec=WebScrapingService)
    
    # Configure default return values
    service.scrape_property_listings.return_value = []
    service.scrape_single_property.return_value = None
    service.verify_property_exists.return_value = True
    service.extract_property_images.return_value = []
    service.get_scraping_stats.return_value = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0
    }
    
    return service


@pytest.fixture
def mock_market_data_service():
    """Mock MarketDataService for testing"""
    
    service = AsyncMock(spec=MarketDataService)
    
    # Configure default return values
    service.get_neighborhood_trends.return_value = {
        'annual_appreciation': 0.05,
        'price_trend': 'stable'
    }
    service.get_rental_yield_estimates.return_value = {
        'average_yield': 4.0
    }
    service.get_comparable_sales.return_value = []
    service.calculate_market_valuation.return_value = {
        'estimated_value': 250000,
        'confidence': 0.85
    }
    service.get_market_indicators.return_value = {
        'market_health': 'good',
        'liquidity': 'high'
    }
    
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock AnalyticsService for testing"""
    
    service = AsyncMock(spec=AnalyticsService)
    
    # Configure default return values
    service.predict_price.return_value = {
        'predicted_price': 280000,
        'confidence': 0.78
    }
    service.calculate_investment_score.return_value = 75.5
    service.detect_anomalies.return_value = []
    service.cluster_properties.return_value = {
        'cluster_0': ['prop_1', 'prop_2'],
        'cluster_1': ['prop_3', 'prop_4']
    }
    service.optimize_portfolio.return_value = []
    
    return service


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_location():
    """Create a sample Location object"""
    return Location(
        neighborhood="Kolonaki",
        district="Athens Center",
        municipality="Athens",
        region="Attica",
        country="Greece"
    )


@pytest.fixture
def sample_property(sample_location):
    """Create a sample Property object"""
    return Property(
        property_id="test-property-123",
        url="https://example.com/property/123",
        title="Beautiful Apartment in Kolonaki",
        property_type=PropertyType.APARTMENT,
        listing_type=ListingType.SALE,
        location=sample_location,
        sqm=85.0,
        rooms=2,
        floor=3,
        energy_class=EnergyClass.B,
        price=Decimal("350000"),
        timestamp=datetime.now(),
        source="test",
        extraction_confidence=0.95,
        year_built=2010
    )


@pytest.fixture
def sample_properties(sample_location):
    """Create a list of sample properties for testing"""
    
    properties = []
    neighborhoods = ["Kolonaki", "Glyfada", "Kifisia", "Marousi", "Nea Smyrni"]
    property_types = [PropertyType.APARTMENT, PropertyType.HOUSE, PropertyType.STUDIO]
    energy_classes = [EnergyClass.A, EnergyClass.B, EnergyClass.C, EnergyClass.D]
    
    for i in range(50):
        location = Location(
            neighborhood=neighborhoods[i % len(neighborhoods)],
            municipality="Athens"
        )
        
        property = Property(
            property_id=f"test-property-{i:03d}",
            url=f"https://example.com/property/{i}",
            title=f"Test Property {i}",
            property_type=property_types[i % len(property_types)],
            listing_type=ListingType.SALE,
            location=location,
            sqm=50.0 + (i * 2),  # Varying sizes
            rooms=1 + (i % 4),  # 1-4 rooms
            floor=i % 10,  # 0-9 floors
            energy_class=energy_classes[i % len(energy_classes)],
            price=Decimal(str(150000 + (i * 5000))),  # Varying prices
            timestamp=datetime.now() - timedelta(days=i),
            source="test",
            extraction_confidence=0.8 + (i * 0.004),  # Varying confidence
            year_built=2000 + (i % 23)  # 2000-2022
        )
        
        properties.append(property)
    
    return properties


@pytest.fixture
def sample_investment(sample_property):
    """Create a sample Investment object"""
    return Investment(
        property=sample_property,
        investment_score=78.5,
        estimated_rental_yield=4.2,
        roi_projection_5y=45.8,
        risk_level=InvestmentRisk.MEDIUM,
        neighborhood_rank=3,
        total_investment_needed=Decimal("385000"),
        holding_period_rec=7
    )


@pytest.fixture
def sample_portfolio(sample_properties):
    """Create a sample Portfolio object"""
    
    # Create investments from first 5 properties
    investments = []
    for prop in sample_properties[:5]:
        investment = Investment(
            property=prop,
            investment_score=70.0 + np.random.random() * 20,  # 70-90 score
            estimated_rental_yield=3.5 + np.random.random() * 2,  # 3.5-5.5% yield
            roi_projection_5y=30.0 + np.random.random() * 30,  # 30-60% ROI
            risk_level=InvestmentRisk.MEDIUM
        )
        investments.append(investment)
    
    return Portfolio(
        name="Test Portfolio",
        investments=investments,
        target_budget=Decimal("1500000")
    )


@pytest.fixture
def sample_market_segment():
    """Create a sample MarketSegment object"""
    return MarketSegment(
        segment_id="test-segment-kolonaki",
        neighborhood="Kolonaki",
        property_count=25,
        avg_price=Decimal("420000"),
        median_price=Decimal("395000"),
        avg_price_per_sqm=Decimal("4800"),
        price_std_dev=Decimal("85000"),
        avg_sqm=87.5,
        dominant_property_type=PropertyType.APARTMENT,
        energy_efficiency_score=7.2,
        avg_investment_score=82.3,
        estimated_avg_yield=3.8,
        market_activity_score=8.5,
        price_volatility=0.18,
        market_maturity="mature",
        liquidity_score=0.85
    )


# ============================================================================
# Data Generation Helpers
# ============================================================================

@pytest.fixture
def property_data_generator():
    """Generator for creating test property data"""
    
    def generate_properties(count: int = 10, **kwargs) -> List[Property]:
        properties = []
        
        for i in range(count):
            # Base property data
            base_data = {
                'property_id': f"gen-prop-{i:04d}",
                'url': f"https://test.example.com/property/{i}",
                'title': f"Generated Property {i}",
                'property_type': PropertyType.APARTMENT,
                'listing_type': ListingType.SALE,
                'location': Location(neighborhood=f"Test Area {i % 5}"),
                'sqm': 60.0 + (i * 1.5),
                'rooms': 1 + (i % 4),
                'floor': i % 8,
                'energy_class': EnergyClass.B,
                'price': Decimal(str(200000 + (i * 3000))),
                'timestamp': datetime.now() - timedelta(hours=i),
                'source': 'test_generator',
                'extraction_confidence': 0.85
            }
            
            # Override with any provided kwargs
            base_data.update(kwargs)
            
            # Create property with randomized data where not specified
            if 'year_built' not in base_data:
                base_data['year_built'] = 2005 + (i % 18)
            
            properties.append(Property(**base_data))
        
        return properties
    
    return generate_properties


@pytest.fixture
def dataframe_generator():
    """Generator for creating test pandas DataFrames"""
    
    def generate_df(rows: int = 100, columns: List[str] = None) -> pd.DataFrame:
        if columns is None:
            columns = ['price', 'sqm', 'rooms', 'neighborhood', 'energy_score']
        
        np.random.seed(42)  # For reproducible tests
        
        data = {}
        for col in columns:
            if col == 'price':
                data[col] = np.random.normal(300000, 100000, rows).clip(50000, 2000000)
            elif col == 'sqm':
                data[col] = np.random.normal(80, 30, rows).clip(20, 300)
            elif col == 'rooms':
                data[col] = np.random.choice([1, 2, 3, 4, 5], rows)
            elif col == 'neighborhood':
                data[col] = np.random.choice(['Kolonaki', 'Glyfada', 'Kifisia', 'Marousi'], rows)
            elif col == 'energy_score':
                data[col] = np.random.uniform(1, 10, rows)
            else:
                data[col] = np.random.random(rows)
        
        return pd.DataFrame(data)
    
    return generate_df


# ============================================================================
# Service Instance Fixtures
# ============================================================================

@pytest.fixture
async def investment_analysis_service(
    mock_property_repository,
    mock_investment_repository,
    mock_cache_repository,
    mock_market_data_service,
    mock_analytics_service
):
    """Create InvestmentAnalysisService instance with mocked dependencies"""
    
    return InvestmentAnalysisService(
        property_repo=mock_property_repository,
        investment_repo=mock_investment_repository,
        cache_repo=mock_cache_repository,
        market_service=mock_market_data_service,
        analytics_service=mock_analytics_service
    )


@pytest.fixture
async def market_segmentation_service(mock_property_repository):
    """Create MarketSegmentationAnalytics instance with mocked dependencies"""
    
    return MarketSegmentationAnalytics(
        property_repo=mock_property_repository
    )


@pytest.fixture
def monte_carlo_simulator():
    """Create MonteCarloSimulator instance for testing"""
    
    from src.core.analytics.monte_carlo_modeling import SimulationConfig, MarketParameters
    
    # Fast simulation config for testing
    config = SimulationConfig(
        n_simulations=100,  # Smaller for tests
        n_years=5,
        time_step=1.0,  # Annual steps for speed
        market_params=MarketParameters(
            annual_appreciation_mean=0.05,
            annual_appreciation_std=0.15,
            rental_yield_mean=0.04,
            rental_yield_std=0.01
        )
    )
    
    return MonteCarloSimulator(config)


# ============================================================================
# Database and Integration Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def test_database():
    """Set up test database (if using real database for integration tests)"""
    
    # This would set up a test database instance
    # For now, we'll use in-memory SQLite for tests
    
    database_url = "sqlite:///:memory:"
    
    # Database setup would go here
    # For real tests, you might use a Docker container with PostgreSQL
    
    yield database_url
    
    # Cleanup would go here


@pytest.fixture
async def populated_property_repository(mock_property_repository, sample_properties):
    """Property repository populated with sample data"""
    
    # Configure mock to return sample data
    mock_property_repository.find_all.return_value = sample_properties
    mock_property_repository.count_total.return_value = len(sample_properties)
    
    # Configure find_by_neighborhood
    def find_by_neighborhood(neighborhood):
        return [p for p in sample_properties if p.location.neighborhood == neighborhood]
    
    mock_property_repository.find_by_neighborhood.side_effect = find_by_neighborhood
    
    # Configure find_by_id
    def find_by_id(property_id):
        for prop in sample_properties:
            if prop.property_id == property_id:
                return prop
        return None
    
    mock_property_repository.find_by_id.side_effect = find_by_id
    
    return mock_property_repository


# ============================================================================
# Web Scraping Test Fixtures
# ============================================================================

@pytest.fixture
def mock_playwright_page():
    """Mock Playwright page for scraping tests"""
    
    page = AsyncMock()
    
    # Configure common page methods
    page.goto.return_value = None
    page.content.return_value = "<html><body>Mock HTML</body></html>"
    page.screenshot.return_value = None
    page.query_selector.return_value = None
    page.query_selector_all.return_value = []
    
    # Mock element
    mock_element = AsyncMock()
    mock_element.inner_text.return_value = "Mock Text"
    mock_element.get_attribute.return_value = "mock-value"
    
    page.query_selector.return_value = mock_element
    page.query_selector_all.return_value = [mock_element]
    
    return page


@pytest.fixture
def mock_browser_context():
    """Mock browser context for scraping tests"""
    
    context = AsyncMock()
    context.new_page.return_value = AsyncMock()
    context.close.return_value = None
    
    return context


@pytest.fixture
def scraper_test_data():
    """Test data for web scraping tests"""
    
    return {
        'html_content': '''
        <div class="property-card">
            <h2>Test Property</h2>
            <div class="price">€250,000</div>
            <div class="area">75 m²</div>
            <div class="rooms">2 rooms</div>
            <div class="energy">Energy Class: B</div>
            <div class="location">Kolonaki, Athens</div>
        </div>
        ''',
        'expected_property': {
            'title': 'Test Property',
            'price': 250000,
            'sqm': 75,
            'rooms': 2,
            'energy_class': 'B',
            'neighborhood': 'Kolonaki'
        }
    }


# ============================================================================
# Performance Test Fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Timer utility for performance testing"""
    
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
        
        def __enter__(self):
            self.start()
            return self
        
        def __exit__(self, *args):
            self.stop()
    
    return Timer()


# ============================================================================
# Cleanup and Utilities
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_async():
    """Automatic cleanup after each async test"""
    yield
    # Cleanup code would go here
    # Close any open connections, clear caches, etc.


@pytest.fixture
def mock_logger():
    """Mock logger for testing log outputs"""
    
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    
    return logger


# ============================================================================
# Test Utilities
# ============================================================================

@pytest.fixture
def assert_helpers():
    """Helper functions for common test assertions"""
    
    class AssertHelpers:
        
        @staticmethod
        def assert_property_equal(prop1: Property, prop2: Property):
            """Assert two properties are equal"""
            assert prop1.property_id == prop2.property_id
            assert prop1.price == prop2.price
            assert prop1.sqm == prop2.sqm
            assert prop1.location.neighborhood == prop2.location.neighborhood
        
        @staticmethod
        def assert_investment_valid(investment: Investment):
            """Assert investment object is valid"""
            assert investment.investment_score >= 0
            assert investment.investment_score <= 100
            assert investment.property is not None
            if investment.estimated_rental_yield:
                assert investment.estimated_rental_yield > 0
        
        @staticmethod
        def assert_portfolio_valid(portfolio: Portfolio):
            """Assert portfolio object is valid"""
            assert len(portfolio.investments) >= 0
            assert portfolio.total_value >= 0
            assert portfolio.name is not None
        
        @staticmethod
        def assert_dataframe_shape(df: pd.DataFrame, expected_rows: int, expected_cols: int):
            """Assert DataFrame has expected shape"""
            assert df.shape == (expected_rows, expected_cols)
        
        @staticmethod
        def assert_within_range(value: float, min_val: float, max_val: float):
            """Assert value is within specified range"""
            assert min_val <= value <= max_val
    
    return AssertHelpers()


# Export fixtures for external test modules
__all__ = [
    'sample_property',
    'sample_properties', 
    'sample_investment',
    'sample_portfolio',
    'sample_market_segment',
    'mock_property_repository',
    'mock_investment_repository',
    'investment_analysis_service',
    'market_segmentation_service',
    'monte_carlo_simulator',
    'property_data_generator',
    'assert_helpers',
    'performance_timer'
]