#!/usr/bin/env python3
"""
🏛️ Athens Center Blocks Analyzer - Precision Investment Targeting

Specialized analyzer for Athens city center blocks with detailed property-by-property
analysis, investment scoring, and actionable buy/sell recommendations.

Focus Areas:
- Syntagma (Historic & Government district)
- Plaka (Historic tourism premium)
- Monastiraki (Cultural & commercial hub)
- Psyrri (Emerging nightlife district)
- Koukaki (Gentrifying residential)
- Exarchia (Cultural bohemian area)
- Kolonaki (Premium established)
"""

import asyncio
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CenterBlockProperty:
    """Complete property profile for Athens center blocks"""
    # Property Identification
    property_id: str
    block_id: str
    street_address: str
    neighborhood: str
    district_zone: str  # HISTORIC, COMMERCIAL, RESIDENTIAL, CULTURAL
    
    # Basic Property Data
    url: str
    price: int
    sqm: int
    energy_class: str
    property_type: str  # apartment, maisonette, studio, etc.
    floor: str
    year_built: Optional[int]
    rooms: Optional[int]
    bathrooms: Optional[int]
    
    # Location Intelligence
    metro_distance: int  # meters to nearest metro
    syntagma_distance: int  # meters to Syntagma Square
    acropolis_distance: int  # meters to Acropolis
    commercial_score: float  # 1-10 commercial activity nearby
    tourism_score: float  # 1-10 tourism attraction value
    
    # Investment Metrics
    price_per_sqm: float
    investment_score: float  # 1-10 overall investment potential
    rental_yield_estimate: float
    appreciation_potential: float
    renovation_cost_estimate: int
    post_renovation_value: int
    
    # Market Intelligence
    days_on_market: int
    price_trend: str  # RISING, STABLE, DECLINING
    comparable_sales: int  # number of recent comparable sales
    market_activity: str  # HIGH, MEDIUM, LOW
    
    # Investment Strategy
    recommended_action: str  # IMMEDIATE_BUY, STRONG_BUY, CONDITIONAL_BUY, HOLD, AVOID
    investment_strategy: str  # TOURISM_RENTAL, ENERGY_RETROFIT, GENTRIFICATION_PLAY, HOLD_APPRECIATE
    target_price: int
    max_bid: int
    expected_roi_12m: float
    expected_roi_24m: float
    
    # Risk Assessment
    liquidity_risk: str  # LOW, MEDIUM, HIGH
    renovation_risk: str
    market_risk: str
    overall_risk: str
    confidence_score: float  # Data confidence 0-1

class AthensCenterBlocksAnalyzer:
    """
    Specialized analyzer for Athens center blocks investment opportunities
    
    This analyzer focuses on the highest-value central Athens blocks with
    detailed property-by-property analysis and investment recommendations.
    """
    
    def __init__(self):
        self.setup_logging()
        self.center_blocks = self.define_center_blocks()
        self.metro_stations = self.load_metro_stations()
        self.tourism_attractions = self.load_tourism_attractions()
        
    def setup_logging(self):
        """Setup logging for center blocks analysis"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def define_center_blocks(self) -> Dict[str, Dict]:
        """Define Athens center blocks with detailed mapping"""
        return {
            # Syntagma Area - Government & Historic
            "SYN-001": {
                "name": "Syntagma Square East",
                "boundaries": "Amalias Ave, Vasilissis Sofias, Herodou Attikou",
                "district_zone": "HISTORIC",
                "priority": "PREMIUM",
                "expected_properties": 45,
                "avg_price_sqm": 6500,
                "metro_stations": ["Syntagma"],
                "tourism_score": 10.0,
                "commercial_score": 9.5
            },
            "SYN-002": {
                "name": "Syntagma Square West", 
                "boundaries": "Ermou, Mitropoleos, Voulis",
                "district_zone": "COMMERCIAL",
                "priority": "HIGH",
                "expected_properties": 35,
                "avg_price_sqm": 5800,
                "metro_stations": ["Syntagma"],
                "tourism_score": 9.5,
                "commercial_score": 10.0
            },
            
            # Plaka Area - Historic Tourism
            "PLA-001": {
                "name": "Plaka Central",
                "boundaries": "Adrianou, Kydathinaion, Lysikratous",
                "district_zone": "HISTORIC",
                "priority": "PREMIUM",
                "expected_properties": 28,
                "avg_price_sqm": 5200,
                "metro_stations": ["Monastiraki", "Acropoli"],
                "tourism_score": 10.0,
                "commercial_score": 8.0
            },
            "PLA-002": {
                "name": "Plaka North",
                "boundaries": "Pandrossou, Areos, Erechtheiou",
                "district_zone": "HISTORIC",
                "priority": "HIGH",
                "expected_properties": 32,
                "avg_price_sqm": 4800,
                "metro_stations": ["Monastiraki"],
                "tourism_score": 9.0,
                "commercial_score": 7.5
            },
            
            # Monastiraki Area - Cultural Hub
            "MON-001": {
                "name": "Monastiraki Square",
                "boundaries": "Athinas, Ermou, Areos, Mitropoleos",
                "district_zone": "COMMERCIAL",
                "priority": "HIGH",
                "expected_properties": 40,
                "avg_price_sqm": 4500,
                "metro_stations": ["Monastiraki"],
                "tourism_score": 8.5,
                "commercial_score": 9.0
            },
            
            # Psyrri Area - Emerging Nightlife
            "PSY-001": {
                "name": "Psyrri Central",
                "boundaries": "Ermou, Athinas, Evripidou, Sarri",
                "district_zone": "CULTURAL",
                "priority": "MEDIUM",
                "expected_properties": 55,
                "avg_price_sqm": 3200,
                "metro_stations": ["Monastiraki", "Omonia"],
                "tourism_score": 6.5,
                "commercial_score": 7.0
            },
            
            # Koukaki Area - Gentrifying Residential
            "KOU-001": {
                "name": "Koukaki North",
                "boundaries": "Dimitrakopoulou, Falirou, Veikou",
                "district_zone": "RESIDENTIAL",
                "priority": "HIGH",
                "expected_properties": 65,
                "avg_price_sqm": 3800,
                "metro_stations": ["Acropoli", "Syggrou-Fix"],
                "tourism_score": 7.0,
                "commercial_score": 6.0
            },
            "KOU-002": {
                "name": "Koukaki Central",
                "boundaries": "Olympiou, Zacharitsa, Georgiou Olympiou",
                "district_zone": "RESIDENTIAL", 
                "priority": "HIGH",
                "expected_properties": 58,
                "avg_price_sqm": 3600,
                "metro_stations": ["Acropoli"],
                "tourism_score": 6.5,
                "commercial_score": 5.5
            },
            
            # Exarchia Area - Cultural District
            "EXA-001": {
                "name": "Exarchia Central",
                "boundaries": "Patission, Stournari, Themistokleous, Kallidromiou",
                "district_zone": "CULTURAL",
                "priority": "MEDIUM",
                "expected_properties": 70,
                "avg_price_sqm": 3400,
                "metro_stations": ["Omonia", "Exarchia"],
                "tourism_score": 5.5,
                "commercial_score": 6.5
            },
            
            # Kolonaki Area - Premium Established
            "KOL-001": {
                "name": "Kolonaki Central",
                "boundaries": "Voukourestiou, Skoufa, Kanari, Patriarchou Ioakim",
                "district_zone": "RESIDENTIAL",
                "priority": "PREMIUM",
                "expected_properties": 42,
                "avg_price_sqm": 7200,
                "metro_stations": ["Syntagma", "Evangelismos"],
                "tourism_score": 4.0,
                "commercial_score": 8.5
            },
            "KOL-002": {
                "name": "Kolonaki East",
                "boundaries": "Vassilissis Sofias, Neofytou Douka, Loukianou",
                "district_zone": "RESIDENTIAL",
                "priority": "PREMIUM", 
                "expected_properties": 38,
                "avg_price_sqm": 6800,
                "metro_stations": ["Evangelismos"],
                "tourism_score": 3.5,
                "commercial_score": 7.5
            }
        }
    
    def load_metro_stations(self) -> Dict[str, Tuple[float, float]]:
        """Load metro station coordinates for distance calculations"""
        return {
            "Syntagma": (37.9755, 23.7348),
            "Monastiraki": (37.9769, 23.7286),
            "Acropoli": (37.9685, 23.7278),
            "Omonia": (37.9838, 23.7275),
            "Evangelismos": (37.9733, 23.7581),
            "Syggrou-Fix": (37.9520, 23.7320)
        }
    
    def load_tourism_attractions(self) -> Dict[str, Tuple[float, float]]:
        """Load major tourism attractions for proximity scoring"""
        return {
            "Syntagma_Square": (37.9755, 23.7348),
            "Acropolis": (37.9715, 23.7267),
            "Ancient_Agora": (37.9753, 23.7230),
            "National_Garden": (37.9741, 23.7370),
            "Benaki_Museum": (37.9749, 23.7537),
            "National_Archaeological_Museum": (37.9891, 23.7324)
        }
    
    async def analyze_center_blocks(self) -> List[CenterBlockProperty]:
        """
        Main analysis method for Athens center blocks
        
        Returns comprehensive property analysis with investment recommendations
        """
        self.logger.info("🏛️ Starting Athens Center Blocks Analysis")
        self.logger.info(f"📍 Analyzing {len(self.center_blocks)} center blocks")
        
        all_properties = []
        
        # Analyze each center block
        for block_id, block_info in self.center_blocks.items():
            self.logger.info(f"🔍 Analyzing block {block_id}: {block_info['name']}")
            
            try:
                # Collect properties for this block
                block_properties = await self.analyze_single_block(block_id, block_info)
                all_properties.extend(block_properties)
                
                self.logger.info(f"✅ Block {block_id}: {len(block_properties)} properties analyzed")
                
            except Exception as e:
                self.logger.error(f"❌ Block {block_id} analysis failed: {e}")
                continue
        
        # Sort properties by investment score
        all_properties.sort(key=lambda x: x.investment_score, reverse=True)
        
        self.logger.info(f"🎯 Analysis Complete: {len(all_properties)} center properties analyzed")
        
        return all_properties
    
    async def analyze_single_block(self, block_id: str, block_info: Dict) -> List[CenterBlockProperty]:
        """Analyze properties in a single center block"""
        
        properties = []
        expected_count = block_info['expected_properties']
        
        # Simulate property collection for demonstration
        # In production, this would scrape real property data
        for i in range(min(expected_count, 20)):  # Limit to 20 for demo
            property_data = await self.collect_property_data(block_id, block_info, i)
            
            if property_data:
                # Generate comprehensive property analysis
                property_analysis = self.generate_property_analysis(property_data, block_info)
                properties.append(property_analysis)
        
        return properties
    
    async def collect_property_data(self, block_id: str, block_info: Dict, property_index: int) -> Optional[Dict]:
        """Collect individual property data (simulated for demo)"""
        
        # Simulate realistic property data
        base_price = block_info['avg_price_sqm']
        price_variation = 0.8 + (property_index * 0.03)  # ±20% variation
        
        sqm_base = 75 + (property_index * 3)  # 75-135 sqm range
        energy_classes = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D']
        
        return {
            'property_id': f"{block_id}-{property_index:03d}",
            'block_id': block_id,
            'url': f"https://spitogatos.gr/property/{block_id.lower()}-{property_index}",
            'price': int(base_price * sqm_base * price_variation),
            'sqm': sqm_base,
            'energy_class': energy_classes[property_index % len(energy_classes)],
            'property_type': 'apartment',
            'floor': f"{(property_index % 5) + 1}rd",
            'year_built': 1970 + (property_index * 2),
            'rooms': 2 + (property_index % 3),
            'bathrooms': 1 + (property_index % 2),
            'days_on_market': 30 + (property_index * 5),
            'street_address': f"{block_info['name']} Street {property_index + 1}",
            'neighborhood': block_info['name']
        }
    
    def generate_property_analysis(self, property_data: Dict, block_info: Dict) -> CenterBlockProperty:
        """Generate comprehensive property analysis"""
        
        # Calculate investment metrics
        price_per_sqm = property_data['price'] / property_data['sqm']
        
        # Investment scoring (1-10 scale)
        investment_score = self.calculate_investment_score(property_data, block_info)
        
        # Location intelligence
        metro_distance = self.calculate_metro_distance(block_info)
        syntagma_distance = self.calculate_syntagma_distance(block_info)
        acropolis_distance = self.calculate_acropolis_distance(block_info)
        
        # Financial projections
        rental_yield = self.estimate_rental_yield(property_data, block_info)
        appreciation_potential = self.estimate_appreciation_potential(property_data, block_info)
        renovation_cost = self.estimate_renovation_cost(property_data)
        post_renovation_value = property_data['price'] + renovation_cost * 2.5
        
        # Investment strategy
        strategy, action, target_price, max_bid = self.determine_investment_strategy(
            property_data, block_info, investment_score
        )
        
        # ROI calculations
        roi_12m = self.calculate_roi_projection(property_data, block_info, 12)
        roi_24m = self.calculate_roi_projection(property_data, block_info, 24)
        
        # Risk assessment
        liquidity_risk, renovation_risk, market_risk, overall_risk = self.assess_risks(
            property_data, block_info
        )
        
        return CenterBlockProperty(
            # Property Identification
            property_id=property_data['property_id'],
            block_id=property_data['block_id'],
            street_address=property_data['street_address'],
            neighborhood=property_data['neighborhood'],
            district_zone=block_info['district_zone'],
            
            # Basic Property Data
            url=property_data['url'],
            price=property_data['price'],
            sqm=property_data['sqm'],
            energy_class=property_data['energy_class'],
            property_type=property_data['property_type'],
            floor=property_data['floor'],
            year_built=property_data['year_built'],
            rooms=property_data['rooms'],
            bathrooms=property_data['bathrooms'],
            
            # Location Intelligence
            metro_distance=metro_distance,
            syntagma_distance=syntagma_distance,
            acropolis_distance=acropolis_distance,
            commercial_score=block_info['commercial_score'],
            tourism_score=block_info['tourism_score'],
            
            # Investment Metrics
            price_per_sqm=price_per_sqm,
            investment_score=investment_score,
            rental_yield_estimate=rental_yield,
            appreciation_potential=appreciation_potential,
            renovation_cost_estimate=renovation_cost,
            post_renovation_value=post_renovation_value,
            
            # Market Intelligence
            days_on_market=property_data['days_on_market'],
            price_trend=self.determine_price_trend(block_info),
            comparable_sales=self.estimate_comparable_sales(block_info),
            market_activity=self.assess_market_activity(block_info),
            
            # Investment Strategy
            recommended_action=action,
            investment_strategy=strategy,
            target_price=target_price,
            max_bid=max_bid,
            expected_roi_12m=roi_12m,
            expected_roi_24m=roi_24m,
            
            # Risk Assessment
            liquidity_risk=liquidity_risk,
            renovation_risk=renovation_risk,
            market_risk=market_risk,
            overall_risk=overall_risk,
            confidence_score=0.92
        )
    
    def calculate_investment_score(self, property_data: Dict, block_info: Dict) -> float:
        """Calculate comprehensive investment score (1-10)"""
        
        # Location score (based on district zone and tourism/commercial scores)
        location_score = {
            'HISTORIC': 9.5,
            'COMMERCIAL': 8.5,
            'RESIDENTIAL': 7.5,
            'CULTURAL': 6.5
        }.get(block_info['district_zone'], 7.0)
        
        # Energy efficiency score
        energy_score = {
            'A+': 10.0, 'A': 9.0, 'B+': 8.0, 'B': 7.0, 'C+': 6.0,
            'C': 5.0, 'D': 4.0, 'E': 3.0
        }.get(property_data['energy_class'], 5.0)
        
        # Value score (price vs market average)
        market_avg = block_info['avg_price_sqm']
        actual_price_sqm = property_data['price'] / property_data['sqm']
        value_ratio = market_avg / actual_price_sqm
        
        if value_ratio >= 1.15:  # 15%+ below market
            value_score = 10.0
        elif value_ratio >= 1.10:  # 10%+ below market
            value_score = 8.5
        elif value_ratio >= 1.05:  # 5%+ below market
            value_score = 7.0
        elif value_ratio >= 0.95:  # At market
            value_score = 6.0
        else:  # Above market
            value_score = 4.0
        
        # Size premium/penalty
        size_score = min(10.0, max(5.0, property_data['sqm'] / 10))  # 50-100+ sqm optimal
        
        # Age adjustment
        building_age = 2025 - property_data['year_built']
        if building_age < 10:
            age_score = 9.0
        elif building_age < 25:
            age_score = 7.0
        elif building_age < 40:
            age_score = 6.0
        else:
            age_score = 5.0
        
        # Weighted composite score
        composite_score = (
            location_score * 0.30 +
            energy_score * 0.25 +
            value_score * 0.20 +
            size_score * 0.15 +
            age_score * 0.10
        )
        
        # Tourism/commercial bonus
        if block_info['tourism_score'] >= 8.0:
            composite_score += 0.5
        if block_info['commercial_score'] >= 8.0:
            composite_score += 0.3
        
        return min(10.0, max(1.0, composite_score))
    
    def calculate_metro_distance(self, block_info: Dict) -> int:
        """Calculate distance to nearest metro station (meters)"""
        metro_stations = block_info.get('metro_stations', [])
        if 'Syntagma' in metro_stations:
            return 150
        elif 'Monastiraki' in metro_stations:
            return 200
        elif 'Acropoli' in metro_stations:
            return 250
        else:
            return 400
    
    def calculate_syntagma_distance(self, block_info: Dict) -> int:
        """Calculate distance to Syntagma Square (meters)"""
        if 'Syntagma' in block_info['name']:
            return 100
        elif block_info['district_zone'] == 'HISTORIC':
            return 300
        elif block_info['district_zone'] == 'COMMERCIAL':
            return 500
        else:
            return 800
    
    def calculate_acropolis_distance(self, block_info: Dict) -> int:
        """Calculate distance to Acropolis (meters)"""
        if 'Plaka' in block_info['name']:
            return 200
        elif 'Koukaki' in block_info['name']:
            return 400
        elif block_info['district_zone'] == 'HISTORIC':
            return 600
        else:
            return 1200
    
    def estimate_rental_yield(self, property_data: Dict, block_info: Dict) -> float:
        """Estimate rental yield potential"""
        base_yield = 0.055  # 5.5% base
        
        # Tourism premium
        if block_info['tourism_score'] >= 8.0:
            base_yield += 0.02  # +2% for high tourism
        elif block_info['tourism_score'] >= 6.0:
            base_yield += 0.01  # +1% for medium tourism
        
        # Energy efficiency bonus
        energy_bonus = {
            'A+': 0.015, 'A': 0.01, 'B+': 0.005, 'B': 0.002
        }.get(property_data['energy_class'], 0)
        
        return base_yield + energy_bonus
    
    def estimate_appreciation_potential(self, property_data: Dict, block_info: Dict) -> float:
        """Estimate annual appreciation potential"""
        base_appreciation = 0.06  # 6% base
        
        # District zone multiplier
        zone_multiplier = {
            'HISTORIC': 1.2,    # Historic areas stable premium
            'COMMERCIAL': 1.1,  # Commercial areas steady growth
            'RESIDENTIAL': 1.0, # Residential baseline
            'CULTURAL': 1.3     # Cultural areas gentrification potential
        }.get(block_info['district_zone'], 1.0)
        
        return base_appreciation * zone_multiplier
    
    def estimate_renovation_cost(self, property_data: Dict) -> int:
        """Estimate renovation cost based on property characteristics"""
        base_cost_per_sqm = 400  # €400/sqm base renovation
        
        # Energy class renovation requirements
        energy_multiplier = {
            'A+': 0.5, 'A': 0.6, 'B+': 0.7, 'B': 0.8, 'C+': 1.0,
            'C': 1.2, 'D': 1.5, 'E': 2.0
        }.get(property_data['energy_class'], 1.0)
        
        # Age adjustment
        building_age = 2025 - property_data['year_built']
        if building_age > 40:
            age_multiplier = 1.5
        elif building_age > 25:
            age_multiplier = 1.2
        else:
            age_multiplier = 1.0
        
        return int(base_cost_per_sqm * property_data['sqm'] * energy_multiplier * age_multiplier)
    
    def determine_investment_strategy(self, property_data: Dict, block_info: Dict, 
                                   investment_score: float) -> Tuple[str, str, int, int]:
        """Determine optimal investment strategy"""
        
        energy_class = property_data['energy_class']
        tourism_score = block_info['tourism_score']
        district_zone = block_info['district_zone']
        price = property_data['price']
        
        # Strategy determination
        if tourism_score >= 8.0 and energy_class in ['A+', 'A', 'B+']:
            strategy = "TOURISM_RENTAL"
        elif energy_class in ['C', 'D', 'E'] and investment_score >= 7.0:
            strategy = "ENERGY_RETROFIT"
        elif district_zone == 'CULTURAL' and investment_score >= 6.5:
            strategy = "GENTRIFICATION_PLAY"
        else:
            strategy = "HOLD_APPRECIATE"
        
        # Action recommendation
        if investment_score >= 9.0:
            action = "IMMEDIATE_BUY"
            discount = 0.02  # 2% below asking
        elif investment_score >= 7.5:
            action = "STRONG_BUY"
            discount = 0.05  # 5% below asking
        elif investment_score >= 6.0:
            action = "CONDITIONAL_BUY"
            discount = 0.10  # 10% below asking
        else:
            action = "HOLD"
            discount = 0.15  # 15% below asking
        
        target_price = int(price * (1 - discount))
        max_bid = int(price * (1 - discount + 0.02))  # 2% buffer above target
        
        return strategy, action, target_price, max_bid
    
    def calculate_roi_projection(self, property_data: Dict, block_info: Dict, months: int) -> float:
        """Calculate ROI projection for specified timeframe"""
        
        rental_yield = self.estimate_rental_yield(property_data, block_info)
        appreciation = self.estimate_appreciation_potential(property_data, block_info)
        
        # Annual ROI components
        annual_roi = rental_yield + appreciation
        
        # Adjust for timeframe
        timeframe_roi = annual_roi * (months / 12)
        
        # Strategy bonus
        if property_data['energy_class'] in ['C', 'D'] and months >= 18:
            timeframe_roi += 0.15  # Energy retrofit bonus
        
        return timeframe_roi
    
    def assess_risks(self, property_data: Dict, block_info: Dict) -> Tuple[str, str, str, str]:
        """Comprehensive risk assessment"""
        
        # Liquidity risk
        if block_info['district_zone'] in ['HISTORIC', 'COMMERCIAL']:
            liquidity_risk = "LOW"
        elif block_info['district_zone'] == 'RESIDENTIAL':
            liquidity_risk = "MEDIUM"
        else:
            liquidity_risk = "HIGH"
        
        # Renovation risk
        building_age = 2025 - property_data['year_built']
        energy_class = property_data['energy_class']
        
        if building_age < 20 and energy_class in ['A+', 'A', 'B+']:
            renovation_risk = "LOW"
        elif building_age < 40 and energy_class in ['B', 'C+', 'C']:
            renovation_risk = "MEDIUM"
        else:
            renovation_risk = "HIGH"
        
        # Market risk
        if block_info['priority'] == 'PREMIUM':
            market_risk = "LOW"
        elif block_info['priority'] == 'HIGH':
            market_risk = "MEDIUM"
        else:
            market_risk = "MEDIUM"
        
        # Overall risk
        risk_scores = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        avg_risk = (risk_scores[liquidity_risk] + risk_scores[renovation_risk] + risk_scores[market_risk]) / 3
        
        if avg_risk <= 1.3:
            overall_risk = "LOW"
        elif avg_risk <= 2.0:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "HIGH"
        
        return liquidity_risk, renovation_risk, market_risk, overall_risk
    
    def determine_price_trend(self, block_info: Dict) -> str:
        """Determine price trend for block"""
        if block_info['priority'] == 'PREMIUM':
            return "STABLE"
        elif block_info['district_zone'] == 'CULTURAL':
            return "RISING"
        else:
            return "STABLE"
    
    def estimate_comparable_sales(self, block_info: Dict) -> int:
        """Estimate number of comparable sales"""
        return max(5, int(block_info['expected_properties'] * 0.15))
    
    def assess_market_activity(self, block_info: Dict) -> str:
        """Assess market activity level"""
        if block_info['priority'] == 'PREMIUM':
            return "HIGH"
        elif block_info['priority'] == 'HIGH':
            return "MEDIUM"
        else:
            return "MEDIUM"
    
    def save_analysis_results(self, properties: List[CenterBlockProperty], 
                            output_dir: str = "data/processed") -> str:
        """Save comprehensive analysis results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{output_dir}/athens_center_blocks_analysis_{timestamp}.json"
        
        # Convert to serializable format
        results = {
            "analysis_metadata": {
                "timestamp": timestamp,
                "total_properties": len(properties),
                "blocks_analyzed": len(set(p.block_id for p in properties)),
                "avg_investment_score": sum(p.investment_score for p in properties) / len(properties),
                "total_investment_value": sum(p.target_price for p in properties if p.recommended_action in ["IMMEDIATE_BUY", "STRONG_BUY"])
            },
            "properties": [
                {
                    "property_id": p.property_id,
                    "block_id": p.block_id,
                    "neighborhood": p.neighborhood,
                    "district_zone": p.district_zone,
                    "url": p.url,
                    "price": p.price,
                    "sqm": p.sqm,
                    "energy_class": p.energy_class,
                    "price_per_sqm": p.price_per_sqm,
                    "investment_score": p.investment_score,
                    "recommended_action": p.recommended_action,
                    "investment_strategy": p.investment_strategy,
                    "target_price": p.target_price,
                    "expected_roi_12m": p.expected_roi_12m,
                    "expected_roi_24m": p.expected_roi_24m,
                    "tourism_score": p.tourism_score,
                    "commercial_score": p.commercial_score,
                    "metro_distance": p.metro_distance,
                    "overall_risk": p.overall_risk,
                    "confidence_score": p.confidence_score
                }
                for p in properties
            ]
        }
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Athens Center Blocks Analysis saved: {output_path}")
        return output_path

# Main execution function
async def main():
    """Execute Athens center blocks analysis"""
    
    print("🏛️ ATHintel - Athens Center Blocks Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = AthensCenterBlocksAnalyzer()
    
    # Run comprehensive analysis
    properties = await analyzer.analyze_center_blocks()
    
    # Save results
    results_path = analyzer.save_analysis_results(properties)
    
    # Generate summary
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Properties Analyzed: {len(properties)}")
    print(f"Blocks Covered: {len(set(p.block_id for p in properties))}")
    
    # Investment recommendations
    immediate_buy = [p for p in properties if p.recommended_action == "IMMEDIATE_BUY"]
    strong_buy = [p for p in properties if p.recommended_action == "STRONG_BUY"]
    
    print(f"IMMEDIATE BUY: {len(immediate_buy)} properties")
    print(f"STRONG BUY: {len(strong_buy)} properties")
    
    total_investment_value = sum(p.target_price for p in immediate_buy + strong_buy)
    print(f"Total Investment Value: €{total_investment_value:,.0f}")
    
    # Top opportunities
    print(f"\n🏆 TOP 5 INVESTMENT OPPORTUNITIES")
    print("-" * 60)
    for i, prop in enumerate(properties[:5], 1):
        print(f"{i}. {prop.neighborhood} ({prop.block_id})")
        print(f"   Score: {prop.investment_score:.1f}/10 | Action: {prop.recommended_action}")
        print(f"   Price: €{prop.price:,} | Target: €{prop.target_price:,}")
        print(f"   ROI (24m): {prop.expected_roi_24m:.1%} | Strategy: {prop.investment_strategy}")
        print()
    
    print(f"📋 Detailed results saved to: {results_path}")

if __name__ == "__main__":
    asyncio.run(main())