"""
🔍 CQRS Queries

Query objects for the Command Query Responsibility Segregation pattern.
Queries represent read operations and data retrieval without side effects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from abc import ABC, abstractmethod

from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.entities.property_energy import BuildingType, HeatingSystem

class Query(ABC):
    """Base class for all queries"""
    
    def __init__(self):
        self.query_id = None  # Set by query bus
        self.requested_by = "system"
        self.requested_at = datetime.now()
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate query parameters, return list of validation errors"""
        pass

# Property Energy Queries

@dataclass
class GetPropertyEnergyAssessmentQuery(Query):
    """Query to retrieve property energy assessment details"""
    
    property_id: str
    include_recommendations: bool = True
    include_historical_data: bool = False
    include_market_comparison: bool = False
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.property_id or len(self.property_id.strip()) == 0:
            errors.append("Property ID is required")
        
        return errors

@dataclass
class SearchPropertiesByEnergyClassQuery(Query):
    """Query to search properties by energy class and criteria"""
    
    energy_classes: List[EnergyClass] = None
    building_types: List[BuildingType] = None
    construction_year_min: Optional[int] = None
    construction_year_max: Optional[int] = None
    area_min: Optional[Decimal] = None
    area_max: Optional[Decimal] = None
    location: Optional[str] = None
    
    # Pagination
    page: int = 1
    page_size: int = 50
    
    # Sorting
    sort_by: str = "energy_class"  # energy_class, construction_year, area, last_assessed
    sort_order: str = "asc"  # asc, desc
    
    def __post_init__(self):
        super().__init__()
        if self.energy_classes is None:
            self.energy_classes = []
        if self.building_types is None:
            self.building_types = []
    
    def validate(self) -> List[str]:
        errors = []
        
        if self.page < 1:
            errors.append("Page must be at least 1")
        
        if not (1 <= self.page_size <= 1000):
            errors.append("Page size must be between 1 and 1000")
        
        if self.construction_year_min and self.construction_year_max:
            if self.construction_year_min > self.construction_year_max:
                errors.append("Min construction year cannot be greater than max")
        
        if self.area_min and self.area_max:
            if self.area_min > self.area_max:
                errors.append("Min area cannot be greater than max area")
        
        valid_sort_fields = ["energy_class", "construction_year", "area", "last_assessed", "roi_potential"]
        if self.sort_by not in valid_sort_fields:
            errors.append(f"Invalid sort field. Must be one of: {valid_sort_fields}")
        
        if self.sort_order not in ["asc", "desc"]:
            errors.append("Sort order must be 'asc' or 'desc'")
        
        return errors

@dataclass
class GetUpgradeRecommendationsQuery(Query):
    """Query to retrieve upgrade recommendations for a property"""
    
    property_id: str
    assessment_id: Optional[str] = None
    max_investment_budget: Optional[Decimal] = None
    priority_filter: Optional[List[str]] = None  # ["critical", "high", "medium"]
    upgrade_type_filter: Optional[List[str]] = None
    include_subsidies: bool = True
    include_financial_analysis: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.property_id:
            errors.append("Property ID is required")
        
        if self.max_investment_budget and self.max_investment_budget <= 0:
            errors.append("Maximum investment budget must be positive")
        
        if self.priority_filter:
            valid_priorities = ["critical", "high", "medium", "low", "optional"]
            for priority in self.priority_filter:
                if priority not in valid_priorities:
                    errors.append(f"Invalid priority filter: {priority}")
        
        return errors

# Portfolio Queries

@dataclass
class GetEnergyPortfolioQuery(Query):
    """Query to retrieve energy portfolio details"""
    
    portfolio_id: str
    include_property_details: bool = True
    include_aggregate_metrics: bool = True
    include_optimization_opportunities: bool = False
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.portfolio_id:
            errors.append("Portfolio ID is required")
        
        return errors

@dataclass
class GetPortfolioAnalysisQuery(Query):
    """Query to retrieve comprehensive portfolio analysis"""
    
    portfolio_id: str
    analysis_type: str = "full"  # "full", "financial", "environmental", "risk"
    benchmark_against: Optional[str] = None  # "market_average", "top_quartile"
    include_property_breakdown: bool = True
    include_recommendations: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.portfolio_id:
            errors.append("Portfolio ID is required")
        
        valid_analysis_types = ["full", "financial", "environmental", "risk", "quick"]
        if self.analysis_type not in valid_analysis_types:
            errors.append(f"Invalid analysis type: {self.analysis_type}")
        
        valid_benchmarks = ["market_average", "top_quartile", "regulatory_standards"]
        if self.benchmark_against and self.benchmark_against not in valid_benchmarks:
            errors.append(f"Invalid benchmark: {self.benchmark_against}")
        
        return errors

@dataclass
class GetOptimizationOpportunitiesQuery(Query):
    """Query to find optimization opportunities across properties"""
    
    portfolio_id: Optional[str] = None
    property_ids: Optional[List[str]] = None
    available_budget: Optional[Decimal] = None
    time_horizon_years: int = 10
    optimization_goal: str = "maximize_roi"  # maximize_roi, minimize_cost, maximize_savings
    include_phased_approach: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.portfolio_id and not self.property_ids:
            errors.append("Either portfolio ID or property IDs must be provided")
        
        if self.property_ids and len(self.property_ids) == 0:
            errors.append("Property IDs list cannot be empty")
        
        if self.available_budget and self.available_budget <= 0:
            errors.append("Available budget must be positive")
        
        if not (1 <= self.time_horizon_years <= 30):
            errors.append("Time horizon must be between 1 and 30 years")
        
        valid_goals = ["maximize_roi", "minimize_cost", "maximize_savings", "minimize_risk"]
        if self.optimization_goal not in valid_goals:
            errors.append(f"Invalid optimization goal: {self.optimization_goal}")
        
        return errors

# Market Data Queries

@dataclass
class GetEnergyMarketDataQuery(Query):
    """Query to retrieve energy market data for analysis"""
    
    market_regions: List[str]
    data_types: List[str]  # electricity_price, gas_price, subsidies, etc.
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_trends: bool = True
    include_forecasts: bool = False
    
    def __post_init__(self):
        super().__init__()
        if not self.date_to:
            self.date_to = datetime.now()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.market_regions:
            errors.append("At least one market region is required")
        
        if not self.data_types:
            errors.append("At least one data type is required")
        
        valid_data_types = [
            "electricity_price", "gas_price", "oil_price", "subsidies",
            "regulations", "carbon_tax", "feed_in_tariff", "market_rates"
        ]
        
        for data_type in self.data_types:
            if data_type not in valid_data_types:
                errors.append(f"Invalid data type: {data_type}")
        
        if self.date_from and self.date_to and self.date_from > self.date_to:
            errors.append("Date from cannot be after date to")
        
        return errors

@dataclass
class GetMarketBenchmarkQuery(Query):
    """Query to get market benchmarks for property comparison"""
    
    property_id: str
    benchmark_type: str = "regional"  # regional, national, similar_properties
    include_energy_class_distribution: bool = True
    include_upgrade_trends: bool = True
    include_roi_comparisons: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.property_id:
            errors.append("Property ID is required")
        
        valid_benchmark_types = ["regional", "national", "similar_properties", "building_type"]
        if self.benchmark_type not in valid_benchmark_types:
            errors.append(f"Invalid benchmark type: {self.benchmark_type}")
        
        return errors

# Reporting Queries

@dataclass
class GetEnergyReportsQuery(Query):
    """Query to retrieve available energy reports"""
    
    report_types: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_by: Optional[str] = None
    scope_ids: Optional[List[str]] = None
    page: int = 1
    page_size: int = 20
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if self.page < 1:
            errors.append("Page must be at least 1")
        
        if not (1 <= self.page_size <= 100):
            errors.append("Page size must be between 1 and 100")
        
        if self.report_types:
            valid_types = ["property", "portfolio", "market", "comparative", "executive"]
            for report_type in self.report_types:
                if report_type not in valid_types:
                    errors.append(f"Invalid report type: {report_type}")
        
        return errors

@dataclass
class GetDashboardDataQuery(Query):
    """Query to retrieve dashboard data for energy overview"""
    
    user_id: str
    portfolio_ids: Optional[List[str]] = None
    date_range_days: int = 30
    include_alerts: bool = True
    include_recommendations: bool = True
    include_market_updates: bool = True
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not (1 <= self.date_range_days <= 365):
            errors.append("Date range must be between 1 and 365 days")
        
        return errors

# Analytics Queries

@dataclass
class GetEnergyTrendsQuery(Query):
    """Query to analyze energy efficiency trends"""
    
    analysis_scope: str = "national"  # national, regional, portfolio, property_type
    scope_identifiers: Optional[List[str]] = None
    time_period_months: int = 12
    trend_metrics: List[str] = None  # energy_class_improvements, cost_savings, roi_trends
    include_predictions: bool = False
    
    def __post_init__(self):
        super().__init__()
        if self.trend_metrics is None:
            self.trend_metrics = ["energy_class_improvements", "cost_savings"]
    
    def validate(self) -> List[str]:
        errors = []
        
        valid_scopes = ["national", "regional", "portfolio", "property_type", "building_age"]
        if self.analysis_scope not in valid_scopes:
            errors.append(f"Invalid analysis scope: {self.analysis_scope}")
        
        if not (1 <= self.time_period_months <= 60):
            errors.append("Time period must be between 1 and 60 months")
        
        valid_metrics = [
            "energy_class_improvements", "cost_savings", "roi_trends", 
            "upgrade_adoption", "subsidy_utilization", "market_penetration"
        ]
        
        for metric in self.trend_metrics:
            if metric not in valid_metrics:
                errors.append(f"Invalid trend metric: {metric}")
        
        return errors

@dataclass
class GetPerformanceMetricsQuery(Query):
    """Query to retrieve system performance and usage metrics"""
    
    metric_types: List[str]  # assessment_accuracy, processing_speed, user_engagement
    date_from: datetime
    date_to: datetime
    aggregation_level: str = "daily"  # hourly, daily, weekly, monthly
    include_breakdown: bool = False
    
    def __post_init__(self):
        super().__init__()
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.metric_types:
            errors.append("At least one metric type is required")
        
        valid_metrics = [
            "assessment_accuracy", "processing_speed", "user_engagement",
            "recommendation_effectiveness", "system_uptime", "api_performance"
        ]
        
        for metric in self.metric_types:
            if metric not in valid_metrics:
                errors.append(f"Invalid metric type: {metric}")
        
        if self.date_from >= self.date_to:
            errors.append("Date from must be before date to")
        
        valid_aggregations = ["hourly", "daily", "weekly", "monthly"]
        if self.aggregation_level not in valid_aggregations:
            errors.append(f"Invalid aggregation level: {self.aggregation_level}")
        
        return errors

# Query Result Classes

@dataclass
class QueryResult:
    """Result of query execution"""
    success: bool
    query_id: str
    data: Optional[Dict[str, Any]] = None
    total_count: Optional[int] = None  # For paginated results
    validation_errors: List[str] = None
    execution_time_ms: Optional[float] = None
    cached: bool = False
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

@dataclass  
class PagedQueryResult(QueryResult):
    """Paginated query result with navigation info"""
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False