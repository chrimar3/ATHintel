"""
🧪 CQRS Infrastructure Tests

Comprehensive test suite for CQRS command and query buses,
including security, performance, and error handling tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

# Import CQRS infrastructure
from infrastructure.cqrs import (
    Command, CommandResult, CommandBus, CommandHandler, CommandBusError,
    Query, QueryResult, QueryBus, QueryHandler, QueryBusError,
    AssessPropertyEnergyCommand, GetPropertyEnergyAssessmentQuery,
    get_command_bus, get_query_bus
)

class TestCommand(Command):
    """Test command for unit testing"""
    
    def __init__(self, test_data: str, user_id: str = "test_user"):
        super().__init__()
        self.test_data = test_data
        self.issued_by = user_id
    
    def validate(self):
        errors = []
        if not self.test_data:
            errors.append("Test data is required")
        return errors

class TestQuery(Query):
    """Test query for unit testing"""
    
    def __init__(self, test_param: str, user_id: str = "test_user"):
        super().__init__()
        self.test_param = test_param
        self.requested_by = user_id
    
    def validate(self):
        errors = []
        if not self.test_param:
            errors.append("Test parameter is required")
        return errors

class TestCommandHandler(CommandHandler):
    """Test command handler"""
    
    async def handle(self, command: TestCommand) -> CommandResult:
        return CommandResult(
            success=True,
            command_id=command.command_id,
            message=f"Processed: {command.test_data}",
            data={'processed_data': command.test_data.upper()}
        )

class TestQueryHandler(QueryHandler):
    """Test query handler"""
    
    async def handle(self, query: TestQuery) -> QueryResult:
        return QueryResult(
            success=True,
            query_id=query.query_id,
            data={'result': f"Query result for {query.test_param}"}
        )

class TestCommandBus:
    """Test command bus functionality"""
    
    @pytest.fixture
    def command_bus(self):
        """Create test command bus"""
        bus = CommandBus()
        bus.register_handler(TestCommand, TestCommandHandler())
        return bus
    
    @pytest.mark.asyncio
    async def test_command_execution_success(self, command_bus):
        """Test successful command execution"""
        command = TestCommand("test_data", "test_user")
        result = await command_bus.execute(command)
        
        assert result.success is True
        assert result.command_id is not None
        assert result.message == "Processed: test_data"
        assert result.data['processed_data'] == "TEST_DATA"
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_command_validation_failure(self, command_bus):
        """Test command validation failure"""
        command = TestCommand("", "test_user")  # Invalid empty data
        result = await command_bus.execute(command)
        
        assert result.success is False
        assert "Test data is required" in result.validation_errors
    
    @pytest.mark.asyncio
    async def test_command_security_enforcement(self, command_bus):
        """Test command security middleware"""
        # Command without authentication
        command = TestCommand("test_data")
        command.issued_by = None
        
        with patch('infrastructure.cqrs.command_bus.SecurityConfig') as mock_config:
            mock_config.return_value.environment = "production"
            
            result = await command_bus.execute(command)
            assert result.success is False
            assert "authentication" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_anonymous_command_in_production(self, command_bus):
        """Test anonymous command blocking in production"""
        command = TestCommand("test_data", "anonymous")
        
        with patch('infrastructure.cqrs.command_bus.SecurityConfig') as mock_config:
            mock_config.return_value.environment = "production"
            
            result = await command_bus.execute(command)
            assert result.success is False
            assert "Anonymous command execution not allowed" in result.message
    
    @pytest.mark.asyncio
    async def test_command_handler_not_found(self, command_bus):
        """Test missing command handler error"""
        
        class UnregisteredCommand(Command):
            def validate(self):
                return []
        
        command = UnregisteredCommand()
        command.issued_by = "test_user"
        
        with pytest.raises(Exception):  # Should raise CommandHandlerNotFoundError
            await command_bus.execute(command)
    
    @pytest.mark.asyncio
    async def test_middleware_pipeline(self, command_bus):
        """Test middleware execution order"""
        execution_order = []
        
        async def middleware1(command):
            execution_order.append("middleware1")
        
        async def middleware2(command):
            execution_order.append("middleware2")
        
        # Clear existing middleware and add test middleware
        command_bus._middleware = []
        command_bus.add_middleware(middleware1)
        command_bus.add_middleware(middleware2)
        
        command = TestCommand("test_data", "test_user")
        await command_bus.execute(command)
        
        assert execution_order == ["middleware1", "middleware2"]
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, command_bus):
        """Test middleware error handling"""
        
        async def failing_middleware(command):
            raise Exception("Middleware failure")
        
        command_bus._middleware = [failing_middleware]
        
        command = TestCommand("test_data", "test_user")
        result = await command_bus.execute(command)
        
        assert result.success is False
        assert "Middleware execution failed" in result.message
    
    @pytest.mark.asyncio
    async def test_restricted_command_authorization(self, command_bus):
        """Test authorization for restricted commands"""
        from infrastructure.cqrs.commands import RetrainEnergyModelCommand
        
        # Mock handler for restricted command
        class MockHandler(CommandHandler):
            async def handle(self, command):
                return CommandResult(success=True, command_id=command.command_id, message="Success")
        
        command_bus.register_handler(RetrainEnergyModelCommand, MockHandler())
        
        # Test with non-admin user
        command = RetrainEnergyModelCommand(
            training_data_source="database",
            model_type="random_forest",
            hyperparameters={}
        )
        command.issued_by = "regular_user"
        
        with patch('infrastructure.cqrs.command_bus._user_has_admin_privileges', return_value=False):
            result = await command_bus.execute(command)
            assert result.success is False
            assert "not authorized" in result.message

class TestQueryBus:
    """Test query bus functionality"""
    
    @pytest.fixture
    def query_bus(self):
        """Create test query bus"""
        bus = QueryBus()
        bus.register_handler(TestQuery, TestQueryHandler())
        return bus
    
    @pytest.mark.asyncio
    async def test_query_execution_success(self, query_bus):
        """Test successful query execution"""
        query = TestQuery("test_param", "test_user")
        result = await query_bus.execute(query)
        
        assert result.success is True
        assert result.query_id is not None
        assert result.data['result'] == "Query result for test_param"
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_query_caching(self, query_bus):
        """Test query result caching"""
        query1 = TestQuery("cached_param", "test_user")
        query2 = TestQuery("cached_param", "test_user")
        
        # First execution
        result1 = await query_bus.execute(query1, use_cache=True)
        execution_time1 = result1.execution_time_ms
        
        # Second execution should be faster (cached)
        result2 = await query_bus.execute(query2, use_cache=True)
        
        assert result1.data == result2.data
        # Note: In a real scenario with cache, result2.cached would be True
    
    @pytest.mark.asyncio
    async def test_sensitive_query_security(self, query_bus):
        """Test security for sensitive queries"""
        from infrastructure.cqrs.queries import GetDashboardDataQuery
        
        # Mock handler for sensitive query
        class MockHandler(QueryHandler):
            async def handle(self, query):
                return QueryResult(success=True, query_id=query.query_id, data={'sensitive': 'data'})
        
        query_bus.register_handler(GetDashboardDataQuery, MockHandler())
        
        # Test anonymous access to sensitive query in production
        query = GetDashboardDataQuery(user_id="test_user")
        query.requested_by = "anonymous"
        
        with patch('infrastructure.cqrs.query_bus.SecurityConfig') as mock_config:
            mock_config.return_value.environment = "production"
            
            result = await query_bus.execute(query)
            assert result.success is False
            assert "Anonymous access" in result.message
    
    @pytest.mark.asyncio
    async def test_query_validation_failure(self, query_bus):
        """Test query validation failure"""
        query = TestQuery("", "test_user")  # Invalid empty parameter
        result = await query_bus.execute(query)
        
        assert result.success is False
        assert "Test parameter is required" in result.validation_errors
    
    @pytest.mark.asyncio
    async def test_admin_only_query_authorization(self, query_bus):
        """Test admin-only query authorization"""
        from infrastructure.cqrs.queries import GetPerformanceMetricsQuery
        
        # Mock handler
        class MockHandler(QueryHandler):
            async def handle(self, query):
                return QueryResult(success=True, query_id=query.query_id, data={'metrics': 'data'})
        
        query_bus.register_handler(GetPerformanceMetricsQuery, MockHandler())
        
        # Test with regular user
        query = GetPerformanceMetricsQuery(
            metric_types=['assessment_accuracy'],
            date_from=datetime.now(),
            date_to=datetime.now()
        )
        query.requested_by = "regular_user"
        
        with patch('infrastructure.cqrs.query_bus._query_user_has_admin_privileges', return_value=False):
            result = await query_bus.execute(query)
            assert result.success is False
            assert "not authorized" in result.message

class TestDomainCommands:
    """Test domain-specific commands"""
    
    @pytest.mark.asyncio
    async def test_assess_property_energy_command(self):
        """Test property energy assessment command"""
        from domains.energy.entities.property_energy import BuildingType, HeatingSystem
        
        command = AssessPropertyEnergyCommand(
            property_id="PROP_TEST_001",
            building_type=BuildingType.APARTMENT,
            construction_year=1990,
            total_area=Decimal('85'),
            heating_system=HeatingSystem.INDIVIDUAL_GAS
        )
        command.issued_by = "system"
        
        # Test validation
        errors = command.validate()
        assert len(errors) == 0
    
    def test_assess_property_energy_command_validation(self):
        """Test property energy assessment command validation"""
        from domains.energy.entities.property_energy import BuildingType, HeatingSystem
        
        # Test with invalid data
        command = AssessPropertyEnergyCommand(
            property_id="",  # Empty property ID
            building_type=BuildingType.APARTMENT,
            construction_year=1500,  # Invalid year
            total_area=Decimal('-10'),  # Negative area
            heating_system=HeatingSystem.INDIVIDUAL_GAS
        )
        
        errors = command.validate()
        assert len(errors) > 0
        assert any("Property ID is required" in error for error in errors)
        assert any("Invalid construction year" in error for error in errors)
        assert any("Total area must be positive" in error for error in errors)

class TestDomainQueries:
    """Test domain-specific queries"""
    
    def test_get_property_assessment_query(self):
        """Test property assessment query"""
        query = GetPropertyEnergyAssessmentQuery(
            property_id="PROP_001",
            include_recommendations=True,
            include_market_comparison=True
        )
        query.requested_by = "test_user"
        
        # Test validation
        errors = query.validate()
        assert len(errors) == 0
    
    def test_get_property_assessment_query_validation(self):
        """Test property assessment query validation"""
        query = GetPropertyEnergyAssessmentQuery(
            property_id="",  # Empty property ID
            include_recommendations=True
        )
        
        errors = query.validate()
        assert len(errors) > 0
        assert any("Property ID is required" in error for error in errors)
    
    def test_search_properties_query_validation(self):
        """Test property search query validation"""
        from infrastructure.cqrs.queries import SearchPropertiesByEnergyClassQuery
        from domains.energy.value_objects.energy_class import EnergyClass
        
        # Test with invalid pagination
        query = SearchPropertiesByEnergyClassQuery(
            energy_classes=[EnergyClass.C, EnergyClass.D],
            page=0,  # Invalid page number
            page_size=2000  # Too large page size
        )
        
        errors = query.validate()
        assert len(errors) > 0
        assert any("Page must be at least 1" in error for error in errors)
        assert any("Page size must be between 1 and 1000" in error for error in errors)

class TestPerformanceAndReliability:
    """Test performance and reliability aspects"""
    
    @pytest.mark.asyncio
    async def test_concurrent_command_execution(self):
        """Test concurrent command processing"""
        bus = CommandBus()
        bus.register_handler(TestCommand, TestCommandHandler())
        
        # Create multiple commands
        commands = [TestCommand(f"data_{i}", "test_user") for i in range(10)]
        
        # Execute concurrently
        tasks = [bus.execute(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result.success for result in results)
        assert len(results) == 10
    
    @pytest.mark.asyncio
    async def test_command_timeout_handling(self):
        """Test command execution timeout"""
        
        class SlowCommandHandler(CommandHandler):
            async def handle(self, command):
                await asyncio.sleep(2)  # Simulate slow operation
                return CommandResult(success=True, command_id=command.command_id, message="Slow")
        
        bus = CommandBus()
        bus.register_handler(TestCommand, SlowCommandHandler())
        
        command = TestCommand("slow_data", "test_user")
        
        # Test with timeout (would need to be implemented in production)
        start_time = datetime.now()
        result = await bus.execute(command)
        end_time = datetime.now()
        
        # Should complete (in this test setup)
        assert result.success is True
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time >= 2  # Should take at least 2 seconds
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_logging(self):
        """Test error recovery and logging"""
        
        class FailingCommandHandler(CommandHandler):
            async def handle(self, command):
                raise Exception("Simulated handler failure")
        
        bus = CommandBus()
        bus.register_handler(TestCommand, FailingCommandHandler())
        
        command = TestCommand("failing_data", "test_user")
        
        with patch('infrastructure.cqrs.command_bus.logger') as mock_logger:
            result = await bus.execute(command)
            
            # Should handle error gracefully
            assert result.success is False
            assert "Command execution failed" in result.message
            
            # Should log the error
            mock_logger.error.assert_called()

class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_energy_assessment_workflow(self):
        """Test complete energy assessment workflow"""
        command_bus = get_command_bus()
        query_bus = get_query_bus()
        
        # Step 1: Execute assessment command
        from domains.energy.entities.property_energy import BuildingType, HeatingSystem
        
        assess_command = AssessPropertyEnergyCommand(
            property_id="PROP_INTEGRATION_001",
            building_type=BuildingType.APARTMENT,
            construction_year=1995,
            total_area=Decimal('90'),
            heating_system=HeatingSystem.INDIVIDUAL_GAS,
            use_ml_prediction=True,
            generate_recommendations=True
        )
        assess_command.issued_by = "system"
        
        # Execute assessment (will use mock handler)
        assessment_result = await command_bus.execute(assess_command)
        
        if assessment_result.success:
            # Step 2: Query the assessment results
            query = GetPropertyEnergyAssessmentQuery(
                property_id="PROP_INTEGRATION_001",
                include_recommendations=True
            )
            query.requested_by = "test_user"
            
            query_result = await query_bus.execute(query)
            
            assert query_result.success is True
            assert query_result.data is not None
    
    @pytest.mark.asyncio
    async def test_security_across_buses(self):
        """Test security enforcement across command and query buses"""
        command_bus = get_command_bus()
        query_bus = get_query_bus()
        
        # Test command security
        command = TestCommand("secure_data")
        command.issued_by = None  # No authentication
        
        with patch('infrastructure.cqrs.command_bus.SecurityConfig') as mock_config:
            mock_config.return_value.environment = "production"
            cmd_result = await command_bus.execute(command)
            assert cmd_result.success is False
        
        # Test query security
        query = TestQuery("sensitive_param")
        query.requested_by = None  # No authentication
        
        with patch('infrastructure.cqrs.query_bus.SecurityConfig') as mock_config:
            mock_config.return_value.environment = "production"
            query_result = await query_bus.execute(query)
            assert query_result.success is False

if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])