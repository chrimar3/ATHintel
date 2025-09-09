"""
🏗️ CQRS Commands

Command objects for the Command Query Responsibility Segregation pattern.
Commands represent write operations and business operations that change state.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from abc import ABC, abstractmethod

from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.entities.property_energy import BuildingType, HeatingSystem

class Command(ABC):
    """Base class for all commands"""
    
    def __init__(self):
        self.command_id = None  # Set by command bus
        self.issued_by = "system"
        self.issued_at = datetime.now()
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate command parameters, return list of validation errors"""
        pass

# Property Energy Commands

@dataclass
class AssessPropertyEnergyCommand(Command):
    """Command to assess or re-assess a property's energy efficiency"""
    
    property_id: str
    building_type: BuildingType
    construction_year: int
    total_area: Decimal
    heating_system: HeatingSystem
    current_energy_class: Optional[EnergyClass] = None
    
    # Optional detailed information
    annual_energy_consumption: Optional[Decimal] = None
    annual_energy_cost: Optional[Decimal] = None
    has_solar_panels: bool = False
    insulation_walls: bool = False
    insulation_roof: bool = False
    double_glazed_windows: bool = False
    smart_thermostat: bool = False
    
    # Assessment preferences
    use_ml_prediction: bool = True
    generate_recommendations: bool = True
    calculate_portfolio_impact: bool = False
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.property_id or len(self.property_id.strip()) == 0:
            errors.append("Property ID is required")
        
        if self.construction_year < 1800 or self.construction_year > datetime.now().year:
            errors.append(f"Invalid construction year: {self.construction_year}")
        
        if self.total_area <= 0:
            errors.append("Total area must be positive")
        
        if self.total_area > 10000:  # 10,000 m² upper limit
            errors.append("Total area too large (max 10,000 m²)")
        
        if self.annual_energy_consumption and self.annual_energy_consumption < 0:
            errors.append("Annual energy consumption cannot be negative")
        
        if self.annual_energy_cost and self.annual_energy_cost < 0:
            errors.append("Annual energy cost cannot be negative")
        
        return errors

@dataclass
class UpdateEnergyPredictionCommand(Command):
    """Command to update energy prediction for a property"""
    
    property_id: str
    assessment_id: str
    predicted_energy_class: EnergyClass
    prediction_confidence: Decimal
    ml_model_version: str = "v1.0"
    prediction_factors: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.property_id:
            errors.append("Property ID is required")
        
        if not self.assessment_id:
            errors.append("Assessment ID is required")
        
        if not (0 <= self.prediction_confidence <= 1):
            errors.append("Prediction confidence must be between 0 and 1")
        
        return errors

@dataclass
class GenerateUpgradeRecommendationsCommand(Command):
    """Command to generate upgrade recommendations for a property"""
    
    property_id: str
    assessment_id: str
    target_energy_class: Optional[EnergyClass] = None
    max_investment_budget: Optional[Decimal] = None
    priority_factors: List[str] = None  # e.g., ["roi", "payback", "environmental"]
    include_subsidies: bool = True
    
    def __post_init__(self):
        super().__init__()
        if self.priority_factors is None:
            self.priority_factors = ["roi", "payback"]
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.property_id:
            errors.append("Property ID is required")
        
        if not self.assessment_id:
            errors.append("Assessment ID is required")
        
        if self.max_investment_budget and self.max_investment_budget <= 0:
            errors.append("Investment budget must be positive")
        
        valid_factors = ["roi", "payback", "environmental", "implementation_ease"]
        for factor in self.priority_factors:
            if factor not in valid_factors:
                errors.append(f"Invalid priority factor: {factor}")
        
        return errors

# Portfolio Commands

@dataclass
class CreateEnergyPortfolioCommand(Command):
    """Command to create a new energy portfolio for analysis"""
    
    portfolio_name: str
    property_ids: List[str]
    owner_id: str
    analysis_goals: List[str]  # e.g., ["maximize_roi", "minimize_cost", "achieve_target_class"]
    target_investment_budget: Optional[Decimal] = None
    target_completion_date: Optional[datetime] = None
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.portfolio_name or len(self.portfolio_name.strip()) == 0:
            errors.append("Portfolio name is required")
        
        if not self.property_ids or len(self.property_ids) == 0:
            errors.append("At least one property is required")
        
        if len(self.property_ids) > 1000:
            errors.append("Portfolio cannot contain more than 1000 properties")
        
        if not self.owner_id:
            errors.append("Owner ID is required")
        
        if self.target_investment_budget and self.target_investment_budget <= 0:
            errors.append("Target investment budget must be positive")
        
        if self.target_completion_date and self.target_completion_date <= datetime.now():
            errors.append("Target completion date must be in the future")
        
        return errors

@dataclass
class OptimizePortfolioInvestmentCommand(Command):
    """Command to optimize investment allocation across portfolio properties"""
    
    portfolio_id: str
    available_budget: Decimal
    optimization_strategy: str  # "maximize_roi", "minimize_risk", "balanced"
    constraints: Dict[str, Any]  # Additional constraints
    
    def __post_init__(self):
        super().__init__()
        if self.constraints is None:
            self.constraints = {}
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.portfolio_id:
            errors.append("Portfolio ID is required")
        
        if self.available_budget <= 0:
            errors.append("Available budget must be positive")
        
        valid_strategies = ["maximize_roi", "minimize_risk", "balanced", "quick_wins"]
        if self.optimization_strategy not in valid_strategies:
            errors.append(f"Invalid optimization strategy: {self.optimization_strategy}")
        
        return errors

# Market Data Commands

@dataclass
class UpdateEnergyMarketDataCommand(Command):
    """Command to update energy market data (prices, subsidies, etc.)"""
    
    market_region: str
    data_type: str  # "electricity_price", "gas_price", "subsidies", "regulations"
    data_value: Decimal
    effective_date: datetime
    data_source: str
    expiry_date: Optional[datetime] = None
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.market_region:
            errors.append("Market region is required")
        
        valid_data_types = [
            "electricity_price", "gas_price", "oil_price", "subsidies", 
            "regulations", "carbon_tax", "feed_in_tariff"
        ]
        if self.data_type not in valid_data_types:
            errors.append(f"Invalid data type: {self.data_type}")
        
        if self.data_value < 0:
            errors.append("Data value cannot be negative")
        
        if not self.data_source:
            errors.append("Data source is required")
        
        if self.effective_date > datetime.now():
            errors.append("Effective date cannot be in the future")
        
        if self.expiry_date and self.expiry_date <= self.effective_date:
            errors.append("Expiry date must be after effective date")
        
        return errors

# ML Model Commands

@dataclass
class RetrainEnergyModelCommand(Command):
    """Command to retrain the energy prediction ML model"""
    
    training_data_source: str  # "database", "file", "api"
    model_type: str  # "random_forest", "gradient_boost", "neural_network"
    hyperparameters: Dict[str, Any]
    validation_split: Decimal = Decimal('0.2')
    cross_validation_folds: int = 5
    target_accuracy: Decimal = Decimal('0.85')
    
    def __post_init__(self):
        super().__init__()
        if self.hyperparameters is None:
            self.hyperparameters = {}
    
    def validate(self) -> List[str]:
        errors = []
        
        valid_sources = ["database", "file", "api"]
        if self.training_data_source not in valid_sources:
            errors.append(f"Invalid training data source: {self.training_data_source}")
        
        valid_models = ["random_forest", "gradient_boost", "neural_network", "ensemble"]
        if self.model_type not in valid_models:
            errors.append(f"Invalid model type: {self.model_type}")
        
        if not (0 < self.validation_split < 1):
            errors.append("Validation split must be between 0 and 1")
        
        if self.cross_validation_folds < 2 or self.cross_validation_folds > 10:
            errors.append("Cross validation folds must be between 2 and 10")
        
        if not (0 < self.target_accuracy <= 1):
            errors.append("Target accuracy must be between 0 and 1")
        
        return errors

# Batch Processing Commands

@dataclass
class ProcessPropertyBatchCommand(Command):
    """Command to process a batch of properties for energy assessment"""
    
    batch_name: str
    property_ids: List[str]
    processing_priority: str = "normal"  # "low", "normal", "high", "urgent"
    include_recommendations: bool = True
    include_portfolio_analysis: bool = False
    notification_email: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.batch_name:
            errors.append("Batch name is required")
        
        if not self.property_ids:
            errors.append("Property IDs list is required")
        
        if len(self.property_ids) == 0:
            errors.append("At least one property ID is required")
        
        if len(self.property_ids) > 10000:
            errors.append("Batch size cannot exceed 10,000 properties")
        
        valid_priorities = ["low", "normal", "high", "urgent"]
        if self.processing_priority not in valid_priorities:
            errors.append(f"Invalid processing priority: {self.processing_priority}")
        
        if self.notification_email and "@" not in self.notification_email:
            errors.append("Invalid notification email format")
        
        return errors

# Reporting Commands

@dataclass
class GenerateEnergyReportCommand(Command):
    """Command to generate energy analysis reports"""
    
    report_type: str  # "property", "portfolio", "market", "comparative"
    scope_ids: List[str]  # Property IDs, Portfolio IDs, or Market Region IDs
    report_format: str = "pdf"  # "pdf", "excel", "json", "html"
    include_sections: List[str] = None
    custom_parameters: Dict[str, Any] = None
    delivery_method: str = "download"  # "download", "email", "api"
    recipient_email: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()
        if self.include_sections is None:
            self.include_sections = ["summary", "recommendations", "financial_analysis"]
        if self.custom_parameters is None:
            self.custom_parameters = {}
    
    def validate(self) -> List[str]:
        errors = []
        
        valid_types = ["property", "portfolio", "market", "comparative", "executive"]
        if self.report_type not in valid_types:
            errors.append(f"Invalid report type: {self.report_type}")
        
        if not self.scope_ids:
            errors.append("Scope IDs are required")
        
        valid_formats = ["pdf", "excel", "json", "html", "csv"]
        if self.report_format not in valid_formats:
            errors.append(f"Invalid report format: {self.report_format}")
        
        valid_delivery = ["download", "email", "api", "storage"]
        if self.delivery_method not in valid_delivery:
            errors.append(f"Invalid delivery method: {self.delivery_method}")
        
        if self.delivery_method == "email" and not self.recipient_email:
            errors.append("Recipient email required for email delivery")
        
        return errors

# Command Result Classes

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    command_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = None
    execution_time_ms: Optional[float] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

@dataclass
class AsyncCommandResult:
    """Result of asynchronous command execution"""
    command_id: str
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    estimated_completion_time: Optional[datetime] = None
    progress_percentage: Decimal = Decimal('0')
    status_url: Optional[str] = None