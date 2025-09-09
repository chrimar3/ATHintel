#!/usr/bin/env python3
"""
🏠 Large Scale Real Data Scraper
Scale up to extract 100+ authentic Athens properties with ALL required fields

Strategy:
- Multiple search pages and pagination
- Enhanced URL discovery methods
- Robust error handling for scale
- All required fields: URL, Price, SQM, Energy Class
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
class ScaledRealProperty:
    """Real property with all required fields for large scale extraction"""
    property_id: str
    url: str
    timestamp: str
    title: str
    neighborhood: str
    
    # REQUIRED FIELDS
    price: Optional[float]
    sqm: Optional[float]
    energy_class: Optional[str]
    
    # CALCULATED
    price_per_sqm: Optional[float]
    
    # ADDITIONAL
    rooms: Optional[int]
    floor: Optional[str]
    property_type: str
    listing_type: str
    description: str
    
    # VALIDATION
    html_source_hash: str
    extraction_confidence: float
    validation_flags: List[str]
    
    def is_complete_authentic_data(self) -> bool:
        """Strict validation for scaled extraction"""
        
        # Must have all required fields
        if not all([self.url, self.price, self.sqm, self.energy_class]):
            missing = []
            if not self.url: missing.append("URL")
            if not self.price: missing.append("PRICE")
            if not self.sqm: missing.append("SQM")
            if not self.energy_class: missing.append("ENERGY_CLASS")
            self.validation_flags.extend([f"MISSING_{field}" for field in missing])
            return False
        
        # Athens market validation
        if self.price < 30000 or self.price > 20000000:  # €30k - €20M
            self.validation_flags.append("UNREALISTIC_PRICE")
            return False
        
        if self.sqm < 15 or self.sqm > 1000:  # 15m² - 1000m²
            self.validation_flags.append("UNREALISTIC_SIZE")
            return False
        
        # Energy class validation
        valid_energy = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']
        if self.energy_class not in valid_energy:
            self.validation_flags.append("INVALID_ENERGY_CLASS")
            return False
        
        # Price per sqm check
        if self.price_per_sqm:
            if self.price_per_sqm < 300 or self.price_per_sqm > 25000:  # €300-€25k/m²
                self.validation_flags.append("UNREALISTIC_PRICE_PER_SQM")
                return False
        
        self.validation_flags.append("SCALED_AUTHENTIC_DATA")
        return True

class LargeScaleRealScraper:
    """Large scale scraper for 100+ authentic properties"""
    
    def __init__(self):
        self.complete_properties = []
        self.incomplete_properties = []
        self.failed_extractions = []
        self.processed_urls = set()
        
        # Multiple search strategies for scale
        self.search_strategies = [
            # Main Athens searches
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center",
            "https://www.spitogatos.gr/en/for_sale-apartments/athens-center",
            "https://www.spitogatos.gr/en/for_rent-homes/athens-center",
            "https://www.spitogatos.gr/en/for_rent-apartments/athens-center",
            
            # Broader Athens
            "https://www.spitogatos.gr/en/for_sale-homes/athens",
            "https://www.spitogatos.gr/en/for_sale-apartments/athens",
            
            # Price range searches
            "https://www.spitogatos.gr/search/results?geo_place_id=2995&sort=price&listing_type=1",
            "https://www.spitogatos.gr/search/results?geo_place_id=2995&sort=date&listing_type=1",
            
            # Alternative formats
            "https://www.spitogatos.gr/en/search/for_sale",
            "https://www.spitogatos.gr/en/search/for_rent"
        ]
        
        logger.info("🏠 LARGE SCALE REAL DATA SCRAPER")
        logger.info(f"🔍 Using {len(self.search_strategies)} search strategies")
        logger.info("🎯 Target: 100+ properties with ALL required fields")
    
    async def create_scaled_browser(self):
        """Browser optimized for large scale extraction"""
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Keep visible for monitoring
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-dev-shm-usage',
                '--disable-gpu'
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
    
    async def discover_urls_with_pagination(self, page, search_url: str, max_pages: int = 5) -> List[str]:
        """Enhanced URL discovery with pagination support"""
        
        logger.info(f"🔍 Large scale discovery: {search_url}")
        
        all_urls = set()
        
        try:
            # Initial page load
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            # Handle cookies once
            try:
                cookie_button = page.locator('button:has-text("AGREE"), button:has-text("Αποδοχή")')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    await asyncio.sleep(2)
            except:
                pass
            
            # Extract URLs from current page
            page_urls = await self._extract_urls_from_page(page)
            all_urls.update(page_urls)
            logger.info(f"📋 Page 1: {len(page_urls)} URLs")
            
            # Try pagination
            for page_num in range(2, max_pages + 1):
                try:
                    # Look for next page button
                    next_selectors = [
                        'a:has-text("Next")',
                        'a:has-text("Επόμενη")', 
                        '.next-page',
                        '.pagination-next',
                        f'a:has-text("{page_num}")'
                    ]
                    
                    next_clicked = False
                    for selector in next_selectors:
                        next_button = page.locator(selector)
                        if await next_button.count() > 0:
                            await next_button.first.click()
                            await page.wait_for_load_state('domcontentloaded', timeout=15000)
                            await asyncio.sleep(2)
                            next_clicked = True
                            break
                    
                    if not next_clicked:
                        # Try URL-based pagination
                        if '?' in search_url:
                            paginated_url = f"{search_url}&page={page_num}"
                        else:
                            paginated_url = f"{search_url}?page={page_num}"
                        
                        await page.goto(paginated_url, wait_until='domcontentloaded', timeout=20000)
                        await asyncio.sleep(2)
                    
                    # Extract URLs from this page
                    page_urls = await self._extract_urls_from_page(page)
                    if not page_urls:
                        logger.info(f"📄 Page {page_num}: No URLs found, stopping pagination")
                        break
                    
                    all_urls.update(page_urls)
                    logger.info(f"📋 Page {page_num}: {len(page_urls)} URLs")
                    
                    # Don't overwhelm the server
                    await asyncio.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Pagination page {page_num} failed: {e}")
                    break
            
            unique_urls = list(all_urls)
            logger.info(f"✅ Total URLs discovered: {len(unique_urls)}")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"❌ URL discovery failed: {e}")
            return []
    
    async def _extract_urls_from_page(self, page) -> List[str]:
        """Extract property URLs from current page"""
        
        try:
            html_content = await page.content()
            urls = set()
            
            # Enhanced URL patterns
            url_patterns = [
                r'href="(/en/property/\d+)"',
                r'href="(https://www\.spitogatos\.gr/en/property/\d+)"',
                r'"/en/property/(\d+)"',
                r'/property/(\d+)',
                r'property-(\d+)',
                r'listing-(\d+)',
                r'data-property-id="(\d+)"',
                r'property_id[\'\"]:[\s]*[\'\"]*(\d+)'
            ]
            
            for pattern in url_patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    try:
                        if match.group(1).startswith('/'):
                            url = f"https://www.spitogatos.gr{match.group(1)}"
                        elif match.group(1).startswith('http'):
                            url = match.group(1)
                        else:
                            # It's just a property ID
                            property_id = match.group(1)
                            url = f"https://www.spitogatos.gr/en/property/{property_id}"
                        
                        urls.add(url)
                    except:
                        continue
            
            return list(urls)
            
        except Exception as e:
            logger.error(f"❌ URL extraction from page failed: {e}")
            return []
    
    async def extract_scaled_property_data(self, page, url: str) -> Optional[ScaledRealProperty]:
        """Extract property data optimized for large scale"""
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(1)  # Shorter delay for scale
            
            html_content = await page.content()
            
            # Fast extraction methods
            title = await self._fast_extract_title(page, html_content)
            price = await self._fast_extract_price(page, html_content)
            sqm = await self._fast_extract_sqm(page, html_content, title)
            energy_class = await self._fast_extract_energy_class(page, html_content)
            
            # Additional data
            neighborhood = self._extract_neighborhood_fast(title, html_content)
            rooms = await self._fast_extract_rooms(page, html_content)
            description = await self._fast_extract_description(page, html_content)
            
            # Calculate price per sqm
            price_per_sqm = None
            if price and sqm and sqm > 0:
                price_per_sqm = price / sqm
            
            # Generate IDs
            property_id = hashlib.md5(url.encode()).hexdigest()[:12]
            html_hash = hashlib.md5(html_content.encode()).hexdigest()[:16]
            
            # Create property object
            property_data = ScaledRealProperty(
                property_id=property_id,
                url=url,
                timestamp=datetime.now().isoformat(),
                title=title or "Unknown Property",
                neighborhood=neighborhood,
                price=price,
                sqm=sqm,
                energy_class=energy_class,
                price_per_sqm=price_per_sqm,
                rooms=rooms,
                floor=None,
                property_type="apartment",
                listing_type="sale",
                description=description or "",
                html_source_hash=html_hash,
                extraction_confidence=0.90,  # Slightly lower for speed
                validation_flags=[]
            )
            
            # Validate
            if property_data.is_complete_authentic_data():
                return property_data
            else:
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Fast extraction failed: {url[-15:]} - {e}")
            return None
    
    async def _fast_extract_title(self, page, html_content: str) -> str:
        """Fast title extraction"""
        try:
            title = await page.title()
            if title and len(title) > 10:
                return title
        except:
            pass
        
        # Quick HTML pattern
        match = re.search(r'<title>([^<]+)</title>', html_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return ""
    
    async def _fast_extract_price(self, page, html_content: str) -> Optional[float]:
        """Fast price extraction"""
        
        # Quick patterns for common price formats
        price_patterns = [
            r'€\s*([\d,]+)',
            r'(\d{4,})\s*€',
            r'"price"\s*:\s*(\d+)',
            r'€([\d,.]+)'
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, html_content)
            for match in matches:
                try:
                    price_str = match.group(1).replace(',', '').replace('.', '')
                    if len(price_str) >= 4:
                        return float(price_str)
                except:
                    continue
        
        return None
    
    async def _fast_extract_sqm(self, page, html_content: str, title: str) -> Optional[float]:
        """Fast SQM extraction"""
        
        # Try title first (most reliable)
        title_match = re.search(r'(\d+)m²', title)
        if title_match:
            return float(title_match.group(1))
        
        # Quick HTML patterns
        sqm_patterns = [
            r'(\d+)\s*m²',
            r'(\d+)\s*sqm',
            r'"sqm"\s*:\s*(\d+)'
        ]
        
        for pattern in sqm_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    async def _fast_extract_energy_class(self, page, html_content: str) -> Optional[str]:
        """Fast energy class extraction"""
        
        # Enhanced energy class patterns
        energy_patterns = [
            r'energy[_\s-]*class["\s:]*([A-G][+]?)',
            r'energy[_\s-]*([A-G][+]?)',
            r'class["\s:]*([A-G][+]?)',
            r'([A-G][+]?)\s*class',
            r'"energy"[^}]*?"([A-G][+]?)"',
            r'ενεργειακή["\s:]*([A-G][+]?)',
            r'κατηγορία["\s:]*([A-G][+]?)'
        ]
        
        for pattern in energy_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                energy_class = match.group(1).upper()
                if energy_class in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']:
                    return energy_class
        
        return None
    
    async def _fast_extract_rooms(self, page, html_content: str) -> Optional[int]:
        """Fast rooms extraction"""
        
        room_patterns = [
            r'(\d+)\s*bedroom',
            r'(\d+)\s*room',
            r'rooms["\s:]*(\d+)'
        ]
        
        for pattern in room_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    async def _fast_extract_description(self, page, html_content: str) -> str:
        """Fast description extraction"""
        
        # Look for common description patterns
        desc_patterns = [
            r'Make this property yours with a mortgage[^<]*',
            r'Compare & save up to[^<]*'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(0)[:200]  # Limit length
        
        return ""
    
    def _extract_neighborhood_fast(self, title: str, html_content: str) -> str:
        """Fast neighborhood extraction"""
        
        neighborhoods = [
            'Kolonaki', 'Κολωνάκι', 'Plaka', 'Πλάκα', 'Syntagma', 'Σύνταγμα',
            'Exarchia', 'Εξάρχεια', 'Psyrri', 'Ψυρρή', 'Monastiraki', 'Μοναστηράκι',
            'Koukaki', 'Κουκάκι', 'Mets', 'Μετς', 'Pangrati', 'Παγκράτι',
            'Petralona', 'Πετράλωνα', 'Kipseli', 'Κυψέλη', 'Ampelokipoi', 'Αμπελόκηποι'
        ]
        
        text_check = title.lower()
        
        for neighborhood in neighborhoods:
            if neighborhood.lower() in text_check:
                return neighborhood
        
        return "Athens Center"
    
    async def scrape_large_scale_athens(self, target_properties: int = 100) -> List[ScaledRealProperty]:
        """Main large scale scraping method"""
        
        logger.info("🚀 STARTING LARGE SCALE ATHENS EXTRACTION")
        logger.info(f"🎯 Target: {target_properties} complete properties")
        
        complete_properties = []
        playwright, browser, context = await self.create_scaled_browser()
        
        try:
            page = await context.new_page()
            
            properties_per_strategy = max(10, target_properties // len(self.search_strategies))
            
            for i, search_url in enumerate(self.search_strategies, 1):
                if len(complete_properties) >= target_properties:
                    break
                
                logger.info(f"📍 Strategy {i}/{len(self.search_strategies)}: {search_url.split('/')[-1]}")
                
                try:
                    # Discover URLs with pagination
                    property_urls = await self.discover_urls_with_pagination(
                        page, search_url, max_pages=3
                    )
                    
                    if not property_urls:
                        logger.warning(f"⚠️ No URLs from strategy {i}")
                        continue
                    
                    # Remove already processed URLs
                    new_urls = [url for url in property_urls if url not in self.processed_urls]
                    logger.info(f"📊 Processing {len(new_urls)} new URLs from strategy {i}")
                    
                    # Process URLs in batches
                    batch_size = 20
                    for batch_start in range(0, len(new_urls), batch_size):
                        if len(complete_properties) >= target_properties:
                            break
                        
                        batch_urls = new_urls[batch_start:batch_start + batch_size]
                        logger.info(f"🔄 Processing batch {batch_start//batch_size + 1}: {len(batch_urls)} URLs")
                        
                        for j, url in enumerate(batch_urls, 1):
                            if len(complete_properties) >= target_properties:
                                break
                            
                            if url in self.processed_urls:
                                continue
                            
                            logger.info(f"🔍 Extracting {len(complete_properties)+1}/{target_properties}: ...{url[-15:]}")
                            
                            property_data = await self.extract_scaled_property_data(page, url)
                            
                            if property_data:
                                complete_properties.append(property_data)
                                logger.info(f"✅ #{len(complete_properties)}: {property_data.neighborhood} - €{property_data.price:,} - {property_data.sqm}m² - {property_data.energy_class}")
                            else:
                                self.incomplete_properties.append(url)
                            
                            self.processed_urls.add(url)
                            
                            # Shorter delays for scale
                            await asyncio.sleep(random.uniform(1, 2))
                        
                        # Batch break  
                        await asyncio.sleep(random.uniform(3, 5))
                    
                    logger.info(f"📊 Strategy {i} complete: {len(complete_properties)} total properties")
                    
                    # Strategy break
                    await asyncio.sleep(random.uniform(5, 8))
                    
                except Exception as e:
                    logger.error(f"❌ Strategy {i} failed: {e}")
                    continue
        
        finally:
            await browser.close()
            await playwright.stop()
        
        logger.info("🎯 LARGE SCALE EXTRACTION COMPLETED")
        logger.info(f"✅ Complete properties: {len(complete_properties)}")
        logger.info(f"⚠️ Incomplete properties: {len(self.incomplete_properties)}")
        logger.info(f"🔄 Total URLs processed: {len(self.processed_urls)}")
        
        return complete_properties
    
    def save_large_scale_results(self, properties: List[ScaledRealProperty], output_dir: str = "data/processed"):
        """Save large scale results"""
        
        if not properties:
            logger.warning("No properties to save")
            return None, None
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        properties_data = [asdict(prop) for prop in properties]
        json_file = output_path / f'athens_large_scale_real_data_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, indent=2, ensure_ascii=False)
        
        # Save CSV
        csv_file = output_path / f'athens_large_scale_summary_{timestamp}.csv'
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Rooms,Title\n")
            for prop in properties:
                f.write(f'"{prop.url}",{prop.price},{prop.sqm},"{prop.energy_class}",{prop.price_per_sqm:.0f},"{prop.neighborhood}",{prop.rooms or ""},"{prop.title[:50]}..."\n')
        
        logger.info(f"💾 Large scale results saved:")
        logger.info(f"   JSON: {json_file}")
        logger.info(f"   CSV: {csv_file}")
        
        # Statistics
        prices = [p.price for p in properties]
        sqms = [p.sqm for p in properties]
        energy_classes = [p.energy_class for p in properties]
        neighborhoods = set(p.neighborhood for p in properties)
        
        logger.info(f"📊 LARGE SCALE STATISTICS:")
        logger.info(f"   Properties: {len(properties)}")
        logger.info(f"   Price range: €{min(prices):,.0f} - €{max(prices):,.0f}")
        logger.info(f"   Size range: {min(sqms):.0f}m² - {max(sqms):.0f}m²")
        logger.info(f"   Energy classes: {sorted(set(energy_classes))}")  
        logger.info(f"   Neighborhoods: {len(neighborhoods)}")
        logger.info(f"   Avg price/m²: €{sum(p.price_per_sqm for p in properties)/len(properties):.0f}")
        
        return str(json_file), str(csv_file)

# Main execution
async def extract_large_scale_athens_data(target_properties: int = 100):
    """Extract large scale Athens data"""
    
    scraper = LargeScaleRealScraper()
    
    logger.info(f"🚀 STARTING LARGE SCALE EXTRACTION: {target_properties} properties")
    
    properties = await scraper.scrape_large_scale_athens(target_properties)
    
    if properties:
        json_file, csv_file = scraper.save_large_scale_results(properties)
        
        logger.info("🎉 LARGE SCALE EXTRACTION SUCCESS!")
        logger.info(f"📁 Data: {json_file}")
        logger.info(f"📊 CSV: {csv_file}")
        
        # Show top properties by price
        top_properties = sorted(properties, key=lambda x: x.price, reverse=True)[:5]
        logger.info("\n🏆 TOP 5 MOST EXPENSIVE PROPERTIES:")
        for i, prop in enumerate(top_properties, 1):
            logger.info(f"{i}. {prop.neighborhood}: €{prop.price:,} - {prop.sqm}m² - {prop.energy_class}")
            logger.info(f"   {prop.url}")
        
        return json_file, csv_file
    else:
        logger.error("❌ No properties extracted")
        return None, None

if __name__ == "__main__":
    # You can change target_properties here
    asyncio.run(extract_large_scale_athens_data(target_properties=100))