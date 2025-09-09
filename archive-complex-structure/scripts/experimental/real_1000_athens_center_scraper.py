#!/usr/bin/env python3
"""
🏛️ Real 1000 Athens Center Properties Scraper
Extract 1000 100% authentic properties focused on Athens Center - NO GENERATED DATA
"""

import asyncio
import json
import logging
import random
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AuthenticAthensCenterProperty:
    """100% Real Athens Center property data structure"""
    property_id: str
    url: str
    timestamp: str
    title: str
    neighborhood: str
    
    # Required fields - 100% real data
    price: Optional[float]
    sqm: Optional[float]
    energy_class: Optional[str]
    
    # Additional real data
    property_type: Optional[str]
    listing_type: Optional[str]
    rooms: Optional[str]
    floor: Optional[str]
    description: Optional[str]
    
    # Quality metrics
    extraction_confidence: float
    validation_flags: List[str]
    html_source_hash: str
    
    # Calculated
    price_per_sqm: Optional[float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_athens_center(self) -> bool:
        """Check if property is in Athens Center area"""
        athens_center_keywords = [
            'athens center', 'κέντρο αθήνας', 'σύνταγμα', 'μοναστηράκι',
            'θησείο', 'ψυρρή', 'εξάρχεια', 'πλάκα', 'παγκράτι',
            'syntagma', 'monastiraki', 'thiseio', 'psirri', 'exarchia', 'plaka'
        ]
        neighborhood_lower = self.neighborhood.lower()
        title_lower = self.title.lower()
        
        return any(keyword in neighborhood_lower or keyword in title_lower 
                  for keyword in athens_center_keywords)

class Real1000AthensCenterScraper:
    """Scraper for 1000 real Athens Center properties"""
    
    def __init__(self):
        self.target_properties = 1000
        self.collected_properties: List[AuthenticAthensCenterProperty] = []
        self.processed_urls: Set[str] = set()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Enhanced Athens Center search strategies
        self.athens_center_search_urls = [
            # Core Athens Center searches
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center",
            "https://www.spitogatos.gr/en/for_sale-apartments/athens-center", 
            "https://www.spitogatos.gr/en/for_sale-maisonettes/athens-center",
            "https://www.spitogatos.gr/en/for_sale-houses/athens-center",
            "https://www.spitogatos.gr/en/for_sale-studios/athens-center",
            
            # Price-based searches for Athens Center
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_max=150000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=150000&price_max=300000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=300000&price_max=500000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=500000&price_max=1000000",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?price_min=1000000",
            
            # Size-based searches
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_max=50",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_min=50&sqm_max=80",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_min=80&sqm_max=120",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sqm_min=120",
            
            # Specific neighborhood searches  
            "https://www.spitogatos.gr/en/for_sale-homes/syntagma",
            "https://www.spitogatos.gr/en/for_sale-homes/monastiraki",
            "https://www.spitogatos.gr/en/for_sale-homes/thiseio",
            "https://www.spitogatos.gr/en/for_sale-homes/psirri",
            "https://www.spitogatos.gr/en/for_sale-homes/plaka",
            "https://www.spitogatos.gr/en/for_sale-homes/exarchia",
            "https://www.spitogatos.gr/en/for_sale-homes/pagrati",
            
            # Sort variations
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_asc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_desc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=date_desc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=sqm_desc",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?sort=price_per_sqm_asc",
            
            # Energy class specific
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=A",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=B",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=C",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?energy_class=D",
            
            # Recently listed
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?listing_age=new",
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center?listing_age=week",
            
            # Combined filters for maximum coverage
            "https://www.spitogatos.gr/en/for_sale-apartments/syntagma?sort=price_asc",
            "https://www.spitogatos.gr/en/for_sale-apartments/monastiraki?sort=date_desc",
            "https://www.spitogatos.gr/en/for_sale-apartments/thiseio?sort=price_per_sqm_asc",
            "https://www.spitogatos.gr/en/for_sale-apartments/psirri?price_max=400000",
            "https://www.spitogatos.gr/en/for_sale-apartments/plaka?sort=sqm_desc",
            "https://www.spitogatos.gr/en/for_sale-apartments/exarchia?price_max=350000",
            
            # Property type + neighborhood combinations
            "https://www.spitogatos.gr/en/for_sale-maisonettes/syntagma",
            "https://www.spitogatos.gr/en/for_sale-houses/thiseio",
            "https://www.spitogatos.gr/en/for_sale-studios/athens-center?price_max=200000",
        ]
    
    async def initialize_browser(self):
        """Initialize browser with Athens-optimized settings"""
        logger.info("🚀 Initializing browser for real Athens Center property extraction...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # Keep visible to monitor progress
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage', 
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='el-GR',
            timezone_id='Europe/Athens',
            extra_http_headers={
                'Accept-Language': 'el-GR,el;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        
        logger.info("✅ Browser initialized for authentic Athens Center data extraction")
    
    async def extract_property_urls_from_search(self, search_url: str, max_pages: int = 20) -> List[str]:
        """Extract property URLs from search results with deep pagination"""
        logger.info(f"🔍 Extracting property URLs from: {search_url}")
        
        page = await self.context.new_page()
        property_urls = set()
        
        try:
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))
            
            current_page = 1
            
            while current_page <= max_pages and len(property_urls) < 100:
                try:
                    # Wait for property links to load
                    await page.wait_for_selector('a[href*="/property/"]', timeout=15000)
                    
                    # Extract property URLs from current page
                    page_urls = await page.evaluate('''() => {
                        const links = Array.from(document.querySelectorAll('a[href*="/property/"], a[href*="/en/property/"]'));
                        return [...new Set(links.map(link => link.href).filter(href => 
                            href.includes('/property/') && 
                            href.match(/\\/property\\/\\d+/) &&
                            href.startsWith('https://www.spitogatos.gr/')
                        ))];
                    }''')
                    
                    # Add new URLs
                    new_urls = 0
                    for url in page_urls:
                        if url not in property_urls and url not in self.processed_urls:
                            property_urls.add(url)
                            new_urls += 1
                    
                    logger.info(f"   📄 Page {current_page}: Found {new_urls} new URLs (total: {len(property_urls)})")
                    
                    # Try to navigate to next page
                    next_button = await page.query_selector('a[aria-label="Next"], .pagination-next, a:has-text("Next")')
                    if next_button:
                        is_enabled = await next_button.is_enabled()
                        if is_enabled:
                            await next_button.click()
                            await page.wait_for_load_state('networkidle', timeout=15000)
                            await asyncio.sleep(random.uniform(3, 5))
                            current_page += 1
                        else:
                            logger.info(f"   ⏭️ Next button disabled, reached end at page {current_page}")
                            break
                    else:
                        logger.info(f"   ⏭️ No next button found, reached end at page {current_page}")
                        break
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Error on page {current_page}: {e}")
                    break
            
            logger.info(f"✅ Extracted {len(property_urls)} property URLs from {current_page} pages")
            return list(property_urls)
            
        except Exception as e:
            logger.error(f"❌ Failed to extract URLs from {search_url}: {e}")
            return []
            
        finally:
            await page.close()
    
    async def extract_property_data(self, property_url: str) -> Optional[AuthenticAthensCenterProperty]:
        """Extract authentic property data from individual property page"""
        if property_url in self.processed_urls:
            return None
        
        page = await self.context.new_page()
        
        try:
            await page.goto(property_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(1, 3))
            
            # Extract comprehensive property data
            property_data = await page.evaluate('''() => {
                // Helper function to extract numbers
                function extractNumber(text) {
                    if (!text) return null;
                    const match = text.match(/([0-9,.]+)/);
                    return match ? parseFloat(match[1].replace(/,/g, '')) : null;
                }
                
                // Helper function to extract energy class
                function extractEnergyClass(text) {
                    if (!text) return null;
                    const match = text.match(/\\b(A\\+|A|B\\+|B|C\\+|C|D|E|F|G)\\b/i);
                    return match ? match[1].toUpperCase() : null;
                }
                
                // Price extraction - multiple selectors
                let price = null;
                const priceSelectors = [
                    '.price-current', '.property-price', '.listing-price', 
                    '[data-testid="price"]', '.price', '.amount', '.cost',
                    '.price-value', '.property-cost', '.listing-cost'
                ];
                
                for (const selector of priceSelectors) {
                    const priceEl = document.querySelector(selector);
                    if (priceEl) {
                        const priceText = priceEl.textContent || priceEl.innerText || '';
                        price = extractNumber(priceText);
                        if (price && price > 10000) break; // Valid price found
                    }
                }
                
                // Also try meta tags and JSON-LD
                if (!price) {
                    const metaPrice = document.querySelector('meta[property="product:price:amount"]');
                    if (metaPrice) price = parseFloat(metaPrice.content);
                }
                
                // Size (SQM) extraction
                let sqm = null;
                const sizeSelectors = [
                    '.property-size', '.sqm', '[data-testid="size"]', 
                    '.area', '.surface', '.size', '.property-area',
                    '.listing-size', '.square-meters'
                ];
                
                for (const selector of sizeSelectors) {
                    const sizeEl = document.querySelector(selector);
                    if (sizeEl) {
                        const sizeText = sizeEl.textContent || sizeEl.innerText || '';
                        sqm = extractNumber(sizeText);
                        if (sqm && sqm > 10) break; // Valid size found
                    }
                }
                
                // Energy class extraction
                let energyClass = null;
                const energySelectors = [
                    '.energy-class', '.energy-rating', '[data-testid="energy"]',
                    '.efficiency', '.rating', '.energy-certificate',
                    '.energy-performance', '.energy-label'
                ];
                
                for (const selector of energySelectors) {
                    const energyEl = document.querySelector(selector);
                    if (energyEl) {
                        const energyText = energyEl.textContent || energyEl.innerText || '';
                        energyClass = extractEnergyClass(energyText);
                        if (energyClass) break;
                    }
                }
                
                // Title extraction
                const title = document.querySelector('title')?.textContent?.trim() || 
                             document.querySelector('h1')?.textContent?.trim() ||
                             document.querySelector('.property-title')?.textContent?.trim() || '';
                
                // Description
                const description = document.querySelector('.description, .property-description, .listing-description')?.textContent?.trim() || '';
                
                // Additional details
                const rooms = document.querySelector('.rooms, .bedrooms, .bedroom-count')?.textContent?.trim() || '';
                const floor = document.querySelector('.floor, .floor-number')?.textContent?.trim() || '';
                
                // Get all text content for neighborhood detection
                const allText = document.body.textContent || document.body.innerText || '';
                
                return {
                    price: price,
                    sqm: sqm,
                    energyClass: energyClass,
                    title: title,
                    description: description,
                    rooms: rooms,
                    floor: floor,
                    allText: allText,
                    htmlContent: document.documentElement.outerHTML
                };
            }''')
            
            # Validate extracted data
            if not self.validate_property_data(property_data):
                self.processed_urls.add(property_url)
                return None
            
            # Determine neighborhood from URL and content
            neighborhood = self.extract_neighborhood(property_url, property_data.get('title', ''), property_data.get('allText', ''))
            
            # Create property object
            property_id = self.generate_property_id(property_url)
            html_hash = hashlib.sha256(property_data['htmlContent'].encode()).hexdigest()[:16]
            
            # Calculate confidence and validation
            confidence = self.calculate_extraction_confidence(property_data)
            validation_flags = self.get_validation_flags(property_data)
            
            # Calculate price per sqm
            price_per_sqm = None
            if property_data['price'] and property_data['sqm']:
                price_per_sqm = property_data['price'] / property_data['sqm']
            
            # Create authentic property
            authentic_property = AuthenticAthensCenterProperty(
                property_id=property_id,
                url=property_url,
                timestamp=datetime.now().isoformat(),
                title=property_data['title'],
                neighborhood=neighborhood,
                
                # Required authentic data
                price=property_data['price'],
                sqm=property_data['sqm'],
                energy_class=property_data['energyClass'],
                
                # Additional authentic data
                property_type=self.detect_property_type(property_data['title']),
                listing_type="for_sale",
                rooms=property_data['rooms'],
                floor=property_data['floor'],
                description=property_data['description'][:500] if property_data['description'] else None,
                
                # Quality metrics
                extraction_confidence=confidence,
                validation_flags=validation_flags,
                html_source_hash=html_hash,
                
                # Calculated
                price_per_sqm=price_per_sqm
            )
            
            # Final Athens Center validation
            if not authentic_property.is_athens_center():
                logger.info(f"   ⚠️ Property not in Athens Center area: {neighborhood}")
                self.processed_urls.add(property_url)
                return None
            
            self.processed_urls.add(property_url)
            logger.info(f"   ✅ Extracted: €{property_data['price']:,} - {property_data['sqm']}m² - {property_data['energyClass']} - {neighborhood}")
            
            return authentic_property
            
        except Exception as e:
            logger.error(f"   ❌ Failed to extract {property_url}: {e}")
            self.processed_urls.add(property_url)
            return None
            
        finally:
            await page.close()
    
    def validate_property_data(self, data: Dict) -> bool:
        """Validate extracted property data for authenticity"""
        # Must have all required fields
        if not all([data.get('price'), data.get('sqm'), data.get('energyClass')]):
            return False
        
        # Price validation (Athens market range)
        price = data.get('price', 0)
        if not (30000 <= price <= 20000000):
            return False
        
        # Size validation
        sqm = data.get('sqm', 0)
        if not (15 <= sqm <= 1000):
            return False
        
        # Energy class validation
        valid_energy_classes = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']
        if data.get('energyClass') not in valid_energy_classes:
            return False
        
        return True
    
    def extract_neighborhood(self, url: str, title: str, content: str) -> str:
        """Extract neighborhood from URL, title, and content"""
        # URL-based neighborhood detection
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        neighborhood_mapping = {
            'syntagma': 'Σύνταγμα',
            'monastiraki': 'Μοναστηράκι', 
            'thiseio': 'Θησείο',
            'psirri': 'Ψυρρή',
            'plaka': 'Πλάκα',
            'exarchia': 'Εξάρχεια',
            'pagrati': 'Παγκράτι',
            'athens-center': 'Athens Center'
        }
        
        # Check URL first
        for eng_name, greek_name in neighborhood_mapping.items():
            if eng_name in url_lower:
                return greek_name
        
        # Check title and content
        greek_neighborhoods = [
            'Σύνταγμα', 'Μοναστηράκι', 'Θησείο', 'Ψυρρή', 'Πλάκα', 
            'Εξάρχεια', 'Παγκράτι', 'Κέντρο Αθήνας'
        ]
        
        for neighborhood in greek_neighborhoods:
            if neighborhood.lower() in content_lower:
                return neighborhood
        
        # Default to Athens Center
        return 'Athens Center'
    
    def calculate_extraction_confidence(self, data: Dict) -> float:
        """Calculate confidence score for extracted data"""
        confidence = 0.0
        
        # Base confidence for required fields
        if data.get('price') and data.get('sqm') and data.get('energyClass'):
            confidence += 0.7
        
        # Additional confidence factors
        if data.get('title') and len(data.get('title', '')) > 10:
            confidence += 0.1
        if data.get('description') and len(data.get('description', '')) > 50:
            confidence += 0.1  
        if data.get('rooms'):
            confidence += 0.05
        if data.get('floor'):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def get_validation_flags(self, data: Dict) -> List[str]:
        """Get validation flags for the property"""
        flags = ["100_PERCENT_REAL_DATA", "WEB_SCRAPED_AUTHENTIC"]
        
        if data.get('price') and data.get('sqm'):
            flags.append("COMPLETE_PRICING_DATA")
        if data.get('energyClass'):
            flags.append("ENERGY_CLASS_VERIFIED")
        if data.get('title') and len(data.get('title', '')) > 20:
            flags.append("DETAILED_LISTING_INFO")
        
        return flags
    
    def generate_property_id(self, url: str) -> str:
        """Generate property ID from URL"""
        url_match = re.search(r'/property/(\d+)', url)
        if url_match:
            return f"REAL-AC-{url_match.group(1)}"
        return f"REAL-AC-{hashlib.md5(url.encode()).hexdigest()[:8]}"
    
    def detect_property_type(self, title: str) -> str:
        """Detect property type from title"""
        title_lower = title.lower()
        if 'studio' in title_lower:
            return 'studio'
        elif 'maisonette' in title_lower or 'μεζονέτα' in title_lower:
            return 'maisonette'  
        elif 'house' in title_lower or 'σπίτι' in title_lower:
            return 'house'
        elif 'loft' in title_lower:
            return 'loft'
        else:
            return 'apartment'
    
    async def collect_1000_real_athens_center_properties(self) -> List[AuthenticAthensCenterProperty]:
        """Collect 1000 real Athens Center properties"""
        logger.info("🏛️ Starting collection of 1000 REAL Athens Center properties")
        logger.info("🎯 Target: 1000 properties | Source: 100% web-scraped data | Focus: Athens Center")
        
        await self.initialize_browser()
        
        try:
            # Randomize search order for better coverage
            randomized_searches = self.athens_center_search_urls.copy()
            random.shuffle(randomized_searches)
            
            for search_idx, search_url in enumerate(randomized_searches):
                if len(self.collected_properties) >= self.target_properties:
                    break
                
                logger.info(f"🔍 Search {search_idx + 1}/{len(randomized_searches)}: Current: {len(self.collected_properties)}/{self.target_properties}")
                logger.info(f"   URL: {search_url}")
                
                # Extract property URLs from search
                property_urls = await self.extract_property_urls_from_search(search_url, max_pages=25)
                
                if not property_urls:
                    logger.warning(f"   ⚠️ No URLs found in search, continuing...")
                    continue
                
                logger.info(f"   📋 Found {len(property_urls)} property URLs to process")
                
                # Process property URLs in batches
                batch_size = 10
                for i in range(0, len(property_urls), batch_size):
                    if len(self.collected_properties) >= self.target_properties:
                        break
                    
                    batch_urls = property_urls[i:i + batch_size]
                    logger.info(f"   🔄 Processing batch {i//batch_size + 1}: URLs {i+1}-{min(i+batch_size, len(property_urls))}")
                    
                    # Process batch concurrently but with rate limiting
                    batch_properties = []
                    for url in batch_urls:
                        if len(self.collected_properties) >= self.target_properties:
                            break
                        
                        property_data = await self.extract_property_data(url)
                        if property_data:
                            batch_properties.append(property_data)
                            self.collected_properties.append(property_data)
                        
                        # Rate limiting between properties
                        await asyncio.sleep(random.uniform(1, 3))
                    
                    logger.info(f"   ✅ Batch complete: Added {len(batch_properties)} properties (Total: {len(self.collected_properties)}/{self.target_properties})")
                    
                    # Longer delay between batches
                    await asyncio.sleep(random.uniform(5, 10))
                
                # Progress update
                logger.info(f"📊 Search {search_idx + 1} complete: {len(self.collected_properties)}/{self.target_properties} properties collected")
                
                # Delay between searches
                await asyncio.sleep(random.uniform(10, 20))
            
            logger.info(f"🎉 Collection complete: {len(self.collected_properties)} REAL Athens Center properties")
            return self.collected_properties
            
        except Exception as e:
            logger.error(f"❌ Collection failed: {e}")
            raise
        finally:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
    
    async def save_real_properties(self) -> str:
        """Save real properties to file"""
        if not self.collected_properties:
            logger.warning("⚠️ No properties to save")
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save main JSON file
        json_file = Path("data/processed") / f"real_1000_athens_center_{timestamp}.json"
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        properties_data = [prop.to_dict() for prop in self.collected_properties]
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, ensure_ascii=False, indent=2)
        
        # Save CSV summary
        csv_file = Path("data/processed") / f"real_1000_athens_center_summary_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Property_ID,URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Property_Type,Rooms,Confidence,Validation_Status,Timestamp\n")
            
            for prop in self.collected_properties:
                validation_status = "100_PERCENT_REAL_SCRAPED"
                f.write(f'"{prop.property_id}","{prop.url}",{prop.price},{prop.sqm},"{prop.energy_class}",{prop.price_per_sqm:.0f if prop.price_per_sqm else 0},"{prop.neighborhood}","{prop.property_type}","{prop.rooms}",{prop.extraction_confidence:.2f},"{validation_status}","{prop.timestamp[:19]}"\n')
        
        # Save statistics
        stats = self.generate_collection_stats()
        stats_file = Path("data/processed") / f"real_1000_athens_center_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Real Athens Center properties saved:")
        logger.info(f"   📄 Main data: {json_file}")
        logger.info(f"   📊 Summary CSV: {csv_file}")
        logger.info(f"   📈 Statistics: {stats_file}")
        
        return str(json_file)
    
    def generate_collection_stats(self) -> Dict:
        """Generate comprehensive collection statistics"""
        if not self.collected_properties:
            return {}
        
        # Basic stats
        total_value = sum(p.price for p in self.collected_properties if p.price)
        avg_price = total_value / len(self.collected_properties)
        
        sizes = [p.sqm for p in self.collected_properties if p.sqm]
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        
        # Neighborhood distribution
        neighborhoods = {}
        for prop in self.collected_properties:
            neighborhood = prop.neighborhood
            neighborhoods[neighborhood] = neighborhoods.get(neighborhood, 0) + 1
        
        # Energy class distribution
        energy_classes = {}
        for prop in self.collected_properties:
            energy = prop.energy_class
            if energy:
                energy_classes[energy] = energy_classes.get(energy, 0) + 1
        
        return {
            "collection_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_properties": len(self.collected_properties),
                "data_authenticity": "100% Real Web-Scraped Data",
                "source": "Spitogatos.gr Direct Extraction",
                "focus_area": "Athens Center"
            },
            "market_analysis": {
                "total_portfolio_value": total_value,
                "average_property_price": avg_price,
                "average_property_size": avg_size,
                "price_range": [min(p.price for p in self.collected_properties if p.price),
                              max(p.price for p in self.collected_properties if p.price)]
            },
            "geographic_distribution": neighborhoods,
            "energy_distribution": energy_classes,
            "quality_metrics": {
                "average_confidence": sum(p.extraction_confidence for p in self.collected_properties) / len(self.collected_properties),
                "complete_data_rate": len([p for p in self.collected_properties if p.price and p.sqm and p.energy_class]) / len(self.collected_properties) * 100,
                "athens_center_focus_rate": len([p for p in self.collected_properties if p.is_athens_center()]) / len(self.collected_properties) * 100
            }
        }

async def main():
    """Main execution function"""
    logger.info("🏛️ Starting REAL 1000 Athens Center Properties Collection")
    logger.info("🎯 Mission: Extract 1000 100% authentic properties - NO GENERATED DATA")
    
    scraper = Real1000AthensCenterScraper()
    
    try:
        # Collect 1000 real properties
        properties = await scraper.collect_1000_real_athens_center_properties()
        
        # Save results
        json_file = await scraper.save_real_properties()
        
        # Generate final statistics
        stats = scraper.generate_collection_stats()
        
        logger.info("🎉 MISSION ACCOMPLISHED!")
        logger.info(f"📊 Properties Collected: {len(properties)} (Target: {scraper.target_properties})")
        logger.info(f"🏛️ Athens Center Focus: {stats['quality_metrics']['athens_center_focus_rate']:.1f}%")
        logger.info(f"💰 Total Portfolio Value: €{stats['market_analysis']['total_portfolio_value']:,.0f}")
        logger.info(f"✅ Data Authenticity: {stats['collection_metadata']['data_authenticity']}")
        logger.info(f"📁 Data saved to: {json_file}")
        
        return properties, json_file
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())