"""
Service Interfaces - Hexagonal Architecture Ports

These interfaces define contracts for external services without specifying implementation.
Adapters will implement these for specific external service integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ..domain.entities import Property, Location, PropertyType


class WebScrapingService(ABC):
    """Interface for web scraping services"""
    
    @abstractmethod
    async def scrape_property_listings(
        self,
        base_url: str,
        search_criteria: Dict[str, Any],
        max_pages: int = 10
    ) -> AsyncGenerator[Property, None]:
        """Scrape property listings from a real estate website"""
        pass
    
    @abstractmethod
    async def scrape_single_property(self, url: str) -> Optional[Property]:
        """Scrape details for a single property"""
        pass
    
    @abstractmethod
    async def verify_property_exists(self, url: str) -> bool:
        """Verify if property still exists at URL"""
        pass
    
    @abstractmethod
    async def extract_property_images(self, url: str) -> List[str]:
        """Extract property image URLs"""
        pass
    
    @abstractmethod
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping performance statistics"""
        pass


class GeolocationService(ABC):
    """Interface for geolocation and mapping services"""
    
    @abstractmethod
    async def geocode_address(self, address: str) -> Optional[Location]:
        """Convert address to geographic coordinates"""
        pass
    
    @abstractmethod
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """Convert coordinates to address"""
        pass
    
    @abstractmethod
    async def calculate_distance(
        self, 
        location1: Location, 
        location2: Location
    ) -> Optional[float]:
        """Calculate distance between two locations in km"""
        pass
    
    @abstractmethod
    async def find_nearby_amenities(
        self,
        location: Location,
        amenity_type: str,
        radius_km: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Find nearby amenities (schools, hospitals, metro stations)"""
        pass
    
    @abstractmethod
    async def get_neighborhood_boundaries(self, neighborhood: str) -> Optional[Dict[str, Any]]:
        """Get geographic boundaries of a neighborhood"""
        pass


class MarketDataService(ABC):
    """Interface for market data and analytics services"""
    
    @abstractmethod
    async def get_neighborhood_trends(
        self,
        neighborhood: str,
        time_period: str = "1y"
    ) -> Dict[str, Any]:
        """Get price and market trends for neighborhood"""
        pass
    
    @abstractmethod
    async def get_comparable_sales(
        self,
        property: Property,
        radius_km: float = 1.0,
        max_results: int = 10
    ) -> List[Property]:
        """Find comparable recent sales"""
        pass
    
    @abstractmethod
    async def calculate_market_valuation(self, property: Property) -> Dict[str, Any]:
        """Calculate estimated market valuation"""
        pass
    
    @abstractmethod
    async def get_rental_yield_estimates(
        self,
        neighborhood: str,
        property_type: PropertyType
    ) -> Dict[str, float]:
        """Get rental yield estimates by area and type"""
        pass
    
    @abstractmethod
    async def get_market_indicators(self) -> Dict[str, Any]:
        """Get overall market indicators"""
        pass


class NotificationService(ABC):
    """Interface for notification services"""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """Send email notification"""
        pass
    
    @abstractmethod
    async def send_slack_message(
        self,
        channel: str,
        message: str,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """Send Slack notification"""
        pass
    
    @abstractmethod
    async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Send webhook notification"""
        pass
    
    @abstractmethod
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS notification"""
        pass


class ReportingService(ABC):
    """Interface for report generation services"""
    
    @abstractmethod
    async def generate_investment_report(
        self,
        properties: List[Property],
        template: str = "default"
    ) -> bytes:
        """Generate PDF investment report"""
        pass
    
    @abstractmethod
    async def generate_market_analysis(
        self,
        neighborhood: str,
        include_charts: bool = True
    ) -> bytes:
        """Generate market analysis report"""
        pass
    
    @abstractmethod
    async def generate_portfolio_summary(
        self,
        portfolio_id: str,
        format: str = "pdf"
    ) -> bytes:
        """Generate portfolio summary report"""
        pass
    
    @abstractmethod
    async def generate_excel_export(
        self,
        properties: List[Property],
        include_analytics: bool = True
    ) -> bytes:
        """Generate Excel export of properties"""
        pass


class CacheService(ABC):
    """Interface for caching services"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set cached value with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter value"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        pass


class FileStorageService(ABC):
    """Interface for file storage services"""
    
    @abstractmethod
    async def upload_file(
        self,
        file_path: Path,
        destination_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload file and return public URL"""
        pass
    
    @abstractmethod
    async def download_file(self, file_key: str, local_path: Path) -> bool:
        """Download file to local path"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """Delete file from storage"""
        pass
    
    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files with optional prefix filter"""
        pass
    
    @abstractmethod
    async def get_file_url(
        self,
        file_key: str,
        expires_in_seconds: int = 3600
    ) -> str:
        """Get signed URL for file access"""
        pass


class AnalyticsService(ABC):
    """Interface for analytics and machine learning services"""
    
    @abstractmethod
    async def predict_price(self, property: Property) -> Dict[str, Any]:
        """Predict property price using ML models"""
        pass
    
    @abstractmethod
    async def detect_anomalies(self, properties: List[Property]) -> List[str]:
        """Detect anomalous properties"""
        pass
    
    @abstractmethod
    async def cluster_properties(
        self,
        properties: List[Property],
        method: str = "kmeans"
    ) -> Dict[str, List[str]]:
        """Cluster properties into groups"""
        pass
    
    @abstractmethod
    async def calculate_investment_score(
        self,
        property: Property,
        market_context: Dict[str, Any]
    ) -> float:
        """Calculate investment attractiveness score"""
        pass
    
    @abstractmethod
    async def optimize_portfolio(
        self,
        available_properties: List[Property],
        budget: Decimal,
        risk_tolerance: str
    ) -> List[Property]:
        """Optimize property portfolio selection"""
        pass


class MonitoringService(ABC):
    """Interface for system monitoring and health checks"""
    
    @abstractmethod
    async def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Record application metric"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, str]:
        """Perform system health check"""
        pass
    
    @abstractmethod
    async def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "info"
    ) -> bool:
        """Log application event"""
        pass
    
    @abstractmethod
    async def create_alert(
        self,
        alert_name: str,
        message: str,
        severity: str = "warning"
    ) -> bool:
        """Create monitoring alert"""
        pass


class ExternalAPIService(ABC):
    """Interface for external API integrations"""
    
    @abstractmethod
    async def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API call with retry logic and error handling"""
        pass
    
    @abstractmethod
    async def get_api_health(self, service_name: str) -> Dict[str, Any]:
        """Check external API health status"""
        pass
    
    @abstractmethod
    async def get_rate_limit_status(self, service_name: str) -> Dict[str, Any]:
        """Get API rate limit status"""
        pass


class ConfigurationService(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        pass
    
    @abstractmethod
    def update(self, key: str, value: Any) -> bool:
        """Update configuration value"""
        pass
    
    @abstractmethod
    def reload(self) -> bool:
        """Reload configuration from source"""
        pass
    
    @abstractmethod
    def validate(self) -> Dict[str, Any]:
        """Validate current configuration"""
        pass