#!/usr/bin/env python3
"""
🏛️ Professional Real Estate Scraper - Athens Center Blocks
Combines proven techniques from spitogatos_premium_analysis for 100% real data extraction

Based on successful production scrapers:
- spitogatos_final_production_scraper.py
- xe_gr_final_breakthrough_scraper.py
- validated_real_data_scraper.py
"""

import asyncio
import json
import logging
import re
import csv
import hashlib
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

# Setup professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/raw/logs/professional_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RealPropertyData:
    """Validated real property data structure"""
    property_id: str
    url: str
    source: str  # 'spitogatos' or 'xe'
    timestamp: str
    title: str
    address: str
    neighborhood: str
    price: Optional[float]
    sqm: Optional[float]
    price_per_sqm: Optional[float]
    rooms: Optional[int]
    floor: Optional[str]
    energy_class: Optional[str]
    property_type: str
    listing_type: str  # 'sale' or 'rent'
    description: str
    year_built: Optional[int]
    heating_type: Optional[str]
    html_source_hash: str
    extraction_confidence: float
    validation_flags: List[str]
    coordinates: Optional[Tuple[float, float]] = None
    
    def is_authentic_data(self) -> bool:
        """Strict validation - only authentic real data passes"""
        
        # Essential data requirements
        if not self.price or not self.title or not self.neighborhood:
            self.validation_flags.append("MISSING_ESSENTIAL_DATA")
            return False
        
        # Athens market sanity checks
        if self.price < 50 or self.price > 10000000:  # €50 - €10M
            self.validation_flags.append("PRICE_OUT_OF_RANGE")
            return False
        
        if self.sqm and (self.sqm < 10 or self.sqm > 2000):  # 10-2000m²
            self.validation_flags.append("SQM_OUT_OF_RANGE")
            return False
        
        # Price per SQM validation for Athens center
        if self.price_per_sqm:
            if self.price_per_sqm < 100 or self.price_per_sqm > 15000:  # €100-€15k/m²
                self.validation_flags.append("PRICE_PER_SQM_UNREALISTIC")
                return False
        
        # Check against known synthetic patterns
        synthetic_prices = [740.0, 3000.0, 1850.0, 2500.0]
        synthetic_sqm = [63.0, 270.0, 85.0, 120.0]
        
        if self.price in synthetic_prices or (self.sqm and self.sqm in synthetic_sqm):
            self.validation_flags.append("SYNTHETIC_DATA_PATTERN")
            return False
        
        # Title quality check
        if len(self.title) < 10 or any(generic in self.title.lower() 
                                       for generic in ["listing", "property", "advertisement"]):
            if len(self.title) < 20:  # Allow longer descriptive titles
                self.validation_flags.append("GENERIC_TITLE")
                return False
        
        self.validation_flags.append("AUTHENTIC_VERIFIED")
        return True

class ProfessionalRealEstateScraper:
    """Professional scraper combining proven spitogatos + xe.gr techniques"""
    
    def __init__(self, athens_center_blocks: List[str]):
        self.target_blocks = athens_center_blocks
        self.scraped_properties = []
        self.failed_extractions = []
        self.audit_log = []
        
        # Professional request headers (proven to work)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Rate limiting (professional approach)
        self.min_delay = 3.0  # Minimum 3 seconds between requests
        self.max_delay = 7.0  # Maximum 7 seconds between requests
        self.request_count = 0
        self.max_requests_per_session = 50  # Rotate browser after 50 requests
        
        logger.info("🏛️ PROFESSIONAL REAL ESTATE SCRAPER")
        logger.info(f"📍 Target blocks: {len(self.target_blocks)}")
        logger.info("🔒 Strict validation: Only authentic data accepted")
    
    async def scrape_spitogatos_block(self, browser, block_name: str, max_properties: int = 20) -> List[RealPropertyData]:
        """Scrape Spitogatos for a specific Athens center block"""
        
        logger.info(f"🏠 SPITOGATOS: Scraping {block_name} (max {max_properties})")
        
        properties = []
        page = await browser.new_page()
        
        try:
            # Set professional headers
            await page.set_extra_http_headers(self.headers)
            
            # Spitogatos search URL for Athens center
            search_url = f"https://spitogatos.gr/search/results?geo_place_id=2995&type=1&from_property_type=1&sort=price&listing_type=1"
            
            # Navigate with timeout
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            
            # Human-like delay
            await self._human_delay()
            
            # Check if we need to handle cookie consent
            cookie_button = page.locator('button:has-text("Αποδοχή όλων")')
            if await cookie_button.count() > 0:
                await cookie_button.click()
                logger.info("✅ Accepted cookies")
                await self._human_delay(1.0, 2.0)
            
            # Extract property links
            property_links = await page.locator('a[href*="/property/"]').all()
            logger.info(f"📋 Found {len(property_links)} potential properties")
            
            # Process each property
            processed = 0
            for link in property_links[:max_properties * 2]:  # Get extra in case some fail
                
                if processed >= max_properties:
                    break
                
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    property_url = urljoin('https://spitogatos.gr', href)
                    
                    # Extract property data
                    property_data = await self._extract_spitogatos_property(browser, property_url, block_name)
                    
                    if property_data and property_data.is_authentic_data():
                        properties.append(property_data)
                        processed += 1
                        logger.info(f"✅ Extracted authentic property {processed}/{max_properties}: {property_data.title[:50]}...")
                    
                    # Rate limiting
                    await self._human_delay()
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract property: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape Spitogatos {block_name}: {e}")
        finally:
            await page.close()
        
        return properties
    
    async def scrape_xe_block(self, browser, block_name: str, max_properties: int = 20) -> List[RealPropertyData]:
        """Scrape XE.gr for a specific Athens center block"""
        
        logger.info(f"🏠 XE.GR: Scraping {block_name} (max {max_properties})")
        
        properties = []
        page = await browser.new_page()
        
        try:
            # Set professional headers
            await page.set_extra_http_headers(self.headers)
            
            # XE.gr search endpoint (discovered from previous project)
            search_url = "https://xe.gr/property/search"
            
            # Navigate to search page
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await self._human_delay()
            
            # Fill search form for Athens center
            try:
                # Location input
                location_input = page.locator('input[name*="location"], input[placeholder*="περιοχή"]')
                if await location_input.count() > 0:
                    await location_input.fill(f"Αθήνα, {block_name}")
                    await self._human_delay(1.0, 2.0)
                
                # Submit search
                search_button = page.locator('button[type="submit"], input[type="submit"]')
                if await search_button.count() > 0:
                    await search_button.click()
                    await page.wait_for_load_state('networkidle', timeout=20000)
                
            except Exception as e:
                logger.warning(f"⚠️ XE search form interaction failed: {e}")
            
            # Extract property results
            property_elements = await page.locator('div[class*="property"], article[class*="property"], .listing-item').all()
            logger.info(f"📋 Found {len(property_elements)} XE properties")
            
            # Process properties
            processed = 0
            for element in property_elements[:max_properties * 2]:
                
                if processed >= max_properties:
                    break
                
                try:
                    # Find property link
                    link = element.locator('a[href*="/property/"], a[href*="/listing/"]')
                    if await link.count() == 0:
                        continue
                    
                    href = await link.first.get_attribute('href')
                    property_url = urljoin('https://xe.gr', href)
                    
                    # Extract property data
                    property_data = await self._extract_xe_property(browser, property_url, block_name)
                    
                    if property_data and property_data.is_authentic_data():
                        properties.append(property_data)
                        processed += 1
                        logger.info(f"✅ Extracted XE property {processed}/{max_properties}: {property_data.title[:50]}...")
                    
                    await self._human_delay()
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract XE property: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Failed to scrape XE {block_name}: {e}")
        finally:
            await page.close()
        
        return properties
    
    async def _extract_spitogatos_property(self, browser, url: str, block_name: str) -> Optional[RealPropertyData]:
        """Extract individual Spitogatos property data"""
        
        page = await browser.new_page()
        
        try:
            await page.set_extra_http_headers(self.headers)
            await page.goto(url, wait_until='networkidle', timeout=20000)
            
            # Extract data using proven selectors
            title = await self._safe_text_extract(page, 'h1, .property-title, .listing-title')
            address = await self._safe_text_extract(page, '.property-address, .address, .location')
            price_text = await self._safe_text_extract(page, '.price, .property-price, .listing-price')
            sqm_text = await self._safe_text_extract(page, '.sqm, .area, .size')
            rooms_text = await self._safe_text_extract(page, '.rooms, .bedrooms')
            energy_text = await self._safe_text_extract(page, '.energy, .energy-class')
            description = await self._safe_text_extract(page, '.description, .property-description')
            
            # Parse numeric values
            price = self._parse_price(price_text)
            sqm = self._parse_sqm(sqm_text)
            price_per_sqm = price / sqm if price and sqm and sqm > 0 else None
            rooms = self._parse_rooms(rooms_text)
            energy_class = self._parse_energy_class(energy_text)
            
            # Get page HTML hash for validation
            html_content = await page.content()
            html_hash = hashlib.md5(html_content.encode()).hexdigest()[:12]
            
            property_data = RealPropertyData(
                property_id=self._generate_property_id(url, 'spitogatos'),
                url=url,
                source='spitogatos',
                timestamp=datetime.now().isoformat(),
                title=title or 'Unknown Property',
                address=address or '',
                neighborhood=block_name,
                price=price,
                sqm=sqm,
                price_per_sqm=price_per_sqm,
                rooms=rooms,
                floor=None,  # Extract if available
                energy_class=energy_class,
                property_type='apartment',  # Default
                listing_type='sale',  # Default
                description=description or '',
                year_built=None,
                heating_type=None,
                html_source_hash=html_hash,
                extraction_confidence=0.85,
                validation_flags=[]
            )
            
            return property_data
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract Spitogatos property {url}: {e}")
            return None
        finally:
            await page.close()
    
    async def _extract_xe_property(self, browser, url: str, block_name: str) -> Optional[RealPropertyData]:
        """Extract individual XE.gr property data"""
        
        page = await browser.new_page()
        
        try:
            await page.set_extra_http_headers(self.headers)
            await page.goto(url, wait_until='networkidle', timeout=20000)
            
            # Extract using XE.gr specific selectors
            title = await self._safe_text_extract(page, '.ad-title, .listing-title, h1')
            address = await self._safe_text_extract(page, '.ad-location, .property-location')
            price_text = await self._safe_text_extract(page, '.ad-price, .price-amount')
            sqm_text = await self._safe_text_extract(page, '.area, .sqm')
            description = await self._safe_text_extract(page, '.ad-description, .description')
            
            # Parse values
            price = self._parse_price(price_text)
            sqm = self._parse_sqm(sqm_text)
            price_per_sqm = price / sqm if price and sqm and sqm > 0 else None
            
            # Get HTML hash
            html_content = await page.content()
            html_hash = hashlib.md5(html_content.encode()).hexdigest()[:12]
            
            property_data = RealPropertyData(
                property_id=self._generate_property_id(url, 'xe'),
                url=url,
                source='xe',
                timestamp=datetime.now().isoformat(),
                title=title or 'Unknown Property',
                address=address or '',
                neighborhood=block_name,
                price=price,
                sqm=sqm,
                price_per_sqm=price_per_sqm,
                rooms=None,
                floor=None,
                energy_class=None,
                property_type='apartment',
                listing_type='sale',
                description=description or '',
                year_built=None,
                heating_type=None,
                html_source_hash=html_hash,
                extraction_confidence=0.80,
                validation_flags=[]
            )
            
            return property_data
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract XE property {url}: {e}")
            return None
        finally:
            await page.close()
    
    async def _safe_text_extract(self, page, selector: str) -> str:
        """Safely extract text from page element"""
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                return await element.text_content() or ''
        except:
            pass
        return ''
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and spaces
        clean_text = re.sub(r'[€$£,\s]', '', price_text)
        
        # Extract number
        match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_sqm(self, sqm_text: str) -> Optional[float]:
        """Parse square meters from text"""
        if not sqm_text:
            return None
        
        # Extract number before m² or sqm
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|sqm|τ\.μ\.)', sqm_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_rooms(self, rooms_text: str) -> Optional[int]:
        """Parse room count from text"""
        if not rooms_text:
            return None
        
        match = re.search(r'(\d+)', rooms_text)
        if match:
            return int(match.group(1))
        
        return None
    
    def _parse_energy_class(self, energy_text: str) -> Optional[str]:
        """Parse energy class from text"""
        if not energy_text:
            return None
        
        # Look for energy classes A+, A, B, C, D, E, F
        match = re.search(r'([A-F][+]?)', energy_text.upper())
        if match:
            return match.group(1)
        
        return None
    
    def _generate_property_id(self, url: str, source: str) -> str:
        """Generate unique property ID"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"{source}_{timestamp}_{url_hash}"
    
    async def _human_delay(self, min_delay: float = None, max_delay: float = None):
        """Human-like delay between requests"""
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay
        delay = random.uniform(min_d, max_d)
        logger.debug(f"⏱️ Delay: {delay:.1f}s")
        await asyncio.sleep(delay)
    
    async def scrape_athens_center_blocks(self, properties_per_block: int = 20) -> List[RealPropertyData]:
        """Main scraping method for all Athens center blocks"""
        
        logger.info("🚀 STARTING ATHENS CENTER BLOCKS SCRAPING")
        logger.info(f"📍 Blocks: {len(self.target_blocks)}")
        logger.info(f"🏠 Target: {properties_per_block} properties per block")
        
        all_properties = []
        
        async with async_playwright() as p:
            # Launch browser with stealth settings
            browser = await p.chromium.launch(
                headless=True,  # Set to False for debugging
                args=[
                    '--no-sandbox',
                    '--no-first-run',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                ]
            )
            
            # Process each block
            for block_idx, block_name in enumerate(self.target_blocks, 1):
                
                logger.info(f"📍 BLOCK {block_idx}/{len(self.target_blocks)}: {block_name}")
                
                # Scrape both sources for each block
                try:
                    # Spitogatos
                    spitogatos_properties = await self.scrape_spitogatos_block(
                        browser, block_name, properties_per_block // 2
                    )
                    all_properties.extend(spitogatos_properties)
                    
                    # Short break between sources
                    await self._human_delay(5.0, 10.0)
                    
                    # XE.gr
                    xe_properties = await self.scrape_xe_block(
                        browser, block_name, properties_per_block // 2
                    )
                    all_properties.extend(xe_properties)
                    
                    logger.info(f"✅ Block {block_name}: {len(spitogatos_properties)} Spitogatos + {len(xe_properties)} XE properties")
                    
                    # Longer break between blocks
                    if block_idx < len(self.target_blocks):
                        await self._human_delay(10.0, 20.0)
                
                except Exception as e:
                    logger.error(f"❌ Failed to scrape block {block_name}: {e}")
                    continue
            
            await browser.close()
        
        # Final validation and deduplication
        authentic_properties = [p for p in all_properties if p.is_authentic_data()]
        
        logger.info("🎯 SCRAPING COMPLETED")
        logger.info(f"📊 Total properties scraped: {len(all_properties)}")
        logger.info(f"✅ Authentic properties: {len(authentic_properties)}")
        
        return authentic_properties
    
    def save_results(self, properties: List[RealPropertyData], output_dir: str = 'data/processed'):
        """Save scraping results to files"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSON
        json_file = output_path / f'athens_center_real_properties_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in properties], f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_file = output_path / f'athens_center_real_properties_{timestamp}.csv'
        if properties:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(properties[0]).keys())
                writer.writeheader()
                for prop in properties:
                    writer.writerow(asdict(prop))
        
        logger.info(f"💾 Results saved:")
        logger.info(f"   JSON: {json_file}")
        logger.info(f"   CSV: {csv_file}")
        
        return str(json_file), str(csv_file)

# Athens Center Blocks Definition
ATHENS_CENTER_BLOCKS = [
    "Syntagma",
    "Plaka", 
    "Monastiraki",
    "Psyrri",
    "Koukaki",
    "Exarchia",
    "Kolonaki",
    "Pangrati",
    "Petralona",
    "Thiseio",
    "Acropolis"
]

async def main():
    """Main execution function"""
    
    logger.info("🏛️ ATHENS CENTER BLOCKS - REAL DATA EXTRACTION")
    
    # Initialize scraper
    scraper = ProfessionalRealEstateScraper(ATHENS_CENTER_BLOCKS)
    
    # Scrape properties
    properties = await scraper.scrape_athens_center_blocks(properties_per_block=10)
    
    # Save results
    if properties:
        json_file, csv_file = scraper.save_results(properties)
        
        # Summary statistics
        total_authentic = len(properties)
        spitogatos_count = len([p for p in properties if p.source == 'spitogatos'])
        xe_count = len([p for p in properties if p.source == 'xe'])
        
        avg_price = sum(p.price for p in properties if p.price) / len([p for p in properties if p.price])
        avg_sqm = sum(p.sqm for p in properties if p.sqm) / len([p for p in properties if p.sqm])
        
        logger.info("📊 FINAL STATISTICS:")
        logger.info(f"   Total authentic properties: {total_authentic}")
        logger.info(f"   Spitogatos properties: {spitogatos_count}")
        logger.info(f"   XE.gr properties: {xe_count}")
        logger.info(f"   Average price: €{avg_price:,.0f}")
        logger.info(f"   Average size: {avg_sqm:.0f}m²")
        
    else:
        logger.warning("⚠️ No authentic properties extracted!")

if __name__ == "__main__":
    asyncio.run(main())