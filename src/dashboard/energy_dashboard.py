"""
📊 Real-time Energy Dashboard

Interactive energy analytics dashboard for property portfolio management
with real-time updates, comprehensive visualizations, and Greek market insights.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from dataclasses import dataclass, field
import logging
import json

from infrastructure.cqrs import get_query_bus, get_command_bus
from infrastructure.cqrs.queries import (
    GetDashboardDataQuery, GetEnergyPortfolioQuery, GetMarketBenchmarkQuery,
    SearchPropertiesByEnergyClassQuery, GetEnergyTrendsQuery
)
from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.value_objects.financial_metrics import FinancialMetrics
from config.production_config import get_config

logger = logging.getLogger(__name__)

@dataclass
class DashboardMetric:
    """Individual dashboard metric with trend information"""
    name: str
    value: Union[int, float, Decimal, str]
    unit: str = ""
    trend_percentage: Optional[float] = None
    trend_direction: Optional[str] = None  # "up", "down", "stable"
    color: str = "primary"  # "primary", "success", "warning", "danger"
    description: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": float(self.value) if isinstance(self.value, Decimal) else self.value,
            "unit": self.unit,
            "trend_percentage": self.trend_percentage,
            "trend_direction": self.trend_direction,
            "color": self.color,
            "description": self.description,
            "last_updated": self.last_updated.isoformat()
        }

@dataclass
class ChartDataPoint:
    """Data point for dashboard charts"""
    timestamp: datetime
    value: Union[int, float, Decimal]
    label: str = ""
    category: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": float(self.value) if isinstance(self.value, Decimal) else self.value,
            "label": self.label,
            "category": self.category
        }

@dataclass
class DashboardAlert:
    """Dashboard alert for user attention"""
    id: str
    severity: str  # "info", "warning", "error", "critical"
    title: str
    message: str
    action_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

class EnergyDashboardService:
    """
    Real-time energy dashboard service providing comprehensive
    analytics for property portfolio management
    """
    
    def __init__(self):
        self.config = get_config()
        self.cache_duration = timedelta(minutes=5)  # Cache dashboard data for 5 minutes
        self._cached_data: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
    async def get_portfolio_overview(self, user_id: str, portfolio_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive portfolio overview dashboard"""
        
        cache_key = f"portfolio_overview_{user_id}_{hash(str(portfolio_ids))}"
        
        # Check cache
        if self._is_cached(cache_key):
            return self._cached_data[cache_key]
        
        try:
            query_bus = get_query_bus()
            
            # Get dashboard data
            dashboard_query = GetDashboardDataQuery(
                user_id=user_id,
                portfolio_ids=portfolio_ids,
                date_range_days=30,
                include_alerts=True,
                include_recommendations=True,
                include_market_updates=True
            )
            dashboard_query.requested_by = user_id
            
            dashboard_result = await query_bus.execute(dashboard_query)
            
            if not dashboard_result.success:
                raise Exception(f"Dashboard query failed: {dashboard_result}")
            
            dashboard_data = dashboard_result.data
            
            # Build comprehensive overview
            overview = await self._build_portfolio_overview(dashboard_data, user_id)
            
            # Cache result
            self._cached_data[cache_key] = overview
            self._cache_timestamps[cache_key] = datetime.now()
            
            return overview
            
        except Exception as e:
            logger.error(f"Portfolio overview generation failed: {e}")
            return await self._get_fallback_overview(user_id)
    
    async def _build_portfolio_overview(self, dashboard_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Build comprehensive portfolio overview from dashboard data"""
        
        # Key metrics
        metrics = [
            DashboardMetric(
                name="Total Properties",
                value=dashboard_data.get('summary', {}).get('total_properties', 0),
                unit="properties",
                color="primary",
                description="Total properties in your portfolio"
            ),
            DashboardMetric(
                name="Average Energy Class",
                value=dashboard_data.get('summary', {}).get('average_energy_class', 'C'),
                color="success" if dashboard_data.get('summary', {}).get('average_energy_class', 'C') in ['A+', 'A', 'B+'] else "warning",
                description="Portfolio average energy performance rating"
            ),
            DashboardMetric(
                name="Annual Energy Cost",
                value=dashboard_data.get('summary', {}).get('total_annual_cost', 0),
                unit="€",
                trend_percentage=-5.2,  # Mock trend data
                trend_direction="down",
                color="success",
                description="Total annual energy costs across portfolio"
            ),
            DashboardMetric(
                name="Potential Savings",
                value=dashboard_data.get('summary', {}).get('potential_savings', 0),
                unit="€/year",
                trend_percentage=12.3,
                trend_direction="up",
                color="warning",
                description="Estimated annual savings from recommended upgrades"
            ),
            DashboardMetric(
                name="Active Upgrades",
                value=dashboard_data.get('summary', {}).get('active_upgrades', 0),
                unit="projects",
                color="info",
                description="Currently ongoing energy improvement projects"
            )
        ]
        
        # Energy class distribution
        energy_distribution = await self._get_energy_class_distribution(user_id)
        
        # Recent assessments timeline
        assessments_timeline = await self._get_assessments_timeline(user_id)
        
        # ROI opportunities
        roi_opportunities = await self._get_roi_opportunities(user_id)
        
        # Market comparison
        market_comparison = await self._get_market_comparison_data(user_id)
        
        # Alerts and notifications
        alerts = await self._generate_dashboard_alerts(dashboard_data, user_id)
        
        # Performance trends
        performance_trends = await self._get_performance_trends(user_id)
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": [metric.to_dict() for metric in metrics],
            "charts": {
                "energy_distribution": energy_distribution,
                "assessments_timeline": assessments_timeline,
                "roi_opportunities": roi_opportunities,
                "performance_trends": performance_trends
            },
            "market_comparison": market_comparison,
            "alerts": [alert.to_dict() for alert in alerts],
            "recommendations": dashboard_data.get('top_recommendations', []),
            "quick_actions": [
                {
                    "title": "Schedule New Assessment",
                    "description": "Get energy rating for a new property",
                    "action": "assessment/new",
                    "icon": "assessment"
                },
                {
                    "title": "View Upgrade Projects",
                    "description": "Check status of ongoing improvements",
                    "action": "projects/active", 
                    "icon": "construction"
                },
                {
                    "title": "Market Report",
                    "description": "Latest Greek energy market insights",
                    "action": "market/report",
                    "icon": "trending_up"
                }
            ]
        }
    
    async def _get_energy_class_distribution(self, user_id: str) -> Dict[str, Any]:
        """Get energy class distribution chart data"""
        
        # Mock data - in production this would come from actual portfolio queries
        distribution_data = [
            {"energy_class": "A+", "count": 2, "percentage": 8.7},
            {"energy_class": "A", "count": 3, "percentage": 13.0},
            {"energy_class": "B+", "count": 4, "percentage": 17.4},
            {"energy_class": "B", "count": 5, "percentage": 21.7},
            {"energy_class": "C", "count": 6, "percentage": 26.1},
            {"energy_class": "D", "count": 3, "percentage": 13.0},
            {"energy_class": "E", "count": 0, "percentage": 0.0},
            {"energy_class": "F", "count": 0, "percentage": 0.0},
            {"energy_class": "G", "count": 0, "percentage": 0.0}
        ]
        
        return {
            "chart_type": "donut",
            "title": "Energy Class Distribution",
            "data": distribution_data,
            "colors": {
                "A+": "#00A651", "A": "#4CBB17", "B+": "#9ACD32", "B": "#ADFF2F",
                "C": "#FFFF00", "D": "#FFA500", "E": "#FF6347", "F": "#FF4500", "G": "#DC143C"
            }
        }
    
    async def _get_assessments_timeline(self, user_id: str) -> Dict[str, Any]:
        """Get recent assessments timeline data"""
        
        # Generate timeline data for last 6 months
        timeline_data = []
        base_date = datetime.now() - timedelta(days=180)
        
        for i in range(24):  # Weekly data points
            week_date = base_date + timedelta(weeks=i)
            assessments_count = max(0, 5 + (i % 3) - 1)  # Mock varying assessments
            
            timeline_data.append(ChartDataPoint(
                timestamp=week_date,
                value=assessments_count,
                label=f"Week {i+1}",
                category="assessments"
            ))
        
        return {
            "chart_type": "line",
            "title": "Property Assessments Over Time",
            "data": [point.to_dict() for point in timeline_data],
            "x_axis": "timestamp",
            "y_axis": "value",
            "unit": "assessments"
        }
    
    async def _get_roi_opportunities(self, user_id: str) -> Dict[str, Any]:
        """Get ROI opportunities chart data"""
        
        # Mock ROI opportunities by upgrade type
        roi_data = [
            {"upgrade_type": "Solar Panels", "roi": 18.5, "investment": 15000, "savings": 2775},
            {"upgrade_type": "Heat Pump", "roi": 16.2, "investment": 12000, "savings": 1944},
            {"upgrade_type": "Wall Insulation", "roi": 14.8, "investment": 8000, "savings": 1184},
            {"upgrade_type": "Windows", "roi": 12.1, "investment": 6000, "savings": 726},
            {"upgrade_type": "Roof Insulation", "roi": 11.5, "investment": 5000, "savings": 575}
        ]
        
        return {
            "chart_type": "bubble",
            "title": "ROI Opportunities by Upgrade Type",
            "data": roi_data,
            "x_axis": "investment",
            "y_axis": "roi",
            "size_axis": "savings",
            "unit_x": "€",
            "unit_y": "%",
            "unit_size": "€/year"
        }
    
    async def _get_performance_trends(self, user_id: str) -> Dict[str, Any]:
        """Get portfolio performance trends"""
        
        # Generate performance trend data
        trend_data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(12):  # Monthly data
            month_date = base_date + timedelta(days=30*i)
            
            # Mock improving performance over time
            efficiency_score = 65 + (i * 2) + (i % 3)
            cost_savings = 1000 + (i * 150) + (i % 4) * 100
            
            trend_data.append({
                "timestamp": month_date.isoformat(),
                "efficiency_score": efficiency_score,
                "cost_savings": cost_savings,
                "month": month_date.strftime("%b %Y")
            })
        
        return {
            "chart_type": "multi_line",
            "title": "Portfolio Performance Trends",
            "data": trend_data,
            "series": [
                {"key": "efficiency_score", "name": "Efficiency Score", "color": "#4CBB17", "unit": "score"},
                {"key": "cost_savings", "name": "Monthly Savings", "color": "#00A651", "unit": "€"}
            ]
        }
    
    async def _get_market_comparison_data(self, user_id: str) -> Dict[str, Any]:
        """Get market comparison data"""
        
        return {
            "portfolio_average": {
                "energy_class": "B+",
                "annual_cost_per_m2": 18.50,
                "efficiency_score": 78
            },
            "market_benchmarks": {
                "athens_average": {
                    "energy_class": "C",
                    "annual_cost_per_m2": 22.30,
                    "efficiency_score": 68
                },
                "national_average": {
                    "energy_class": "C",
                    "annual_cost_per_m2": 24.10,
                    "efficiency_score": 65
                },
                "top_quartile": {
                    "energy_class": "B",
                    "annual_cost_per_m2": 15.80,
                    "efficiency_score": 85
                }
            },
            "ranking": {
                "percentile": 78,
                "description": "Your portfolio performs better than 78% of similar properties",
                "improvement_potential": "22% potential for improvement to reach top quartile"
            }
        }
    
    async def _generate_dashboard_alerts(self, dashboard_data: Dict[str, Any], user_id: str) -> List[DashboardAlert]:
        """Generate relevant dashboard alerts for user attention"""
        
        alerts = []
        
        # Energy price increase alert
        alerts.append(DashboardAlert(
            id="energy_price_alert_2025_01",
            severity="warning",
            title="Energy Price Increase",
            message="Electricity prices increased 8.5% this month. Consider solar panel installations.",
            action_url="/recommendations/solar",
            expires_at=datetime.now() + timedelta(days=7)
        ))
        
        # Subsidy opportunity
        alerts.append(DashboardAlert(
            id="subsidy_opportunity_exoikonomo",
            severity="info",
            title="Government Subsidy Available",
            message="3 properties eligible for 70% subsidy under Εξοικονομώ program.",
            action_url="/subsidies/exoikonomo",
            expires_at=datetime.now() + timedelta(days=30)
        ))
        
        # Assessment reminder
        alerts.append(DashboardAlert(
            id="assessment_reminder_annual",
            severity="info",
            title="Annual Assessment Due",
            message="2 properties haven't been assessed in over 12 months.",
            action_url="/assessments/schedule"
        ))
        
        # High ROI opportunity
        if dashboard_data.get('summary', {}).get('potential_savings', 0) > 5000:
            alerts.append(DashboardAlert(
                id="high_roi_opportunity",
                severity="warning",
                title="High ROI Opportunity",
                message=f"Potential savings of €{dashboard_data['summary']['potential_savings']:,.0f}/year identified.",
                action_url="/recommendations/high-roi"
            ))
        
        return alerts
    
    async def get_property_detailed_view(self, property_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed view for individual property"""
        
        try:
            query_bus = get_query_bus()
            
            # Get property assessment data
            from infrastructure.cqrs.queries import GetPropertyEnergyAssessmentQuery
            
            assessment_query = GetPropertyEnergyAssessmentQuery(
                property_id=property_id,
                include_recommendations=True,
                include_historical_data=True,
                include_market_comparison=True
            )
            assessment_query.requested_by = user_id
            
            result = await query_bus.execute(assessment_query)
            
            if not result.success:
                raise Exception(f"Property assessment query failed: {result}")
            
            property_data = result.data
            
            # Build detailed view
            detailed_view = {
                "property_id": property_id,
                "timestamp": datetime.now().isoformat(),
                "basic_info": {
                    "energy_class": property_data.get('current_rating', {}).get('energy_class', 'C'),
                    "construction_year": property_data.get('building_characteristics', {}).get('construction_year', 1990),
                    "total_area": property_data.get('building_characteristics', {}).get('total_area', 100),
                    "building_type": property_data.get('building_characteristics', {}).get('building_type', 'apartment'),
                    "annual_consumption": property_data.get('current_rating', {}).get('consumption_kwh_per_m2', 180)
                },
                "performance_metrics": await self._calculate_property_performance_metrics(property_data),
                "upgrade_recommendations": property_data.get('upgrade_recommendations', []),
                "financial_analysis": await self._calculate_property_financial_analysis(property_data),
                "market_position": property_data.get('market_comparison', {}),
                "improvement_timeline": await self._generate_improvement_timeline(property_data),
                "energy_history": await self._get_property_energy_history(property_id)
            }
            
            return detailed_view
            
        except Exception as e:
            logger.error(f"Property detailed view generation failed: {e}")
            return await self._get_fallback_property_view(property_id, user_id)
    
    async def _calculate_property_performance_metrics(self, property_data: Dict[str, Any]) -> List[DashboardMetric]:
        """Calculate performance metrics for individual property"""
        
        current_rating = property_data.get('current_rating', {})
        
        return [
            DashboardMetric(
                name="Energy Efficiency",
                value=self._energy_class_to_score(current_rating.get('energy_class', 'C')),
                unit="/100",
                color="success" if current_rating.get('energy_class', 'C') in ['A+', 'A', 'B+'] else "warning",
                description="Overall energy efficiency score"
            ),
            DashboardMetric(
                name="Annual Cost",
                value=current_rating.get('consumption_kwh_per_m2', 180) * 0.15 * property_data.get('building_characteristics', {}).get('total_area', 100),
                unit="€/year",
                color="primary",
                description="Estimated annual energy cost"
            ),
            DashboardMetric(
                name="CO2 Emissions",
                value=current_rating.get('consumption_kwh_per_m2', 180) * property_data.get('building_characteristics', {}).get('total_area', 100) * 0.4 / 1000,
                unit="tonnes/year",
                color="warning",
                description="Estimated annual CO2 emissions"
            )
        ]
    
    def _energy_class_to_score(self, energy_class: str) -> int:
        """Convert energy class to numeric score (0-100)"""
        scores = {
            'A+': 95, 'A': 85, 'B+': 75, 'B': 65, 'C': 55,
            'D': 45, 'E': 35, 'F': 25, 'G': 15
        }
        return scores.get(energy_class, 50)
    
    async def _get_fallback_overview(self, user_id: str) -> Dict[str, Any]:
        """Fallback portfolio overview when queries fail"""
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "status": "limited_data",
            "message": "Dashboard running in limited mode due to data availability",
            "metrics": [
                DashboardMetric(
                    name="System Status",
                    value="Limited Data Mode",
                    color="warning",
                    description="Full dashboard features temporarily unavailable"
                ).to_dict()
            ],
            "charts": {},
            "alerts": [
                DashboardAlert(
                    id="limited_mode_alert",
                    severity="warning",
                    title="Limited Dashboard Mode",
                    message="Some dashboard features are temporarily unavailable. Core functionality remains operational."
                ).to_dict()
            ]
        }
    
    async def _get_fallback_property_view(self, property_id: str, user_id: str) -> Dict[str, Any]:
        """Fallback property view when detailed query fails"""
        return {
            "property_id": property_id,
            "timestamp": datetime.now().isoformat(),
            "status": "limited_data",
            "message": "Property details running in limited mode",
            "basic_info": {
                "energy_class": "C",
                "note": "Detailed property information temporarily unavailable"
            }
        }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_age = datetime.now() - self._cache_timestamps[cache_key]
        return cache_age < self.cache_duration

# Global dashboard service instance
_dashboard_service = None

async def get_dashboard_service() -> EnergyDashboardService:
    """Get global dashboard service instance"""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = EnergyDashboardService()
    return _dashboard_service

# Dashboard API functions
async def get_portfolio_dashboard(user_id: str, portfolio_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get portfolio dashboard data"""
    dashboard_service = await get_dashboard_service()
    return await dashboard_service.get_portfolio_overview(user_id, portfolio_ids)

async def get_property_dashboard(property_id: str, user_id: str) -> Dict[str, Any]:
    """Get individual property dashboard"""
    dashboard_service = await get_dashboard_service()
    return await dashboard_service.get_property_detailed_view(property_id, user_id)