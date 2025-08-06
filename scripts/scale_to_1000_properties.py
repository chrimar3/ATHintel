#!/usr/bin/env python3
"""
🏛️ Scale ATHintel to 1000 Properties
Expand dataset to 1000 authenticated properties with Athens Center focus
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import random

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.collectors.working_spitogatos_scraper import WorkingSpitogatosScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScaledDatasetCollector:
    """Collector for scaling to 1000 properties with Athens Center focus"""
    
    def __init__(self):
        self.target_properties = 1000
        self.athens_center_focus_percentage = 60  # 60% Athens Center focus
        self.collected_properties = []
        self.existing_urls = set()
        
        # Enhanced Athens Center search strategies
        self.athens_center_searches = [
            # Core Athens Center areas
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_asc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_desc", 
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=date_desc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=sqm_desc",
            
            # Price segments for Athens Center
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_max=100000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=100000&price_max=200000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=200000&price_max=300000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=300000&price_max=500000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=500000&price_max=1000000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=1000000",
            
            # Size segments for Athens Center
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_max=50",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_min=50&sqm_max=80",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_min=80&sqm_max=120",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_min=120",
            
            # Energy class focused searches
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=A",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=B",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=C",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=D",
            
            # Specific central neighborhoods
            "https://www.spitogatos.gr/en/for_sale-homes/syntagma",
            "https://www.spitogatos.gr/en/for_sale-homes/monastiraki",
            "https://www.spitogatos.gr/en/for_sale-homes/thiseio", 
            "https://www.spitogatos.gr/en/for_sale-homes/psirri",
            "https://www.spitogatos.gr/en/for_sale-homes/plaka",
            "https://www.spitogatos.gr/en/for_sale-homes/exarchia",
            "https://www.spitogatos.gr/en/for_sale-homes/pagrati",
            
            # Property type variations
            "https://www.spitogatos.gr/en/for_sale-apartments/athens-center",
            "https://www.spitogatos.gr/en/for_sale-maisonettes/athens-center",
            "https://www.spitogatos.gr/en/for_sale-houses/athens-center",
            "https://www.spitogatos.gr/en/for_sale-studios/athens-center",
            
            # Additional sorting and filtering
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_per_sqm_asc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_per_sqm_desc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?listing_age=new",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?listing_age=week",
        ]
        
        # Supporting areas for diversification
        self.supporting_area_searches = [
            # Premium areas
            "https://www.spitogatos.gr/en/for_sale-homes/kolonaki",
            "https://www.spitogatos.gr/en/for_sale-homes/kolonaki?sort=price_asc",
            "https://www.spitogatos.gr/en/for_sale-homes/koukaki",
            "https://www.spitogatos.gr/en/for_sale-homes/koukaki?sort=price_asc",
            
            # Growth areas
            "https://www.spitogatos.gr/en/for_sale-homes/kipseli",
            "https://www.spitogatos.gr/en/for_sale-homes/kipseli?sort=price_asc",
            "https://www.spitogatos.gr/en/for_sale-homes/ampelokipoi",
            "https://www.spitogatos.gr/en/for_sale-homes/ampelokipoi?sort=price_asc",
            
            # Emerging areas
            "https://www.spitogatos.gr/en/for_sale-homes/petralona",
            "https://www.spitogatos.gr/en/for_sale-homes/gazi",
            "https://www.spitogatos.gr/en/for_sale-homes/metaxourgeio",
            "https://www.spitogatos.gr/en/for_sale-homes/keramikos",
            
            # Northern suburbs
            "https://www.spitogatos.gr/en/for_sale-homes/kifisia",
            "https://www.spitogatos.gr/en/for_sale-homes/chalandri",
            "https://www.spitogatos.gr/en/for_sale-homes/marousi",
            
            # Southern areas
            "https://www.spitogatos.gr/en/for_sale-homes/glyfada",
            "https://www.spitogatos.gr/en/for_sale-homes/voula",
            "https://www.spitogatos.gr/en/for_sale-homes/vouliagmeni",
            
            # Additional central areas
            "https://www.spitogatos.gr/en/for_sale-homes/nea-smyrni",
            "https://www.spitogatos.gr/en/for_sale-homes/kallithea",
            "https://www.spitogatos.gr/en/for_sale-homes/neos-kosmos",
        ]
    
    def load_existing_dataset(self):
        """Load existing dataset to avoid duplicates"""
        logger.info("📊 Loading existing dataset to avoid duplicates...")
        
        existing_file = Path("data/processed/athens_large_scale_real_data_20250805_175443.json")
        if existing_file.exists():
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                self.existing_urls = {prop.get('url') for prop in existing_data if prop.get('url')}
                self.collected_properties.extend(existing_data)
                logger.info(f"✅ Loaded {len(existing_data)} existing properties")
        else:
            logger.info("ℹ️ No existing dataset found - starting fresh")
    
    async def collect_scaled_dataset(self) -> List[Dict]:
        """Collect scaled dataset with Athens Center focus"""
        logger.info(f"🏛️ Starting collection for {self.target_properties} properties")
        logger.info(f"🎯 Athens Center Focus: {self.athens_center_focus_percentage}%")
        
        # Load existing dataset
        self.load_existing_dataset()
        
        # Calculate targets
        athens_center_target = int(self.target_properties * (self.athens_center_focus_percentage / 100))
        supporting_target = self.target_properties - athens_center_target
        
        current_athens_center = len([p for p in self.collected_properties 
                                   if self.is_athens_center_property(p)])
        current_supporting = len(self.collected_properties) - current_athens_center
        
        athens_center_needed = max(0, athens_center_target - current_athens_center)
        supporting_needed = max(0, supporting_target - current_supporting)
        
        logger.info(f"📊 Current: {len(self.collected_properties)} properties")
        logger.info(f"🏛️ Athens Center: {current_athens_center}/{athens_center_target} (need {athens_center_needed})")
        logger.info(f"🏘️ Supporting Areas: {current_supporting}/{supporting_target} (need {supporting_needed})")
        
        # Collect Athens Center properties
        if athens_center_needed > 0:
            logger.info(f"🏛️ Collecting {athens_center_needed} Athens Center properties...")
            athens_center_props = await self.collect_properties_from_searches(
                self.athens_center_searches, 
                athens_center_needed,
                "Athens Center"
            )
            self.collected_properties.extend(athens_center_props)
            logger.info(f"✅ Added {len(athens_center_props)} Athens Center properties")
        
        # Collect supporting area properties
        if supporting_needed > 0:
            logger.info(f"🏘️ Collecting {supporting_needed} supporting area properties...")
            supporting_props = await self.collect_properties_from_searches(
                self.supporting_area_searches,
                supporting_needed,
                "Supporting Areas"
            )
            self.collected_properties.extend(supporting_props)
            logger.info(f"✅ Added {len(supporting_props)} supporting area properties")
        
        # Remove duplicates and ensure quality
        self.collected_properties = self.deduplicate_and_validate_properties()
        
        logger.info(f"🎉 Final dataset: {len(self.collected_properties)} properties")
        return self.collected_properties
    
    def is_athens_center_property(self, prop: Dict) -> bool:
        """Check if property is in Athens Center area"""
        neighborhood = prop.get('neighborhood', '').lower()
        athens_center_areas = [
            'athens center', 'κέντρο αθήνας', 'σύνταγμα', 'μοναστηράκι',
            'θησείο', 'ψυρρή', 'εξάρχεια', 'πλάκα', 'παγκράτι', 'syntagma',
            'monastiraki', 'thiseio', 'psirri', 'exarchia', 'plaka', 'pagrati'
        ]
        return any(area in neighborhood for area in athens_center_areas)
    
    async def collect_properties_from_searches(self, search_urls: List[str], 
                                             target_count: int, area_name: str) -> List[Dict]:
        """Collect properties from search URLs"""
        collected = []
        scraper = WorkingSpitogatosScraper()
        
        try:
            await scraper.initialize()
            
            # Randomize search order for better coverage
            randomized_searches = search_urls.copy()
            random.shuffle(randomized_searches)
            
            for i, search_url in enumerate(randomized_searches):
                if len(collected) >= target_count:
                    break
                
                logger.info(f"🔍 Searching {area_name} ({i+1}/{len(randomized_searches)}): {len(collected)}/{target_count} found")
                
                try:
                    # Extract properties from this search
                    search_properties = await scraper.extract_properties_from_search_with_pagination(
                        search_url, 
                        max_properties=min(50, target_count - len(collected)),  # Limit per search
                        max_pages=10
                    )
                    
                    # Filter out duplicates and validate
                    for prop in search_properties:
                        if (len(collected) < target_count and 
                            prop.url not in self.existing_urls and
                            self.validate_property_data(prop)):
                            
                            collected.append(prop.to_dict())
                            self.existing_urls.add(prop.url)
                    
                    logger.info(f"📊 Progress: {len(collected)}/{target_count} {area_name} properties")
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Search failed for {search_url}: {e}")
                    continue
            
            return collected
            
        finally:
            await scraper.close()
    
    def validate_property_data(self, prop) -> bool:
        """Validate property has all required data"""
        return (hasattr(prop, 'url') and prop.url and
                hasattr(prop, 'price') and prop.price and prop.price > 0 and
                hasattr(prop, 'sqm') and prop.sqm and prop.sqm > 0 and
                hasattr(prop, 'energy_class') and prop.energy_class and
                30000 <= prop.price <= 20000000 and  # Reasonable price range
                15 <= prop.sqm <= 1000)  # Reasonable size range
    
    def deduplicate_and_validate_properties(self) -> List[Dict]:
        """Remove duplicates and validate all properties"""
        logger.info("🔍 Removing duplicates and validating properties...")
        
        seen_urls = set()
        validated_properties = []
        
        for prop in self.collected_properties:
            url = prop.get('url')
            if (url and url not in seen_urls and
                prop.get('price') and prop.get('sqm') and prop.get('energy_class')):
                
                seen_urls.add(url)
                validated_properties.append(prop)
        
        logger.info(f"✅ Validation complete: {len(validated_properties)} unique, valid properties")
        return validated_properties
    
    async def save_scaled_dataset(self) -> str:
        """Save the scaled dataset"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save comprehensive JSON
        json_file = Path("data/processed") / f"athens_scaled_1000_properties_{timestamp}.json"
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.collected_properties, f, ensure_ascii=False, indent=2)
        
        # Create summary statistics
        stats = self.generate_dataset_statistics()
        
        # Save statistics
        stats_file = Path("data/processed") / f"athens_scaled_1000_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Save CSV summary
        csv_file = Path("data/processed") / f"athens_scaled_1000_summary_{timestamp}.csv"
        self.create_csv_summary(csv_file)
        
        logger.info(f"💾 Scaled dataset saved:")
        logger.info(f"   📄 Main data: {json_file}")
        logger.info(f"   📊 Statistics: {stats_file}")
        logger.info(f"   📋 CSV summary: {csv_file}")
        
        return str(json_file)
    
    def generate_dataset_statistics(self) -> Dict:
        """Generate comprehensive dataset statistics"""
        properties = self.collected_properties
        
        # Neighborhood distribution
        neighborhoods = {}
        for prop in properties:
            neighborhood = prop.get('neighborhood', 'Unknown')
            neighborhoods[neighborhood] = neighborhoods.get(neighborhood, 0) + 1
        
        # Price analysis
        prices = [p.get('price', 0) for p in properties if p.get('price')]
        sizes = [p.get('sqm', 0) for p in properties if p.get('sqm')]
        
        # Energy class distribution
        energy_classes = {}
        for prop in properties:
            energy = prop.get('energy_class', 'Unknown')
            energy_classes[energy] = energy_classes.get(energy, 0) + 1
        
        # Athens Center analysis
        athens_center_count = len([p for p in properties if self.is_athens_center_property(p)])
        athens_center_percentage = (athens_center_count / len(properties)) * 100 if properties else 0
        
        return {
            "collection_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_properties": len(properties),
                "target_achieved_percentage": (len(properties) / self.target_properties) * 100,
                "data_quality": "100% Authenticated with Required Fields"
            },
            "geographic_distribution": {
                "neighborhoods": neighborhoods,
                "athens_center_focus": {
                    "count": athens_center_count,
                    "percentage": athens_center_percentage,
                    "target_percentage": self.athens_center_focus_percentage
                }
            },
            "market_analysis": {
                "price_statistics": {
                    "count": len(prices),
                    "min": min(prices) if prices else 0,
                    "max": max(prices) if prices else 0,
                    "average": sum(prices) / len(prices) if prices else 0,
                    "total_value": sum(prices)
                },
                "size_statistics": {
                    "count": len(sizes),
                    "min": min(sizes) if sizes else 0,
                    "max": max(sizes) if sizes else 0,
                    "average": sum(sizes) / len(sizes) if sizes else 0,
                    "total_area": sum(sizes)
                },
                "energy_distribution": energy_classes
            },
            "quality_metrics": {
                "url_completion": len([p for p in properties if p.get('url')]),
                "price_completion": len([p for p in properties if p.get('price')]),
                "size_completion": len([p for p in properties if p.get('sqm')]),
                "energy_completion": len([p for p in properties if p.get('energy_class')]),
                "complete_data_rate": len([p for p in properties 
                                         if all([p.get('url'), p.get('price'), 
                                               p.get('sqm'), p.get('energy_class')])]) / len(properties) * 100 if properties else 0
            }
        }
    
    def create_csv_summary(self, csv_file: Path):
        """Create CSV summary of all properties"""
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Property_ID,URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Property_Type,Rooms,Confidence,Timestamp\n")
            
            for i, prop in enumerate(self.collected_properties, 1):
                price_per_sqm = 0
                if prop.get('price') and prop.get('sqm'):
                    price_per_sqm = prop.get('price') / prop.get('sqm')
                
                f.write(f'ATHS-{i:04d},')
                f.write(f'"{prop.get("url", "")}",')
                f.write(f'{prop.get("price", 0)},')
                f.write(f'{prop.get("sqm", 0)},')
                f.write(f'"{prop.get("energy_class", "")}",')
                f.write(f'{price_per_sqm:.0f},')
                f.write(f'"{prop.get("neighborhood", "")}",')
                f.write(f'"{prop.get("property_type", "")}",')
                f.write(f'"{prop.get("rooms", "")}",')
                f.write(f'{prop.get("extraction_confidence", 0.9):.2f},')
                f.write(f'"{prop.get("timestamp", datetime.now().isoformat())}"')
                f.write('\n')

async def main():
    """Main execution function"""
    logger.info("🏛️ Starting ATHintel Scale to 1000 Properties")
    
    collector = ScaledDatasetCollector()
    
    try:
        # Collect scaled dataset
        properties = await collector.collect_scaled_dataset()
        
        # Save results
        json_file = await collector.save_scaled_dataset()
        
        # Generate final statistics
        stats = collector.generate_dataset_statistics()
        
        logger.info("🎉 Dataset Scaling Complete!")
        logger.info(f"📊 Final Count: {len(properties)} properties")
        logger.info(f"🏛️ Athens Center: {stats['geographic_distribution']['athens_center_focus']['count']} ({stats['geographic_distribution']['athens_center_focus']['percentage']:.1f}%)")
        logger.info(f"💰 Total Portfolio Value: €{stats['market_analysis']['price_statistics']['total_value']:,.0f}")
        logger.info(f"✅ Data Quality: {stats['quality_metrics']['complete_data_rate']:.1f}% complete")
        logger.info(f"📁 Dataset saved: {json_file}")
        
        return properties, json_file
        
    except Exception as e:
        logger.error(f"❌ Scaling failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())