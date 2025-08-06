"""
Repository Interfaces - Hexagonal Architecture Ports

These interfaces define contracts for data access without specifying implementation.
Adapters will implement these interfaces for specific databases/storage systems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from ..domain.entities import Property, Investment, Portfolio, MarketSegment, PropertyType, Location


class PropertyRepository(ABC):
    """Repository interface for Property entity operations"""
    
    @abstractmethod
    async def save(self, property: Property) -> Property:
        """Save a property to the repository"""
        pass
    
    @abstractmethod
    async def find_by_id(self, property_id: str) -> Optional[Property]:
        """Find property by unique identifier"""
        pass
    
    @abstractmethod
    async def find_by_url(self, url: str) -> Optional[Property]:
        """Find property by source URL"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Property]:
        """Find all properties with optional pagination"""
        pass
    
    @abstractmethod
    async def find_by_neighborhood(self, neighborhood: str) -> List[Property]:
        """Find properties by neighborhood"""
        pass
    
    @abstractmethod
    async def find_by_price_range(self, min_price: Decimal, max_price: Decimal) -> List[Property]:
        """Find properties within price range"""
        pass
    
    @abstractmethod
    async def find_by_sqm_range(self, min_sqm: float, max_sqm: float) -> List[Property]:
        """Find properties within size range"""
        pass
    
    @abstractmethod
    async def find_by_property_type(self, property_type: PropertyType) -> List[Property]:
        """Find properties by type"""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Property]:
        """Find properties matching multiple criteria"""
        pass
    
    @abstractmethod
    async def search(self, query: str) -> List[Property]:
        """Full-text search across properties"""
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """Count total number of properties"""
        pass
    
    @abstractmethod
    async def count_by_neighborhood(self) -> Dict[str, int]:
        """Count properties grouped by neighborhood"""
        pass
    
    @abstractmethod
    async def get_price_statistics(self) -> Dict[str, Any]:
        """Get price statistics across all properties"""
        pass
    
    @abstractmethod
    async def get_neighborhood_statistics(self, neighborhood: str) -> Dict[str, Any]:
        """Get statistics for specific neighborhood"""
        pass
    
    @abstractmethod
    async def update(self, property: Property) -> Property:
        """Update existing property"""
        pass
    
    @abstractmethod
    async def delete(self, property_id: str) -> bool:
        """Delete property by ID"""
        pass
    
    @abstractmethod
    async def bulk_save(self, properties: List[Property]) -> List[Property]:
        """Bulk save multiple properties"""
        pass


class InvestmentRepository(ABC):
    """Repository interface for Investment entity operations"""
    
    @abstractmethod
    async def save(self, investment: Investment) -> Investment:
        """Save investment analysis"""
        pass
    
    @abstractmethod
    async def find_by_id(self, investment_id: str) -> Optional[Investment]:
        """Find investment by ID"""
        pass
    
    @abstractmethod
    async def find_by_property_id(self, property_id: str) -> Optional[Investment]:
        """Find investment analysis for specific property"""
        pass
    
    @abstractmethod
    async def find_top_opportunities(self, limit: int = 10) -> List[Investment]:
        """Find top investment opportunities by score"""
        pass
    
    @abstractmethod
    async def find_by_score_range(self, min_score: float, max_score: float) -> List[Investment]:
        """Find investments within score range"""
        pass
    
    @abstractmethod
    async def find_by_yield_range(self, min_yield: float, max_yield: float) -> List[Investment]:
        """Find investments within yield range"""
        pass
    
    @abstractmethod
    async def find_by_budget(self, max_budget: Decimal) -> List[Investment]:
        """Find investments within budget"""
        pass
    
    @abstractmethod
    async def update(self, investment: Investment) -> Investment:
        """Update investment analysis"""
        pass
    
    @abstractmethod
    async def delete(self, investment_id: str) -> bool:
        """Delete investment analysis"""
        pass


class PortfolioRepository(ABC):
    """Repository interface for Portfolio entity operations"""
    
    @abstractmethod
    async def save(self, portfolio: Portfolio) -> Portfolio:
        """Save portfolio"""
        pass
    
    @abstractmethod
    async def find_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        """Find portfolio by ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Portfolio]:
        """Find all portfolios"""
        pass
    
    @abstractmethod
    async def find_by_budget_range(self, min_budget: Decimal, max_budget: Decimal) -> List[Portfolio]:
        """Find portfolios within budget range"""
        pass
    
    @abstractmethod
    async def update(self, portfolio: Portfolio) -> Portfolio:
        """Update portfolio"""
        pass
    
    @abstractmethod
    async def delete(self, portfolio_id: str) -> bool:
        """Delete portfolio"""
        pass
    
    @abstractmethod
    async def add_investment(self, portfolio_id: str, investment: Investment) -> Portfolio:
        """Add investment to portfolio"""
        pass
    
    @abstractmethod
    async def remove_investment(self, portfolio_id: str, investment_id: str) -> Portfolio:
        """Remove investment from portfolio"""
        pass


class MarketSegmentRepository(ABC):
    """Repository interface for MarketSegment entity operations"""
    
    @abstractmethod
    async def save(self, segment: MarketSegment) -> MarketSegment:
        """Save market segment analysis"""
        pass
    
    @abstractmethod
    async def find_by_neighborhood(self, neighborhood: str) -> Optional[MarketSegment]:
        """Find market segment by neighborhood"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[MarketSegment]:
        """Find all market segments"""
        pass
    
    @abstractmethod
    async def find_top_performing(self, limit: int = 5) -> List[MarketSegment]:
        """Find top performing market segments"""
        pass
    
    @abstractmethod
    async def update(self, segment: MarketSegment) -> MarketSegment:
        """Update market segment analysis"""
        pass
    
    @abstractmethod
    async def delete(self, segment_id: str) -> bool:
        """Delete market segment"""
        pass


class CacheRepository(ABC):
    """Repository interface for caching operations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set cached value with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        pass


class SearchRepository(ABC):
    """Repository interface for advanced search operations"""
    
    @abstractmethod
    async def index_property(self, property: Property) -> bool:
        """Index property for search"""
        pass
    
    @abstractmethod
    async def search_properties(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Property]:
        """Advanced property search with filters"""
        pass
    
    @abstractmethod
    async def suggest_neighborhoods(self, partial: str) -> List[str]:
        """Auto-suggest neighborhoods"""
        pass
    
    @abstractmethod
    async def get_similar_properties(
        self, 
        property: Property, 
        limit: int = 5
    ) -> List[Property]:
        """Find similar properties"""
        pass
    
    @abstractmethod
    async def bulk_index(self, properties: List[Property]) -> bool:
        """Bulk index properties for search"""
        pass


class MetricsRepository(ABC):
    """Repository interface for metrics and monitoring"""
    
    @abstractmethod
    async def record_metric(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Record a metric data point"""
        pass
    
    @abstractmethod
    async def get_metric_history(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Get historical metric data"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics"""
        pass


class EventRepository(ABC):
    """Repository interface for event sourcing and audit trail"""
    
    @abstractmethod
    async def save_event(
        self,
        event_type: str,
        entity_id: str,
        entity_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Save domain event"""
        pass
    
    @abstractmethod
    async def get_entity_events(
        self,
        entity_id: str,
        entity_type: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get events for specific entity"""
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get events by type and time range"""
        pass