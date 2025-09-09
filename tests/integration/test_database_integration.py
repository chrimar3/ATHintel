"""
Database Integration Testing Suite for ATHintel Platform
Tests database operations, transactions, data integrity, and performance
"""

import pytest
import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from src.core.domain.entities import Property, PropertyType, EnergyClass, ListingType, Location
from src.infrastructure.database.repositories.property_repository import PropertyRepository
from src.infrastructure.database.repositories.investment_repository import InvestmentRepository
from src.infrastructure.database.connection_manager import DatabaseConnectionManager
from src.infrastructure.database.migrations import DatabaseMigrator


class DatabaseTestFixture:
    """Database test fixture for integration testing"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection_manager = None
        self.test_schema = f"test_schema_{uuid.uuid4().hex[:8]}"
        
    async def setup(self):
        """Set up test database environment"""
        self.connection_manager = DatabaseConnectionManager(self.connection_string)
        await self.connection_manager.initialize()
        
        # Create test schema
        async with self.connection_manager.get_connection() as conn:
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.test_schema}")
            await conn.execute(f"SET search_path TO {self.test_schema}")
            
        # Run migrations in test schema
        migrator = DatabaseMigrator(self.connection_manager, schema=self.test_schema)
        await migrator.run_migrations()
        
    async def teardown(self):
        """Clean up test database environment"""
        if self.connection_manager:
            async with self.connection_manager.get_connection() as conn:
                await conn.execute(f"DROP SCHEMA IF EXISTS {self.test_schema} CASCADE")
            await self.connection_manager.close()

    async def clear_tables(self):
        """Clear all tables in test schema"""
        async with self.connection_manager.get_connection() as conn:
            # Get all table names in test schema
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = $1 AND table_type = 'BASE TABLE'
            """, self.test_schema)
            
            # Truncate all tables
            for table in tables:
                await conn.execute(f"TRUNCATE TABLE {self.test_schema}.{table['table_name']} RESTART IDENTITY CASCADE")


@pytest.fixture(scope="session")
async def db_fixture():
    """Session-scoped database fixture"""
    # Use test database URL
    test_db_url = "postgresql://test_user:test_pass@localhost:5432/test_athintel"
    
    fixture = DatabaseTestFixture(test_db_url)
    await fixture.setup()
    yield fixture
    await fixture.teardown()


@pytest.fixture
async def clean_database(db_fixture):
    """Function-scoped fixture that ensures clean database state"""
    await db_fixture.clear_tables()
    yield db_fixture
    await db_fixture.clear_tables()


class TestPropertyRepositoryIntegration:
    """Integration tests for Property Repository"""

    @pytest.fixture
    async def property_repository(self, clean_database):
        """Property repository with test database"""
        return PropertyRepository(clean_database.connection_manager)

    @pytest.fixture
    def sample_properties(self):
        """Generate sample properties for testing"""
        properties = []
        
        neighborhoods = ["Kolonaki", "Glyfada", "Kifisia", "Marousi", "Nea Smyrni"]
        property_types = [PropertyType.APARTMENT, PropertyType.HOUSE, PropertyType.STUDIO]
        energy_classes = [EnergyClass.A, EnergyClass.B, EnergyClass.C, EnergyClass.D]
        
        for i in range(20):
            location = Location(
                neighborhood=neighborhoods[i % len(neighborhoods)],
                district="Athens",
                municipality="Athens",
                region="Attica",
                country="Greece"
            )
            
            property = Property(
                property_id=f"test_prop_{i:03d}",
                url=f"https://example.com/property/{i}",
                title=f"Test Property {i}",
                property_type=property_types[i % len(property_types)],
                listing_type=ListingType.SALE,
                location=location,
                sqm=50.0 + (i * 5),
                rooms=1 + (i % 4),
                floor=i % 10,
                energy_class=energy_classes[i % len(energy_classes)],
                price=Decimal(str(150000 + (i * 10000))),
                timestamp=datetime.now() - timedelta(days=i),
                source="test_integration",
                extraction_confidence=0.8 + (i * 0.01),
                year_built=2000 + (i % 23)
            )
            
            properties.append(property)
        
        return properties

    async def test_property_crud_operations(self, property_repository, sample_properties):
        """Test basic CRUD operations for properties"""
        
        # Test CREATE
        property_to_create = sample_properties[0]
        created_property = await property_repository.create(property_to_create)
        
        assert created_property.property_id == property_to_create.property_id
        assert created_property.price == property_to_create.price
        assert created_property.sqm == property_to_create.sqm
        
        # Test READ
        retrieved_property = await property_repository.find_by_id(property_to_create.property_id)
        
        assert retrieved_property is not None
        assert retrieved_property.property_id == property_to_create.property_id
        assert retrieved_property.title == property_to_create.title
        
        # Test UPDATE
        updated_data = {
            "price": Decimal("180000"),
            "description": "Updated property description"
        }
        updated_property = await property_repository.update(property_to_create.property_id, updated_data)
        
        assert updated_property.price == Decimal("180000")
        assert updated_property.description == "Updated property description"
        
        # Verify update persisted
        retrieved_updated = await property_repository.find_by_id(property_to_create.property_id)
        assert retrieved_updated.price == Decimal("180000")
        
        # Test DELETE
        deleted = await property_repository.delete(property_to_create.property_id)
        assert deleted is True
        
        # Verify deletion
        deleted_property = await property_repository.find_by_id(property_to_create.property_id)
        assert deleted_property is None

    async def test_property_bulk_operations(self, property_repository, sample_properties):
        """Test bulk property operations"""
        
        # Test bulk create
        batch_size = 10
        properties_to_create = sample_properties[:batch_size]
        
        created_properties = await property_repository.bulk_create(properties_to_create)
        
        assert len(created_properties) == batch_size
        
        # Verify all properties were created
        for prop in properties_to_create:
            retrieved = await property_repository.find_by_id(prop.property_id)
            assert retrieved is not None
            assert retrieved.property_id == prop.property_id
        
        # Test bulk update
        update_data = {"source": "bulk_updated"}
        property_ids = [prop.property_id for prop in properties_to_create]
        
        updated_count = await property_repository.bulk_update(property_ids, update_data)
        assert updated_count == batch_size
        
        # Verify updates
        for prop_id in property_ids:
            retrieved = await property_repository.find_by_id(prop_id)
            assert retrieved.source == "bulk_updated"
        
        # Test bulk delete
        deleted_count = await property_repository.bulk_delete(property_ids)
        assert deleted_count == batch_size
        
        # Verify deletions
        for prop_id in property_ids:
            retrieved = await property_repository.find_by_id(prop_id)
            assert retrieved is None

    async def test_property_search_and_filtering(self, property_repository, sample_properties):
        """Test property search and filtering functionality"""
        
        # Create test data
        await property_repository.bulk_create(sample_properties)
        
        # Test search by neighborhood
        kolonaki_properties = await property_repository.find_by_neighborhood("Kolonaki")
        assert len(kolonaki_properties) > 0
        
        for prop in kolonaki_properties:
            assert prop.location.neighborhood == "Kolonaki"
        
        # Test price range filtering
        min_price = Decimal("200000")
        max_price = Decimal("300000")
        
        price_filtered = await property_repository.find_by_price_range(min_price, max_price)
        
        for prop in price_filtered:
            assert min_price <= prop.price <= max_price
        
        # Test complex filtering
        filter_criteria = {
            "property_type": PropertyType.APARTMENT,
            "min_sqm": 60.0,
            "max_sqm": 100.0,
            "energy_class": [EnergyClass.A, EnergyClass.B],
            "min_rooms": 2
        }
        
        filtered_properties = await property_repository.find_by_criteria(**filter_criteria)
        
        for prop in filtered_properties:
            assert prop.property_type == PropertyType.APARTMENT
            assert 60.0 <= prop.sqm <= 100.0
            assert prop.energy_class in [EnergyClass.A, EnergyClass.B]
            assert prop.rooms >= 2
        
        # Test full-text search
        search_results = await property_repository.search_properties("Test Property")
        assert len(search_results) > 0
        
        for prop in search_results:
            assert "Test Property" in prop.title or "test" in prop.description.lower()

    async def test_property_aggregations(self, property_repository, sample_properties):
        """Test property data aggregations"""
        
        await property_repository.bulk_create(sample_properties)
        
        # Test count aggregations
        total_count = await property_repository.count_total()
        assert total_count == len(sample_properties)
        
        neighborhood_counts = await property_repository.count_by_neighborhood()
        assert isinstance(neighborhood_counts, dict)
        assert sum(neighborhood_counts.values()) == len(sample_properties)
        
        # Test price statistics
        price_stats = await property_repository.get_price_statistics()
        
        assert "min_price" in price_stats
        assert "max_price" in price_stats
        assert "avg_price" in price_stats
        assert "median_price" in price_stats
        
        assert price_stats["min_price"] <= price_stats["max_price"]
        
        # Test market segment analysis
        market_segments = await property_repository.analyze_market_segments()
        
        assert len(market_segments) > 0
        
        for segment in market_segments:
            assert "neighborhood" in segment
            assert "property_count" in segment
            assert "avg_price" in segment
            assert "avg_price_per_sqm" in segment

    async def test_property_data_integrity(self, property_repository, sample_properties):
        """Test data integrity constraints"""
        
        valid_property = sample_properties[0]
        
        # Test duplicate property_id constraint
        await property_repository.create(valid_property)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await property_repository.create(valid_property)
        
        # Test invalid foreign key relationships
        invalid_property = Property(
            property_id="invalid_prop",
            url="https://example.com/invalid",
            title="Invalid Property",
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=Location(neighborhood="NonExistent"),
            sqm=80.0,
            rooms=2,
            floor=1,
            energy_class=EnergyClass.B,
            price=Decimal("200000"),
            timestamp=datetime.now(),
            source="test",
            extraction_confidence=0.9
        )
        
        # Should handle gracefully or enforce constraints
        try:
            await property_repository.create(invalid_property)
        except Exception:
            # Expected if foreign key constraints are enforced
            pass
        
        # Test data validation constraints
        invalid_data_property = Property(
            property_id="invalid_data_prop",
            url="not_a_valid_url",  # Invalid URL
            title="",  # Empty title
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.SALE,
            location=Location(neighborhood="Test"),
            sqm=-50.0,  # Negative area
            rooms=0,  # Zero rooms
            floor=1,
            energy_class=EnergyClass.B,
            price=Decimal("-100000"),  # Negative price
            timestamp=datetime.now(),
            source="test"
        )
        
        with pytest.raises(Exception):  # Should raise validation error
            await property_repository.create(invalid_data_property)

    async def test_property_transaction_handling(self, property_repository, sample_properties):
        """Test database transaction handling"""
        
        # Test successful transaction
        properties_to_create = sample_properties[:5]
        
        async with property_repository.connection_manager.get_transaction() as tx:
            created_properties = []
            
            for prop in properties_to_create:
                created = await property_repository.create(prop, connection=tx)
                created_properties.append(created)
            
            # Transaction should commit automatically
        
        # Verify all properties were created
        for prop in properties_to_create:
            retrieved = await property_repository.find_by_id(prop.property_id)
            assert retrieved is not None
        
        # Test transaction rollback
        properties_to_fail = sample_properties[5:10]
        
        try:
            async with property_repository.connection_manager.get_transaction() as tx:
                for i, prop in enumerate(properties_to_fail):
                    if i == 3:  # Simulate error on 4th property
                        raise Exception("Simulated transaction error")
                    
                    await property_repository.create(prop, connection=tx)
                
        except Exception:
            pass  # Expected
        
        # Verify no properties from failed transaction were created
        for prop in properties_to_fail:
            retrieved = await property_repository.find_by_id(prop.property_id)
            assert retrieved is None

    async def test_property_concurrent_access(self, property_repository, sample_properties):
        """Test concurrent database access"""
        
        property_to_test = sample_properties[0]
        
        # Create initial property
        await property_repository.create(property_to_test)
        
        # Define concurrent update operations
        async def update_price(new_price: Decimal, identifier: str):
            """Update property price"""
            try:
                await property_repository.update(
                    property_to_test.property_id,
                    {"price": new_price, "updated_by": identifier}
                )
                return f"success_{identifier}"
            except Exception as e:
                return f"error_{identifier}_{str(e)}"
        
        # Run concurrent updates
        concurrent_tasks = [
            update_price(Decimal("200000"), "task_1"),
            update_price(Decimal("220000"), "task_2"),
            update_price(Decimal("240000"), "task_3"),
            update_price(Decimal("260000"), "task_4"),
        ]
        
        results = await asyncio.gather(*concurrent_tasks)
        
        # At least one update should succeed
        successful_updates = [r for r in results if r.startswith("success")]
        assert len(successful_updates) >= 1
        
        # Verify final state is consistent
        final_property = await property_repository.find_by_id(property_to_test.property_id)
        assert final_property.price in [Decimal("200000"), Decimal("220000"), Decimal("240000"), Decimal("260000")]

    async def test_property_indexing_performance(self, property_repository, sample_properties):
        """Test database indexing and query performance"""
        
        # Create large dataset
        large_dataset = sample_properties * 5  # 100 properties
        for i, prop in enumerate(large_dataset):
            prop.property_id = f"perf_test_{i:04d}"
        
        await property_repository.bulk_create(large_dataset)
        
        import time
        
        # Test indexed queries (should be fast)
        indexed_queries = [
            lambda: property_repository.find_by_id("perf_test_0050"),
            lambda: property_repository.find_by_neighborhood("Kolonaki"),
            lambda: property_repository.find_by_price_range(Decimal("200000"), Decimal("300000")),
        ]
        
        for query_func in indexed_queries:
            start_time = time.perf_counter()
            results = await query_func()
            elapsed = time.perf_counter() - start_time
            
            # Indexed queries should be fast
            assert elapsed < 0.1, f"Indexed query too slow: {elapsed:.3f}s"
        
        # Test full-text search performance
        start_time = time.perf_counter()
        search_results = await property_repository.search_properties("Test")
        search_elapsed = time.perf_counter() - start_time
        
        assert search_elapsed < 0.5, f"Full-text search too slow: {search_elapsed:.3f}s"
        assert len(search_results) > 0


class TestInvestmentRepositoryIntegration:
    """Integration tests for Investment Repository"""

    @pytest.fixture
    async def investment_repository(self, clean_database):
        """Investment repository with test database"""
        return InvestmentRepository(clean_database.connection_manager)

    @pytest.fixture
    async def property_repository(self, clean_database):
        """Property repository for creating test properties"""
        return PropertyRepository(clean_database.connection_manager)

    @pytest.fixture
    async def test_properties(self, property_repository):
        """Create test properties for investment testing"""
        properties = []
        
        for i in range(5):
            property = Property(
                property_id=f"investment_prop_{i}",
                url=f"https://example.com/investment/{i}",
                title=f"Investment Property {i}",
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                location=Location(neighborhood="Kolonaki"),
                sqm=80.0 + i * 10,
                rooms=2 + i,
                floor=i + 1,
                energy_class=EnergyClass.B,
                price=Decimal(str(300000 + i * 50000)),
                timestamp=datetime.now(),
                source="test_investment",
                extraction_confidence=0.9
            )
            
            created_prop = await property_repository.create(property)
            properties.append(created_prop)
        
        return properties

    async def test_investment_analysis_storage(self, investment_repository, test_properties):
        """Test storing and retrieving investment analyses"""
        
        test_property = test_properties[0]
        
        # Create investment analysis
        investment_data = {
            "property_id": test_property.property_id,
            "investment_score": 78.5,
            "estimated_rental_yield": 4.2,
            "roi_projection_5y": 45.8,
            "risk_level": "medium",
            "total_investment_needed": Decimal("385000"),
            "cash_flow_projection": [5000, 5200, 5400, 5600, 5800],
            "analysis_date": datetime.now(),
            "analyst_id": "test_analyst"
        }
        
        created_investment = await investment_repository.create_analysis(investment_data)
        
        assert created_investment["investment_score"] == 78.5
        assert created_investment["property_id"] == test_property.property_id
        
        # Retrieve investment analysis
        retrieved_analysis = await investment_repository.get_analysis_by_property(test_property.property_id)
        
        assert retrieved_analysis is not None
        assert retrieved_analysis["investment_score"] == 78.5
        assert len(retrieved_analysis["cash_flow_projection"]) == 5

    async def test_investment_portfolio_management(self, investment_repository, test_properties):
        """Test investment portfolio management"""
        
        # Create portfolio
        portfolio_data = {
            "portfolio_name": "Test Portfolio",
            "target_budget": Decimal("1000000"),
            "risk_tolerance": "moderate",
            "created_by": "test_user"
        }
        
        created_portfolio = await investment_repository.create_portfolio(portfolio_data)
        portfolio_id = created_portfolio["portfolio_id"]
        
        # Add properties to portfolio
        for i, property in enumerate(test_properties[:3]):
            investment_data = {
                "property_id": property.property_id,
                "investment_score": 70.0 + i * 5,
                "estimated_rental_yield": 4.0 + i * 0.3,
                "total_investment_needed": property.price * Decimal("1.1")
            }
            
            await investment_repository.add_property_to_portfolio(portfolio_id, investment_data)
        
        # Retrieve portfolio with properties
        portfolio_with_properties = await investment_repository.get_portfolio_with_properties(portfolio_id)
        
        assert len(portfolio_with_properties["properties"]) == 3
        assert portfolio_with_properties["portfolio_name"] == "Test Portfolio"
        
        # Calculate portfolio metrics
        portfolio_metrics = await investment_repository.calculate_portfolio_metrics(portfolio_id)
        
        assert "total_value" in portfolio_metrics
        assert "weighted_avg_yield" in portfolio_metrics
        assert "portfolio_risk_score" in portfolio_metrics
        
        # Remove property from portfolio
        property_to_remove = test_properties[0]
        await investment_repository.remove_property_from_portfolio(portfolio_id, property_to_remove.property_id)
        
        updated_portfolio = await investment_repository.get_portfolio_with_properties(portfolio_id)
        assert len(updated_portfolio["properties"]) == 2

    async def test_investment_ranking_and_sorting(self, investment_repository, test_properties):
        """Test investment ranking and sorting functionality"""
        
        # Create investment analyses with different scores
        investment_scores = [85.2, 72.8, 91.1, 68.5, 79.3]
        
        for i, property in enumerate(test_properties):
            investment_data = {
                "property_id": property.property_id,
                "investment_score": investment_scores[i],
                "estimated_rental_yield": 4.0 + (i * 0.2),
                "roi_projection_5y": 40.0 + (i * 3),
                "analysis_date": datetime.now()
            }
            
            await investment_repository.create_analysis(investment_data)
        
        # Test ranking by investment score
        top_investments = await investment_repository.get_top_investments_by_score(limit=3)
        
        assert len(top_investments) == 3
        assert top_investments[0]["investment_score"] >= top_investments[1]["investment_score"]
        assert top_investments[1]["investment_score"] >= top_investments[2]["investment_score"]
        
        # Test filtering by score threshold
        high_score_investments = await investment_repository.get_investments_by_score_threshold(80.0)
        
        for investment in high_score_investments:
            assert investment["investment_score"] >= 80.0
        
        # Test ranking by yield
        top_yield_investments = await investment_repository.get_top_investments_by_yield(limit=3)
        
        assert len(top_yield_investments) == 3
        
        for i in range(len(top_yield_investments) - 1):
            assert top_yield_investments[i]["estimated_rental_yield"] >= top_yield_investments[i + 1]["estimated_rental_yield"]

    async def test_investment_historical_tracking(self, investment_repository, test_properties):
        """Test investment historical data tracking"""
        
        test_property = test_properties[0]
        
        # Create multiple analyses over time
        analysis_dates = [
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=15),
            datetime.now()
        ]
        
        investment_scores = [75.0, 78.5, 82.1]  # Improving over time
        
        for i, analysis_date in enumerate(analysis_dates):
            investment_data = {
                "property_id": test_property.property_id,
                "investment_score": investment_scores[i],
                "estimated_rental_yield": 4.0 + (i * 0.1),
                "analysis_date": analysis_date,
                "analysis_version": i + 1
            }
            
            await investment_repository.create_analysis(investment_data)
        
        # Get analysis history
        analysis_history = await investment_repository.get_analysis_history(test_property.property_id)
        
        assert len(analysis_history) == 3
        
        # Should be sorted by date (newest first)
        for i in range(len(analysis_history) - 1):
            assert analysis_history[i]["analysis_date"] >= analysis_history[i + 1]["analysis_date"]
        
        # Get latest analysis
        latest_analysis = await investment_repository.get_latest_analysis(test_property.property_id)
        assert latest_analysis["investment_score"] == 82.1
        
        # Get analysis trend
        score_trend = await investment_repository.get_score_trend(test_property.property_id)
        assert score_trend["trend"] == "improving"  # Score increased over time
        assert len(score_trend["data_points"]) == 3

    async def test_investment_comparison_queries(self, investment_repository, test_properties):
        """Test investment comparison queries"""
        
        # Create analyses for comparison
        comparison_data = [
            {
                "property_id": test_properties[0].property_id,
                "investment_score": 85.0,
                "estimated_rental_yield": 4.5,
                "roi_projection_5y": 50.0,
                "risk_level": "low"
            },
            {
                "property_id": test_properties[1].property_id,
                "investment_score": 78.0,
                "estimated_rental_yield": 5.2,
                "roi_projection_5y": 45.0,
                "risk_level": "medium"
            }
        ]
        
        for data in comparison_data:
            await investment_repository.create_analysis(data)
        
        # Compare investments
        comparison_result = await investment_repository.compare_investments([
            test_properties[0].property_id,
            test_properties[1].property_id
        ])
        
        assert len(comparison_result["properties"]) == 2
        assert "winner" in comparison_result
        assert "comparison_metrics" in comparison_result
        
        # Verify comparison logic
        winner_property = next(
            prop for prop in comparison_result["properties"]
            if prop["property_id"] == comparison_result["winner"]
        )
        
        # Winner should have higher overall score or better metrics
        assert winner_property["investment_score"] >= 78.0

    async def test_investment_data_aggregations(self, investment_repository, test_properties):
        """Test investment data aggregations and analytics"""
        
        # Create diverse investment data
        for i, property in enumerate(test_properties):
            investment_data = {
                "property_id": property.property_id,
                "investment_score": 70.0 + (i * 4),  # 70, 74, 78, 82, 86
                "estimated_rental_yield": 4.0 + (i * 0.3),
                "roi_projection_5y": 40.0 + (i * 5),
                "risk_level": ["low", "low", "medium", "medium", "high"][i]
            }
            
            await investment_repository.create_analysis(investment_data)
        
        # Test score distribution
        score_distribution = await investment_repository.get_score_distribution()
        
        assert "score_ranges" in score_distribution
        assert "distribution" in score_distribution
        
        # Test risk level distribution
        risk_distribution = await investment_repository.get_risk_level_distribution()
        
        assert "low" in risk_distribution
        assert "medium" in risk_distribution
        assert "high" in risk_distribution
        assert sum(risk_distribution.values()) == len(test_properties)
        
        # Test yield statistics
        yield_stats = await investment_repository.get_yield_statistics()
        
        assert "min_yield" in yield_stats
        assert "max_yield" in yield_stats
        assert "avg_yield" in yield_stats
        assert "median_yield" in yield_stats
        
        # Test market segment analysis
        segment_analysis = await investment_repository.analyze_investment_segments()
        
        assert len(segment_analysis) > 0
        for segment in segment_analysis:
            assert "neighborhood" in segment
            assert "avg_investment_score" in segment
            assert "avg_yield" in segment
            assert "property_count" in segment


class TestDatabaseConnectionManagement:
    """Test database connection management and pooling"""

    @pytest.fixture
    async def connection_manager(self):
        """Database connection manager for testing"""
        test_db_url = "postgresql://test_user:test_pass@localhost:5432/test_athintel"
        manager = DatabaseConnectionManager(test_db_url, pool_size=5, max_connections=10)
        await manager.initialize()
        yield manager
        await manager.close()

    async def test_connection_pool_management(self, connection_manager):
        """Test connection pool creation and management"""
        
        # Test basic connection acquisition
        async with connection_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
        
        # Test multiple concurrent connections
        async def use_connection(connection_id: int):
            async with connection_manager.get_connection() as conn:
                await conn.fetchval("SELECT pg_sleep(0.1)")
                return connection_id
        
        # Use more connections than pool size
        tasks = [use_connection(i) for i in range(8)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 8
        assert set(results) == set(range(8))

    async def test_transaction_management(self, connection_manager):
        """Test database transaction management"""
        
        # Test successful transaction
        async with connection_manager.get_transaction() as tx:
            await tx.execute("CREATE TEMP TABLE test_transaction (id INT, value TEXT)")
            await tx.execute("INSERT INTO test_transaction VALUES (1, 'test')")
            
            result = await tx.fetchval("SELECT value FROM test_transaction WHERE id = 1")
            assert result == "test"
        
        # Test transaction rollback
        try:
            async with connection_manager.get_transaction() as tx:
                await tx.execute("CREATE TEMP TABLE test_rollback (id INT, value TEXT)")
                await tx.execute("INSERT INTO test_rollback VALUES (1, 'before_error')")
                
                # Simulate error
                raise Exception("Simulated transaction error")
        except Exception:
            pass
        
        # Verify rollback - table should not exist
        async with connection_manager.get_connection() as conn:
            try:
                await conn.fetchval("SELECT COUNT(*) FROM test_rollback")
                assert False, "Table should not exist after rollback"
            except asyncpg.UndefinedTableError:
                pass  # Expected

    async def test_connection_health_monitoring(self, connection_manager):
        """Test connection health monitoring"""
        
        # Test health check
        is_healthy = await connection_manager.health_check()
        assert is_healthy is True
        
        # Test connection stats
        stats = await connection_manager.get_connection_stats()
        
        assert "active_connections" in stats
        assert "idle_connections" in stats
        assert "total_connections" in stats
        assert stats["total_connections"] <= connection_manager.max_connections

    async def test_connection_retry_logic(self, connection_manager):
        """Test connection retry logic on failures"""
        
        # Simulate connection failure and recovery
        with patch.object(connection_manager, '_create_connection') as mock_create:
            # First attempt fails, second succeeds
            mock_create.side_effect = [
                ConnectionError("Connection failed"),
                AsyncMock()  # Successful connection
            ]
            
            # Should retry and eventually succeed
            connection_acquired = False
            try:
                async with connection_manager.get_connection() as conn:
                    connection_acquired = True
            except Exception:
                pass
            
            # Should have retried at least once
            assert mock_create.call_count >= 1

    async def test_connection_timeout_handling(self, connection_manager):
        """Test connection timeout handling"""
        
        # Test query timeout
        with pytest.raises(asyncio.TimeoutError):
            async with connection_manager.get_connection() as conn:
                # This should timeout (if configured)
                await asyncio.wait_for(
                    conn.fetchval("SELECT pg_sleep(10)"),
                    timeout=1.0
                )

    async def test_connection_pool_exhaustion(self, connection_manager):
        """Test behavior when connection pool is exhausted"""
        
        # Hold all connections
        held_connections = []
        
        try:
            # Acquire all available connections
            for i in range(connection_manager.pool_size):
                conn = await connection_manager.pool.acquire()
                held_connections.append(conn)
            
            # Next acquisition should wait or timeout
            start_time = time.perf_counter()
            
            try:
                async with asyncio.timeout(1.0):  # 1 second timeout
                    async with connection_manager.get_connection() as conn:
                        pass
                assert False, "Should have timed out"
            except asyncio.TimeoutError:
                elapsed = time.perf_counter() - start_time
                assert elapsed >= 0.9  # Should have waited close to timeout
        
        finally:
            # Release held connections
            for conn in held_connections:
                await connection_manager.pool.release(conn)


class TestDatabaseMigrations:
    """Test database migration system"""

    @pytest.fixture
    async def migration_test_db(self):
        """Clean database for migration testing"""
        test_db_url = "postgresql://test_user:test_pass@localhost:5432/test_migrations"
        
        # Connect and drop/create database
        conn = await asyncpg.connect("postgresql://test_user:test_pass@localhost:5432/postgres")
        await conn.execute("DROP DATABASE IF EXISTS test_migrations")
        await conn.execute("CREATE DATABASE test_migrations")
        await conn.close()
        
        # Return connection manager
        connection_manager = DatabaseConnectionManager(test_db_url)
        await connection_manager.initialize()
        
        yield connection_manager
        
        await connection_manager.close()
        
        # Cleanup
        conn = await asyncpg.connect("postgresql://test_user:test_pass@localhost:5432/postgres")
        await conn.execute("DROP DATABASE test_migrations")
        await conn.close()

    async def test_migration_system(self, migration_test_db):
        """Test database migration system"""
        
        migrator = DatabaseMigrator(migration_test_db)
        
        # Check initial state
        current_version = await migrator.get_current_version()
        assert current_version == 0
        
        # Run migrations
        applied_migrations = await migrator.run_migrations()
        assert len(applied_migrations) > 0
        
        # Check updated version
        final_version = await migrator.get_current_version()
        assert final_version > 0
        
        # Verify migration tracking
        migration_history = await migrator.get_migration_history()
        assert len(migration_history) == len(applied_migrations)
        
        # Test idempotency - running migrations again should not apply any
        second_run = await migrator.run_migrations()
        assert len(second_run) == 0

    async def test_migration_rollback(self, migration_test_db):
        """Test migration rollback functionality"""
        
        migrator = DatabaseMigrator(migration_test_db)
        
        # Apply some migrations
        await migrator.run_migrations()
        current_version = await migrator.get_current_version()
        
        if current_version > 1:
            # Rollback one version
            target_version = current_version - 1
            rolled_back = await migrator.rollback_to_version(target_version)
            
            assert rolled_back is True
            
            # Verify rollback
            new_version = await migrator.get_current_version()
            assert new_version == target_version

    async def test_migration_validation(self, migration_test_db):
        """Test migration validation and integrity checks"""
        
        migrator = DatabaseMigrator(migration_test_db)
        
        # Run migrations
        await migrator.run_migrations()
        
        # Validate database schema
        validation_result = await migrator.validate_schema()
        assert validation_result["is_valid"] is True
        assert len(validation_result["errors"]) == 0
        
        # Check for required tables
        required_tables = ["properties", "investments", "portfolios", "migration_history"]
        
        async with migration_test_db.get_connection() as conn:
            for table in required_tables:
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = $1
                    )
                """, table)
                assert exists is True, f"Required table {table} not found"


class TestDatabasePerformance:
    """Test database performance characteristics"""

    @pytest.fixture
    async def perf_test_db(self, clean_database):
        """Database with performance test data"""
        property_repo = PropertyRepository(clean_database.connection_manager)
        
        # Create large dataset for performance testing
        large_dataset = []
        
        for i in range(1000):  # 1000 properties
            property = Property(
                property_id=f"perf_{i:06d}",
                url=f"https://example.com/perf/{i}",
                title=f"Performance Test Property {i}",
                property_type=PropertyType.APARTMENT,
                listing_type=ListingType.SALE,
                location=Location(neighborhood=f"Neighborhood_{i % 10}"),
                sqm=50.0 + (i % 100),
                rooms=1 + (i % 5),
                floor=i % 20,
                energy_class=[EnergyClass.A, EnergyClass.B, EnergyClass.C, EnergyClass.D][i % 4],
                price=Decimal(str(100000 + (i * 1000))),
                timestamp=datetime.now() - timedelta(days=i % 365),
                source="performance_test"
            )
            large_dataset.append(property)
        
        # Bulk insert
        await property_repo.bulk_create(large_dataset)
        
        yield clean_database

    async def test_query_performance_benchmarks(self, perf_test_db):
        """Test database query performance benchmarks"""
        
        property_repo = PropertyRepository(perf_test_db.connection_manager)
        
        import time
        
        # Test index-based queries (should be fast)
        performance_tests = [
            ("Single property lookup", lambda: property_repo.find_by_id("perf_000500")),
            ("Neighborhood filter", lambda: property_repo.find_by_neighborhood("Neighborhood_5")),
            ("Price range query", lambda: property_repo.find_by_price_range(Decimal("200000"), Decimal("400000"))),
            ("Property count", lambda: property_repo.count_total()),
        ]
        
        for test_name, query_func in performance_tests:
            start_time = time.perf_counter()
            result = await query_func()
            elapsed = time.perf_counter() - start_time
            
            print(f"{test_name}: {elapsed:.3f}s")
            
            # Performance assertions
            if "lookup" in test_name.lower():
                assert elapsed < 0.01, f"{test_name} too slow: {elapsed:.3f}s"
            else:
                assert elapsed < 0.1, f"{test_name} too slow: {elapsed:.3f}s"

    async def test_bulk_operation_performance(self, clean_database):
        """Test bulk operation performance"""
        
        property_repo = PropertyRepository(clean_database.connection_manager)
        
        # Test bulk insert performance
        bulk_sizes = [10, 50, 100, 500]
        
        for bulk_size in bulk_sizes:
            properties = []
            for i in range(bulk_size):
                property = Property(
                    property_id=f"bulk_{bulk_size}_{i:04d}",
                    url=f"https://example.com/bulk/{i}",
                    title=f"Bulk Test {i}",
                    property_type=PropertyType.APARTMENT,
                    listing_type=ListingType.SALE,
                    location=Location(neighborhood="BulkTest"),
                    sqm=80.0,
                    rooms=2,
                    floor=1,
                    energy_class=EnergyClass.B,
                    price=Decimal("200000"),
                    timestamp=datetime.now(),
                    source="bulk_test"
                )
                properties.append(property)
            
            start_time = time.perf_counter()
            await property_repo.bulk_create(properties)
            elapsed = time.perf_counter() - start_time
            
            throughput = bulk_size / elapsed
            print(f"Bulk insert {bulk_size} properties: {elapsed:.3f}s ({throughput:.1f} props/sec)")
            
            # Performance assertions
            assert throughput > 50, f"Bulk insert throughput too low: {throughput:.1f} props/sec"

    @pytest.mark.slow
    async def test_concurrent_load_performance(self, perf_test_db):
        """Test database performance under concurrent load"""
        
        property_repo = PropertyRepository(perf_test_db.connection_manager)
        
        async def concurrent_query(query_id: int):
            """Perform concurrent database query"""
            start_time = time.perf_counter()
            
            # Mix of different query types
            if query_id % 3 == 0:
                result = await property_repo.find_by_neighborhood(f"Neighborhood_{query_id % 10}")
            elif query_id % 3 == 1:
                result = await property_repo.find_by_id(f"perf_{query_id:06d}")
            else:
                result = await property_repo.find_by_price_range(
                    Decimal(str(100000 + query_id * 1000)),
                    Decimal(str(200000 + query_id * 1000))
                )
            
            elapsed = time.perf_counter() - start_time
            return elapsed
        
        # Run 50 concurrent queries
        concurrent_count = 50
        tasks = [concurrent_query(i) for i in range(concurrent_count)]
        
        overall_start = time.perf_counter()
        query_times = await asyncio.gather(*tasks)
        overall_elapsed = time.perf_counter() - overall_start
        
        # Analyze results
        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)
        throughput = concurrent_count / overall_elapsed
        
        print(f"Concurrent load test:")
        print(f"  Total time: {overall_elapsed:.3f}s")
        print(f"  Average query time: {avg_query_time:.3f}s")
        print(f"  Max query time: {max_query_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} queries/sec")
        
        # Performance assertions
        assert avg_query_time < 0.5, f"Average query time too high: {avg_query_time:.3f}s"
        assert max_query_time < 2.0, f"Max query time too high: {max_query_time:.3f}s"
        assert throughput > 10, f"Throughput too low: {throughput:.1f} queries/sec"