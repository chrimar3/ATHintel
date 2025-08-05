#!/usr/bin/env python3
"""
🔍 Debug Scraper Test - Check actual website structure
"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_spitogatos():
    """Debug Spitogatos website structure"""
    
    logger.info("🔍 DEBUGGING SPITOGATOS STRUCTURE")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser for debugging
        page = await browser.new_page()
        
        # Set Greek headers
        await page.set_extra_http_headers({
            'Accept-Language': 'el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7'
        })
        
        try:
            # Go to Spitogatos search
            logger.info("📍 Navigating to Spitogatos search...")
            await page.goto('https://spitogatos.gr/search/results?geo_place_id=2995&sort=price&listing_type=1', 
                          wait_until='networkidle', timeout=30000)
            
            # Wait a bit and take screenshot
            await asyncio.sleep(3)
            await page.screenshot(path='debug_spitogatos.png')
            logger.info("📸 Screenshot saved: debug_spitogatos.png")
            
            # Check for various property link selectors
            selectors_to_try = [
                'a[href*="/property/"]',
                'a[href*="/listing/"]',
                'a[href*="/ad/"]',
                '.property-card a',
                '.listing-card a',
                '.search-result a',
                '[data-testid*="property"] a',
                '.property-item a'
            ]
            
            for selector in selectors_to_try:
                elements = await page.locator(selector).count()
                logger.info(f"🔍 Selector '{selector}': {elements} elements found")
            
            # Check page title and content
            title = await page.title()
            logger.info(f"📋 Page title: {title}")
            
            # Get some text content to verify page loaded
            content_preview = await page.locator('body').text_content()
            logger.info(f"📄 Page content preview: {content_preview[:200]}...")
            
            # Try to find any links at all
            all_links = await page.locator('a').count()
            logger.info(f"🔗 Total links on page: {all_links}")
            
            # Check for common class names
            common_classes = ['.property', '.listing', '.card', '.item', '.result']
            for class_name in common_classes:
                elements = await page.locator(class_name).count()
                if elements > 0:
                    logger.info(f"🎯 Found {elements} elements with class '{class_name}'")
            
            input("Press Enter to continue to XE.gr debug...")
            
        except Exception as e:
            logger.error(f"❌ Spitogatos debug failed: {e}")
        
        await browser.close()

async def debug_xe():
    """Debug XE.gr website structure"""
    
    logger.info("🔍 DEBUGGING XE.GR STRUCTURE")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.set_extra_http_headers({
            'Accept-Language': 'el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7'
        })
        
        try:
            logger.info("📍 Navigating to XE.gr...")
            await page.goto('https://xe.gr/property/search', wait_until='networkidle', timeout=30000)
            
            await asyncio.sleep(3)
            await page.screenshot(path='debug_xe.png')
            logger.info("📸 Screenshot saved: debug_xe.png")
            
            # Check page structure
            title = await page.title()
            logger.info(f"📋 XE Page title: {title}")
            
            # Look for property selectors
            xe_selectors = [
                'div[class*="property"]',
                'article[class*="property"]', 
                '.listing-item',
                '.ad-item',
                '.search-result',
                '[data-testid*="listing"]'
            ]
            
            for selector in xe_selectors:
                elements = await page.locator(selector).count()
                logger.info(f"🔍 XE Selector '{selector}': {elements} elements found")
            
            # Try searching for Athens
            try:
                search_input = page.locator('input[placeholder*="περιοχή"], input[name*="location"]')
                if await search_input.count() > 0:
                    logger.info("📝 Found search input, trying to search...")
                    await search_input.fill("Αθήνα")
                    await asyncio.sleep(2)
                    
                    # Look for search button
                    search_btn = page.locator('button[type="submit"], input[type="submit"]')
                    if await search_btn.count() > 0:
                        await search_btn.click()
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        await page.screenshot(path='debug_xe_results.png')
                        logger.info("📸 XE results screenshot saved")
                        
                        # Check results
                        for selector in xe_selectors:
                            elements = await page.locator(selector).count()
                            if elements > 0:
                                logger.info(f"🎯 After search '{selector}': {elements} elements found")
                
            except Exception as e:
                logger.warning(f"⚠️ XE search failed: {e}")
            
            input("Press Enter to close...")
            
        except Exception as e:
            logger.error(f"❌ XE debug failed: {e}")
        
        await browser.close()

async def main():
    """Run both debug sessions"""
    
    print("🔍 Website Structure Debug Session")
    print("=" * 50)
    
    # Debug Spitogatos first
    await debug_spitogatos()
    
    # Then debug XE
    await debug_xe()
    
    print("✅ Debug session completed. Check screenshots for visual confirmation.")

if __name__ == "__main__":
    asyncio.run(main())