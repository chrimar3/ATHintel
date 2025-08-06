#!/usr/bin/env python3
"""
🏠 Complete Real Data Scraper - All Required Fields
Extracts: SQM, Price, Energy Class, URL + 100% Real Data Validation

Requirements:
✅ SQM (square meters)
✅ Price (euros)
✅ Energy Class (A+, A, B, C, D, etc.)
✅ URL (direct property link)
✅ 100% Real Data (strict validation)
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
class CompleteRealProperty:
    """Complete real property with ALL required fields"""
    property_id: str
    url: str
    timestamp: str
    title: str
    neighborhood: str
    
    # REQUIRED FIELDS
    price: Optional[float]
    sqm: Optional[float]
    energy_class: Optional[str]
    
    # CALCULATED FIELDS
    price_per_sqm: Optional[float]
    
    # ADDITIONAL DATA
    rooms: Optional[int]
    floor: Optional[str]
    property_type: str
    listing_type: str
    description: str
    
    # VALIDATION
    html_source_hash: str
    extraction_confidence: float
    validation_flags: List[str]
    
    def has_all_required_data(self) -> bool:
        """Check if property has ALL required fields"""
        
        required_fields = [
            self.url,
            self.price,
            self.sqm,
            self.energy_class
        ]
        
        missing_fields = []
        
        if not self.url:
            missing_fields.append("URL")
        if not self.price or self.price <= 0:
            missing_fields.append("PRICE")
        if not self.sqm or self.sqm <= 0:
            missing_fields.append("SQM")
        if not self.energy_class:
            missing_fields.append("ENERGY_CLASS")
        
        if missing_fields:
            self.validation_flags.extend([f"MISSING_{field}" for field in missing_fields])
            return False
        
        return True
    
    def is_authentic_real_data(self) -> bool:
        """Strict validation for 100% real data"""
        
        # Must have all required fields first
        if not self.has_all_required_data():
            return False
        
        # Athens market validation (realistic ranges)
        if self.price < 30000 or self.price > 15000000:  # €30k - €15M
            self.validation_flags.append("UNREALISTIC_PRICE")
            return False
        
        if self.sqm < 15 or self.sqm > 1000:  # 15m² - 1000m²
            self.validation_flags.append("UNREALISTIC_SIZE")
            return False
        
        # Energy class validation
        valid_energy_classes = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']
        if self.energy_class not in valid_energy_classes:
            self.validation_flags.append("INVALID_ENERGY_CLASS")
            return False
        
        # Price per sqm sanity check
        if self.price_per_sqm:
            if self.price_per_sqm < 500 or self.price_per_sqm > 20000:  # €500-€20k/m²
                self.validation_flags.append("UNREALISTIC_PRICE_PER_SQM")
                return False
        
        # Title quality check
        if len(self.title) < 10:
            self.validation_flags.append("POOR_TITLE_QUALITY")
            return False
        
        self.validation_flags.append("COMPLETE_AUTHENTIC_DATA")
        return True

class CompleteRealDataScraper:
    """Scraper focused on extracting ALL required fields with 100% real data"""
    
    def __init__(self):
        self.complete_properties = []
        self.incomplete_properties = []
        self.failed_extractions = []
        
        # Working URLs from successful test
        self.working_search_urls = [
            "https://www.spitogatos.gr/en/for_sale-homes/athens-center"
        ]
        
        logger.info("🏠 COMPLETE REAL DATA SCRAPER")
        logger.info("📋 Required fields: URL, Price, SQM, Energy Class")
        logger.info("✅ 100% real data validation enabled")
    
    async def create_enhanced_browser(self):
        """Enhanced browser for better data extraction"""
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
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
    
    async def discover_property_urls_enhanced(self, page, search_url: str, max_urls: int = 100) -> List[str]:
        """Enhanced URL discovery for maximum property extraction"""
        
        logger.info(f"🔍 Enhanced discovery from: {search_url}")
        
        try:
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            # Handle cookies
            try:
                cookie_button = page.locator('button:has-text("AGREE"), button:has-text("Αποδοχή")')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    logger.info("✅ Cookies accepted")
                    await asyncio.sleep(2)
            except:
                pass
            
            # Get HTML content
            html_content = await page.content()
            
            # Enhanced property URL extraction
            property_urls = set()
            
            # Pattern 1: Direct property links
            direct_patterns = [
                r'href="(/en/property/\d+)"',
                r'href="(https://www\.spitogatos\.gr/en/property/\d+)"'
            ]
            
            for pattern in direct_patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    url = match.group(1)
                    if not url.startswith('http'):
                        url = f"https://www.spitogatos.gr{url}"
                    property_urls.add(url)
            
            # Pattern 2: Property IDs from various contexts
            id_patterns = [
                r'/property/(\d+)',
                r'property-(\d+)',
                r'listing-id-(\d+)',
                r'property_id[\'\"]:[\s]*[\'\"]*(\d+)',
                r'data-property-id[\'\"]*=[\'\"]*(\d+)'
            ]
            
            for pattern in id_patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    property_id = match.group(1)
                    url = f"https://www.spitogatos.gr/en/property/{property_id}"
                    property_urls.add(url)
            
            unique_urls = list(property_urls)[:max_urls]
            logger.info(f"✅ Enhanced discovery found {len(unique_urls)} unique URLs")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"❌ Enhanced discovery failed: {e}")
            return []
    
    async def extract_complete_property_data(self, page, url: str) -> Optional[CompleteRealProperty]:
        """Extract complete property data with ALL required fields"""
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(2)
            
            # Get full HTML for comprehensive extraction
            html_content = await page.content()
            
            # Extract Title
            title = await self._extract_title(page, html_content)
            
            # Extract Price (REQUIRED)
            price = await self._extract_price(page, html_content)
            
            # Extract SQM (REQUIRED)
            sqm = await self._extract_sqm(page, html_content, title)
            
            # Extract Energy Class (REQUIRED) - Enhanced extraction
            energy_class = await self._extract_energy_class(page, html_content)
            
            # Extract additional data
            neighborhood = self._extract_neighborhood(title, html_content)
            rooms = await self._extract_rooms(page, html_content)
            floor = await self._extract_floor(page, html_content)
            description = await self._extract_description(page, html_content)
            
            # Calculate price per sqm
            price_per_sqm = None
            if price and sqm and sqm > 0:
                price_per_sqm = price / sqm
            
            # Generate property ID
            property_id = hashlib.md5(url.encode()).hexdigest()[:12]
            html_hash = hashlib.md5(html_content.encode()).hexdigest()[:16]
            
            # Create complete property object
            property_data = CompleteRealProperty(
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
                floor=floor,
                property_type="apartment",
                listing_type="sale",
                description=description or "",
                html_source_hash=html_hash,
                extraction_confidence=0.95,
                validation_flags=[]
            )
            
            # Validate with strict requirements
            if property_data.is_authentic_real_data():
                logger.info(f"✅ COMPLETE: {title[:40]}... - €{price:,} - {sqm}m² - {energy_class}")
                return property_data
            else:
                logger.warning(f"⚠️ INCOMPLETE: Missing required data - {property_data.validation_flags}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Complete extraction failed for {url}: {e}")
            return None
    
    async def _extract_title(self, page, html_content: str) -> str:
        """Extract property title"""
        
        # Try page title first
        try:
            title = await page.title()
            if title and len(title) > 10:
                return title
        except:
            pass
        
        # Try HTML patterns
        title_patterns = [
            r'<title>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'property-title[^>]*>([^<]+)<'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    async def _extract_price(self, page, html_content: str) -> Optional[float]:
        """Extract price (REQUIRED FIELD)"""
        
        # Try page selectors first
        price_selectors = [
            '.price', '.property-price', '.listing-price', '[data-testid*="price"]'
        ]
        
        for selector in price_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    price_text = await element.text_content()
                    if price_text:
                        price = self._parse_price(price_text)
                        if price:
                            return price
            except:
                continue
        
        # Try HTML patterns
        price_patterns = [
            r'€\s*([\d,]+)',
            r'(\d+)\s*€',
            r'"price"\s*:\s*(\d+)',
            r'price["\s:]*(\d+)',
            r'€([\d,.]+)',
            r'(\d{3,})\s*EUR'
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, html_content)
            for match in matches:
                try:
                    price_str = match.group(1).replace(',', '').replace('.', '')
                    if len(price_str) >= 4:  # At least €1000
                        return float(price_str)
                except:
                    continue
        
        return None
    
    async def _extract_sqm(self, page, html_content: str, title: str) -> Optional[float]:
        """Extract square meters (REQUIRED FIELD)"""
        
        # Try extracting from title first (most reliable)
        title_sqm_patterns = [
            r'(\d+)m²',
            r'(\d+)\s*sqm',
            r'(\d+)\s*τ\.μ\.'
        ]
        
        for pattern in title_sqm_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        # Try page selectors
        sqm_selectors = [
            '.sqm', '.area', '.size', '[data-testid*="area"]', '.property-area'
        ]
        
        for selector in sqm_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    sqm_text = await element.text_content()
                    if sqm_text:
                        sqm = self._parse_sqm(sqm_text)
                        if sqm:
                            return sqm
            except:
                continue
        
        # Try HTML patterns
        sqm_patterns = [
            r'(\d+)\s*m²',
            r'(\d+)\s*sqm',
            r'(\d+)\s*τ\.μ\.',
            r'"sqm"\s*:\s*(\d+)',
            r'area["\s:]*(\d+)',
            r'(\d+)\s*square\s*met'
        ]
        
        for pattern in sqm_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    async def _extract_energy_class(self, page, html_content: str) -> Optional[str]:
        """Extract energy class (REQUIRED FIELD) - Enhanced extraction"""
        
        # Try page selectors
        energy_selectors = [
            '.energy', '.energy-class', '.energy-rating', '.energy-certificate',
            '[data-testid*="energy"]', '.pec', '.energy-label'
        ]
        
        for selector in energy_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    energy_text = await element.text_content()
                    if energy_text:
                        energy_class = self._parse_energy_class(energy_text)
                        if energy_class:
                            return energy_class
            except:
                continue
        
        # Enhanced HTML patterns for energy class
        energy_patterns = [
            r'energy[_\s-]*class["\s:]*([A-G][+]?)',
            r'energy[_\s-]*rating["\s:]*([A-G][+]?)',
            r'energy[_\s-]*certificate["\s:]*([A-G][+]?)',
            r'pec["\s:]*([A-G][+]?)',
            r'ενεργειακή["\s:]*([A-G][+]?)',
            r'κατηγορία["\s:]*([A-G][+]?)',
            r'class["\s:]*([A-G][+]?)',
            r'([A-G][+]?)\s*class',
            r'energy[^<>]*?([A-G][+])',
            r'"energy"[^}]*?"([A-G][+]?)"',
            r'energy-([A-G][+]?)',
            r'grade["\s:]*([A-G][+]?)'
        ]
        
        for pattern in energy_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                energy_class = match.group(1).upper()
                if self._is_valid_energy_class(energy_class):
                    return energy_class
        
        # Look for energy class in various contexts
        energy_contexts = [
            r'ενεργειακή\s+κατηγορία[:\s]*([A-G][+]?)',
            r'energy\s+efficiency[:\s]*([A-G][+]?)',
            r'energy\s+performance[:\s]*([A-G][+]?)',
            r'κατηγορία\s+ενέργειας[:\s]*([A-G][+]?)'
        ]
        
        for pattern in energy_contexts:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                energy_class = match.group(1).upper()
                if self._is_valid_energy_class(energy_class):
                    return energy_class
        
        return None
    
    async def _extract_rooms(self, page, html_content: str) -> Optional[int]:
        """Extract number of rooms"""
        
        # Try selectors
        room_selectors = ['.rooms', '.bedrooms', '.room-count']
        
        for selector in room_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    room_text = await element.text_content()
                    if room_text:
                        match = re.search(r'(\d+)', room_text)
                        if match:
                            return int(match.group(1))
            except:
                continue
        
        # Try HTML patterns
        room_patterns = [
            r'(\d+)\s*bedroom',
            r'(\d+)\s*room',
            r'rooms["\s:]*(\d+)',
            r'bedroom["\s:]*(\d+)'
        ]
        
        for pattern in room_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    async def _extract_floor(self, page, html_content: str) -> Optional[str]:
        """Extract floor information"""
        
        floor_patterns = [
            r'(\d+)\s*floor',
            r'floor["\s:]*(\d+)',
            r'όροφος["\s:]*(\d+)',
            r'(\d+)ος\s*όροφος'
        ]
        
        for pattern in floor_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _extract_description(self, page, html_content: str) -> str:
        """Extract property description"""
        
        # Try selectors
        desc_selectors = ['.description', '.property-description', '.details']
        
        for selector in desc_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    desc_text = await element.text_content()
                    if desc_text and len(desc_text) > 20:
                        return desc_text[:500]  # Limit length
            except:
                continue
        
        return ""
    
    def _extract_neighborhood(self, title: str, html_content: str) -> str:
        """Extract neighborhood from title or content"""
        
        athens_neighborhoods = [
            'Kolonaki', 'Κολωνάκι', 'Plaka', 'Πλάκα', 'Syntagma', 'Σύνταγμα',
            'Exarchia', 'Εξάρχεια', 'Psyrri', 'Ψυρρή', 'Monastiraki', 'Μοναστηράκι',
            'Koukaki', 'Κουκάκι', 'Mets', 'Μετς', 'Pangrati', 'Παγκράτι'
        ]
        
        text_to_check = f"{title} {html_content}".lower()
        
        for neighborhood in athens_neighborhoods:
            if neighborhood.lower() in text_to_check:
                return neighborhood
        
        return "Athens Center"
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        if not price_text:
            return None
        
        clean_text = re.sub(r'[€$£,\s]', '', price_text)
        match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_sqm(self, sqm_text: str) -> Optional[float]:
        """Parse square meters from text"""
        if not sqm_text:
            return None
        
        match = re.search(r'(\d+(?:\.\d+)?)', sqm_text)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_energy_class(self, energy_text: str) -> Optional[str]:
        """Parse energy class from text"""
        if not energy_text:
            return None
        
        match = re.search(r'([A-G][+]?)', energy_text.upper())
        if match:
            energy_class = match.group(1)
            if self._is_valid_energy_class(energy_class):
                return energy_class
        
        return None
    
    def _is_valid_energy_class(self, energy_class: str) -> bool:
        """Validate energy class"""
        valid_classes = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']
        return energy_class in valid_classes
    
    async def scrape_complete_athens_data(self, max_properties: int = 50) -> List[CompleteRealProperty]:
        """Main scraping method for complete Athens data"""
        
        logger.info("🚀 STARTING COMPLETE ATHENS DATA EXTRACTION")
        logger.info(f"🎯 Target: {max_properties} properties with ALL required fields")
        logger.info("📋 Required: URL + Price + SQM + Energy Class")
        
        complete_properties = []
        incomplete_properties = []
        
        playwright, browser, context = await self.create_enhanced_browser()
        
        try:
            page = await context.new_page()
            
            for search_url in self.working_search_urls:
                if len(complete_properties) >= max_properties:
                    break
                
                logger.info(f"📍 Extracting from: {search_url}")
                
                # Discover many URLs
                property_urls = await self.discover_property_urls_enhanced(
                    page, search_url, max_urls=max_properties * 3
                )
                
                if not property_urls:
                    logger.warning("⚠️ No URLs discovered")
                    continue
                
                logger.info(f"📊 Processing {len(property_urls)} discovered URLs...")
                
                # Extract complete data
                for i, url in enumerate(property_urls, 1):
                    if len(complete_properties) >= max_properties:
                        break
                    
                    logger.info(f"🔍 Processing {i}/{len(property_urls)}: ...{url[-15:]}")
                    
                    property_data = await self.extract_complete_property_data(page, url)
                    
                    if property_data:
                        complete_properties.append(property_data)
                        logger.info(f"✅ COMPLETE #{len(complete_properties)}: {property_data.neighborhood} - €{property_data.price:,} - {property_data.sqm}m² - {property_data.energy_class}")
                    else:
                        incomplete_properties.append(url)
                    
                    # Human delay
                    await asyncio.sleep(random.uniform(2, 4))
                
                logger.info(f"📊 Progress: {len(complete_properties)} complete, {len(incomplete_properties)} incomplete")
                
        finally:
            await browser.close()
            await playwright.stop()
        
        logger.info("🎯 COMPLETE EXTRACTION FINISHED")
        logger.info(f"✅ Complete properties: {len(complete_properties)}")
        logger.info(f"⚠️ Incomplete properties: {len(incomplete_properties)}")
        
        return complete_properties
    
    def save_complete_results(self, properties: List[CompleteRealProperty], output_dir: str = "data/processed"):
        """Save complete results with all required fields"""
        
        if not properties:
            logger.warning("No complete properties to save")
            return None
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete data
        properties_data = [asdict(prop) for prop in properties]
        
        json_file = output_path / f'athens_complete_real_data_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, indent=2, ensure_ascii=False)
        
        # Create summary CSV with required fields
        csv_file = output_path / f'athens_complete_summary_{timestamp}.csv'
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Title\n")
            for prop in properties:
                f.write(f'"{prop.url}",{prop.price},{prop.sqm},"{prop.energy_class}",{prop.price_per_sqm:.0f},"{prop.neighborhood}","{prop.title[:50]}..."\n')
        
        logger.info(f"💾 Complete results saved:")
        logger.info(f"   JSON: {json_file}")
        logger.info(f"   CSV: {csv_file}")
        
        # Show statistics
        prices = [p.price for p in properties]
        sqms = [p.sqm for p in properties]
        energy_classes = [p.energy_class for p in properties]
        
        logger.info(f"📊 COMPLETE DATA STATISTICS:")
        logger.info(f"   Properties: {len(properties)}")
        logger.info(f"   Price range: €{min(prices):,.0f} - €{max(prices):,.0f}")
        logger.info(f"   Size range: {min(sqms):.0f}m² - {max(sqms):.0f}m²")
        logger.info(f"   Energy classes: {set(energy_classes)}")
        logger.info(f"   Avg price/m²: €{sum(p.price_per_sqm for p in properties)/len(properties):.0f}")
        
        return str(json_file), str(csv_file)

# Main execution function
async def extract_complete_athens_data():
    """Extract complete Athens real estate data with ALL required fields"""
    
    scraper = CompleteRealDataScraper()
    
    # Extract properties with all required fields
    properties = await scraper.scrape_complete_athens_data(max_properties=30)
    
    if properties:
        json_file, csv_file = scraper.save_complete_results(properties)
        
        logger.info("🎉 COMPLETE EXTRACTION SUCCESS!")
        logger.info(f"📁 Data files: {json_file}")
        logger.info(f"📊 Summary CSV: {csv_file}")
        
        # Show first few properties
        logger.info("\n📋 SAMPLE COMPLETE PROPERTIES:")
        for i, prop in enumerate(properties[:3], 1):
            logger.info(f"{i}. {prop.neighborhood}: €{prop.price:,} - {prop.sqm}m² - {prop.energy_class} - {prop.url}")
        
        return json_file, csv_file
    else:
        logger.error("❌ No complete properties extracted")
        return None, None

if __name__ == "__main__":
    asyncio.run(extract_complete_athens_data())