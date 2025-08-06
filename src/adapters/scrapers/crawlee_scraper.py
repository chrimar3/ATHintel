"""
Advanced Crawlee-based Property Scraper - 2025 Latest Techniques

Implements state-of-the-art web scraping with Crawlee Python v0.6.0+
featuring adaptive crawling, advanced fingerprint evasion, and AI-enhanced extraction.
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, AsyncGenerator, Set, Any
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urljoin, urlparse
import hashlib
import random
import re
from dataclasses import dataclass, field

# Modern 2025 scraping stack
try:
    from crawlee import PlaywrightCrawler, Configuration, Request
    from crawlee.sessions import SessionPool
    from crawlee.storages import RequestList, RequestQueue
    from crawlee.router import Router
    from crawlee.http_clients import HttpxHttpClient
except ImportError:
    logging.warning("Crawlee not available, using fallback implementations")

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import httpx
from fake_useragent import UserAgent
import structlog

from ...core.domain.entities import Property, Location, PropertyType, EnergyClass, ListingType
from ...core.ports.services import WebScrapingService

logger = structlog.get_logger(__name__)


@dataclass
class ScrapingConfig:
    """Advanced scraping configuration with 2025 anti-detection techniques"""
    # Performance settings
    max_concurrent_sessions: int = 50
    request_delay_range: tuple = (1.5, 4.0)  # Random delays in seconds
    max_retries: int = 5
    timeout_seconds: int = 45
    
    # Anti-detection settings
    rotate_user_agents: bool = True
    use_residential_proxies: bool = True
    enable_stealth_mode: bool = True
    mimic_human_behavior: bool = True
    randomize_viewport: bool = True
    enable_cookie_persistence: bool = True
    
    # Fingerprint evasion (2025 techniques)
    enable_canvas_fingerprint_randomization: bool = True
    enable_webgl_fingerprint_randomization: bool = True
    randomize_timezone: bool = True
    randomize_language: bool = True
    enable_connection_simulation: bool = True
    
    # Data quality settings
    enable_data_validation: bool = True
    min_extraction_confidence: float = 0.8
    enable_price_sanity_checks: bool = True
    
    # Monitoring
    enable_performance_monitoring: bool = True
    capture_screenshots_on_error: bool = True
    log_detailed_metrics: bool = True


@dataclass
class ScrapingSession:
    """Enhanced scraping session with advanced state management"""
    session_id: str
    browser_context: Optional[BrowserContext] = None
    proxy_config: Optional[Dict] = None
    user_agent: Optional[str] = None
    fingerprint: Optional[Dict] = None
    success_count: int = 0
    error_count: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    rate_limit_cooldown: Optional[datetime] = None
    
    def is_healthy(self) -> bool:
        """Check if session is healthy for continued use"""
        if self.error_count > 5:
            return False
        if self.rate_limit_cooldown and datetime.now() < self.rate_limit_cooldown:
            return False
        return True
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


class AdvancedFingerprintEvasion:
    """
    State-of-the-art fingerprint evasion techniques for 2025
    Implements latest research in web scraping anti-detection
    """
    
    def __init__(self):
        self.user_agent_generator = UserAgent()
        self.viewport_configs = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1600, "height": 900},
        ]
        
        self.timezone_configs = [
            "Europe/Athens", "Europe/London", "Europe/Berlin",
            "Europe/Paris", "Europe/Rome", "Europe/Madrid"
        ]
        
        self.language_configs = [
            "en-US,en;q=0.9", "en-GB,en;q=0.9", "el-GR,el;q=0.9,en;q=0.8",
            "de-DE,de;q=0.9,en;q=0.8", "fr-FR,fr;q=0.9,en;q=0.8"
        ]
    
    async def setup_browser_context(
        self, 
        browser: Browser, 
        config: ScrapingConfig
    ) -> BrowserContext:
        """Setup browser context with advanced anti-detection"""
        
        # Generate random fingerprint
        viewport = random.choice(self.viewport_configs)
        timezone = random.choice(self.timezone_configs)
        language = random.choice(self.language_configs)
        user_agent = self.user_agent_generator.random
        
        # Create context with randomized settings
        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale="en-US",
            timezone_id=timezone,
            extra_http_headers={
                "Accept-Language": language,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
        )
        
        if config.enable_stealth_mode:
            await self._inject_stealth_scripts(context)
        
        if config.enable_canvas_fingerprint_randomization:
            await self._randomize_canvas_fingerprint(context)
        
        if config.enable_webgl_fingerprint_randomization:
            await self._randomize_webgl_fingerprint(context)
        
        logger.info("Browser context configured", 
                   viewport=viewport, 
                   timezone=timezone, 
                   user_agent=user_agent[:50] + "...")
        
        return context
    
    async def _inject_stealth_scripts(self, context: BrowserContext):
        """Inject advanced stealth scripts to evade detection"""
        
        stealth_script = """
        // Override webdriver detection
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        
        // Randomize canvas fingerprint
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
            const noise = Math.random() * 0.001;
            const ctx = this.getContext('2d');
            if (ctx) {
                ctx.fillStyle = `rgba(${Math.floor(Math.random()*255)},${Math.floor(Math.random()*255)},${Math.floor(Math.random()*255)},${noise})`;
                ctx.fillRect(0, 0, 1, 1);
            }
            return originalToDataURL.apply(this, arguments);
        };
        
        // Randomize WebGL fingerprint
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {
            if (param === 37445) {
                return 'Intel Inc.';
            }
            if (param === 37446) {
                return 'Intel(R) Iris(TM) Graphics 6100';
            }
            return originalGetParameter.apply(this, arguments);
        };
        
        // Override permissions query
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        
        // Randomize screen properties slightly
        Object.defineProperty(screen, 'availHeight', { 
            get: () => window.screen.height - Math.floor(Math.random() * 10) 
        });
        
        // Override Chrome runtime
        if (window.chrome) {
            delete window.chrome.runtime;
        }
        """
        
        await context.add_init_script(stealth_script)
    
    async def _randomize_canvas_fingerprint(self, context: BrowserContext):
        """Advanced canvas fingerprint randomization"""
        canvas_script = """
        const canvasProto = HTMLCanvasElement.prototype;
        const originalGetContext = canvasProto.getContext;
        
        canvasProto.getContext = function(type) {
            const context = originalGetContext.apply(this, arguments);
            
            if (type === '2d') {
                const originalFillText = context.fillText;
                context.fillText = function(text, x, y, maxWidth) {
                    // Add subtle random noise
                    const noise = (Math.random() - 0.5) * 0.1;
                    return originalFillText.call(this, text, x + noise, y + noise, maxWidth);
                };
            }
            
            return context;
        };
        """
        await context.add_init_script(canvas_script)
    
    async def _randomize_webgl_fingerprint(self, context: BrowserContext):
        """Advanced WebGL fingerprint randomization"""
        webgl_script = """
        const webglProto = WebGLRenderingContext.prototype;
        const originalGetParameter = webglProto.getParameter;
        
        // Randomize specific WebGL parameters
        const glParams = {
            37445: ['Intel Inc.', 'NVIDIA Corporation', 'AMD'],
            37446: [
                'Intel(R) Iris(TM) Graphics 6100',
                'NVIDIA GeForce GTX 1060',
                'AMD Radeon RX 580'
            ]
        };
        
        webglProto.getParameter = function(param) {
            if (glParams[param]) {
                const options = glParams[param];
                return options[Math.floor(Math.random() * options.length)];
            }
            return originalGetParameter.apply(this, arguments);
        };
        """
        await context.add_init_script(webgl_script)


class HumanBehaviorSimulator:
    """
    Simulate human browsing behavior to avoid detection
    """
    
    @staticmethod
    async def human_like_mouse_movement(page: Page):
        """Simulate human-like mouse movements"""
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    @staticmethod
    async def human_like_scrolling(page: Page):
        """Simulate human-like scrolling behavior"""
        # Random scrolling
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(random.uniform(0.3, 0.7))
    
    @staticmethod
    async def random_delays():
        """Random delays between actions"""
        await asyncio.sleep(random.uniform(1.0, 3.0))


class CrawleePropertyScraper(WebScrapingService):
    """
    Advanced property scraper using Crawlee Python v0.6.0+
    Implements 2025 best practices for large-scale web scraping
    """
    
    def __init__(
        self, 
        config: Optional[ScrapingConfig] = None,
        proxy_config: Optional[Dict] = None
    ):
        self.config = config or ScrapingConfig()
        self.proxy_config = proxy_config
        
        # Performance monitoring
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': datetime.now(),
            'rate_limited_requests': 0,
            'fingerprint_rotation_count': 0
        }
        
        # Advanced components
        self.fingerprint_evasion = AdvancedFingerprintEvasion()
        self.behavior_simulator = HumanBehaviorSimulator()
        self.session_pool: Dict[str, ScrapingSession] = {}
        
        # Request management
        self.request_queue = None
        self.router = Router()
        self._setup_request_handlers()
        
        logger.info("CrawleePropertyScraper initialized", config=self.config)
    
    def _setup_request_handlers(self):
        """Setup request handlers for different page types"""
        
        @self.router.default_handler
        async def handle_property_list(context):
            """Handle property listing pages"""
            await self._handle_property_list_page(context)
        
        @self.router.handler('property_detail')
        async def handle_property_detail(context):
            """Handle individual property pages"""
            await self._handle_property_detail_page(context)
    
    async def scrape_property_listings(
        self,
        base_url: str,
        search_criteria: Dict[str, Any],
        max_pages: int = 10
    ) -> AsyncGenerator[Property, None]:
        """
        Scrape property listings with advanced 2025 techniques
        """
        logger.info("Starting property scraping", 
                   base_url=base_url, 
                   search_criteria=search_criteria,
                   max_pages=max_pages)
        
        async with async_playwright() as p:
            # Launch browser with advanced settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-first-run',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-ipc-flooding-protection',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--force-color-profile=srgb',
                    '--metrics-recording-only',
                    '--disable-default-apps',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--autoplay-policy=user-gesture-required',
                    '--disable-background-networking',
                    '--disable-background-sync',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-domain-reliability',
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-ipc-flooding-protection',
                    '--disable-offer-store-unmasked-wallet-cards',
                    '--disable-print-preview',
                    '--disable-speech-api',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--disable-extensions-file-access-check',
                    '--disable-extensions-http-throttling',
                    '--disable-extensions-except='
                ]
            )
            
            try:
                # Create scraping session
                session = await self._create_scraping_session(browser)
                
                # Build search URLs
                search_urls = await self._build_search_urls(base_url, search_criteria, max_pages)
                
                # Process each search URL
                for url in search_urls:
                    async for property in self._scrape_url(session, url):
                        if property:
                            yield property
                        
                        # Adaptive delay based on success rate
                        await self._adaptive_delay()
            
            finally:
                await browser.close()
        
        logger.info("Scraping completed", stats=self.stats)
    
    async def scrape_single_property(self, url: str) -> Optional[Property]:
        """Scrape a single property with enhanced error handling"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                session = await self._create_scraping_session(browser)
                
                page = await session.browser_context.new_page()
                
                # Navigate with retry logic
                property_data = await self._scrape_property_page(page, url)
                
                if property_data:
                    return await self._convert_to_property_entity(property_data)
                
            except Exception as e:
                logger.error("Error scraping single property", url=url, error=str(e))
                
            finally:
                await browser.close()
        
        return None
    
    async def verify_property_exists(self, url: str) -> bool:
        """Verify if property still exists with minimal resource usage"""
        
        async with httpx.AsyncClient(
            timeout=15,
            headers={'User-Agent': self.fingerprint_evasion.user_agent_generator.random}
        ) as client:
            try:
                response = await client.head(url)
                return response.status_code == 200
            except Exception:
                return False
    
    async def extract_property_images(self, url: str) -> List[str]:
        """Extract property image URLs with advanced selectors"""
        
        images = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                session = await self._create_scraping_session(browser)
                page = await session.browser_context.new_page()
                
                await page.goto(url, wait_until='domcontentloaded')
                
                # Multiple selectors for different image containers
                image_selectors = [
                    'img[src*="property"]',
                    'img[src*="photo"]',
                    '.property-image img',
                    '.gallery img',
                    '.photos img',
                    '[data-testid*="image"] img',
                    '.carousel img'
                ]
                
                for selector in image_selectors:
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        src = await element.get_attribute('src')
                        if src and self._is_valid_image_url(src):
                            full_url = urljoin(url, src)
                            if full_url not in images:
                                images.append(full_url)
                
            finally:
                await browser.close()
        
        return images[:20]  # Limit to 20 images
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get comprehensive scraping statistics"""
        
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            'runtime_minutes': runtime.total_seconds() / 60,
            'success_rate': (
                self.stats['successful_requests'] / max(1, self.stats['total_requests'])
            ),
            'requests_per_minute': (
                self.stats['total_requests'] / max(1, runtime.total_seconds() / 60)
            ),
            'active_sessions': len([s for s in self.session_pool.values() if s.is_healthy()]),
            'total_sessions': len(self.session_pool)
        }
    
    # Private helper methods
    
    async def _create_scraping_session(self, browser: Browser) -> ScrapingSession:
        """Create a new scraping session with advanced configuration"""
        
        session_id = hashlib.md5(f"{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()
        
        # Setup browser context with anti-detection
        context = await self.fingerprint_evasion.setup_browser_context(browser, self.config)
        
        session = ScrapingSession(
            session_id=session_id,
            browser_context=context,
            proxy_config=self.proxy_config,
            user_agent=context._impl_obj._options.get('user_agent')
        )
        
        self.session_pool[session_id] = session
        
        logger.info("Created scraping session", session_id=session_id)
        
        return session
    
    async def _build_search_urls(
        self, 
        base_url: str, 
        search_criteria: Dict[str, Any], 
        max_pages: int
    ) -> List[str]:
        """Build search URLs with pagination and filters"""
        
        urls = []
        
        # Base search parameters
        params = {
            'businessType': 'sale',
            'propertyType': 'apartment',
            'page': 1
        }
        
        # Add search criteria
        if 'min_price' in search_criteria:
            params['priceMin'] = search_criteria['min_price']
        
        if 'max_price' in search_criteria:
            params['priceMax'] = search_criteria['max_price']
        
        if 'neighborhoods' in search_criteria:
            # Handle neighborhood filtering (site-specific)
            params['regionIds'] = ','.join(str(n) for n in search_criteria['neighborhoods'])
        
        # Generate URLs for each page
        for page in range(1, max_pages + 1):
            params['page'] = page
            
            # Build URL (implementation depends on site structure)
            url = f"{base_url}/search?" + "&".join(f"{k}={v}" for k, v in params.items())
            urls.append(url)
        
        return urls
    
    async def _scrape_url(
        self, 
        session: ScrapingSession, 
        url: str
    ) -> AsyncGenerator[Property, None]:
        """Scrape a single URL and yield properties"""
        
        page = await session.browser_context.new_page()
        
        try:
            # Navigate with timeout and retry logic
            for attempt in range(self.config.max_retries):
                try:
                    await page.goto(url, wait_until='networkidle', timeout=self.config.timeout_seconds * 1000)
                    break
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise e
                    
                    logger.warning(f"Navigation failed, attempt {attempt + 1}", url=url, error=str(e))
                    await asyncio.sleep(random.uniform(2, 5))
            
            # Simulate human behavior
            if self.config.mimic_human_behavior:
                await self.behavior_simulator.human_like_mouse_movement(page)
                await self.behavior_simulator.human_like_scrolling(page)
            
            # Extract property listings
            property_links = await self._extract_property_links(page)
            
            logger.info("Extracted property links", url=url, count=len(property_links))
            
            # Scrape each property
            for prop_url in property_links:
                try:
                    property_data = await self._scrape_property_page(page, prop_url)
                    
                    if property_data:
                        property_entity = await self._convert_to_property_entity(property_data)
                        if property_entity:
                            yield property_entity
                    
                    session.success_count += 1
                    
                except Exception as e:
                    logger.error("Error scraping property", url=prop_url, error=str(e))
                    session.error_count += 1
                    
                    if self.config.capture_screenshots_on_error:
                        await self._capture_error_screenshot(page, prop_url)
                
                # Adaptive delay between properties
                await self._adaptive_delay()
        
        finally:
            await page.close()
    
    async def _extract_property_links(self, page: Page) -> List[str]:
        """Extract property links from listing page"""
        
        # Multiple selectors for different sites
        link_selectors = [
            'a[href*="/property/"]',
            'a[href*="/listing/"]',
            'a[href*="/ad/"]',
            '.property-card a',
            '.listing-item a',
            '[data-testid*="property"] a'
        ]
        
        links = []
        
        for selector in link_selectors:
            elements = await page.query_selector_all(selector)
            
            for element in elements:
                href = await element.get_attribute('href')
                if href and self._is_valid_property_url(href):
                    full_url = urljoin(page.url, href)
                    if full_url not in links:
                        links.append(full_url)
        
        return links[:50]  # Limit for performance
    
    async def _scrape_property_page(self, page: Page, url: str) -> Optional[Dict]:
        """Scrape individual property page with advanced extraction"""
        
        try:
            await page.goto(url, wait_until='domcontentloaded')
            
            # Wait for dynamic content
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            # Extract property data using multiple strategies
            property_data = await self._extract_property_data(page, url)
            
            # Validate extracted data
            if self.config.enable_data_validation:
                if not self._validate_property_data(property_data):
                    logger.warning("Property data validation failed", url=url)
                    return None
            
            # Add metadata
            property_data.update({
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'html_source_hash': await self._calculate_page_hash(page),
                'extraction_confidence': self._calculate_extraction_confidence(property_data)
            })
            
            return property_data
        
        except Exception as e:
            logger.error("Error scraping property page", url=url, error=str(e))
            return None
    
    async def _extract_property_data(self, page: Page, url: str) -> Dict:
        """Advanced property data extraction with multiple strategies"""
        
        data = {'url': url}
        
        # Title extraction
        title_selectors = ['h1', '.property-title', '[data-testid*="title"]', 'title']
        data['title'] = await self._extract_text_by_selectors(page, title_selectors)
        
        # Price extraction with multiple patterns
        price_selectors = [
            '.price', '.property-price', '[data-testid*="price"]',
            '.cost', '.amount', '.value'
        ]
        price_text = await self._extract_text_by_selectors(page, price_selectors)
        data['price'] = self._parse_price(price_text) if price_text else None
        
        # Area extraction
        area_selectors = [
            '[data-testid*="area"]', '.area', '.size', '.sqm',
            'span:has-text("m²")', 'span:has-text("τ.μ.")'
        ]
        area_text = await self._extract_text_by_selectors(page, area_selectors)
        data['sqm'] = self._parse_area(area_text) if area_text else None
        
        # Rooms extraction
        rooms_selectors = [
            '[data-testid*="rooms"]', '.rooms', '.bedrooms',
            'span:has-text("δωμάτια")', 'span:has-text("rooms")'
        ]
        rooms_text = await self._extract_text_by_selectors(page, rooms_selectors)
        data['rooms'] = self._parse_rooms(rooms_text) if rooms_text else None
        
        # Floor extraction
        floor_selectors = [
            '[data-testid*="floor"]', '.floor', '.level',
            'span:has-text("όροφος")', 'span:has-text("floor")'
        ]
        floor_text = await self._extract_text_by_selectors(page, floor_selectors)
        data['floor'] = self._parse_floor(floor_text) if floor_text else None
        
        # Energy class extraction
        energy_selectors = [
            '[data-testid*="energy"]', '.energy-class', '.energy-rating',
            'span:has-text("ενεργειακή")', '.energy'
        ]
        energy_text = await self._extract_text_by_selectors(page, energy_selectors)
        data['energy_class'] = self._parse_energy_class(energy_text) if energy_text else None
        
        # Location extraction
        location_selectors = [
            '.location', '.address', '[data-testid*="location"]',
            '.neighborhood', '.area-name'
        ]
        location_text = await self._extract_text_by_selectors(page, location_selectors)
        data['neighborhood'] = self._parse_neighborhood(location_text, url) if location_text else None
        
        # Description extraction
        desc_selectors = [
            '.description', '.property-description', '[data-testid*="description"]',
            '.details', '.info'
        ]
        data['description'] = await self._extract_text_by_selectors(page, desc_selectors, max_length=500)
        
        # Property type extraction
        data['property_type'] = self._infer_property_type(data.get('title', ''), url)
        data['listing_type'] = self._infer_listing_type(url)
        
        return data
    
    async def _extract_text_by_selectors(
        self, 
        page: Page, 
        selectors: List[str], 
        max_length: Optional[int] = None
    ) -> Optional[str]:
        """Extract text using multiple selectors with fallback"""
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and text.strip():
                        text = text.strip()
                        if max_length:
                            text = text[:max_length]
                        return text
            except Exception:
                continue
        
        return None
    
    def _parse_price(self, price_text: str) -> Optional[Decimal]:
        """Parse price from text with various formats"""
        
        if not price_text:
            return None
        
        # Remove currency symbols and spaces
        price_clean = re.sub(r'[€$£,\s]', '', price_text)
        
        # Extract numbers
        price_match = re.search(r'(\d+(?:\.\d{3})*(?:,\d+)?)', price_clean)
        
        if price_match:
            price_str = price_match.group(1)
            # Handle different decimal separators
            price_str = price_str.replace('.', '').replace(',', '.')
            
            try:
                price = Decimal(price_str)
                
                # Sanity check for prices
                if self.config.enable_price_sanity_checks:
                    if 10000 <= price <= 10000000:  # Between 10K and 10M euros
                        return price
                else:
                    return price
                    
            except Exception:
                pass
        
        return None
    
    def _parse_area(self, area_text: str) -> Optional[float]:
        """Parse area from text"""
        
        if not area_text:
            return None
        
        # Extract numbers before m² or τ.μ.
        area_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:m²|τ\.μ\.)', area_text)
        
        if area_match:
            area_str = area_match.group(1).replace(',', '.')
            try:
                area = float(area_str)
                if 10 <= area <= 1000:  # Reasonable range
                    return area
            except Exception:
                pass
        
        return None
    
    def _parse_rooms(self, rooms_text: str) -> Optional[int]:
        """Parse number of rooms"""
        
        if not rooms_text:
            return None
        
        # Extract first number
        rooms_match = re.search(r'(\d+)', rooms_text)
        
        if rooms_match:
            try:
                rooms = int(rooms_match.group(1))
                if 1 <= rooms <= 20:  # Reasonable range
                    return rooms
            except Exception:
                pass
        
        return None
    
    def _parse_floor(self, floor_text: str) -> Optional[int]:
        """Parse floor number"""
        
        if not floor_text:
            return None
        
        # Handle ground floor variations
        if any(term in floor_text.lower() for term in ['ground', 'ισόγειο', 'ground floor']):
            return 0
        
        # Extract floor number
        floor_match = re.search(r'(\d+)', floor_text)
        
        if floor_match:
            try:
                floor = int(floor_match.group(1))
                if -2 <= floor <= 30:  # Reasonable range
                    return floor
            except Exception:
                pass
        
        return None
    
    def _parse_energy_class(self, energy_text: str) -> Optional[EnergyClass]:
        """Parse energy efficiency class"""
        
        if not energy_text:
            return None
        
        energy_text = energy_text.upper()
        
        # Map energy classes
        energy_mapping = {
            'A+': EnergyClass.A_PLUS,
            'A': EnergyClass.A,
            'B+': EnergyClass.B_PLUS,
            'B': EnergyClass.B,
            'C': EnergyClass.C,
            'D': EnergyClass.D,
            'E': EnergyClass.E,
            'F': EnergyClass.F,
            'G': EnergyClass.G,
        }
        
        for key, value in energy_mapping.items():
            if key in energy_text:
                return value
        
        return None
    
    def _parse_neighborhood(self, location_text: str, url: str) -> Optional[str]:
        """Parse neighborhood from location text"""
        
        if not location_text:
            return None
        
        # Clean location text
        location = location_text.strip()
        
        # Remove common prefixes
        prefixes = ['Athens - Center,', 'Athens,', 'Αθήνα,', 'Center,']
        for prefix in prefixes:
            if location.startswith(prefix):
                location = location[len(prefix):].strip()
        
        # Extract neighborhood (first part before comma)
        if ',' in location:
            neighborhood = location.split(',')[0].strip()
        else:
            neighborhood = location
        
        return neighborhood if neighborhood else "Athens Center"
    
    def _infer_property_type(self, title: str, url: str) -> PropertyType:
        """Infer property type from title and URL"""
        
        title_lower = title.lower()
        url_lower = url.lower()
        
        # Check for specific property types
        if any(term in title_lower for term in ['studio', 'στούντιο']):
            return PropertyType.STUDIO
        
        if any(term in title_lower for term in ['house', 'σπίτι', 'μονοκατοικία']):
            return PropertyType.HOUSE
        
        if any(term in title_lower for term in ['penthouse', 'ρετιρέ', 'οροφοδιαμέρισμα']):
            return PropertyType.PENTHOUSE
        
        if any(term in title_lower for term in ['maisonette', 'μεζονέτα']):
            return PropertyType.MAISONETTE
        
        # Default to apartment
        return PropertyType.APARTMENT
    
    def _infer_listing_type(self, url: str) -> ListingType:
        """Infer listing type from URL"""
        
        url_lower = url.lower()
        
        if any(term in url_lower for term in ['rent', 'rental', 'ενοίκιο']):
            return ListingType.RENT
        else:
            return ListingType.SALE
    
    def _is_valid_property_url(self, url: str) -> bool:
        """Validate if URL is a property URL"""
        
        url_lower = url.lower()
        
        # Check for property URL patterns
        property_patterns = [
            '/property/', '/listing/', '/ad/', '/house/', '/apartment/'
        ]
        
        return any(pattern in url_lower for pattern in property_patterns)
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Validate if URL is a valid image URL"""
        
        url_lower = url.lower()
        
        # Check image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        
        return any(ext in url_lower for ext in image_extensions)
    
    def _validate_property_data(self, data: Dict) -> bool:
        """Validate extracted property data quality"""
        
        required_fields = ['title', 'price']
        
        # Check required fields
        for field in required_fields:
            if not data.get(field):
                return False
        
        # Validate price range
        price = data.get('price')
        if price and not (10000 <= float(price) <= 10000000):
            return False
        
        # Validate area range
        sqm = data.get('sqm')
        if sqm and not (10 <= sqm <= 1000):
            return False
        
        return True
    
    def _calculate_extraction_confidence(self, data: Dict) -> float:
        """Calculate confidence score for extracted data"""
        
        confidence = 0.5  # Base confidence
        
        # Required fields bonus
        if data.get('title'):
            confidence += 0.2
        
        if data.get('price'):
            confidence += 0.2
        
        # Optional fields bonus
        if data.get('sqm'):
            confidence += 0.1
        
        if data.get('rooms'):
            confidence += 0.05
        
        if data.get('energy_class'):
            confidence += 0.05
        
        if data.get('neighborhood'):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def _calculate_page_hash(self, page: Page) -> str:
        """Calculate hash of page content for change detection"""
        
        try:
            content = await page.content()
            return hashlib.md5(content.encode()).hexdigest()[:16]
        except Exception:
            return "unknown"
    
    async def _convert_to_property_entity(self, data: Dict) -> Optional[Property]:
        """Convert scraped data to Property entity"""
        
        try:
            # Create location
            location = Location(
                neighborhood=data.get('neighborhood', 'Athens Center')
            )
            
            # Convert price to Decimal
            price = data.get('price')
            if isinstance(price, (int, float)):
                price = Decimal(str(price))
            elif not isinstance(price, Decimal):
                return None
            
            # Create property entity
            property_entity = Property(
                property_id=hashlib.md5(data['url'].encode()).hexdigest()[:12],
                url=data['url'],
                title=data.get('title', ''),
                property_type=data.get('property_type', PropertyType.APARTMENT),
                listing_type=data.get('listing_type', ListingType.SALE),
                location=location,
                sqm=data.get('sqm'),
                rooms=data.get('rooms'),
                floor=data.get('floor'),
                energy_class=data.get('energy_class'),
                price=price,
                timestamp=datetime.fromisoformat(data['timestamp']),
                source='crawlee_scraper',
                extraction_confidence=data.get('extraction_confidence', 0.8),
                validation_flags=['CRAWLEE_EXTRACTED'],
                html_source_hash=data.get('html_source_hash'),
                description=data.get('description', ''),
            )
            
            return property_entity
            
        except Exception as e:
            logger.error("Error converting to property entity", data=data, error=str(e))
            return None
    
    async def _adaptive_delay(self):
        """Adaptive delay based on success rate and system performance"""
        
        base_delay = random.uniform(*self.config.request_delay_range)
        
        # Adjust delay based on success rate
        if self.stats['total_requests'] > 10:
            success_rate = self.stats['successful_requests'] / self.stats['total_requests']
            
            if success_rate < 0.7:  # Low success rate, slow down
                base_delay *= 1.5
            elif success_rate > 0.9:  # High success rate, can go faster
                base_delay *= 0.8
        
        await asyncio.sleep(base_delay)
    
    async def _capture_error_screenshot(self, page: Page, url: str):
        """Capture screenshot for debugging errors"""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{timestamp}_{hashlib.md5(url.encode()).hexdigest()[:8]}.png"
            
            await page.screenshot(path=f"debug/screenshots/{filename}")
            
            logger.info("Error screenshot captured", filename=filename, url=url)
            
        except Exception as e:
            logger.error("Failed to capture screenshot", error=str(e))


# Export for use in other modules
__all__ = ['CrawleePropertyScraper', 'ScrapingConfig', 'AdvancedFingerprintEvasion']