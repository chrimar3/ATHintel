"""
🏗️ CQRS Infrastructure Package

Command Query Responsibility Segregation (CQRS) implementation for the energy domain.
Provides separation between write operations (commands) and read operations (queries).

Key Components:
- Commands: Write operations that change system state
- Queries: Read operations that retrieve data without side effects
- Command Bus: Routes and executes commands with middleware support
- Query Bus: Routes and executes queries with caching and optimization
- Event Integration: Domain events published from command handlers

Usage:
    from infrastructure.cqrs import get_command_bus, get_query_bus
    from infrastructure.cqrs.commands import AssessPropertyEnergyCommand
    from infrastructure.cqrs.queries import GetPropertyEnergyAssessmentQuery
    
    # Execute command
    command_bus = get_command_bus()
    command = AssessPropertyEnergyCommand(...)
    result = await command_bus.execute(command)
    
    # Execute query
    query_bus = get_query_bus()
    query = GetPropertyEnergyAssessmentQuery(...)
    result = await query_bus.execute(query)
"""

from .commands import (
    # Base classes
    Command, CommandResult, AsyncCommandResult,
    
    # Property commands
    AssessPropertyEnergyCommand,
    UpdateEnergyPredictionCommand,
    GenerateUpgradeRecommendationsCommand,
    
    # Portfolio commands
    CreateEnergyPortfolioCommand,
    OptimizePortfolioInvestmentCommand,
    
    # Market data commands
    UpdateEnergyMarketDataCommand,
    
    # ML model commands
    RetrainEnergyModelCommand,
    
    # Batch processing commands
    ProcessPropertyBatchCommand,
    
    # Reporting commands
    GenerateEnergyReportCommand,
)

from .queries import (
    # Base classes
    Query, QueryResult, PagedQueryResult,
    
    # Property queries
    GetPropertyEnergyAssessmentQuery,
    SearchPropertiesByEnergyClassQuery,
    GetUpgradeRecommendationsQuery,
    
    # Portfolio queries
    GetEnergyPortfolioQuery,
    GetPortfolioAnalysisQuery,
    GetOptimizationOpportunitiesQuery,
    
    # Market data queries
    GetEnergyMarketDataQuery,
    GetMarketBenchmarkQuery,
    
    # Reporting queries
    GetEnergyReportsQuery,
    GetDashboardDataQuery,
    
    # Analytics queries
    GetEnergyTrendsQuery,
    GetPerformanceMetricsQuery,
)

from .command_bus import (
    CommandBus,
    CommandHandler,
    CommandBusError,
    CommandValidationError,
    CommandHandlerNotFoundError,
    get_command_bus,
    create_command_bus,
)

from .query_bus import (
    QueryBus,
    QueryHandler,
    QueryBusError,
    QueryValidationError,
    QueryHandlerNotFoundError,
    QueryCache,
    get_query_bus,
    create_query_bus,
)

__all__ = [
    # Commands
    "Command",
    "CommandResult", 
    "AsyncCommandResult",
    "AssessPropertyEnergyCommand",
    "UpdateEnergyPredictionCommand",
    "GenerateUpgradeRecommendationsCommand",
    "CreateEnergyPortfolioCommand",
    "OptimizePortfolioInvestmentCommand",
    "UpdateEnergyMarketDataCommand",
    "RetrainEnergyModelCommand",
    "ProcessPropertyBatchCommand",
    "GenerateEnergyReportCommand",
    
    # Queries
    "Query",
    "QueryResult",
    "PagedQueryResult",
    "GetPropertyEnergyAssessmentQuery",
    "SearchPropertiesByEnergyClassQuery",
    "GetUpgradeRecommendationsQuery",
    "GetEnergyPortfolioQuery",
    "GetPortfolioAnalysisQuery",
    "GetOptimizationOpportunitiesQuery",
    "GetEnergyMarketDataQuery",
    "GetMarketBenchmarkQuery",
    "GetEnergyReportsQuery",
    "GetDashboardDataQuery",
    "GetEnergyTrendsQuery",
    "GetPerformanceMetricsQuery",
    
    # Command Bus
    "CommandBus",
    "CommandHandler", 
    "CommandBusError",
    "CommandValidationError",
    "CommandHandlerNotFoundError",
    "get_command_bus",
    "create_command_bus",
    
    # Query Bus
    "QueryBus",
    "QueryHandler",
    "QueryBusError", 
    "QueryValidationError",
    "QueryHandlerNotFoundError",
    "QueryCache",
    "get_query_bus",
    "create_query_bus",
]