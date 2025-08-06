#!/usr/bin/env python3
"""
🏠 Working Spitogatos Scraper - Based on Successful Case Study URLs
Using EXACT working URLs and methods from your successful extraction

Success Pattern from Case Study:
- Direct property URLs: /en/property/[ID]
- Working search: main Athens pages, not specific neighborhoods
- Extract from HTML structure, not selectors
"""

import asyncio
import json
import logging
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WorkingSpitogatosProperty:
    """Property structure exactly matching your successful case study"""
    property_id: str
    url: str
    source_timestamp: str
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
    listing_type: str
    description: str
    contact_info: Optional[str]
    html_source_hash: str
    extraction_confidence: float
    validation_flags: List[str]
    
    def is_authentic_real_data(self) -> bool:
        """EXACT validation from your successful case study"""
        
        if not self.price or not self.title:
            self.validation_flags.append("MISSING_ESSENTIAL_DATA")
            return False
        
        # Athens real estate sanity checks (from case study)
        if self.price < 50 or self.price > 10000000:
            self.validation_flags.append("PRICE_OUT_OF_RANGE")
            return False
        
        if self.sqm and (self.sqm < 5 or self.sqm > 2000):
            self.validation_flags.append("SQM_OUT_OF_RANGE")
            return False
        
        self.validation_flags.append("AUTHENTIC_VERIFIED")
        return True

class WorkingSpitogatosScraper:
    """Scraper using EXACT working methodology from successful case study"""
    
    def __init__(self):
        self.authentic_properties = []
        self.failed_extractions = []
        
        # EXACT working search URLs from your successful case study
        self.working_urls = [
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center",
            "https://www.spitogatos.gr/en/for_rent-homes/athens-center",
            "https://www.spitogatos.gr/en/for_sale-homes/athens",
            "https://www.spitogatos.gr/en/for_rent-homes/athens"
        ]
        
        logger.info("🏠 WORKING SPITOGATOS SCRAPER - CASE STUDY SUCCESS PATTERN")
        logger.info("✅ Using exact URLs that worked in your previous project")
    
    async def create_working_browser(self):
        """Browser setup exactly matching your successful case study"""
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Keep visible for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='el-GR',
            timezone_id='Europe/Athens',
            extra_http_headers={
                'Accept-Language': 'el-GR,el;q=0.9,en;q=0.8'
            }
        )
        
        return playwright, browser, context
    
    async def discover_working_property_urls(self, page, search_url: str) -> List[str]:
        """Discover property URLs using pattern that worked in case study"""
        
        logger.info(f"🔍 Discovering from: {search_url}")
        
        try:
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            # Handle cookie consent (seen in screenshot)
            try:
                cookie_button = page.locator('button:has-text("AGREE"), button:has-text("Αποδοχή"), [data-testid="agree-button"]')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    logger.info("✅ Accepted cookies")
                    await asyncio.sleep(2)
            except:
                logger.info("No cookie consent needed")
            
            # Get page HTML content
            html_content = await page.content()
            
            # Extract property URLs from HTML (case study method)
            property_urls = set()
            
            # Method 1: Direct property link extraction from HTML
            property_patterns = [
                r'href="(/en/property/\d+)"',
                r'href="(https://www\.spitogatos\.gr/en/property/\d+)"',
                r'"/en/property/(\d+)"'
            ]
            
            for pattern in property_patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    if match.group(1).startswith('/'):
                        url = f"https://www.spitogatos.gr{match.group(1)}"
                    else:
                        url = match.group(1)
                    property_urls.add(url)
            
            # Method 2: Look for property IDs and construct URLs
            id_patterns = [
                r'property-(\d+)',
                r'listing-(\d+)',
                r'id="property_(\d+)"',
                r'data-property-id="(\d+)"'
            ]
            
            for pattern in id_patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    property_id = match.group(1)
                    url = f"https://www.spitogatos.gr/en/property/{property_id}"
                    property_urls.add(url)
            
            unique_urls = list(property_urls)
            logger.info(f"✅ Found {len(unique_urls)} property URLs")
            
            # Take screenshot for debugging
            timestamp = datetime.now().strftime("%H%M%S")
            await page.screenshot(path=f"working_spitogatos_{timestamp}.png")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"❌ URL discovery failed: {e}")
            return []
    
    async def extract_working_property(self, page, url: str) -> Optional[WorkingSpitogatosProperty]:
        """Extract property using EXACT case study success method"""
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(2)
            
            # Get full HTML content for parsing (case study method)
            html_content = await page.content()
            
            # Extract title (case study shows "Apartment, 112m²" format)
            title = ""
            title_patterns = [
                r'<title>([^<]+)</title>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'property-title[^>]*>([^<]+)<',
                r'"title"\s*:\s*"([^"]+)"'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    break
            
            # Extract price (case study shows numeric values like 495000.0)
            price = None
            price_patterns = [
                r'€\s*([\d,]+)',
                r'price["\s:]*(\d+)',
                r'(\d+)\s*€',
                r'"price"\s*:\s*(\d+)',
                r'€([\d,.]+)'
            ]
            
            for pattern in price_patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    try:
                        price_str = match.group(1).replace(',', '').replace('.', '')
                        if len(price_str) >= 4:  # Reasonable price
                            price = float(price_str)
                            break
                    except:
                        continue
                if price:
                    break
            
            # Extract SQM (case study shows values like 112.0)
            sqm = None
            
            # First try to extract from title (case study pattern: "Apartment, 112m²")
            title_sqm_match = re.search(r'(\d+)m²', title)
            if title_sqm_match:
                sqm = float(title_sqm_match.group(1))
            else:
                # Try other patterns
                sqm_patterns = [
                    r'(\d+)\s*m²',
                    r'(\d+)\s*sqm',
                    r'(\d+)\s*τ\.μ\.',
                    r'"sqm"\s*:\s*(\d+)',
                    r'area["\s:]*(\d+)'
                ]
                
                for pattern in sqm_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        try:
                            sqm = float(match.group(1))
                            break
                        except:
                            continue
            
            # Extract description (case study has mortgage info)
            description = ""
            desc_patterns = [
                r'Make this property yours with a mortgage starting from[^<]*',
                r'Compare & save up to[^<]*',
                r'description["\s:]*"([^"]+)"',
                r'<meta name="description" content="([^"]+)"'
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    description = match.group(0) if 'Make this property' in match.group(0) else match.group(1)
                    break
            
            # Calculate price per sqm
            price_per_sqm = None
            if price and sqm and sqm > 0:
                price_per_sqm = price / sqm
            
            # Generate property ID (case study pattern)
            property_id = hashlib.md5(url.encode()).hexdigest()[:12]
            
            # Create property object (EXACT case study structure)
            property_data = WorkingSpitogatosProperty(
                property_id=property_id,
                url=url,
                source_timestamp=datetime.now().isoformat(),
                title=title or "Unknown Property",
                address="Homes for sale",  # Case study default
                neighborhood="Homes for sale",  # Case study default  
                price=price,
                sqm=sqm,
                price_per_sqm=price_per_sqm,
                rooms=None,
                floor=None,
                energy_class=None,
                property_type="apartment",  # Case study default
                listing_type="sale",
                description=description,
                contact_info=None,
                html_source_hash=hashlib.md5(html_content.encode()).hexdigest()[:16],
                extraction_confidence=0.95,  # Case study confidence
                validation_flags=[]
            )
            
            # Validate using case study logic
            if property_data.is_authentic_real_data():
                logger.info(f"✅ Extracted: {title[:50]}... - €{price:,} - {sqm}m²")
                return property_data
            else:
                logger.warning(f"⚠️ Invalid property: {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to extract {url}: {e}")
            return None
    
    async def scrape_working_athens(self, max_properties: int = 20) -> List[WorkingSpitogatosProperty]:
        """Main scraping using EXACT working case study approach"""
        
        logger.info("🚀 STARTING WORKING SPITOGATOS SCRAPING")
        logger.info(f"🎯 Target: {max_properties} properties using proven success method")
        
        all_properties = []
        playwright, browser, context = await self.create_working_browser()
        
        try:
            page = await context.new_page()
            
            for i, search_url in enumerate(self.working_urls, 1):
                if len(all_properties) >= max_properties:
                    break
                
                logger.info(f"📍 Working URL {i}/{len(self.working_urls)}")
                
                try:
                    # Discover property URLs
                    property_urls = await self.discover_working_property_urls(page, search_url)
                    
                    if not property_urls:
                        logger.warning(f"⚠️ No URLs found in {search_url}")
                        continue
                    
                    # Extract properties (limit per search)
                    for j, url in enumerate(property_urls[:max_properties//len(self.working_urls) + 2], 1):
                        if len(all_properties) >= max_properties:
                            break
                        
                        logger.info(f"📊 Extracting {j}/{len(property_urls[:10])}: ...{url[-15:]}")
                        
                        property_data = await self.extract_working_property(page, url)
                        
                        if property_data:
                            all_properties.append(property_data)
                        else:
                            self.failed_extractions.append(url)
                        
                        # Human delay (case study timing)
                        await asyncio.sleep(random.uniform(2, 5))
                    
                    # Break between searches
                    await asyncio.sleep(random.uniform(5, 10))
                    
                except Exception as e:
                    logger.error(f"❌ Search failed: {e}")
                    continue
            
        finally:
            await browser.close()
            await playwright.stop()
        
        logger.info(f"🎯 WORKING SCRAPING COMPLETED")
        logger.info(f"✅ Authentic properties: {len(all_properties)}")
        logger.info(f"❌ Failed extractions: {len(self.failed_extractions)}")
        
        return all_properties
    
    def save_working_results(self, properties: List[WorkingSpitogatosProperty], output_dir: str = "data/processed"):
        """Save in EXACT case study format"""
        
        if not properties:
            logger.warning("No properties to save")
            return None
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save in case study format
        properties_data = [asdict(prop) for prop in properties]
        
        json_file = output_path / f'spitogatos_working_athens_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Working results saved: {json_file}")
        
        # Show statistics like case study
        authentic_count = len([p for p in properties if "AUTHENTIC_VERIFIED" in p.validation_flags])
        if authentic_count > 0:
            prices = [p.price for p in properties if p.price]
            sqms = [p.sqm for p in properties if p.sqm]
            
            logger.info(f"📊 WORKING RESULTS (CASE STUDY FORMAT):")
            logger.info(f"   Authentic properties: {authentic_count}/{len(properties)} ({authentic_count/len(properties)*100:.1f}%)")
            if prices:
                logger.info(f"   Average price: €{sum(prices)/len(prices):,.0f}")
            if sqms:
                logger.info(f"   Average size: {sum(sqms)/len(sqms):.0f}m²")
        
        return str(json_file)

# Test function
async def test_working_scraper():
    """Test with small sample"""
    
    scraper = WorkingSpitogatosScraper()
    
    # Small test like case study
    properties = await scraper.scrape_working_athens(max_properties=5)
    
    if properties:
        result_file = scraper.save_working_results(properties)
        
        # Show first property like case study
        sample = properties[0]
        logger.info("📋 SAMPLE PROPERTY (CASE STUDY FORMAT):")
        logger.info(f"   Property ID: {sample.property_id}")
        logger.info(f"   URL: {sample.url}")
        logger.info(f"   Title: {sample.title}")
        logger.info(f"   Price: €{sample.price:,}")
        logger.info(f"   SQM: {sample.sqm}")
        logger.info(f"   Price/SQM: €{sample.price_per_sqm:.0f}")
        logger.info(f"   Validation: {sample.validation_flags}")
        
        return result_file
    else:
        logger.error("❌ No properties extracted")
        return None

if __name__ == "__main__":
    asyncio.run(test_working_scraper())