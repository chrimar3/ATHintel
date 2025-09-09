"""
Investment Analysis Service - Core Business Logic

This service contains the pure business logic for investment analysis,
independent of external dependencies and frameworks.
"""

from typing import List, Dict, Optional, Tuple, Set, Any
from decimal import Decimal
from datetime import datetime, date, timedelta
import asyncio
from dataclasses import dataclass
import numpy as np
from scipy import stats
from collections import defaultdict

from ..domain.entities import (
    Property, Investment, Portfolio, MarketSegment, 
    PropertyType, InvestmentRisk, ListingType, EnergyClass
)
from ..ports.repositories import PropertyRepository, InvestmentRepository, CacheRepository
from ..ports.services import MarketDataService, AnalyticsService


@dataclass
class InvestmentCriteria:
    """Investment search and filtering criteria"""
    max_budget: Optional[Decimal] = None
    min_budget: Optional[Decimal] = None
    target_yield: Optional[float] = None
    min_sqm: Optional[float] = None
    max_sqm: Optional[float] = None
    neighborhoods: Optional[Set[str]] = None
    property_types: Optional[Set[PropertyType]] = None
    max_year_built: Optional[int] = None
    min_energy_class: Optional[EnergyClass] = None
    risk_tolerance: InvestmentRisk = InvestmentRisk.MEDIUM


@dataclass
class MarketAnalysis:
    """Market analysis results"""
    total_properties: int
    avg_price: Decimal
    median_price: Decimal
    avg_price_per_sqm: Decimal
    price_trend: str  # "up", "down", "stable"
    market_activity: float  # 0-10 score
    investment_opportunities: int
    risk_level: InvestmentRisk
    
    # Neighborhood breakdown
    neighborhood_stats: Dict[str, Dict[str, float]]
    
    # Price distribution
    price_distribution: Dict[str, int]  # price ranges
    
    # Key insights
    insights: List[str]


class InvestmentAnalysisService:
    """
    Core investment analysis service implementing sophisticated
    real estate investment evaluation algorithms
    """
    
    def __init__(
        self,
        property_repo: PropertyRepository,
        investment_repo: InvestmentRepository,
        cache_repo: CacheRepository,
        market_service: MarketDataService,
        analytics_service: AnalyticsService
    ):
        self.property_repo = property_repo
        self.investment_repo = investment_repo
        self.cache_repo = cache_repo
        self.market_service = market_service
        self.analytics_service = analytics_service
    
    async def analyze_property(
        self, 
        property: Property,
        market_context: Optional[Dict] = None
    ) -> Investment:
        """
        Comprehensive property investment analysis
        """
        # Get market context if not provided
        if not market_context:
            market_context = await self._get_market_context(property.location.neighborhood)
        
        # Calculate investment score using multiple factors
        investment_score = await self._calculate_investment_score(property, market_context)
        
        # Estimate rental yield
        rental_yield = await self._estimate_rental_yield(property, market_context)
        
        # Project ROI for 5 years
        roi_5y = await self._calculate_roi_projection(property, rental_yield, 5)
        
        # Assess risk level
        risk_level = self._assess_risk_level(property, market_context)
        
        # Calculate total investment needed
        total_cost = self._calculate_total_investment_cost(property)
        
        # Get neighborhood ranking
        neighborhood_rank = await self._get_neighborhood_ranking(property.location.neighborhood)
        
        # Generate financing options
        financing_options = self._generate_financing_options(property)
        
        # Create investment analysis
        investment = Investment(
            property=property,
            investment_score=investment_score,
            estimated_rental_yield=rental_yield,
            roi_projection_5y=roi_5y,
            risk_level=risk_level,
            neighborhood_rank=neighborhood_rank,
            total_investment_needed=total_cost,
            financing_options=financing_options,
            holding_period_rec=self._recommend_holding_period(property, market_context)
        )
        
        return investment
    
    async def find_investment_opportunities(
        self,
        criteria: InvestmentCriteria,
        limit: int = 50
    ) -> List[Investment]:
        """
        Find investment opportunities matching criteria
        """
        # Build property filters from criteria
        filters = self._build_property_filters(criteria)
        
        # Get properties matching criteria
        properties = await self.property_repo.find_by_criteria(filters)
        
        # Analyze each property for investment potential
        investments = []
        market_contexts = {}
        
        for prop in properties[:limit * 2]:  # Get more than needed for filtering
            try:
                # Cache market context by neighborhood
                neighborhood = prop.location.neighborhood
                if neighborhood not in market_contexts:
                    market_contexts[neighborhood] = await self._get_market_context(neighborhood)
                
                investment = await self.analyze_property(prop, market_contexts[neighborhood])
                
                # Filter by investment criteria
                if self._matches_investment_criteria(investment, criteria):
                    investments.append(investment)
                
            except Exception as e:
                # Log error but continue with other properties
                print(f"Error analyzing property {prop.property_id}: {e}")
                continue
        
        # Sort by investment score and return top opportunities
        investments.sort(key=lambda x: x.investment_score, reverse=True)
        return investments[:limit]
    
    async def analyze_market_segment(self, neighborhood: str) -> MarketSegment:
        """
        Comprehensive market segment analysis for a neighborhood
        """
        # Get all properties in neighborhood
        properties = await self.property_repo.find_by_neighborhood(neighborhood)
        
        if not properties:
            raise ValueError(f"No properties found for neighborhood: {neighborhood}")
        
        # Calculate basic statistics
        prices = [float(p.price) for p in properties]
        sqm_values = [p.sqm for p in properties if p.sqm]
        prices_per_sqm = [float(p.price_per_sqm) for p in properties if p.price_per_sqm]
        
        # Property type analysis
        type_counts = defaultdict(int)
        for prop in properties:
            type_counts[prop.property_type] += 1
        dominant_type = max(type_counts, key=type_counts.get)
        
        # Energy efficiency analysis
        energy_scores = []
        energy_map = {
            EnergyClass.A_PLUS: 10, EnergyClass.A: 9, EnergyClass.B_PLUS: 8,
            EnergyClass.B: 7, EnergyClass.C: 6, EnergyClass.D: 5,
            EnergyClass.E: 4, EnergyClass.F: 3, EnergyClass.G: 2
        }
        for prop in properties:
            if prop.energy_class:
                energy_scores.append(energy_map.get(prop.energy_class, 5))
        
        avg_energy_score = np.mean(energy_scores) if energy_scores else 5.0
        
        # Investment analysis
        investment_scores = []
        yields = []
        
        for prop in properties[:50]:  # Sample for performance
            try:
                investment = await self.analyze_property(prop)
                investment_scores.append(investment.investment_score)
                if investment.estimated_rental_yield:
                    yields.append(investment.estimated_rental_yield)
            except Exception:
                continue
        
        # Market activity and liquidity analysis
        market_activity = await self._calculate_market_activity(neighborhood, properties)
        liquidity_score = await self._calculate_liquidity_score(neighborhood, properties)
        
        # Price volatility
        price_volatility = np.std(prices) / np.mean(prices) if prices else 0
        
        # Market maturity assessment
        market_maturity = self._assess_market_maturity(properties, market_activity)
        
        # Create market segment
        segment = MarketSegment(
            segment_id=f"{neighborhood.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}",
            neighborhood=neighborhood,
            property_count=len(properties),
            avg_price=Decimal(str(round(np.mean(prices)))),
            median_price=Decimal(str(round(np.median(prices)))),
            avg_price_per_sqm=Decimal(str(round(np.mean(prices_per_sqm)))),
            price_std_dev=Decimal(str(round(np.std(prices)))),
            avg_sqm=float(np.mean(sqm_values)) if sqm_values else 0,
            dominant_property_type=dominant_type,
            energy_efficiency_score=avg_energy_score,
            avg_investment_score=np.mean(investment_scores) if investment_scores else 50.0,
            estimated_avg_yield=np.mean(yields) if yields else 3.5,
            market_activity_score=market_activity,
            price_volatility=price_volatility,
            market_maturity=market_maturity,
            liquidity_score=liquidity_score
        )
        
        return segment
    
    async def perform_market_analysis(
        self,
        neighborhoods: Optional[List[str]] = None
    ) -> MarketAnalysis:
        """
        Comprehensive market analysis across neighborhoods
        """
        # Get all properties if no specific neighborhoods
        if not neighborhoods:
            properties = await self.property_repo.find_all()
            # Extract unique neighborhoods
            neighborhoods = list(set(p.location.neighborhood for p in properties))
        else:
            properties = []
            for neighborhood in neighborhoods:
                props = await self.property_repo.find_by_neighborhood(neighborhood)
                properties.extend(props)
        
        if not properties:
            raise ValueError("No properties found for analysis")
        
        # Basic statistics
        prices = [float(p.price) for p in properties]
        prices_per_sqm = [float(p.price_per_sqm) for p in properties if p.price_per_sqm]
        
        avg_price = Decimal(str(round(np.mean(prices))))
        median_price = Decimal(str(round(np.median(prices))))
        avg_price_per_sqm = Decimal(str(round(np.mean(prices_per_sqm))))
        
        # Neighborhood breakdown
        neighborhood_stats = {}
        for neighborhood in neighborhoods:
            neighborhood_props = [p for p in properties if p.location.neighborhood == neighborhood]
            if neighborhood_props:
                neighborhood_prices = [float(p.price) for p in neighborhood_props]
                neighborhood_stats[neighborhood] = {
                    'count': len(neighborhood_props),
                    'avg_price': float(np.mean(neighborhood_prices)),
                    'median_price': float(np.median(neighborhood_prices)),
                    'price_per_sqm': float(np.mean([float(p.price_per_sqm) for p in neighborhood_props if p.price_per_sqm]))
                }
        
        # Price distribution analysis
        price_ranges = {
            "0-100K": 0, "100K-200K": 0, "200K-300K": 0, 
            "300K-500K": 0, "500K-1M": 0, "1M+": 0
        }
        
        for price in prices:
            if price < 100000:
                price_ranges["0-100K"] += 1
            elif price < 200000:
                price_ranges["100K-200K"] += 1
            elif price < 300000:
                price_ranges["200K-300K"] += 1
            elif price < 500000:
                price_ranges["300K-500K"] += 1
            elif price < 1000000:
                price_ranges["500K-1M"] += 1
            else:
                price_ranges["1M+"] += 1
        
        # Market trend analysis
        price_trend = await self._analyze_price_trend(properties)
        
        # Market activity score
        total_activity = 0
        for neighborhood in neighborhoods:
            neighborhood_props = [p for p in properties if p.location.neighborhood == neighborhood]
            activity = await self._calculate_market_activity(neighborhood, neighborhood_props)
            total_activity += activity
        
        avg_market_activity = total_activity / len(neighborhoods) if neighborhoods else 5.0
        
        # Count high-potential investments
        investment_opportunities = len([p for p in properties if self._is_high_potential_investment(p)])
        
        # Overall risk assessment
        overall_risk = self._assess_overall_market_risk(properties, avg_market_activity)
        
        # Generate insights
        insights = self._generate_market_insights(
            properties, neighborhood_stats, price_trend, avg_market_activity
        )
        
        return MarketAnalysis(
            total_properties=len(properties),
            avg_price=avg_price,
            median_price=median_price,
            avg_price_per_sqm=avg_price_per_sqm,
            price_trend=price_trend,
            market_activity=avg_market_activity,
            investment_opportunities=investment_opportunities,
            risk_level=overall_risk,
            neighborhood_stats=neighborhood_stats,
            price_distribution=price_ranges,
            insights=insights
        )
    
    # Private helper methods
    
    async def _get_market_context(self, neighborhood: str) -> Dict:
        """Get market context for neighborhood with caching"""
        cache_key = f"market_context:{neighborhood}"
        
        # Try cache first
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return cached
        
        # Get neighborhood properties for context
        properties = await self.property_repo.find_by_neighborhood(neighborhood)
        
        if not properties:
            return {}
        
        prices_per_sqm = [float(p.price_per_sqm) for p in properties if p.price_per_sqm]
        context = {
            'avg_price_per_sqm': np.mean(prices_per_sqm) if prices_per_sqm else 0,
            'property_count': len(properties),
            'price_volatility': np.std(prices_per_sqm) / np.mean(prices_per_sqm) if prices_per_sqm else 0,
        }
        
        # Cache for 1 hour
        await self.cache_repo.set(cache_key, context, 3600)
        return context
    
    async def _calculate_investment_score(
        self, 
        property: Property, 
        market_context: Dict
    ) -> float:
        """Calculate comprehensive investment score using ML if available"""
        try:
            # Try ML-based scoring first
            ml_score = await self.analytics_service.calculate_investment_score(
                property, market_context
            )
            return ml_score
        except Exception:
            # Fallback to rule-based scoring
            return property.calculate_investment_score(market_context)
    
    async def _estimate_rental_yield(
        self, 
        property: Property, 
        market_context: Dict
    ) -> Optional[float]:
        """Estimate rental yield using market data"""
        try:
            # Get rental yield from market service
            yield_data = await self.market_service.get_rental_yield_estimates(
                property.location.neighborhood,
                property.property_type
            )
            
            base_yield = yield_data.get('average_yield', 4.0)
            
            # Adjust based on property characteristics
            adjustments = 0
            
            # Size adjustment
            if property.sqm:
                if 50 <= property.sqm <= 120:  # Optimal size
                    adjustments += 0.2
                elif property.sqm < 30:  # Too small
                    adjustments -= 0.3
                elif property.sqm > 200:  # Too large
                    adjustments -= 0.2
            
            # Energy class adjustment
            if property.energy_class in [EnergyClass.A_PLUS, EnergyClass.A]:
                adjustments += 0.3
            elif property.energy_class in [EnergyClass.F, EnergyClass.G]:
                adjustments -= 0.2
            
            # Floor adjustment
            if property.floor is not None:
                if 1 <= property.floor <= 3:
                    adjustments += 0.1
                elif property.floor >= 5:
                    adjustments -= 0.1
            
            return max(1.0, base_yield + adjustments)
            
        except Exception:
            # Fallback to entity method
            return property.estimate_rental_yield(market_context)
    
    async def _calculate_roi_projection(
        self,
        property: Property,
        rental_yield: Optional[float],
        years: int
    ) -> Optional[float]:
        """Calculate ROI projection considering both rental income and appreciation"""
        if not rental_yield:
            return None
        
        try:
            # Get neighborhood trends for appreciation estimate
            trends = await self.market_service.get_neighborhood_trends(
                property.location.neighborhood, "5y"
            )
            
            annual_appreciation = trends.get('annual_appreciation', 0.03)  # Default 3%
            
            # Calculate compound annual returns
            rental_return = rental_yield / 100
            total_annual_return = rental_return + annual_appreciation
            
            # Compound for specified years
            total_return = ((1 + total_annual_return) ** years - 1) * 100
            
            return round(total_return, 2)
            
        except Exception:
            # Simple calculation fallback
            if rental_yield:
                appreciation = 0.03  # Assume 3% annual appreciation
                total_annual = (rental_yield / 100) + appreciation
                return round(((1 + total_annual) ** years - 1) * 100, 2)
            return None
    
    def _assess_risk_level(
        self, 
        property: Property, 
        market_context: Dict
    ) -> InvestmentRisk:
        """Assess investment risk level"""
        risk_score = 50  # Base score
        
        # Price volatility risk
        volatility = market_context.get('price_volatility', 0.2)
        if volatility > 0.3:
            risk_score += 15
        elif volatility < 0.1:
            risk_score -= 10
        
        # Liquidity risk (small markets)
        property_count = market_context.get('property_count', 100)
        if property_count < 20:
            risk_score += 20
        elif property_count > 100:
            risk_score -= 10
        
        # Property-specific risks
        if property.year_built and (datetime.now().year - property.year_built) > 40:
            risk_score += 10
        
        if property.energy_class in [EnergyClass.F, EnergyClass.G]:
            risk_score += 15
        
        # Price risk (overpriced properties)
        avg_price_per_sqm = market_context.get('avg_price_per_sqm', 0)
        if avg_price_per_sqm > 0 and property.price_per_sqm:
            price_ratio = float(property.price_per_sqm) / avg_price_per_sqm
            if price_ratio > 1.3:  # 30% above market
                risk_score += 20
            elif price_ratio < 0.7:  # 30% below market (potential issues)
                risk_score += 10
        
        # Convert score to risk level
        if risk_score >= 80:
            return InvestmentRisk.VERY_HIGH
        elif risk_score >= 65:
            return InvestmentRisk.HIGH
        elif risk_score >= 35:
            return InvestmentRisk.MEDIUM
        elif risk_score >= 20:
            return InvestmentRisk.LOW
        else:
            return InvestmentRisk.VERY_LOW
    
    def _calculate_total_investment_cost(self, property: Property) -> Decimal:
        """Calculate total investment cost including all fees"""
        base_price = property.price
        
        # Transaction costs in Greece (typical 10-12%)
        # - Transfer tax: 3.09%
        # - Notary fees: 1-2%
        # - Lawyer fees: 1-2%
        # - Real estate agent: 2-4%
        # - Other fees: 1-2%
        
        transaction_cost_rate = Decimal("0.11")  # 11% total
        transaction_costs = base_price * transaction_cost_rate
        
        # Renovation/improvement costs (if property is old)
        renovation_costs = Decimal("0")
        if property.year_built and (datetime.now().year - property.year_built) > 30:
            # Estimate renovation needs
            if property.energy_class in [EnergyClass.E, EnergyClass.F, EnergyClass.G]:
                # Energy upgrade needed
                renovation_costs = base_price * Decimal("0.05")  # 5% for energy upgrade
        
        return base_price + transaction_costs + renovation_costs
    
    async def _get_neighborhood_ranking(self, neighborhood: str) -> Optional[int]:
        """Get neighborhood ranking compared to others"""
        # This would typically use cached rankings or call market service
        # For now, return a placeholder
        rankings = {
            "Kolonaki": 1, "Kifisia": 2, "Glyfada": 3, "Marousi": 4,
            "Nea Smyrni": 5, "Koukaki": 6, "Exarchia": 7, "Pagrati": 8,
            "Kipseli": 9, "Patisia": 10
        }
        return rankings.get(neighborhood)
    
    def _generate_financing_options(self, property: Property) -> List[str]:
        """Generate potential financing options"""
        options = []
        price = float(property.price)
        
        # Standard mortgage (80% LTV typical in Greece)
        down_payment = price * 0.2
        options.append(f"Standard mortgage: €{down_payment:,.0f} down payment (20%)")
        
        # High LTV options
        if price < 300000:  # More options for lower-priced properties
            high_ltv_down = price * 0.1
            options.append(f"High-LTV mortgage: €{high_ltv_down:,.0f} down payment (10%)")
        
        # Investment loan
        if property.listing_type == ListingType.SALE:
            investment_down = price * 0.3
            options.append(f"Investment loan: €{investment_down:,.0f} down payment (30%)")
        
        # Cash purchase
        options.append(f"Cash purchase: €{price:,.0f} total")
        
        return options
    
    def _recommend_holding_period(
        self, 
        property: Property, 
        market_context: Dict
    ) -> Optional[int]:
        """Recommend optimal holding period"""
        # Base holding period
        base_period = 5
        
        # Adjust based on market conditions
        volatility = market_context.get('price_volatility', 0.2)
        if volatility > 0.3:
            base_period += 2  # Hold longer in volatile markets
        
        # Adjust based on property characteristics
        if property.year_built and (datetime.now().year - property.year_built) < 10:
            base_period -= 1  # New properties can be sold sooner
        
        if property.energy_class in [EnergyClass.A_PLUS, EnergyClass.A]:
            base_period -= 1  # Energy-efficient properties in demand
        
        return max(3, min(10, base_period))  # Between 3-10 years
    
    def _build_property_filters(self, criteria: InvestmentCriteria) -> Dict[str, Any]:
        """Build property repository filters from investment criteria"""
        filters = {}
        
        if criteria.min_budget:
            filters['min_price'] = criteria.min_budget
        
        if criteria.max_budget:
            filters['max_price'] = criteria.max_budget
        
        if criteria.min_sqm:
            filters['min_sqm'] = criteria.min_sqm
            
        if criteria.max_sqm:
            filters['max_sqm'] = criteria.max_sqm
        
        if criteria.neighborhoods:
            filters['neighborhoods'] = list(criteria.neighborhoods)
        
        if criteria.property_types:
            filters['property_types'] = list(criteria.property_types)
        
        if criteria.max_year_built:
            filters['min_year_built'] = criteria.max_year_built
        
        return filters
    
    def _matches_investment_criteria(
        self, 
        investment: Investment, 
        criteria: InvestmentCriteria
    ) -> bool:
        """Check if investment matches criteria"""
        # Yield requirement
        if criteria.target_yield and investment.estimated_rental_yield:
            if investment.estimated_rental_yield < criteria.target_yield:
                return False
        
        # Risk tolerance
        risk_order = {
            InvestmentRisk.VERY_LOW: 1,
            InvestmentRisk.LOW: 2,
            InvestmentRisk.MEDIUM: 3,
            InvestmentRisk.HIGH: 4,
            InvestmentRisk.VERY_HIGH: 5
        }
        
        if risk_order[investment.risk_level] > risk_order[criteria.risk_tolerance]:
            return False
        
        # Energy class minimum
        if criteria.min_energy_class and investment.property.energy_class:
            energy_order = {
                EnergyClass.G: 1, EnergyClass.F: 2, EnergyClass.E: 3,
                EnergyClass.D: 4, EnergyClass.C: 5, EnergyClass.B: 6,
                EnergyClass.B_PLUS: 7, EnergyClass.A: 8, EnergyClass.A_PLUS: 9
            }
            
            min_order = energy_order.get(criteria.min_energy_class, 1)
            prop_order = energy_order.get(investment.property.energy_class, 1)
            
            if prop_order < min_order:
                return False
        
        return True
    
    async def _calculate_market_activity(
        self, 
        neighborhood: str, 
        properties: List[Property]
    ) -> float:
        """Calculate market activity score (0-10)"""
        # Base activity on number of properties
        property_count = len(properties)
        
        # Activity factors
        activity_score = 5.0  # Base score
        
        # Property count impact
        if property_count > 100:
            activity_score += 2
        elif property_count > 50:
            activity_score += 1
        elif property_count < 10:
            activity_score -= 2
        
        # Recent listings (proxy: properties with recent timestamps)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_properties = [
            p for p in properties 
            if p.timestamp and p.timestamp > recent_cutoff
        ]
        
        if recent_properties:
            recent_ratio = len(recent_properties) / len(properties)
            activity_score += recent_ratio * 3
        
        return max(0, min(10, activity_score))
    
    async def _calculate_liquidity_score(
        self,
        neighborhood: str,
        properties: List[Property]
    ) -> float:
        """Calculate market liquidity score (0-1)"""
        # Base liquidity on property count and diversity
        property_count = len(properties)
        
        if property_count == 0:
            return 0.0
        
        # Property type diversity
        property_types = set(p.property_type for p in properties)
        type_diversity = len(property_types) / len(PropertyType)
        
        # Price range diversity
        prices = [float(p.price) for p in properties]
        price_cv = np.std(prices) / np.mean(prices) if prices else 0
        
        # Size diversity
        sqm_values = [p.sqm for p in properties if p.sqm]
        size_diversity = len(set(int(sqm/10)*10 for sqm in sqm_values)) / 20 if sqm_values else 0
        
        # Combine factors
        liquidity_score = (
            min(1.0, property_count / 50) * 0.4 +  # Volume
            type_diversity * 0.3 +                  # Type diversity
            min(1.0, price_cv) * 0.2 +             # Price diversity
            size_diversity * 0.1                    # Size diversity
        )
        
        return max(0, min(1, liquidity_score))
    
    def _assess_market_maturity(
        self,
        properties: List[Property],
        market_activity: float
    ) -> str:
        """Assess market maturity level"""
        property_count = len(properties)
        
        # Age distribution
        current_year = datetime.now().year
        ages = []
        for prop in properties:
            if prop.year_built:
                ages.append(current_year - prop.year_built)
        
        avg_age = np.mean(ages) if ages else 50
        
        # Determine maturity
        if property_count < 20 or avg_age < 15:
            return "emerging"
        elif property_count < 50 or market_activity < 4:
            return "developing"
        elif market_activity > 7 and property_count > 100:
            return "mature"
        else:
            return "established"
    
    async def _analyze_price_trend(self, properties: List[Property]) -> str:
        """Analyze price trend from property data"""
        # This is a simplified analysis
        # In production, you'd compare with historical data
        
        if not properties:
            return "stable"
        
        # Group by recent vs older listings (proxy for trend)
        recent_cutoff = datetime.now() - timedelta(days=60)
        recent_props = [p for p in properties if p.timestamp > recent_cutoff]
        older_props = [p for p in properties if p.timestamp <= recent_cutoff]
        
        if not recent_props or not older_props:
            return "stable"
        
        recent_avg = np.mean([float(p.price_per_sqm) for p in recent_props if p.price_per_sqm])
        older_avg = np.mean([float(p.price_per_sqm) for p in older_props if p.price_per_sqm])
        
        change_pct = (recent_avg - older_avg) / older_avg * 100
        
        if change_pct > 5:
            return "up"
        elif change_pct < -5:
            return "down"
        else:
            return "stable"
    
    def _is_high_potential_investment(self, property: Property) -> bool:
        """Quick check if property is high potential investment"""
        # Simple scoring based on available data
        score = 0
        
        # Energy efficiency
        if property.energy_class in [EnergyClass.A_PLUS, EnergyClass.A, EnergyClass.B_PLUS]:
            score += 1
        
        # Size optimization
        if property.sqm and 50 <= property.sqm <= 120:
            score += 1
        
        # Age factor
        if property.year_built and (datetime.now().year - property.year_built) < 20:
            score += 1
        
        return score >= 2
    
    def _assess_overall_market_risk(
        self,
        properties: List[Property],
        market_activity: float
    ) -> InvestmentRisk:
        """Assess overall market risk"""
        # Simple risk assessment based on market characteristics
        risk_factors = 0
        
        if len(properties) < 50:
            risk_factors += 1
        
        if market_activity < 4:
            risk_factors += 1
        
        prices = [float(p.price) for p in properties]
        if prices:
            cv = np.std(prices) / np.mean(prices)
            if cv > 0.5:  # High price volatility
                risk_factors += 1
        
        if risk_factors >= 3:
            return InvestmentRisk.HIGH
        elif risk_factors == 2:
            return InvestmentRisk.MEDIUM
        else:
            return InvestmentRisk.LOW
    
    def _generate_market_insights(
        self,
        properties: List[Property],
        neighborhood_stats: Dict,
        price_trend: str,
        market_activity: float
    ) -> List[str]:
        """Generate actionable market insights"""
        insights = []
        
        # Market trend insight
        if price_trend == "up":
            insights.append("Property prices are trending upward, indicating a buyer's market pressure")
        elif price_trend == "down":
            insights.append("Property prices are declining, presenting potential buying opportunities")
        
        # Market activity insight
        if market_activity > 7:
            insights.append("High market activity indicates strong liquidity and investor interest")
        elif market_activity < 4:
            insights.append("Lower market activity may indicate limited liquidity but potential value opportunities")
        
        # Neighborhood comparison
        if neighborhood_stats:
            sorted_neighborhoods = sorted(
                neighborhood_stats.items(),
                key=lambda x: x[1]['avg_price'],
                reverse=True
            )
            
            most_expensive = sorted_neighborhoods[0][0]
            least_expensive = sorted_neighborhoods[-1][0]
            
            insights.append(f"{most_expensive} offers premium properties with highest average prices")
            insights.append(f"{least_expensive} presents entry-level investment opportunities")
        
        # Property type insights
        type_counts = defaultdict(int)
        for prop in properties:
            type_counts[prop.property_type] += 1
        
        if type_counts:
            dominant_type = max(type_counts, key=type_counts.get)
            insights.append(f"{dominant_type.value.title()} properties dominate the market ({type_counts[dominant_type]} properties)")
        
        # Investment timing insight
        total_properties = len(properties)
        if total_properties > 200:
            insights.append("Large property selection provides excellent diversification opportunities")
        elif total_properties < 50:
            insights.append("Limited property selection requires careful due diligence and timing")
        
        return insights