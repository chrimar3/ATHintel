#!/usr/bin/env python3
"""
🏠 Spitogatos Specialized Scraper
Based on proven production scraping techniques from spitogatos_premium_analysis
"""

import asyncio
import json
import logging
import re
import random
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SpitogatosProperty:
    """Spitogatos property data structure"""
    property_id: str
    url: str
    title: str
    address: str
    neighborhood: str
    price: Optional[float]
    sqm: Optional[float]
    price_per_sqm: Optional[float]
    rooms: Optional[int]
    floor: Optional[str]
    energy_class: Optional[str]
    description: str
    source: str = "spitogatos"
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class SpitogatosSpecializedScraper:
    """Specialized Spitogatos scraper using proven techniques"""
    
    def __init__(self):
        self.properties = []
        self.failed_urls = []
        
        # Proven working URLs from your previous project
        self.search_urls = {
            'athens_center_sale': 'https://www.spitogatos.gr/en/for_sale-homes/athens-center',
            'athens_center_rent': 'https://www.spitogatos.gr/en/for_rent-homes/athens-center',
            'athens_sale': 'https://www.spitogatos.gr/en/for_sale-homes/athens',
            'kolonaki_sale': 'https://www.spitogatos.gr/search/results?geo_place_id=2995&type=1&from_property_type=1&sort=price&listing_type=1&area_name=Κολωνάκι'
        }
        
        # Athens center neighborhoods mapping
        self.neighborhoods = {
            'Syntagma': ['Σύνταγμα', 'Syntagma'],
            'Plaka': ['Πλάκα', 'Plaka'],
            'Monastiraki': ['Μοναστηράκι', 'Monastiraki'],
            'Kolonaki': ['Κολωνάκι', 'Kolonaki'],
            'Exarchia': ['Εξάρχεια', 'Exarchia'],
            'Psyrri': ['Ψυρρή', 'Psyrri'],
            'Koukaki': ['Κουκάκι', 'Koukaki']
        }
        
        logger.info("🏠 SPITOGATOS SPECIALIZED SCRAPER INITIALIZED")
        logger.info(f"🎯 Target neighborhoods: {list(self.neighborhoods.keys())}")
    
    async def create_stealth_browser(self):
        """Create stealth browser with Greek locale"""
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Visible for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--start-maximized'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='el-GR',
            timezone_id='Europe/Athens',
            extra_http_headers={
                'Accept-Language': 'el-GR,el;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        )
        
        # Anti-detection script
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['el-GR', 'el', 'en']});
        """)
        
        return playwright, browser, context
    
    async def discover_property_urls(self, page, search_url: str, max_properties: int = 20) -> List[str]:
        """Discover property URLs using proven selectors"""
        
        logger.info(f"🔍 Discovering properties from: {search_url}")
        
        try:
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await self._human_delay(2, 4)
            
            # Take screenshot for debugging
            timestamp = datetime.now().strftime("%H%M%S")
            await page.screenshot(path=f"debug_spitogatos_{timestamp}.png")
            
            # Handle cookie consent if present
            cookie_selectors = [
                'button:has-text("Αποδοχή")',
                'button:has-text("Accept")',
                '.cookie-accept',
                '#accept-cookies'
            ]
            
            for selector in cookie_selectors:
                cookie_btn = page.locator(selector)
                if await cookie_btn.count() > 0:
                    await cookie_btn.click()
                    logger.info("✅ Accepted cookies")
                    await self._human_delay(1, 2)
                    break
            
            # Multiple property link discovery strategies
            property_urls = set()
            
            # Strategy 1: Direct property links
            property_selectors = [
                'a[href*="/property/"]',
                'a[href*="/en/property/"]',
                'a[href*="/listing/"]',
                'a[href*="/ad/"]'
            ]
            
            for selector in property_selectors:
                elements = await page.locator(selector).all()
                logger.info(f"🔍 Selector '{selector}': {len(elements)} elements")
                
                for element in elements[:max_properties]:
                    try:
                        href = await element.get_attribute('href')
                        if href:
                            full_url = self._normalize_url(href)
                            property_urls.add(full_url)
                    except:
                        continue
            
            # Strategy 2: Property cards/containers
            container_selectors = [
                '.property-card a',
                '.listing-card a', 
                '.search-result a',
                '.property-item a',
                '[data-testid*="property"] a'
            ]
            
            for selector in container_selectors:
                elements = await page.locator(selector).all()
                if elements:
                    logger.info(f"🎯 Container '{selector}': {len(elements)} elements")
                    
                    for element in elements[:max_properties]:
                        try:
                            href = await element.get_attribute('href')
                            if href:
                                full_url = self._normalize_url(href)
                                property_urls.add(full_url)
                        except:
                            continue
            
            # Strategy 3: Look for pagination and load more
            try:
                next_page = page.locator('a:has-text("Next"), a:has-text("Επόμενη"), .next-page')
                if await next_page.count() > 0 and len(property_urls) < max_properties:
                    logger.info("📄 Found pagination, getting more properties...")
                    await next_page.click()
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Get additional properties
                    for selector in property_selectors:
                        elements = await page.locator(selector).all()
                        for element in elements[:max_properties - len(property_urls)]:
                            try:
                                href = await element.get_attribute('href')
                                if href:
                                    full_url = self._normalize_url(href)
                                    property_urls.add(full_url)
                            except:
                                continue
            except:
                pass
            
            unique_urls = list(property_urls)[:max_properties]
            logger.info(f"✅ Discovered {len(unique_urls)} unique property URLs")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"❌ Property discovery failed: {e}")
            return []
    
    async def extract_property_data(self, page, url: str) -> Optional[SpitogatosProperty]:
        """Extract individual property data using proven patterns"""
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=20000)
            await self._human_delay(1, 3)
            
            # Extract title
            title_selectors = [
                'h1.property-title',
                'h1',
                '.property-header h1',
                '.listing-title'
            ]
            title = await self._extract_text(page, title_selectors)
            
            # Extract address/location
            address_selectors = [
                '.property-address',
                '.address',
                '.location',
                '.property-location',
                '[data-testid*="address"]'
            ]
            address = await self._extract_text(page, address_selectors)
            
            # Extract price
            price_selectors = [
                '.price',
                '.property-price', 
                '.listing-price',
                '[data-testid*="price"]',
                '.price-amount'
            ]
            price_text = await self._extract_text(page, price_selectors)
            price = self._parse_price(price_text)
            
            # Extract square meters
            sqm_selectors = [
                '.sqm',
                '.area',
                '.size',
                '.property-area',
                '[data-testid*="area"]'
            ]
            sqm_text = await self._extract_text(page, sqm_selectors)
            sqm = self._parse_sqm(sqm_text)
            
            # Extract rooms
            rooms_selectors = [
                '.rooms',
                '.bedrooms',
                '.property-rooms'
            ]
            rooms_text = await self._extract_text(page, rooms_selectors)
            rooms = self._parse_rooms(rooms_text)
            
            # Extract energy class
            energy_selectors = [
                '.energy',
                '.energy-class',
                '.energy-rating',
                '[data-testid*="energy"]'
            ]
            energy_text = await self._extract_text(page, energy_selectors)
            energy_class = self._parse_energy_class(energy_text)
            
            # Extract description
            desc_selectors = [
                '.description',
                '.property-description',
                '.listing-description',
                '.property-details'
            ]
            description = await self._extract_text(page, desc_selectors)
            
            # Determine neighborhood from address or URL
            neighborhood = self._determine_neighborhood(address, url)
            
            # Calculate price per sqm
            price_per_sqm = None
            if price and sqm and sqm > 0:
                price_per_sqm = price / sqm
            
            property_data = SpitogatosProperty(
                property_id=self._generate_property_id(url),
                url=url,
                title=title or "Unknown Property",
                address=address or "",
                neighborhood=neighborhood,
                price=price,
                sqm=sqm,
                price_per_sqm=price_per_sqm,
                rooms=rooms,
                floor=None,  # Could be extracted if needed
                energy_class=energy_class,
                description=description or ""
            )
            
            # Validate property data
            if self._is_valid_property(property_data):
                logger.info(f"✅ Extracted: {title[:50]}... - €{price:,} - {sqm}m²")
                return property_data
            else:
                logger.warning(f"⚠️ Invalid property data: {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to extract {url}: {e}")
            return None
    
    async def _extract_text(self, page, selectors: List[str]) -> str:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return ""
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from Greek text"""
        if not price_text:
            return None
        
        # Remove currency and spaces
        clean_text = re.sub(r'[€$£,\s]', '', price_text)
        clean_text = re.sub(r'[.]\d{3}', '', clean_text)  # Remove thousands separator
        
        # Extract number
        match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_sqm(self, sqm_text: str) -> Optional[float]:
        """Parse square meters from Greek text"""
        if not sqm_text:
            return None
        
        # Look for m², sqm, τ.μ. patterns
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|sqm|τ\.μ\.|μ²)', sqm_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_rooms(self, rooms_text: str) -> Optional[int]:
        """Parse room count"""
        if not rooms_text:
            return None
        
        match = re.search(r'(\d+)', rooms_text)
        if match:
            return int(match.group(1))
        
        return None
    
    def _parse_energy_class(self, energy_text: str) -> Optional[str]:
        """Parse energy class"""
        if not energy_text:
            return None
        
        match = re.search(r'([A-F][+]?)', energy_text.upper())
        if match:
            return match.group(1)
        
        return None
    
    def _determine_neighborhood(self, address: str, url: str) -> str:
        """Determine neighborhood from address or URL"""
        text_to_check = f"{address} {url}".lower()
        
        for neighborhood, variations in self.neighborhoods.items():
            for variation in variations:
                if variation.lower() in text_to_check:
                    return neighborhood
        
        return "Athens Center"  # Default
    
    def _normalize_url(self, href: str) -> str:
        """Normalize URL to full format"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"https://www.spitogatos.gr{href}"
        else:
            return f"https://www.spitogatos.gr/{href}"
    
    def _generate_property_id(self, url: str) -> str:
        """Generate unique property ID"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"spitogatos_{timestamp}_{url_hash}"
    
    def _is_valid_property(self, prop: SpitogatosProperty) -> bool:
        """Validate property data quality"""
        
        # Must have essential data
        if not prop.price or not prop.title:
            return False
        
        # Price sanity check for Athens
        if prop.price < 50 or prop.price > 10000000:
            return False
        
        # Size sanity check
        if prop.sqm and (prop.sqm < 10 or prop.sqm > 2000):
            return False
        
        # Title quality check
        if len(prop.title) < 10:
            return False
        
        return True
    
    async def _human_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def scrape_athens_center(self, max_properties_per_search: int = 10) -> List[SpitogatosProperty]:
        """Main scraping method for Athens center"""
        
        logger.info("🚀 STARTING SPITOGATOS ATHENS CENTER SCRAPING")
        
        all_properties = []
        playwright, browser, context = await self.create_stealth_browser()
        
        try:
            page = await context.new_page()
            
            # Try each search URL
            for search_name, search_url in self.search_urls.items():
                logger.info(f"📍 Searching: {search_name}")
                
                try:
                    # Discover property URLs
                    property_urls = await self.discover_property_urls(
                        page, search_url, max_properties_per_search
                    )
                    
                    if not property_urls:
                        logger.warning(f"⚠️ No properties found for {search_name}")
                        continue
                    
                    # Extract property data
                    for i, url in enumerate(property_urls, 1):
                        logger.info(f"📊 Extracting {i}/{len(property_urls)}: {url}")
                        
                        property_data = await self.extract_property_data(page, url)
                        
                        if property_data:
                            all_properties.append(property_data)
                        else:
                            self.failed_urls.append(url)
                        
                        # Human-like delay between extractions
                        await self._human_delay(3, 7)
                    
                    # Break between search URLs
                    await self._human_delay(10, 15)
                    
                except Exception as e:
                    logger.error(f"❌ Search {search_name} failed: {e}")
                    continue
            
        finally:
            await browser.close()
            await playwright.stop()
        
        logger.info(f"🎯 SPITOGATOS SCRAPING COMPLETED")
        logger.info(f"✅ Properties extracted: {len(all_properties)}")
        logger.info(f"❌ Failed URLs: {len(self.failed_urls)}")
        
        return all_properties
    
    def save_results(self, properties: List[SpitogatosProperty], output_dir: str = "data/processed"):
        """Save results to files"""
        
        if not properties:
            logger.warning("No properties to save")
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Convert to dictionaries
        properties_data = [prop.__dict__ for prop in properties]
        
        # Save JSON
        json_file = output_path / f'spitogatos_athens_center_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved: {json_file}")
        
        return str(json_file)

# Test function
async def test_spitogatos_scraper():
    """Test the specialized scraper"""
    
    scraper = SpitogatosSpecializedScraper()
    
    # Test with small sample
    properties = await scraper.scrape_athens_center(max_properties_per_search=3)
    
    if properties:
        # Save results
        scraper.save_results(properties)
        
        # Show sample
        sample = properties[0]
        logger.info("📋 SAMPLE PROPERTY:")
        logger.info(f"   Title: {sample.title}")
        logger.info(f"   Price: €{sample.price:,}")
        logger.info(f"   Size: {sample.sqm}m²")
        logger.info(f"   Neighborhood: {sample.neighborhood}")
        logger.info(f"   URL: {sample.url}")
    
    return properties

if __name__ == "__main__":
    asyncio.run(test_spitogatos_scraper())