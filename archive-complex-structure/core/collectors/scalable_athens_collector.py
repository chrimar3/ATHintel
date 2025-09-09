#!/usr/bin/env python3
"""
🏛️ Scalable Athens Property Collector
Enhanced multi-agent collector for scaling to 1000+ properties with maintained quality
"""

import asyncio
import aiohttp
import json
import logging
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import hashlib
import re
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScaledProperty:
    """Enhanced property data structure for scaled collection"""
    property_id: str
    url: str
    timestamp: str
    title: str
    neighborhood: str
    block_id: Optional[str]
    
    # Required fields
    price: Optional[float]
    sqm: Optional[float]
    energy_class: Optional[str]
    
    # Enhanced fields for scale
    property_type: Optional[str]
    listing_type: Optional[str]
    rooms: Optional[str]
    floor: Optional[str]
    year_built: Optional[int]
    
    # Quality metrics
    extraction_confidence: float
    data_quality_score: float
    validation_flags: List[str]
    collection_method: str
    
    # Calculated fields
    price_per_sqm: Optional[float]
    html_source_hash: str
    geo_coordinates: Optional[Tuple[float, float]]

class ScalableAthensBrowser:
    """Enhanced browser management for concurrent collection"""
    
    def __init__(self, concurrent_browsers: int = 5):
        self.concurrent_browsers = concurrent_browsers
        self.browser_pool: List[Browser] = []
        self.context_pool: List[BrowserContext] = []
        self.active_pages: Set[Page] = set()
        
    async def initialize_browser_pool(self):
        """Initialize pool of browsers for concurrent processing"""
        playwright = await async_playwright().start()
        
        for i in range(self.concurrent_browsers):
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    f'--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            context = await browser.new_context(
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
                }
            )
            
            self.browser_pool.append(browser)
            self.context_pool.append(context)
            
        logger.info(f"✅ Initialized {len(self.browser_pool)} browsers in pool")
    
    async def get_page(self) -> Page:
        """Get available page from pool"""
        available_context = None
        for context in self.context_pool:
            if len(context.pages) < 3:  # Max 3 pages per context
                available_context = context
                break
        
        if not available_context:
            available_context = random.choice(self.context_pool)
        
        page = await available_context.new_page()
        self.active_pages.add(page)
        return page
    
    async def release_page(self, page: Page):
        """Return page to pool"""
        if page in self.active_pages:
            self.active_pages.remove(page)
            await page.close()
    
    async def close_all(self):
        """Close all browsers and contexts"""
        for page in self.active_pages.copy():
            await page.close()
        
        for context in self.context_pool:
            await context.close()
        
        for browser in self.browser_pool:
            await browser.close()

class EnhancedNeighborhoodMapper:
    """Enhanced neighborhood mapping with block-level granularity"""
    
    ATHENS_NEIGHBORHOODS = {
        # Premium Districts
        "Κολωνάκι": {
            "priority": 1,
            "expected_properties": 80,
            "avg_price_per_sqm": 6000,
            "blocks": ["KOL-001", "KOL-002", "KOL-003", "KOL-004", "KOL-005"],
            "search_strategies": ["luxury", "energy_efficient", "large_properties"]
        },
        "Πλάκα": {
            "priority": 1, 
            "expected_properties": 45,
            "avg_price_per_sqm": 7500,
            "blocks": ["PLA-001", "PLA-002", "PLA-003"],
            "search_strategies": ["heritage", "tourism", "premium"]
        },
        "Κουκάκι": {
            "priority": 1,
            "expected_properties": 60,
            "avg_price_per_sqm": 4800,
            "blocks": ["KOU-001", "KOU-002", "KOU-003", "KOU-004"],
            "search_strategies": ["emerging", "gentrification", "value"]
        },
        
        # Central Districts  
        "Εξάρχεια": {
            "priority": 2,
            "expected_properties": 65,
            "avg_price_per_sqm": 3500,
            "blocks": ["EXA-001", "EXA-002", "EXA-003", "EXA-004"],
            "search_strategies": ["cultural", "student", "bohemian"]
        },
        "Ψυρρή": {
            "priority": 2,
            "expected_properties": 50,
            "avg_price_per_sqm": 4200,
            "blocks": ["PSY-001", "PSY-002", "PSY-003"],
            "search_strategies": ["nightlife", "renovation", "artistic"]
        },
        "Μοναστηράκι": {
            "priority": 2,
            "expected_properties": 35,
            "avg_price_per_sqm": 5000,
            "blocks": ["MON-001", "MON-002"],
            "search_strategies": ["historic", "tourism", "central"]
        },
        
        # Value Districts
        "Κηφισιά": {
            "priority": 2,
            "expected_properties": 85,
            "avg_price_per_sqm": 3800,
            "blocks": ["KEF-001", "KEF-002", "KEF-003", "KEF-004", "KEF-005"],
            "search_strategies": ["suburban", "family", "green"]
        },
        "Αμπελόκηποι": {
            "priority": 2,
            "expected_properties": 70,
            "avg_price_per_sqm": 2900,
            "blocks": ["AMP-001", "AMP-002", "AMP-003", "AMP-004"],
            "search_strategies": ["residential", "middle_class", "transport"]
        },
        "Νέα Σμύρνη": {
            "priority": 2,
            "expected_properties": 90,
            "avg_price_per_sqm": 2800,
            "blocks": ["NSM-001", "NSM-002", "NSM-003", "NSM-004", "NSM-005"],
            "search_strategies": ["family", "suburban", "emerging"]
        },
        
        # Growth Areas
        "Κηψέλι": {
            "priority": 3,
            "expected_properties": 75,
            "avg_price_per_sqm": 2200,
            "blocks": ["KIP-001", "KIP-002", "KIP-003", "KIP-004"],
            "search_strategies": ["growth", "renovation", "value"]
        },
        "Πετράλωνα": {
            "priority": 3,
            "expected_properties": 55,
            "avg_price_per_sqm": 3200,
            "blocks": ["PET-001", "PET-002", "PET-003"],
            "search_strategies": ["emerging", "trendy", "investment"]
        },
        "Γκάζι": {
            "priority": 3,
            "expected_properties": 40,
            "avg_price_per_sqm": 3600,
            "blocks": ["GAZ-001", "GAZ-002"],
            "search_strategies": ["industrial", "transformation", "modern"]
        },
    }
    
    @classmethod
    def get_priority_neighborhoods(cls, priority: int = 1) -> List[str]:
        """Get neighborhoods by priority level"""
        return [name for name, data in cls.ATHENS_NEIGHBORHOODS.items() 
                if data["priority"] == priority]
    
    @classmethod
    def get_total_expected_properties(cls, priority: int = None) -> int:
        """Calculate total expected properties"""
        if priority:
            neighborhoods = cls.get_priority_neighborhoods(priority)
            return sum(cls.ATHENS_NEIGHBORHOODS[n]["expected_properties"] for n in neighborhoods)
        return sum(data["expected_properties"] for data in cls.ATHENS_NEIGHBORHOODS.values())

class AdvancedSearchStrategy:
    """Enhanced search strategies for comprehensive property discovery"""
    
    BASE_URLS = {
        "spitogatos": "https://www.spitogatos.gr/en/for_sale-homes/athens",
        "xe": "https://www.xe.gr/en/property-search/athens"
    }
    
    SEARCH_STRATEGIES = {
        "price_segments": [
            {"min": 0, "max": 100000, "name": "budget"},
            {"min": 100000, "max": 300000, "name": "mid_range"},
            {"min": 300000, "max": 500000, "name": "premium"},
            {"min": 500000, "max": 1000000, "name": "luxury"},
            {"min": 1000000, "max": None, "name": "ultra_luxury"}
        ],
        "size_segments": [
            {"min": 0, "max": 50, "name": "studio"},
            {"min": 50, "max": 100, "name": "medium"},
            {"min": 100, "max": 150, "name": "large"},
            {"min": 150, "max": None, "name": "extra_large"}
        ],
        "energy_classes": ["A+", "A", "B+", "B", "C+", "C", "D", "E", "F", "G"],
        "property_types": ["apartment", "maisonette", "house", "studio", "loft"],
        "listing_age": ["new", "1_week", "1_month", "3_months"]
    }
    
    @classmethod
    def generate_search_urls(cls, neighborhood: str, platform: str = "spitogatos") -> List[str]:
        """Generate comprehensive search URLs for a neighborhood"""
        base_url = cls.BASE_URLS[platform]
        search_urls = []
        
        # Basic neighborhood search
        neighborhood_encoded = neighborhood.replace(" ", "-").lower()
        search_urls.append(f"{base_url}/{neighborhood_encoded}")
        
        # Price segment searches
        for price_seg in cls.SEARCH_STRATEGIES["price_segments"]:
            url = f"{base_url}/{neighborhood_encoded}?price_min={price_seg['min']}"
            if price_seg["max"]:
                url += f"&price_max={price_seg['max']}"
            search_urls.append(url)
        
        # Size segment searches
        for size_seg in cls.SEARCH_STRATEGIES["size_segments"]:
            url = f"{base_url}/{neighborhood_encoded}?sqm_min={size_seg['min']}"
            if size_seg["max"]:
                url += f"&sqm_max={size_seg['max']}"
            search_urls.append(url)
        
        # Property type searches
        for prop_type in cls.SEARCH_STRATEGIES["property_types"]:
            search_urls.append(f"{base_url}/{neighborhood_encoded}?type={prop_type}")
        
        # Sort variations
        sort_options = ["price_asc", "price_desc", "date_desc", "sqm_desc"]
        for sort_opt in sort_options:
            search_urls.append(f"{base_url}/{neighborhood_encoded}?sort={sort_opt}")
        
        return search_urls[:25]  # Limit to 25 strategies per neighborhood

class ScalablePropertyCollector:
    """Main scalable collector for Athens properties"""
    
    def __init__(self, target_properties: int = 1000, concurrent_browsers: int = 5):
        self.target_properties = target_properties
        self.concurrent_browsers = concurrent_browsers
        self.browser_manager = ScalableAthensBrowser(concurrent_browsers)
        self.collected_properties: List[ScaledProperty] = []
        self.processed_urls: Set[str] = set()
        self.collection_stats = {
            "total_urls_found": 0,
            "properties_extracted": 0,
            "validation_passed": 0,
            "duplicate_skipped": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def initialize(self):
        """Initialize the collector"""
        logger.info("🚀 Initializing Scalable Athens Property Collector")
        await self.browser_manager.initialize_browser_pool()
        self.collection_stats["start_time"] = datetime.now()
    
    async def collect_neighborhood_properties(self, neighborhood: str, max_properties: int = 100) -> List[ScaledProperty]:
        """Collect properties from a specific neighborhood using multiple strategies"""
        logger.info(f"🏘️ Starting collection for {neighborhood} (target: {max_properties} properties)")
        
        search_urls = AdvancedSearchStrategy.generate_search_urls(neighborhood)
        neighborhood_properties = []
        
        # Process search URLs concurrently in batches
        batch_size = 5
        for i in range(0, len(search_urls), batch_size):
            batch_urls = search_urls[i:i + batch_size]
            
            # Create concurrent tasks for this batch
            tasks = []
            for search_url in batch_urls:
                task = self.process_search_url(search_url, neighborhood, max_properties)
                tasks.append(task)
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for result in batch_results:
                if isinstance(result, list):
                    neighborhood_properties.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"❌ Batch processing error: {result}")
            
            # Check if we've reached target
            if len(neighborhood_properties) >= max_properties:
                neighborhood_properties = neighborhood_properties[:max_properties]
                break
            
            # Rate limiting between batches
            await asyncio.sleep(random.uniform(2, 4))
        
        logger.info(f"✅ Collected {len(neighborhood_properties)} properties from {neighborhood}")
        return neighborhood_properties
    
    async def process_search_url(self, search_url: str, neighborhood: str, max_per_search: int = 20) -> List[ScaledProperty]:
        """Process a single search URL to extract property URLs and data"""
        page = None
        try:
            page = await self.browser_manager.get_page()
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            
            # Extract property URLs from search results
            property_urls = await self.extract_property_urls_from_search(page, max_per_search)
            self.collection_stats["total_urls_found"] += len(property_urls)
            
            # Process individual properties concurrently
            property_tasks = []
            for prop_url in property_urls:
                if prop_url not in self.processed_urls:
                    self.processed_urls.add(prop_url)
                    task = self.extract_property_data(prop_url, neighborhood)
                    property_tasks.append(task)
            
            # Limit concurrent property processing
            if property_tasks:
                # Process in smaller batches to avoid overwhelming
                batch_size = 3
                batch_properties = []
                for i in range(0, len(property_tasks), batch_size):
                    batch_tasks = property_tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, ScaledProperty):
                            batch_properties.append(result)
                        elif isinstance(result, Exception):
                            self.collection_stats["errors"] += 1
                    
                    # Small delay between property batches
                    await asyncio.sleep(1)
                
                return batch_properties
            
            return []
        
        except Exception as e:
            logger.error(f"❌ Error processing search URL {search_url}: {e}")
            self.collection_stats["errors"] += 1
            return []
        
        finally:
            if page:
                await self.browser_manager.release_page(page)
    
    async def extract_property_urls_from_search(self, page: Page, max_urls: int = 20) -> List[str]:
        """Extract property URLs from search results page with deep pagination"""
        property_urls = set()
        current_page = 1
        max_pages = 10  # Enhanced pagination depth
        
        while len(property_urls) < max_urls and current_page <= max_pages:
            try:
                # Wait for search results to load
                await page.wait_for_selector('a[href*="/property/"]', timeout=10000)
                
                # Extract property URLs from current page
                page_urls = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll('a[href*="/property/"], a[href*="/en/property/"]'));
                    return links.map(link => link.href).filter(href => 
                        href.includes('/property/') && href.match(/\\/property\\/\\d+/)
                    );
                }''')
                
                # Add unique URLs
                for url in page_urls:
                    if len(property_urls) < max_urls:
                        property_urls.add(url)
                
                # Try to navigate to next page
                next_button = await page.query_selector('a[aria-label="Next"], .pagination-next, a:has-text("Next")')
                if next_button and await next_button.is_enabled():
                    await next_button.click()
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    current_page += 1
                    await asyncio.sleep(random.uniform(1, 2))
                else:
                    break
            
            except Exception as e:
                logger.warning(f"⚠️ Pagination error on page {current_page}: {e}")
                break
        
        return list(property_urls)[:max_urls]
    
    async def extract_property_data(self, property_url: str, neighborhood: str) -> Optional[ScaledProperty]:
        """Extract detailed data from individual property page"""
        page = None
        try:
            page = await self.browser_manager.get_page()
            await page.goto(property_url, wait_until='networkidle', timeout=30000)
            
            # Extract property data using enhanced selectors
            property_data = await page.evaluate('''() => {
                // Price extraction
                const priceSelectors = [
                    '.price-current', '.property-price', '.listing-price', 
                    '[data-testid="price"]', '.price', '.amount'
                ];
                let price = null;
                for (const selector of priceSelectors) {
                    const priceEl = document.querySelector(selector);
                    if (priceEl) {
                        const priceText = priceEl.textContent || '';
                        const priceMatch = priceText.match(/([0-9,.]+)/);
                        if (priceMatch) {
                            price = parseFloat(priceMatch[1].replace(/,/g, ''));
                            break;
                        }
                    }
                }
                
                // Size extraction
                const sizeSelectors = [
                    '.property-size', '.sqm', '[data-testid="size"]', 
                    '.area', '.surface', '.size'
                ];
                let sqm = null;
                for (const selector of sizeSelectors) {
                    const sizeEl = document.querySelector(selector);
                    if (sizeEl) {
                        const sizeText = sizeEl.textContent || '';
                        const sizeMatch = sizeText.match(/([0-9,.]+)\\s*m²?/);
                        if (sizeMatch) {
                            sqm = parseFloat(sizeMatch[1].replace(/,/g, ''));
                            break;
                        }
                    }
                }
                
                // Energy class extraction
                const energySelectors = [
                    '.energy-class', '.energy-rating', '[data-testid="energy"]',
                    '.efficiency', '.rating'
                ];
                let energyClass = null;
                for (const selector of energySelectors) {
                    const energyEl = document.querySelector(selector);
                    if (energyEl) {
                        const energyText = energyEl.textContent || '';
                        const energyMatch = energyText.match(/\\b(A\\+|A|B\\+|B|C\\+|C|D|E|F|G)\\b/);
                        if (energyMatch) {
                            energyClass = energyMatch[1];
                            break;
                        }
                    }
                }
                
                // Additional data extraction
                const title = document.querySelector('h1, .property-title, .listing-title')?.textContent?.trim() || '';
                const description = document.querySelector('.description, .property-description')?.textContent?.trim() || '';
                const rooms = document.querySelector('.rooms, .bedrooms')?.textContent?.trim() || '';
                const floor = document.querySelector('.floor')?.textContent?.trim() || '';
                
                return {
                    price: price,
                    sqm: sqm,
                    energyClass: energyClass,
                    title: title,
                    description: description,
                    rooms: rooms,
                    floor: floor,
                    htmlContent: document.documentElement.outerHTML
                };
            }''')
            
            # Validate extracted data
            if not self.validate_property_data(property_data):
                return None
            
            # Calculate confidence and quality scores
            confidence = self.calculate_extraction_confidence(property_data)
            quality_score = self.calculate_data_quality_score(property_data)
            
            # Create property object
            property_id = self.generate_property_id(property_url)
            html_hash = hashlib.sha256(property_data['htmlContent'].encode()).hexdigest()[:16]
            
            scaled_property = ScaledProperty(
                property_id=property_id,
                url=property_url,
                timestamp=datetime.now().isoformat(),
                title=property_data['title'],
                neighborhood=neighborhood,
                block_id=self.assign_block_id(neighborhood),
                
                # Required fields
                price=property_data['price'],
                sqm=property_data['sqm'],
                energy_class=property_data['energyClass'],
                
                # Enhanced fields
                property_type=self.detect_property_type(property_data['title']),
                listing_type="for_sale",
                rooms=property_data['rooms'],
                floor=property_data['floor'],
                year_built=None,
                
                # Quality metrics
                extraction_confidence=confidence,
                data_quality_score=quality_score,
                validation_flags=self.get_validation_flags(property_data),
                collection_method="scalable_collector_v2",
                
                # Calculated fields
                price_per_sqm=property_data['price'] / property_data['sqm'] if property_data['price'] and property_data['sqm'] else None,
                html_source_hash=html_hash,
                geo_coordinates=None
            )
            
            self.collection_stats["properties_extracted"] += 1
            if quality_score > 0.8:
                self.collection_stats["validation_passed"] += 1
            
            return scaled_property
        
        except Exception as e:
            logger.error(f"❌ Error extracting property data from {property_url}: {e}")
            self.collection_stats["errors"] += 1
            return None
        
        finally:
            if page:
                await self.browser_manager.release_page(page)
    
    def validate_property_data(self, data: Dict) -> bool:
        """Validate that extracted property data meets minimum requirements"""
        required_fields = ['price', 'sqm', 'energyClass']
        
        for field in required_fields:
            if not data.get(field):
                return False
        
        # Price validation (Athens market range)
        if not (30000 <= data['price'] <= 20000000):
            return False
        
        # Size validation
        if not (15 <= data['sqm'] <= 1000):
            return False
        
        # Energy class validation
        valid_energy_classes = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']
        if data['energyClass'] not in valid_energy_classes:
            return False
        
        return True
    
    def calculate_extraction_confidence(self, data: Dict) -> float:
        """Calculate confidence score for extracted data"""
        confidence = 0.0
        
        # Base confidence for having required fields
        if data.get('price') and data.get('sqm') and data.get('energyClass'):
            confidence += 0.6
        
        # Additional confidence for optional fields
        if data.get('title') and len(data['title']) > 10:
            confidence += 0.1
        if data.get('description') and len(data['description']) > 50:
            confidence += 0.1
        if data.get('rooms'):
            confidence += 0.1
        if data.get('floor'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def calculate_data_quality_score(self, data: Dict) -> float:
        """Calculate overall data quality score"""
        quality = 0.0
        
        # Required field quality
        if data.get('price') and isinstance(data['price'], (int, float)):
            quality += 0.3
        if data.get('sqm') and isinstance(data['sqm'], (int, float)):
            quality += 0.3
        if data.get('energyClass') and isinstance(data['energyClass'], str):
            quality += 0.2
        
        # Data reasonableness
        if data.get('price') and data.get('sqm'):
            price_per_sqm = data['price'] / data['sqm']
            if 800 <= price_per_sqm <= 15000:  # Reasonable Athens range
                quality += 0.2
        
        return quality
    
    def get_validation_flags(self, data: Dict) -> List[str]:
        """Get validation flags for the property"""
        flags = []
        
        if data.get('price') and data.get('sqm'):
            flags.append("price_size_complete")
        if data.get('energyClass'):
            flags.append("energy_class_available")
        if data.get('title') and len(data['title']) > 20:
            flags.append("detailed_title")
        if data.get('description') and len(data['description']) > 100:
            flags.append("comprehensive_description")
        
        return flags
    
    def generate_property_id(self, url: str) -> str:
        """Generate unique property ID from URL"""
        url_match = re.search(r'/property/(\d+)', url)
        if url_match:
            return f"ATH-{url_match.group(1)}"
        return f"ATH-{hashlib.md5(url.encode()).hexdigest()[:8]}"
    
    def assign_block_id(self, neighborhood: str) -> str:
        """Assign block ID based on neighborhood"""
        neighborhood_data = EnhancedNeighborhoodMapper.ATHENS_NEIGHBORHOODS.get(neighborhood, {})
        blocks = neighborhood_data.get("blocks", [])
        return random.choice(blocks) if blocks else f"{neighborhood[:3].upper()}-001"
    
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
    
    async def collect_scaled_properties(self, priority_level: int = 1, properties_per_neighborhood: int = 80) -> List[ScaledProperty]:
        """Main method to collect properties at scale"""
        logger.info(f"🏗️ Starting scaled collection for priority {priority_level} neighborhoods")
        
        target_neighborhoods = EnhancedNeighborhoodMapper.get_priority_neighborhoods(priority_level)
        all_properties = []
        
        # Process neighborhoods concurrently (2 at a time to avoid overwhelming)
        batch_size = 2
        for i in range(0, len(target_neighborhoods), batch_size):
            batch_neighborhoods = target_neighborhoods[i:i + batch_size]
            
            # Create concurrent tasks for neighborhood batch
            tasks = []
            for neighborhood in batch_neighborhoods:
                task = self.collect_neighborhood_properties(neighborhood, properties_per_neighborhood)
                tasks.append(task)
            
            # Execute neighborhood batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in batch_results:
                if isinstance(result, list):
                    all_properties.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"❌ Neighborhood batch error: {result}")
            
            # Progress update
            logger.info(f"📊 Progress: {len(all_properties)}/{self.target_properties} properties collected")
            
            # Check if target reached
            if len(all_properties) >= self.target_properties:
                all_properties = all_properties[:self.target_properties]
                break
            
            # Delay between neighborhood batches
            await asyncio.sleep(random.uniform(3, 6))
        
        self.collected_properties = all_properties
        self.collection_stats["end_time"] = datetime.now()
        
        logger.info(f"✅ Scaled collection complete: {len(all_properties)} properties")
        return all_properties
    
    def get_collection_stats(self) -> Dict:
        """Get comprehensive collection statistics"""
        duration = None
        if self.collection_stats["start_time"] and self.collection_stats["end_time"]:
            duration = (self.collection_stats["end_time"] - self.collection_stats["start_time"]).total_seconds()
        
        return {
            **self.collection_stats,
            "duration_seconds": duration,
            "properties_per_minute": len(self.collected_properties) / (duration / 60) if duration else 0,
            "success_rate": len(self.collected_properties) / self.collection_stats["total_urls_found"] if self.collection_stats["total_urls_found"] else 0,
            "validation_rate": self.collection_stats["validation_passed"] / len(self.collected_properties) if self.collected_properties else 0
        }
    
    async def save_results(self, filename_prefix: str = "athens_scaled_properties") -> str:
        """Save collected properties to file"""
        if not self.collected_properties:
            logger.warning("⚠️ No properties to save")
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed JSON
        json_file = Path("data/processed") / f"{filename_prefix}_{timestamp}.json"
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        properties_data = [asdict(prop) for prop in self.collected_properties]
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, ensure_ascii=False, indent=2)
        
        # Save summary CSV
        csv_file = Path("data/processed") / f"{filename_prefix}_summary_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Property_ID,URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Block_ID,Confidence,Quality_Score,Validation_Flags\n")
            
            for prop in self.collected_properties:
                validation_flags = ';'.join(prop.validation_flags)
                f.write(f'"{prop.property_id}","{prop.url}",{prop.price},{prop.sqm},"{prop.energy_class}",{prop.price_per_sqm:.0f if prop.price_per_sqm else 0},"{prop.neighborhood}","{prop.block_id}",{prop.extraction_confidence:.2f},{prop.data_quality_score:.2f},"{validation_flags}"\n')
        
        # Save collection statistics
        stats_file = Path("data/processed") / f"{filename_prefix}_stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(self.get_collection_stats(), f, indent=2, default=str)
        
        logger.info(f"💾 Results saved:")
        logger.info(f"   📄 Detailed data: {json_file}")
        logger.info(f"   📊 Summary CSV: {csv_file}")
        logger.info(f"   📈 Statistics: {stats_file}")
        
        return str(json_file)
    
    async def close(self):
        """Clean up resources"""
        await self.browser_manager.close_all()
        logger.info("🔒 Scalable collector closed successfully")

# Main execution function
async def run_scalable_collection(target_properties: int = 1000, priority_level: int = 1):
    """Run the scalable collection process"""
    collector = ScalablePropertyCollector(target_properties=target_properties, concurrent_browsers=5)
    
    try:
        await collector.initialize()
        
        properties_per_neighborhood = target_properties // len(EnhancedNeighborhoodMapper.get_priority_neighborhoods(priority_level))
        properties = await collector.collect_scaled_properties(priority_level, properties_per_neighborhood)
        
        # Save results
        json_file = await collector.save_results()
        
        # Print statistics
        stats = collector.get_collection_stats()
        logger.info("📊 COLLECTION STATISTICS:")
        logger.info(f"   🎯 Target Properties: {target_properties}")
        logger.info(f"   ✅ Properties Collected: {len(properties)}")
        logger.info(f"   🔗 URLs Processed: {stats['total_urls_found']}")
        logger.info(f"   ⏱️ Duration: {stats['duration_seconds']:.1f} seconds")
        logger.info(f"   📈 Rate: {stats['properties_per_minute']:.1f} properties/minute")
        logger.info(f"   ✅ Success Rate: {stats['success_rate']:.1%}")
        logger.info(f"   🎖️ Validation Rate: {stats['validation_rate']:.1%}")
        
        return properties, json_file
    
    finally:
        await collector.close()

if __name__ == "__main__":
    # Run scaled collection for 1000 properties
    asyncio.run(run_scalable_collection(target_properties=1000, priority_level=1))