"""
📊 Energy Efficiency Benchmarking and Comparison Tools

Advanced benchmarking system for energy efficiency analysis:
- Property performance comparison against similar properties
- Regional and national energy efficiency benchmarks
- Industry standards and best practice identification
- ROI comparison for different improvement strategies
- Market positioning analysis for competitive advantage
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import numpy as np
from collections import defaultdict

from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.resilience import get_external_service_client
from monitoring.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of benchmarks"""
    PROPERTY_TYPE = "property_type"
    REGIONAL = "regional"
    NATIONAL = "national"
    SIMILAR_SIZE = "similar_size"
    SIMILAR_AGE = "similar_age"
    ENERGY_CLASS = "energy_class"
    INDUSTRY_STANDARD = "industry_standard"


class ComparisonMetric(Enum):
    """Metrics for comparison"""
    ENERGY_CONSUMPTION = "energy_consumption_kwh_m2"
    ENERGY_COST = "energy_cost_eur_m2"
    CARBON_EMISSIONS = "carbon_emissions_kg_m2"
    EFFICIENCY_SCORE = "efficiency_score"
    ROI_POTENTIAL = "roi_potential_years"
    IMPROVEMENT_COST = "improvement_cost_eur_m2"
    ENERGY_CLASS_NUMERIC = "energy_class_numeric"


@dataclass
class BenchmarkProperty:
    """Property data for benchmarking"""
    property_id: str
    property_type: str
    area_m2: float
    construction_year: int
    region: str
    energy_class: str
    energy_consumption_kwh_m2: float
    energy_cost_eur_m2: float
    carbon_emissions_kg_m2: float
    efficiency_score: float
    improvement_potential: Dict[str, Any]
    assessment_date: datetime


@dataclass
class BenchmarkStats:
    """Statistical benchmarks for a group"""
    count: int
    mean: float
    median: float
    std_dev: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float
    min_value: float
    max_value: float


@dataclass
class ComparisonResult:
    """Result of property comparison"""
    property_id: str
    benchmark_type: BenchmarkType
    metric: ComparisonMetric
    property_value: float
    benchmark_stats: BenchmarkStats
    percentile_rank: float  # Where this property ranks (0-100)
    performance_rating: str  # Excellent/Good/Average/Below Average/Poor
    improvement_potential: float
    similar_properties_count: int
    recommendations: List[str]


@dataclass
class MarketPosition:
    """Market positioning analysis"""
    property_id: str
    overall_rating: str
    market_segment: str  # Premium/Mid-market/Budget
    competitive_advantages: List[str]
    improvement_priorities: List[Dict[str, Any]]
    investment_opportunities: List[Dict[str, Any]]
    target_metrics: Dict[str, float]


class EnergyBenchmarkingEngine:
    """
    Main engine for energy efficiency benchmarking and comparison
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # Benchmark data cache
        self.benchmark_cache: Dict[str, Dict[str, BenchmarkStats]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        
        # Energy class conversion
        self.energy_class_scores = {
            'A+': 95, 'A': 85, 'B+': 75, 'B': 65, 'C+': 55, 
            'C': 45, 'D+': 35, 'D': 25, 'E+': 15, 'E': 10, 'F': 5, 'G': 0
        }
        
        # Greek regions for regional benchmarking
        self.greek_regions = {
            'attica': 'Αττική',
            'thessaloniki': 'Θεσσαλονίκη', 
            'crete': 'Κρήτη',
            'peloponnese': 'Πελοπόννησος',
            'central_greece': 'Στερεά Ελλάδα',
            'macedonia': 'Μακεδονία',
            'thrace': 'Θράκη',
            'aegean_islands': 'Νησιά Αιγαίου',
            'ionian_islands': 'Ιόνια Νησιά'
        }
        
        logger.info("Energy benchmarking engine initialized")
    
    async def benchmark_property(
        self,
        property_id: str,
        benchmark_types: Optional[List[BenchmarkType]] = None
    ) -> Dict[BenchmarkType, List[ComparisonResult]]:
        """
        Comprehensive benchmarking of a property
        
        Args:
            property_id: Property to benchmark
            benchmark_types: Types of benchmarks to perform (default: all)
            
        Returns:
            Benchmark results by type
        """
        # Default to all benchmark types if not specified
        if benchmark_types is None:
            benchmark_types = list(BenchmarkType)
        
        logger.info(f"Starting comprehensive benchmarking for property {property_id}")
        
        # Get property data
        property_data = await self._get_property_data(property_id)
        if not property_data:
            raise ValueError(f"Property {property_id} not found")
        
        results = {}
        
        # Perform each type of benchmarking
        for benchmark_type in benchmark_types:
            try:
                results[benchmark_type] = await self._perform_benchmark(
                    property_data, benchmark_type
                )
                logger.debug(f"Completed {benchmark_type.value} benchmarking for {property_id}")
            except Exception as e:
                logger.error(f"Failed {benchmark_type.value} benchmarking for {property_id}: {e}")
                results[benchmark_type] = []
        
        # Record benchmarking metrics
        metrics_collector = get_metrics_collector()
        if hasattr(metrics_collector, 'record_benchmarking'):
            metrics_collector.record_benchmarking(
                property_id,
                len(benchmark_types),
                sum(len(r) for r in results.values())
            )
        
        logger.info(f"Completed comprehensive benchmarking for property {property_id}")
        return results
    
    async def _get_property_data(self, property_id: str) -> Optional[BenchmarkProperty]:
        """Get property data for benchmarking"""
        try:
            results = await self.db_manager.execute_query(
                "get_property_benchmark_data",
                {"property_id": property_id}
            )
            
            if not results:
                return None
            
            row = results[0]
            
            return BenchmarkProperty(
                property_id=row['property_id'],
                property_type=row['property_type'],
                area_m2=row['area_m2'],
                construction_year=row['construction_year'],
                region=row['region'],
                energy_class=row['energy_class'],
                energy_consumption_kwh_m2=row['energy_consumption_kwh_m2'],
                energy_cost_eur_m2=row['energy_cost_eur_m2'],
                carbon_emissions_kg_m2=row['carbon_emissions_kg_m2'],
                efficiency_score=row['efficiency_score'],
                improvement_potential=row.get('improvement_potential', {}),
                assessment_date=row['assessment_date']
            )
            
        except Exception as e:
            logger.error(f"Failed to get property data for {property_id}: {e}")
            return None
    
    async def _perform_benchmark(
        self,
        property_data: BenchmarkProperty,
        benchmark_type: BenchmarkType
    ) -> List[ComparisonResult]:
        """Perform specific type of benchmarking"""
        
        # Get comparison group
        comparison_properties = await self._get_comparison_group(property_data, benchmark_type)
        
        if len(comparison_properties) < 5:  # Need minimum properties for meaningful comparison
            logger.warning(f"Insufficient properties for {benchmark_type.value} benchmark: {len(comparison_properties)}")
            return []
        
        results = []
        
        # Compare across different metrics
        metrics_to_compare = [
            ComparisonMetric.ENERGY_CONSUMPTION,
            ComparisonMetric.ENERGY_COST,
            ComparisonMetric.CARBON_EMISSIONS,
            ComparisonMetric.EFFICIENCY_SCORE,
            ComparisonMetric.ROI_POTENTIAL
        ]
        
        for metric in metrics_to_compare:
            try:
                result = await self._compare_metric(
                    property_data,
                    comparison_properties,
                    benchmark_type,
                    metric
                )
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to compare {metric.value} for {benchmark_type.value}: {e}")
        
        return results
    
    async def _get_comparison_group(
        self,
        property_data: BenchmarkProperty,
        benchmark_type: BenchmarkType
    ) -> List[BenchmarkProperty]:
        """Get group of properties for comparison"""
        
        # Build query filters based on benchmark type
        filters = {}
        
        if benchmark_type == BenchmarkType.PROPERTY_TYPE:
            filters['property_type'] = property_data.property_type
            
        elif benchmark_type == BenchmarkType.REGIONAL:
            filters['region'] = property_data.region
            
        elif benchmark_type == BenchmarkType.SIMILAR_SIZE:
            # +/- 30% area tolerance
            area_min = property_data.area_m2 * 0.7
            area_max = property_data.area_m2 * 1.3
            filters['area_min'] = area_min
            filters['area_max'] = area_max
            
        elif benchmark_type == BenchmarkType.SIMILAR_AGE:
            # +/- 10 years tolerance
            age_min = property_data.construction_year - 10
            age_max = property_data.construction_year + 10
            filters['construction_year_min'] = age_min
            filters['construction_year_max'] = age_max
            
        elif benchmark_type == BenchmarkType.ENERGY_CLASS:
            filters['energy_class'] = property_data.energy_class
        
        # Get properties from database
        try:
            results = await self.db_manager.execute_query(
                "get_benchmark_comparison_group",
                filters
            )
            
            comparison_properties = []
            for row in results:
                if row['property_id'] != property_data.property_id:  # Exclude the property itself
                    comparison_properties.append(BenchmarkProperty(
                        property_id=row['property_id'],
                        property_type=row['property_type'],
                        area_m2=row['area_m2'],
                        construction_year=row['construction_year'],
                        region=row['region'],
                        energy_class=row['energy_class'],
                        energy_consumption_kwh_m2=row['energy_consumption_kwh_m2'],
                        energy_cost_eur_m2=row['energy_cost_eur_m2'],
                        carbon_emissions_kg_m2=row['carbon_emissions_kg_m2'],
                        efficiency_score=row['efficiency_score'],
                        improvement_potential=row.get('improvement_potential', {}),
                        assessment_date=row['assessment_date']
                    ))
            
            return comparison_properties
            
        except Exception as e:
            logger.error(f"Failed to get comparison group for {benchmark_type.value}: {e}")
            return []
    
    async def _compare_metric(
        self,
        property_data: BenchmarkProperty,
        comparison_properties: List[BenchmarkProperty],
        benchmark_type: BenchmarkType,
        metric: ComparisonMetric
    ) -> Optional[ComparisonResult]:
        """Compare property against group for specific metric"""
        
        # Extract metric values
        property_value = self._get_metric_value(property_data, metric)
        comparison_values = [
            self._get_metric_value(prop, metric) 
            for prop in comparison_properties
        ]
        
        # Filter out None values
        comparison_values = [v for v in comparison_values if v is not None]
        
        if not comparison_values or property_value is None:
            return None
        
        # Calculate statistics
        benchmark_stats = BenchmarkStats(
            count=len(comparison_values),
            mean=statistics.mean(comparison_values),
            median=statistics.median(comparison_values),
            std_dev=statistics.stdev(comparison_values) if len(comparison_values) > 1 else 0,
            percentile_25=np.percentile(comparison_values, 25),
            percentile_75=np.percentile(comparison_values, 75),
            percentile_90=np.percentile(comparison_values, 90),
            percentile_95=np.percentile(comparison_values, 95),
            min_value=min(comparison_values),
            max_value=max(comparison_values)
        )
        
        # Calculate percentile rank
        percentile_rank = self._calculate_percentile_rank(property_value, comparison_values, metric)
        
        # Determine performance rating
        performance_rating = self._get_performance_rating(percentile_rank, metric)
        
        # Calculate improvement potential
        improvement_potential = self._calculate_improvement_potential(
            property_value, benchmark_stats, metric
        )
        
        # Generate recommendations
        recommendations = self._generate_metric_recommendations(
            metric, performance_rating, property_value, benchmark_stats
        )
        
        return ComparisonResult(
            property_id=property_data.property_id,
            benchmark_type=benchmark_type,
            metric=metric,
            property_value=property_value,
            benchmark_stats=benchmark_stats,
            percentile_rank=percentile_rank,
            performance_rating=performance_rating,
            improvement_potential=improvement_potential,
            similar_properties_count=len(comparison_properties),
            recommendations=recommendations
        )
    
    def _get_metric_value(self, property_data: BenchmarkProperty, metric: ComparisonMetric) -> Optional[float]:
        """Extract metric value from property data"""
        if metric == ComparisonMetric.ENERGY_CONSUMPTION:
            return property_data.energy_consumption_kwh_m2
        elif metric == ComparisonMetric.ENERGY_COST:
            return property_data.energy_cost_eur_m2
        elif metric == ComparisonMetric.CARBON_EMISSIONS:
            return property_data.carbon_emissions_kg_m2
        elif metric == ComparisonMetric.EFFICIENCY_SCORE:
            return property_data.efficiency_score
        elif metric == ComparisonMetric.ENERGY_CLASS_NUMERIC:
            return self.energy_class_scores.get(property_data.energy_class, 0)
        elif metric == ComparisonMetric.ROI_POTENTIAL:
            # Extract ROI from improvement potential data
            roi_data = property_data.improvement_potential.get('roi_analysis', {})
            return roi_data.get('best_roi_years')
        elif metric == ComparisonMetric.IMPROVEMENT_COST:
            cost_data = property_data.improvement_potential.get('cost_analysis', {})
            return cost_data.get('cost_per_m2')
        else:
            return None
    
    def _calculate_percentile_rank(
        self,
        value: float,
        comparison_values: List[float],
        metric: ComparisonMetric
    ) -> float:
        """Calculate where the property ranks percentile-wise"""
        
        # For metrics where lower is better (consumption, cost, emissions, ROI years)
        lower_is_better = metric in [
            ComparisonMetric.ENERGY_CONSUMPTION,
            ComparisonMetric.ENERGY_COST,
            ComparisonMetric.CARBON_EMISSIONS,
            ComparisonMetric.ROI_POTENTIAL,
            ComparisonMetric.IMPROVEMENT_COST
        ]
        
        if lower_is_better:
            # Count how many values are higher than this property's value
            better_count = sum(1 for v in comparison_values if v > value)
        else:
            # Count how many values are lower than this property's value  
            better_count = sum(1 for v in comparison_values if v < value)
        
        return (better_count / len(comparison_values)) * 100
    
    def _get_performance_rating(self, percentile_rank: float, metric: ComparisonMetric) -> str:
        """Convert percentile rank to performance rating"""
        if percentile_rank >= 90:
            return "Excellent"
        elif percentile_rank >= 75:
            return "Good"
        elif percentile_rank >= 50:
            return "Average"
        elif percentile_rank >= 25:
            return "Below Average"
        else:
            return "Poor"
    
    def _calculate_improvement_potential(
        self,
        property_value: float,
        benchmark_stats: BenchmarkStats,
        metric: ComparisonMetric
    ) -> float:
        """Calculate improvement potential compared to top performers"""
        
        # For metrics where lower is better
        lower_is_better = metric in [
            ComparisonMetric.ENERGY_CONSUMPTION,
            ComparisonMetric.ENERGY_COST,
            ComparisonMetric.CARBON_EMISSIONS,
            ComparisonMetric.ROI_POTENTIAL,
            ComparisonMetric.IMPROVEMENT_COST
        ]
        
        if lower_is_better:
            # Potential to improve to 25th percentile (best quarter)
            target = benchmark_stats.percentile_25
            if property_value > target:
                return ((property_value - target) / property_value) * 100
            else:
                return 0  # Already in top quarter
        else:
            # Potential to improve to 75th percentile (best quarter)
            target = benchmark_stats.percentile_75
            if property_value < target:
                return ((target - property_value) / property_value) * 100
            else:
                return 0  # Already in top quarter
    
    def _generate_metric_recommendations(
        self,
        metric: ComparisonMetric,
        performance_rating: str,
        property_value: float,
        benchmark_stats: BenchmarkStats
    ) -> List[str]:
        """Generate recommendations based on metric performance"""
        recommendations = []
        
        if performance_rating in ["Poor", "Below Average"]:
            if metric == ComparisonMetric.ENERGY_CONSUMPTION:
                recommendations.extend([
                    "Consider upgrading insulation to reduce energy consumption",
                    "Install high-efficiency heating/cooling systems",
                    "Implement smart energy management systems"
                ])
                
            elif metric == ComparisonMetric.ENERGY_COST:
                recommendations.extend([
                    "Explore renewable energy options (solar panels)",
                    "Switch to more efficient appliances",
                    "Consider time-of-use electricity tariffs"
                ])
                
            elif metric == ComparisonMetric.CARBON_EMISSIONS:
                recommendations.extend([
                    "Transition to renewable energy sources",
                    "Improve building envelope efficiency", 
                    "Install heat pump systems for heating/cooling"
                ])
                
            elif metric == ComparisonMetric.EFFICIENCY_SCORE:
                recommendations.extend([
                    "Comprehensive energy audit recommended",
                    "Multiple efficiency improvements needed",
                    "Consider phased improvement approach"
                ])
                
            elif metric == ComparisonMetric.ROI_POTENTIAL:
                recommendations.extend([
                    "Identify quick-win efficiency improvements",
                    "Apply for government subsidies to improve ROI",
                    "Consider energy performance contracting"
                ])
        
        elif performance_rating == "Average":
            recommendations.append(f"Property performs at market average for {metric.value.replace('_', ' ')}")
            recommendations.append("Targeted improvements could achieve above-average performance")
        
        elif performance_rating in ["Good", "Excellent"]:
            recommendations.append(f"Property performs well in {metric.value.replace('_', ' ')}")
            if performance_rating == "Good":
                recommendations.append("Fine-tuning could achieve excellent performance")
        
        return recommendations
    
    async def analyze_market_position(self, property_id: str) -> MarketPosition:
        """
        Comprehensive market positioning analysis
        
        Args:
            property_id: Property to analyze
            
        Returns:
            Market position analysis
        """
        logger.info(f"Analyzing market position for property {property_id}")
        
        # Get comprehensive benchmarking results
        benchmark_results = await self.benchmark_property(property_id)
        
        # Get property data
        property_data = await self._get_property_data(property_id)
        
        # Analyze overall performance
        overall_ratings = []
        competitive_advantages = []
        improvement_priorities = []
        
        for benchmark_type, results in benchmark_results.items():
            for result in results:
                overall_ratings.append(result.performance_rating)
                
                if result.performance_rating in ["Good", "Excellent"]:
                    competitive_advantages.append(
                        f"{result.metric.value.replace('_', ' ').title()} - {result.performance_rating} "
                        f"(Top {100-result.percentile_rank:.0f}%)"
                    )
                
                elif result.performance_rating in ["Poor", "Below Average"]:
                    improvement_priorities.append({
                        "metric": result.metric.value,
                        "performance": result.performance_rating,
                        "improvement_potential": result.improvement_potential,
                        "recommendations": result.recommendations[:2]  # Top 2 recommendations
                    })
        
        # Determine overall rating
        rating_scores = {"Excellent": 5, "Good": 4, "Average": 3, "Below Average": 2, "Poor": 1}
        if overall_ratings:
            avg_score = statistics.mean([rating_scores[rating] for rating in overall_ratings])
            overall_rating = min(rating_scores.keys(), key=lambda x: abs(rating_scores[x] - avg_score))
        else:
            overall_rating = "Unknown"
        
        # Determine market segment
        market_segment = self._determine_market_segment(property_data, benchmark_results)
        
        # Identify investment opportunities
        investment_opportunities = self._identify_investment_opportunities(
            property_data, benchmark_results
        )
        
        # Set target metrics
        target_metrics = self._calculate_target_metrics(benchmark_results)
        
        return MarketPosition(
            property_id=property_id,
            overall_rating=overall_rating,
            market_segment=market_segment,
            competitive_advantages=competitive_advantages,
            improvement_priorities=improvement_priorities[:5],  # Top 5 priorities
            investment_opportunities=investment_opportunities,
            target_metrics=target_metrics
        )
    
    def _determine_market_segment(
        self,
        property_data: BenchmarkProperty,
        benchmark_results: Dict[BenchmarkType, List[ComparisonResult]]
    ) -> str:
        """Determine market segment based on performance and characteristics"""
        
        # Count excellent and good performances
        performance_counts = {"Excellent": 0, "Good": 0, "Average": 0, "Below Average": 0, "Poor": 0}
        
        for results in benchmark_results.values():
            for result in results:
                performance_counts[result.performance_rating] += 1
        
        total_metrics = sum(performance_counts.values())
        if total_metrics == 0:
            return "Unknown"
        
        excellent_pct = performance_counts["Excellent"] / total_metrics
        good_pct = performance_counts["Good"] / total_metrics
        
        if excellent_pct >= 0.5 or (excellent_pct + good_pct) >= 0.8:
            return "Premium"
        elif (excellent_pct + good_pct) >= 0.4:
            return "Mid-market"
        else:
            return "Budget"
    
    def _identify_investment_opportunities(
        self,
        property_data: BenchmarkProperty,
        benchmark_results: Dict[BenchmarkType, List[ComparisonResult]]
    ) -> List[Dict[str, Any]]:
        """Identify investment opportunities with high ROI potential"""
        opportunities = []
        
        # Analyze improvement potential across metrics
        high_potential_metrics = []
        for results in benchmark_results.values():
            for result in results:
                if (result.improvement_potential > 20 and 
                    result.performance_rating in ["Poor", "Below Average"]):
                    high_potential_metrics.append(result)
        
        # Sort by improvement potential
        high_potential_metrics.sort(key=lambda x: x.improvement_potential, reverse=True)
        
        # Generate investment opportunities
        for result in high_potential_metrics[:3]:  # Top 3 opportunities
            if result.metric == ComparisonMetric.ENERGY_CONSUMPTION:
                opportunities.append({
                    "type": "Energy Efficiency Upgrade",
                    "potential_savings": f"{result.improvement_potential:.1f}% reduction in energy consumption",
                    "investment_areas": ["Insulation", "HVAC Systems", "Windows"],
                    "estimated_payback": "5-8 years",
                    "government_subsidies": "Available through Εξοικονομώ programs"
                })
                
            elif result.metric == ComparisonMetric.CARBON_EMISSIONS:
                opportunities.append({
                    "type": "Carbon Reduction Initiative", 
                    "potential_savings": f"{result.improvement_potential:.1f}% reduction in carbon footprint",
                    "investment_areas": ["Solar Panels", "Heat Pumps", "Smart Controls"],
                    "estimated_payback": "7-12 years",
                    "additional_benefits": "Green certification, ESG compliance"
                })
        
        return opportunities
    
    def _calculate_target_metrics(
        self,
        benchmark_results: Dict[BenchmarkType, List[ComparisonResult]]
    ) -> Dict[str, float]:
        """Calculate target metrics for improvement"""
        targets = {}
        
        for results in benchmark_results.values():
            for result in results:
                metric_key = result.metric.value
                
                # Set target as 75th percentile (top quarter performance)
                if result.metric in [ComparisonMetric.ENERGY_CONSUMPTION, ComparisonMetric.ENERGY_COST, 
                                   ComparisonMetric.CARBON_EMISSIONS]:
                    targets[metric_key] = result.benchmark_stats.percentile_25  # Lower is better
                else:
                    targets[metric_key] = result.benchmark_stats.percentile_75  # Higher is better
        
        return targets
    
    async def get_regional_benchmarks(self, region: str) -> Dict[str, BenchmarkStats]:
        """Get regional benchmark statistics"""
        cache_key = f"regional_{region}"
        
        # Check cache
        if (cache_key in self.benchmark_cache and 
            cache_key in self.cache_expiry and
            datetime.now() < self.cache_expiry[cache_key]):
            return self.benchmark_cache[cache_key]
        
        try:
            # Get regional data from database
            results = await self.db_manager.execute_query(
                "get_regional_benchmarks",
                {"region": region}
            )
            
            if not results:
                return {}
            
            # Calculate statistics for each metric
            regional_stats = {}
            
            metrics_data = defaultdict(list)
            for row in results:
                metrics_data['energy_consumption'].append(row['energy_consumption_kwh_m2'])
                metrics_data['energy_cost'].append(row['energy_cost_eur_m2'])
                metrics_data['carbon_emissions'].append(row['carbon_emissions_kg_m2'])
                metrics_data['efficiency_score'].append(row['efficiency_score'])
            
            for metric_name, values in metrics_data.items():
                if values:
                    regional_stats[metric_name] = BenchmarkStats(
                        count=len(values),
                        mean=statistics.mean(values),
                        median=statistics.median(values),
                        std_dev=statistics.stdev(values) if len(values) > 1 else 0,
                        percentile_25=np.percentile(values, 25),
                        percentile_75=np.percentile(values, 75),
                        percentile_90=np.percentile(values, 90),
                        percentile_95=np.percentile(values, 95),
                        min_value=min(values),
                        max_value=max(values)
                    )
            
            # Cache results
            self.benchmark_cache[cache_key] = regional_stats
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            return regional_stats
            
        except Exception as e:
            logger.error(f"Failed to get regional benchmarks for {region}: {e}")
            return {}
    
    async def generate_benchmark_report(
        self,
        property_id: str,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive benchmarking report"""
        
        # Get all benchmark data
        benchmark_results = await self.benchmark_property(property_id)
        market_position = await self.analyze_market_position(property_id)
        property_data = await self._get_property_data(property_id)
        
        # Create comprehensive report
        report = {
            "property_id": property_id,
            "report_generated": datetime.now().isoformat(),
            "property_summary": {
                "type": property_data.property_type,
                "area_m2": property_data.area_m2,
                "construction_year": property_data.construction_year,
                "region": property_data.region,
                "energy_class": property_data.energy_class,
                "efficiency_score": property_data.efficiency_score
            },
            "market_position": {
                "overall_rating": market_position.overall_rating,
                "market_segment": market_position.market_segment,
                "competitive_advantages": market_position.competitive_advantages
            },
            "benchmark_results": {},
            "performance_summary": {},
            "investment_opportunities": market_position.investment_opportunities,
            "target_metrics": market_position.target_metrics
        }
        
        # Add detailed benchmark results
        for benchmark_type, results in benchmark_results.items():
            report["benchmark_results"][benchmark_type.value] = [
                {
                    "metric": result.metric.value,
                    "property_value": result.property_value,
                    "percentile_rank": result.percentile_rank,
                    "performance_rating": result.performance_rating,
                    "improvement_potential": result.improvement_potential,
                    "similar_properties": result.similar_properties_count,
                    "recommendations": result.recommendations if include_recommendations else []
                }
                for result in results
            ]
        
        # Generate performance summary
        all_results = [result for results in benchmark_results.values() for result in results]
        if all_results:
            performance_summary = {
                "total_metrics_analyzed": len(all_results),
                "excellent_performance": sum(1 for r in all_results if r.performance_rating == "Excellent"),
                "good_performance": sum(1 for r in all_results if r.performance_rating == "Good"),
                "average_performance": sum(1 for r in all_results if r.performance_rating == "Average"),
                "below_average_performance": sum(1 for r in all_results if r.performance_rating == "Below Average"),
                "poor_performance": sum(1 for r in all_results if r.performance_rating == "Poor"),
                "average_percentile_rank": statistics.mean([r.percentile_rank for r in all_results]),
                "improvement_priorities": len(market_position.improvement_priorities)
            }
            report["performance_summary"] = performance_summary
        
        return report


# Global benchmarking engine instance
_benchmarking_engine = None


def get_benchmarking_engine() -> EnergyBenchmarkingEngine:
    """Get or create global benchmarking engine"""
    global _benchmarking_engine
    if _benchmarking_engine is None:
        _benchmarking_engine = EnergyBenchmarkingEngine()
    return _benchmarking_engine


# Convenience functions
async def benchmark_property_comprehensive(property_id: str) -> Dict[str, Any]:
    """Comprehensive property benchmarking"""
    engine = get_benchmarking_engine()
    return await engine.generate_benchmark_report(property_id)


async def get_market_position_analysis(property_id: str) -> MarketPosition:
    """Get market positioning analysis"""
    engine = get_benchmarking_engine()
    return await engine.analyze_market_position(property_id)


async def get_regional_performance_stats(region: str) -> Dict[str, BenchmarkStats]:
    """Get regional performance statistics"""
    engine = get_benchmarking_engine()
    return await engine.get_regional_benchmarks(region)