"""
🚌 CQRS Command Bus

Command bus implementation for routing and executing commands in the CQRS architecture.
Handles command validation, routing, middleware, and event publishing.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Type
from decimal import Decimal
import logging

from .commands import Command, CommandResult, AsyncCommandResult
from domains.energy.events.domain_events import DomainEvent, get_event_publisher

logger = logging.getLogger(__name__)

class CommandHandler:
    """Base class for command handlers"""
    
    async def handle(self, command: Command) -> CommandResult:
        """Handle a command and return result"""
        raise NotImplementedError()

class CommandBusError(Exception):
    """Base exception for command bus errors"""
    pass

class CommandValidationError(CommandBusError):
    """Command validation failed"""
    pass

class CommandHandlerNotFoundError(CommandBusError):
    """No handler found for command type"""
    pass

class CommandBus:
    """
    Command bus for routing and executing commands
    
    Provides:
    - Command validation
    - Handler routing
    - Middleware pipeline
    - Event publishing
    - Async execution support
    """
    
    def __init__(self):
        self._handlers: Dict[Type[Command], CommandHandler] = {}
        self._middleware: List[Callable] = []
        self._event_publisher = get_event_publisher()
        
    def register_handler(self, command_type: Type[Command], handler: CommandHandler):
        """Register a command handler"""
        self._handlers[command_type] = handler
        logger.info(f"Registered handler for {command_type.__name__}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to the processing pipeline"""
        self._middleware.append(middleware)
        logger.info(f"Added middleware: {middleware.__name__}")
    
    async def execute(self, command: Command) -> CommandResult:
        """Execute a command synchronously"""
        start_time = datetime.now()
        
        try:
            # Set command metadata
            command.command_id = str(uuid.uuid4())
            
            # Validate command
            validation_errors = command.validate()
            if validation_errors:
                return CommandResult(
                    success=False,
                    command_id=command.command_id,
                    message="Command validation failed",
                    validation_errors=validation_errors,
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Apply middleware
            for middleware in self._middleware:
                try:
                    await middleware(command)
                except Exception as e:
                    logger.error(f"Middleware {middleware.__name__} failed: {e}")
                    return CommandResult(
                        success=False,
                        command_id=command.command_id,
                        message=f"Middleware execution failed: {str(e)}",
                        execution_time_ms=self._calculate_execution_time(start_time)
                    )
            
            # Find and execute handler
            handler = self._get_handler(command)
            result = await handler.handle(command)
            
            # Set execution metadata
            result.command_id = command.command_id
            result.execution_time_ms = self._calculate_execution_time(start_time)
            
            # Log successful execution
            logger.info(f"Command {command.__class__.__name__} executed successfully in {result.execution_time_ms}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            return CommandResult(
                success=False,
                command_id=command.command_id if hasattr(command, 'command_id') else "unknown",
                message=f"Command execution failed: {str(e)}",
                execution_time_ms=self._calculate_execution_time(start_time)
            )
    
    async def execute_async(self, command: Command) -> AsyncCommandResult:
        """Execute a command asynchronously and return job tracking info"""
        command.command_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Validate command first
        validation_errors = command.validate()
        if validation_errors:
            return AsyncCommandResult(
                command_id=command.command_id,
                job_id=job_id,
                status="failed",
                progress_percentage=Decimal('0')
            )
        
        # Start async execution
        asyncio.create_task(self._execute_async_task(command, job_id))
        
        return AsyncCommandResult(
            command_id=command.command_id,
            job_id=job_id,
            status="queued",
            estimated_completion_time=self._estimate_completion_time(command),
            progress_percentage=Decimal('0'),
            status_url=f"/api/commands/{command.command_id}/status"
        )
    
    async def _execute_async_task(self, command: Command, job_id: str):
        """Internal async task execution"""
        try:
            result = await self.execute(command)
            # In a real implementation, you would store the result
            # and update job status in a persistent store
            logger.info(f"Async command {command.__class__.__name__} completed with job_id {job_id}")
        except Exception as e:
            logger.error(f"Async command {command.__class__.__name__} failed with job_id {job_id}: {e}")
    
    def _get_handler(self, command: Command) -> CommandHandler:
        """Get handler for command type"""
        command_type = type(command)
        
        if command_type not in self._handlers:
            available_handlers = list(self._handlers.keys())
            raise CommandHandlerNotFoundError(
                f"No handler registered for command {command_type.__name__}. "
                f"Available handlers: {[h.__name__ for h in available_handlers]}"
            )
        
        return self._handlers[command_type]
    
    def _calculate_execution_time(self, start_time: datetime) -> float:
        """Calculate execution time in milliseconds"""
        return (datetime.now() - start_time).total_seconds() * 1000
    
    def _estimate_completion_time(self, command: Command) -> Optional[datetime]:
        """Estimate command completion time based on command type"""
        # Simple estimation - in production this would use historical data
        complexity_estimates = {
            'AssessPropertyEnergyCommand': 30,  # seconds
            'GenerateUpgradeRecommendationsCommand': 60,
            'CreateEnergyPortfolioCommand': 15,
            'OptimizePortfolioInvestmentCommand': 300,  # 5 minutes
            'ProcessPropertyBatchCommand': 1800,  # 30 minutes
            'RetrainEnergyModelCommand': 7200,  # 2 hours
            'GenerateEnergyReportCommand': 120,  # 2 minutes
        }
        
        command_name = command.__class__.__name__
        estimated_seconds = complexity_estimates.get(command_name, 60)
        
        return datetime.now().replace(microsecond=0) + \
               asyncio.timedelta(seconds=estimated_seconds)

# Middleware Functions

async def logging_middleware(command: Command):
    """Middleware for command logging"""
    logger.info(f"Executing command: {command.__class__.__name__} "
                f"(ID: {getattr(command, 'command_id', 'unknown')})")

async def performance_monitoring_middleware(command: Command):
    """Middleware for performance monitoring"""
    # In production, this would send metrics to monitoring system
    logger.debug(f"Performance tracking for {command.__class__.__name__}")

async def security_middleware(command: Command):
    """Middleware for security validation and authorization"""
    from config.security_config import SecurityConfig
    
    # Get security configuration
    security_config = SecurityConfig()
    
    # Check if command has proper authentication
    if not hasattr(command, 'issued_by') or not command.issued_by:
        raise CommandBusError("Command must have 'issued_by' field for authentication")
    
    # Block anonymous commands in production
    if command.issued_by == "anonymous":
        if security_config.environment == "production":
            raise CommandBusError("Anonymous command execution not allowed in production")
        else:
            logger.warning(f"Anonymous command execution in {security_config.environment}: {command.__class__.__name__}")
    
    # Validate user authentication for non-system commands
    if command.issued_by != "system":
        # Check if user token/session is valid (mock implementation)
        if not _validate_user_authentication(command.issued_by):
            raise CommandBusError(f"Invalid or expired authentication for user: {command.issued_by}")
    
    # Command-specific authorization checks
    _check_command_authorization(command)
    
    logger.debug(f"Security validation passed for command {command.__class__.__name__} by {command.issued_by}")

def _validate_user_authentication(user_id: str) -> bool:
    """Validate user authentication - implement proper JWT/session validation"""
    # TODO: Implement proper JWT token validation
    # For now, reject obviously invalid user IDs
    if not user_id or len(user_id) < 3 or user_id in ['test', 'admin', 'guest']:
        return False
    return True

def _check_command_authorization(command: Command):
    """Check if user is authorized to execute specific command"""
    command_name = command.__class__.__name__
    user_id = command.issued_by
    
    # Define restricted commands that require special authorization
    restricted_commands = [
        'RetrainEnergyModelCommand',
        'UpdateEnergyMarketDataCommand',
        'ProcessPropertyBatchCommand'
    ]
    
    if command_name in restricted_commands:
        # Check if user has admin privileges (mock implementation)
        if not _user_has_admin_privileges(user_id):
            raise CommandBusError(f"User {user_id} not authorized to execute {command_name}")

def _user_has_admin_privileges(user_id: str) -> bool:
    """Check if user has administrative privileges"""
    # TODO: Implement proper role-based authorization
    # For now, only system and specific admin users
    admin_users = ['system', 'admin_user', 'energy_admin']
    return user_id in admin_users

async def rate_limiting_middleware(command: Command):
    """Middleware for rate limiting"""
    # Simple rate limiting - in production use Redis or similar
    if hasattr(command, 'issued_by'):
        # Check rate limits per user
        pass

# Command Handler Implementations

from .commands import (
    AssessPropertyEnergyCommand, UpdateEnergyPredictionCommand, 
    GenerateUpgradeRecommendationsCommand, CreateEnergyPortfolioCommand,
    OptimizePortfolioInvestmentCommand, UpdateEnergyMarketDataCommand,
    RetrainEnergyModelCommand, ProcessPropertyBatchCommand, GenerateEnergyReportCommand
)

class AssessPropertyEnergyHandler(CommandHandler):
    """Handler for property energy assessment commands"""
    
    async def handle(self, command: AssessPropertyEnergyCommand) -> CommandResult:
        try:
            # Import here to avoid circular dependencies
            from domains.energy.entities.property_energy import PropertyEnergyEntity
            from domains.energy.value_objects.energy_class import EnergyClass
            
            # Simulate energy assessment logic
            # In production, this would integrate with actual ML models and data sources
            
            logger.info(f"Assessing property {command.property_id}")
            
            # Mock assessment result
            assessed_class = EnergyClass.estimate_from_building_age(command.construction_year, False)
            
            # Create domain events
            from domains.energy.events.domain_events import PropertyEnergyAssessed
            
            event = PropertyEnergyAssessed(
                property_id=command.property_id,
                assessment_id=str(uuid.uuid4()),
                old_energy_class=command.current_energy_class,
                new_energy_class=assessed_class,
                confidence=Decimal('0.85'),
                assessor_type="ml_system"
            )
            
            # Publish event
            self._event_publisher = get_event_publisher()
            self._event_publisher.publish(event)
            
            return CommandResult(
                success=True,
                command_id=command.command_id,
                message=f"Property {command.property_id} assessed successfully",
                data={
                    'property_id': command.property_id,
                    'assessment_id': event.assessment_id,
                    'energy_class': assessed_class.value,
                    'confidence': float(event.confidence)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                command_id=command.command_id,
                message=f"Assessment failed: {str(e)}"
            )

class GenerateUpgradeRecommendationsHandler(CommandHandler):
    """Handler for upgrade recommendation generation"""
    
    async def handle(self, command: GenerateUpgradeRecommendationsCommand) -> CommandResult:
        try:
            logger.info(f"Generating upgrade recommendations for property {command.property_id}")
            
            # Import here to avoid circular dependencies
            from domains.energy.value_objects.upgrade_recommendation import (
                UpgradeRecommendation, create_heating_system_upgrade
            )
            from domains.energy.value_objects.energy_class import EnergyClass
            
            # Mock recommendation generation
            recommendations = []
            
            # Generate heating system upgrade recommendation
            heating_upgrade = create_heating_system_upgrade(
                current_system="old_gas_boiler",
                building_area=Decimal('120'),
                target_efficiency_gain=Decimal('30')
            )
            recommendations.append(heating_upgrade)
            
            # Create domain event
            from domains.energy.events.domain_events import UpgradeRecommendationGenerated
            
            for recommendation in recommendations:
                event = UpgradeRecommendationGenerated(
                    property_id=command.property_id,
                    assessment_id=command.assessment_id,
                    upgrade_type=recommendation.upgrade_type,
                    estimated_cost=recommendation.cost,
                    estimated_savings=recommendation.annual_savings,
                    roi=recommendation.roi,
                    priority_score=recommendation.priority_score
                )
                
                # Publish event
                self._event_publisher = get_event_publisher()
                self._event_publisher.publish(event)
            
            return CommandResult(
                success=True,
                command_id=command.command_id,
                message=f"Generated {len(recommendations)} upgrade recommendations",
                data={
                    'property_id': command.property_id,
                    'assessment_id': command.assessment_id,
                    'recommendations_count': len(recommendations),
                    'recommendations': [rec.to_dict() for rec in recommendations]
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                command_id=command.command_id,
                message=f"Recommendation generation failed: {str(e)}"
            )

# Factory function for creating configured command bus

def create_command_bus() -> CommandBus:
    """Create and configure command bus with default handlers and middleware"""
    bus = CommandBus()
    
    # Register middleware
    bus.add_middleware(logging_middleware)
    bus.add_middleware(performance_monitoring_middleware)
    bus.add_middleware(security_middleware)
    bus.add_middleware(rate_limiting_middleware)
    
    # Register handlers
    bus.register_handler(AssessPropertyEnergyCommand, AssessPropertyEnergyHandler())
    bus.register_handler(GenerateUpgradeRecommendationsCommand, GenerateUpgradeRecommendationsHandler())
    
    # Additional handlers would be registered here in a complete implementation
    
    logger.info("Command bus configured with default handlers and middleware")
    return bus

# Global command bus instance
_command_bus = None

def get_command_bus() -> CommandBus:
    """Get global command bus instance"""
    global _command_bus
    if _command_bus is None:
        _command_bus = create_command_bus()
    return _command_bus