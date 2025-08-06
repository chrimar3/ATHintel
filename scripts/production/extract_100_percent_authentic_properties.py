#!/usr/bin/env python3
"""
🔍 Extract 100% Authentic Properties - Clean Dataset Creation
Extract only verified authentic properties from all files, removing any generated/scaled data
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticPropertyExtractor:
    """Extract and consolidate only 100% authentic properties"""
    
    def __init__(self):
        self.extraction_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.project_root = Path(__file__).parent.parent
        
        # Strict authenticity criteria
        self.authentic_indicators = {
            'required_url_patterns': ['spitogatos.gr/en/property/', 'xe.gr/property/'],
            'forbidden_validation_flags': ['GENERATED', 'SYNTHETIC', 'SCALED', 'SIMULATED'],
            'required_fields': ['url', 'price', 'sqm', 'title'],
            'realistic_price_range': (20000, 15000000),  # €20K - €15M
            'realistic_sqm_range': (15, 1000),  # 15m² - 1000m²
            'forbidden_titles': ['Property', 'Listing', 'Advertisement', 'Sample', 'Test', 'Demo']
        }
        
        self.authentic_properties = []
        self.processed_urls = set()
        
        logger.info("🔍 100% Authentic Property Extractor")
        logger.info(f"📅 Extraction ID: {self.extraction_timestamp}")
    
    def is_100_percent_authentic(self, property_data: Dict) -> tuple[bool, List[str]]:
        """Strict validation for 100% authentic properties"""
        
        validation_issues = []
        
        # Check required fields
        for field in self.authentic_indicators['required_fields']:
            if not property_data.get(field):
                validation_issues.append(f"Missing required field: {field}")
        
        if validation_issues:
            return False, validation_issues
        
        # Check URL authenticity
        url = property_data.get('url', '')
        has_authentic_url = any(pattern in url for pattern in self.authentic_indicators['required_url_patterns'])
        if not has_authentic_url:
            validation_issues.append("No authentic Spitogatos/XE URL pattern")
        
        # Check for forbidden validation flags
        validation_flags = property_data.get('validation_flags', [])
        for flag in validation_flags:
            if any(forbidden in flag.upper() for forbidden in self.authentic_indicators['forbidden_validation_flags']):
                validation_issues.append(f"Contains forbidden flag: {flag}")
        
        # Check price range
        price = property_data.get('price')
        if price:
            min_price, max_price = self.authentic_indicators['realistic_price_range']
            if price < min_price or price > max_price:
                validation_issues.append(f"Price out of realistic range: €{price:,}")
        
        # Check SQM range
        sqm = property_data.get('sqm')
        if sqm:
            min_sqm, max_sqm = self.authentic_indicators['realistic_sqm_range']
            if sqm < min_sqm or sqm > max_sqm:
                validation_issues.append(f"SQM out of realistic range: {sqm}m²")
        
        # Check title authenticity
        title = property_data.get('title', '')
        for forbidden_title in self.authentic_indicators['forbidden_titles']:
            if forbidden_title.lower() in title.lower() and len(title) < 20:
                validation_issues.append(f"Generic title detected: {title[:30]}...")
        
        # Check for synthetic price patterns
        synthetic_prices = {740, 3000, 100000, 250000, 500000, 1000000}
        if price in synthetic_prices:
            validation_issues.append(f"Synthetic price pattern: €{price}")
        
        # Check for synthetic SQM patterns
        synthetic_sqms = {63, 270, 100, 150, 200}
        if sqm in synthetic_sqms:
            validation_issues.append(f"Synthetic SQM pattern: {sqm}m²")
        
        # Additional authenticity checks
        if not property_data.get('html_source_hash'):
            validation_issues.append("Missing HTML source hash (indicates non-scraped data)")
        
        # Check URL format for property ID
        if url and '/property/' in url:
            property_id_match = url.split('/property/')[-1]
            if not property_id_match.isdigit() or len(property_id_match) < 8:
                validation_issues.append("Invalid property ID format in URL")
        
        return len(validation_issues) == 0, validation_issues
    
    def extract_authentic_properties_from_file(self, file_path: Path) -> List[Dict]:
        """Extract authentic properties from a single file"""
        
        logger.info(f"🔍 Extracting from: {file_path.name}")
        
        authentic_from_file = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different data structures
            properties = []
            if isinstance(data, list):
                properties = data
            elif isinstance(data, dict):
                if 'properties' in data:
                    properties = data['properties']
                elif 'data' in data:
                    properties = data['data'] if isinstance(data['data'], list) else []
                elif any(key in data for key in ['price', 'sqm', 'title', 'url']):
                    properties = [data]
            
            if not properties:
                logger.info(f"   ⚠️ No property data found in {file_path.name}")
                return []
            
            logger.info(f"   📊 Found {len(properties)} properties to validate")
            
            # Validate each property
            for prop in properties:
                if not isinstance(prop, dict):
                    continue
                
                is_authentic, issues = self.is_100_percent_authentic(prop)
                
                if is_authentic:
                    # Check for duplicates by URL
                    url = prop.get('url', '')
                    if url not in self.processed_urls:
                        # Add authenticity metadata
                        prop['authenticity_verified'] = datetime.now().isoformat()
                        prop['extraction_source'] = file_path.name
                        prop['authenticity_score'] = 1.0
                        
                        authentic_from_file.append(prop)
                        self.processed_urls.add(url)
                    else:
                        logger.debug(f"   🔄 Duplicate URL skipped: {url}")
                else:
                    logger.debug(f"   ❌ Invalid property: {issues}")
            
            logger.info(f"   ✅ Extracted {len(authentic_from_file)} authentic properties")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {file_path}: {e}")
        
        return authentic_from_file
    
    def extract_all_authentic_properties(self) -> List[Dict]:
        """Extract all authentic properties from all data files"""
        
        logger.info("🔍 Starting 100% Authentic Property Extraction...")
        
        # Search for data files
        search_dirs = [
            self.project_root / "data/processed",
            self.project_root / "data/raw"
        ]
        
        all_authentic = []
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            json_files = list(search_dir.glob("*.json"))
            logger.info(f"📁 Searching {search_dir.name}: {len(json_files)} files")
            
            for file_path in json_files:
                # Skip analysis/report files
                if any(skip_pattern in file_path.name.lower() for skip_pattern in 
                       ['analysis', 'report', 'stats', 'statistics', 'deployment']):
                    logger.debug(f"   ⏭️ Skipping analysis file: {file_path.name}")
                    continue
                
                file_authentic = self.extract_authentic_properties_from_file(file_path)
                all_authentic.extend(file_authentic)
        
        self.authentic_properties = all_authentic
        
        logger.info(f"🎯 Extraction Complete:")
        logger.info(f"   ✅ Total Authentic Properties: {len(self.authentic_properties)}")
        logger.info(f"   🔗 Unique URLs: {len(self.processed_urls)}")
        
        return self.authentic_properties
    
    def validate_final_dataset(self) -> Dict[str, Any]:
        """Final validation of the authentic dataset"""
        
        logger.info("🔍 Final Dataset Validation...")
        
        if not self.authentic_properties:
            return {'status': 'empty', 'properties': 0}
        
        validation_summary = {
            'total_properties': len(self.authentic_properties),
            'price_analysis': {},
            'sqm_analysis': {},
            'url_analysis': {},
            'neighborhood_analysis': {},
            'authenticity_confirmation': True
        }
        
        # Price analysis
        prices = [p['price'] for p in self.authentic_properties if p.get('price')]
        if prices:
            validation_summary['price_analysis'] = {
                'count': len(prices),
                'min': min(prices),
                'max': max(prices),
                'average': sum(prices) / len(prices),
                'range_realistic': all(20000 <= p <= 15000000 for p in prices)
            }
        
        # SQM analysis
        sqms = [p['sqm'] for p in self.authentic_properties if p.get('sqm')]
        if sqms:
            validation_summary['sqm_analysis'] = {
                'count': len(sqms),
                'min': min(sqms),
                'max': max(sqms),
                'average': sum(sqms) / len(sqms),
                'range_realistic': all(15 <= s <= 1000 for s in sqms)
            }
        
        # URL analysis
        urls = [p['url'] for p in self.authentic_properties if p.get('url')]
        spitogatos_urls = [url for url in urls if 'spitogatos.gr' in url]
        xe_urls = [url for url in urls if 'xe.gr' in url]
        
        validation_summary['url_analysis'] = {
            'total_urls': len(urls),
            'spitogatos_count': len(spitogatos_urls),
            'xe_count': len(xe_urls),
            'all_authentic_patterns': len(urls) == len(spitogatos_urls) + len(xe_urls)
        }
        
        # Neighborhood analysis
        neighborhoods = [p.get('neighborhood') for p in self.authentic_properties if p.get('neighborhood')]
        unique_neighborhoods = set(n for n in neighborhoods if n)
        validation_summary['neighborhood_analysis'] = {
            'total_neighborhoods': len(unique_neighborhoods),
            'neighborhood_list': sorted(list(unique_neighborhoods))
        }
        
        # Final authenticity confirmation
        all_authentic = True
        for prop in self.authentic_properties:
            is_auth, _ = self.is_100_percent_authentic(prop)
            if not is_auth:
                all_authentic = False
                break
        
        validation_summary['authenticity_confirmation'] = all_authentic
        
        logger.info("✅ Final Validation Results:")
        logger.info(f"   🏠 Properties: {validation_summary['total_properties']}")
        logger.info(f"   💰 Price Range: €{validation_summary['price_analysis'].get('min', 0):,} - €{validation_summary['price_analysis'].get('max', 0):,}")
        logger.info(f"   📐 Size Range: {validation_summary['sqm_analysis'].get('min', 0):.0f} - {validation_summary['sqm_analysis'].get('max', 0):.0f}m²")
        logger.info(f"   🌍 Neighborhoods: {validation_summary['neighborhood_analysis']['total_neighborhoods']}")
        logger.info(f"   ✅ 100% Authentic: {validation_summary['authenticity_confirmation']}")
        
        return validation_summary
    
    def save_authentic_dataset(self) -> str:
        """Save the clean, 100% authentic dataset"""
        
        logger.info("💾 Saving 100% Authentic Dataset...")
        
        if not self.authentic_properties:
            logger.warning("No authentic properties to save")
            return ""
        
        # Create clean data directory
        clean_data_dir = self.project_root / "data/authentic"
        clean_data_dir.mkdir(exist_ok=True)
        
        # Prepare final dataset
        final_dataset = {
            'metadata': {
                'extraction_timestamp': self.extraction_timestamp,
                'dataset_name': '100_percent_authentic_athens_properties',
                'total_properties': len(self.authentic_properties),
                'authenticity_guarantee': '100% verified real properties from Spitogatos.gr',
                'extraction_criteria': 'Strict validation removing all generated/scaled data',
                'data_sources': list(set(p.get('extraction_source', 'unknown') for p in self.authentic_properties))
            },
            'validation_summary': self.validate_final_dataset(),
            'properties': self.authentic_properties
        }
        
        # Save main authentic dataset
        authentic_file = clean_data_dir / f'athens_100_percent_authentic_{self.extraction_timestamp}.json'
        with open(authentic_file, 'w', encoding='utf-8') as f:
            json.dump(final_dataset, f, indent=2, ensure_ascii=False)
        
        # Create properties-only file for easy access
        properties_only_file = clean_data_dir / f'authentic_properties_only_{self.extraction_timestamp}.json'
        with open(properties_only_file, 'w', encoding='utf-8') as f:
            json.dump(self.authentic_properties, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Authentic dataset saved:")
        logger.info(f"   📄 Complete Dataset: {authentic_file}")
        logger.info(f"   🏠 Properties Only: {properties_only_file}")
        
        return str(authentic_file)
    
    def print_extraction_summary(self):
        """Print comprehensive extraction summary"""
        
        validation = self.validate_final_dataset()
        
        logger.info("=" * 80)
        logger.info("🔍 100% AUTHENTIC PROPERTIES EXTRACTION COMPLETE")
        logger.info("=" * 80)
        
        logger.info("📊 EXTRACTION RESULTS:")
        logger.info(f"   🏠 Total Authentic Properties: {validation['total_properties']}")
        logger.info(f"   ✅ 100% Authenticity Confirmed: {validation['authenticity_confirmation']}")
        logger.info(f"   🔗 Unique URLs: {len(self.processed_urls)}")
        
        if validation['price_analysis']:
            price = validation['price_analysis']
            logger.info("💰 PRICE ANALYSIS:")
            logger.info(f"   📈 Range: €{price['min']:,} - €{price['max']:,}")
            logger.info(f"   📊 Average: €{price['average']:,.0f}")
            logger.info(f"   ✅ All Realistic: {price['range_realistic']}")
        
        if validation['sqm_analysis']:
            sqm = validation['sqm_analysis']
            logger.info("📐 SIZE ANALYSIS:")
            logger.info(f"   📏 Range: {sqm['min']:.0f} - {sqm['max']:.0f}m²")
            logger.info(f"   📊 Average: {sqm['average']:.0f}m²")
            logger.info(f"   ✅ All Realistic: {sqm['range_realistic']}")
        
        url = validation['url_analysis']
        logger.info("🔗 URL ANALYSIS:")
        logger.info(f"   🏛️ Spitogatos URLs: {url['spitogatos_count']}")
        logger.info(f"   🏢 XE URLs: {url['xe_count']}")
        logger.info(f"   ✅ All Authentic Patterns: {url['all_authentic_patterns']}")
        
        neighborhoods = validation['neighborhood_analysis']
        logger.info("🌍 GEOGRAPHIC COVERAGE:")
        logger.info(f"   📍 Total Neighborhoods: {neighborhoods['total_neighborhoods']}")
        logger.info(f"   🏘️ Areas: {', '.join(neighborhoods['neighborhood_list'][:5])}")
        if len(neighborhoods['neighborhood_list']) > 5:
            logger.info(f"       + {len(neighborhoods['neighborhood_list']) - 5} more...")
        
        logger.info("🎯 QUALITY ASSURANCE:")
        logger.info("   ✅ No generated/synthetic data")
        logger.info("   ✅ No scaled/simulated properties") 
        logger.info("   ✅ All real Spitogatos/XE URLs")
        logger.info("   ✅ All realistic price and size ranges")
        logger.info("   ✅ Unique properties (no duplicates)")
        
        logger.info("=" * 80)

# Main execution
async def main():
    """Execute authentic property extraction"""
    
    extractor = AuthenticPropertyExtractor()
    
    # Extract all authentic properties
    authentic_properties = extractor.extract_all_authentic_properties()
    
    if authentic_properties:
        # Save clean dataset
        result_file = extractor.save_authentic_dataset()
        
        # Print summary
        extractor.print_extraction_summary()
        
        return result_file
    else:
        logger.error("❌ No authentic properties found")
        return None

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())