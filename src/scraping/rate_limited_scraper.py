"""
Rate-Limited Scraping System
Story 1.6: Respectful web scraping with realistic throughput
Target: 500-2,000 properties/hour (not 23M/minute!)
"""

import time
import random
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import urllib.robotparser
from queue import Queue, PriorityQueue
import logging
import json
from pathlib import Path
import sqlite3


@dataclass
class ScrapingConfig:
    """Configuration for rate-limited scraping"""
    
    # Rate limits (requests per minute)
    rate_limits: Dict[str, int] = field(default_factory=lambda: {
        'spitogatos.gr': 30,    # 30 req/min = 1800/hour
        'xe.gr': 50,            # 50 req/min = 3000/hour  
        'tospitimou.gr': 20,    # 20 req/min = 1200/hour
        'default': 10           # Conservative default
    })
    
    # Request settings
    timeout_seconds: int = 10
    max_retries: int = 3
    retry_delay_base: float = 1.0  # Exponential backoff base
    
    # User agent rotation
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ])
    
    # Politeness settings
    respect_robots_txt: bool = True
    min_delay_between_requests: float = 1.0  # Minimum 1 second between requests
    max_concurrent_domains: int = 3
    
    # Storage settings
    db_path: str = "scraping_data.db"
    output_directory: str = "scraped_data"


@dataclass
class ScrapeRequest:
    """Individual scrape request"""
    url: str
    priority: int
    domain: str
    timestamp: float
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority < other.priority


@dataclass
class ScrapeResult:
    """Result of a scrape request"""
    url: str
    status_code: int
    content: Optional[str]
    response_time: float
    timestamp: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Rate limiter for specific domains"""
    
    def __init__(self, requests_per_minute: int, min_delay: float = 1.0):
        self.requests_per_minute = requests_per_minute
        self.min_delay = min_delay
        self.request_times: List[float] = []
        self.lock = threading.Lock()
        self.last_request = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        with self.lock:
            current_time = time.time()
            
            # Enforce minimum delay
            if current_time - self.last_request < self.min_delay:
                sleep_time = self.min_delay - (current_time - self.last_request)
                time.sleep(sleep_time)
                current_time = time.time()
            
            # Remove requests older than 1 minute
            cutoff_time = current_time - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]
            
            # Check if we're at the rate limit
            if len(self.request_times) >= self.requests_per_minute:
                # Wait until the oldest request is more than 1 minute old
                sleep_time = self.request_times[0] + 60 - current_time + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    current_time = time.time()
            
            # Record this request
            self.request_times.append(current_time)
            self.last_request = current_time


class RobotsChecker:
    """Check robots.txt compliance"""
    
    def __init__(self):
        self.robot_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.cache_lock = threading.Lock()
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """Check if URL can be fetched according to robots.txt"""
        try:
            domain = urlparse(url).netloc
            
            with self.cache_lock:
                if domain not in self.robot_parsers:
                    robots_url = f"https://{domain}/robots.txt"
                    rp = urllib.robotparser.RobotFileParser()
                    rp.set_url(robots_url)
                    try:
                        rp.read()
                        self.robot_parsers[domain] = rp
                    except:
                        # If robots.txt can't be read, assume allowed
                        return True
                
                return self.robot_parsers[domain].can_fetch(user_agent, url)
        
        except:
            # If any error occurs, be conservative and allow
            return True


class RateLimitedScraper:
    """
    Production-ready rate-limited scraper
    Realistic throughput: 500-2,000 properties/hour
    """
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Rate limiters for each domain
        self.rate_limiters = {}
        for domain, rate in config.rate_limits.items():
            self.rate_limiters[domain] = RateLimiter(
                rate, 
                config.min_delay_between_requests
            )
        
        # Request queue and workers
        self.request_queue = PriorityQueue()
        self.result_queue = Queue()
        self.workers = []
        self.is_running = False
        
        # Session for connection reuse
        self.session = requests.Session()
        
        # Robots.txt checker
        self.robots_checker = RobotsChecker()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'robots_blocked': 0,
            'rate_limited': 0,
            'start_time': None
        }
        
        # Database setup
        self._init_database()
        
        # Create output directory
        Path(config.output_directory).mkdir(exist_ok=True)
        
        self.logger.info("Rate-limited scraper initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger('rate_limited_scraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize database for storing scrape results"""
        with sqlite3.connect(self.config.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scrape_results (
                    url TEXT PRIMARY KEY,
                    status_code INTEGER,
                    response_time REAL,
                    timestamp TEXT,
                    content_length INTEGER,
                    error TEXT,
                    domain TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scraping_stats (
                    domain TEXT,
                    date TEXT,
                    requests_made INTEGER,
                    successful_requests INTEGER,
                    failed_requests INTEGER,
                    avg_response_time REAL,
                    PRIMARY KEY (domain, date)
                )
            """)
    
    def start(self, num_workers: int = 3):
        """Start the scraping workers"""
        if self.is_running:
            self.logger.warning("Scraper is already running")
            return
        
        self.is_running = True
        self.stats['start_time'] = time.time()
        
        # Start worker threads
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Started {num_workers} scraping workers")
    
    def stop(self):
        """Stop the scraper"""
        self.is_running = False
        self.logger.info("Scraper stopped")
    
    def add_url(self, url: str, priority: int = 5, callback: Optional[Callable] = None, 
                metadata: Dict[str, Any] = None):
        """
        Add URL to scraping queue
        
        Args:
            url: URL to scrape
            priority: Priority (1=highest, 10=lowest)
            callback: Optional callback function for results
            metadata: Additional metadata
        """
        domain = urlparse(url).netloc
        
        request = ScrapeRequest(
            url=url,
            priority=priority,
            domain=domain,
            timestamp=time.time(),
            callback=callback,
            metadata=metadata or {}
        )
        
        self.request_queue.put(request)
        self.logger.debug(f"Added URL to queue: {url}")
    
    def add_urls_batch(self, urls: List[str], priority: int = 5):
        """Add multiple URLs to queue"""
        for url in urls:
            self.add_url(url, priority)
        
        self.logger.info(f"Added {len(urls)} URLs to queue")
    
    def _worker_loop(self, worker_id: int):
        """Main worker loop"""
        self.logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get next request (blocks until available)
                request = self.request_queue.get(timeout=1)
                
                # Process the request
                result = self._process_request(request)
                
                # Store result
                self._store_result(result)
                
                # Call callback if provided
                if request.callback:
                    try:
                        request.callback(result)
                    except Exception as e:
                        self.logger.error(f"Callback error for {request.url}: {e}")
                
                # Mark task done
                self.request_queue.task_done()
                
            except:
                # Timeout or other error - continue
                continue
        
        self.logger.info(f"Worker {worker_id} stopped")
    
    def _process_request(self, request: ScrapeRequest) -> ScrapeResult:
        """Process a single scrape request"""
        start_time = time.time()
        
        try:
            # Check robots.txt if enabled
            if self.config.respect_robots_txt:
                user_agent = random.choice(self.config.user_agents)
                if not self.robots_checker.can_fetch(request.url, user_agent):
                    self.stats['robots_blocked'] += 1
                    return ScrapeResult(
                        url=request.url,
                        status_code=403,
                        content=None,
                        response_time=time.time() - start_time,
                        timestamp=datetime.now(),
                        error="Blocked by robots.txt"
                    )
            
            # Apply rate limiting
            rate_limiter = self._get_rate_limiter(request.domain)
            rate_limiter.wait_if_needed()
            
            # Make request with retries
            result = self._make_request_with_retries(request, start_time)
            
            # Update statistics
            self.stats['total_requests'] += 1
            if result.error is None:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {request.url}: {e}")
            return ScrapeResult(
                url=request.url,
                status_code=0,
                content=None,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def _make_request_with_retries(self, request: ScrapeRequest, start_time: float) -> ScrapeResult:
        """Make HTTP request with retry logic"""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Prepare headers
                headers = {
                    'User-Agent': random.choice(self.config.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                # Make request
                response = self.session.get(
                    request.url,
                    headers=headers,
                    timeout=self.config.timeout_seconds,
                    allow_redirects=True
                )
                
                # Return successful result
                return ScrapeResult(
                    url=request.url,
                    status_code=response.status_code,
                    content=response.text if response.status_code == 200 else None,
                    response_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    error=None if response.status_code == 200 else f"HTTP {response.status_code}",
                    metadata={'final_url': response.url, 'headers': dict(response.headers)}
                )
                
            except requests.RequestException as e:
                last_error = str(e)
                
                if attempt < self.config.max_retries:
                    # Exponential backoff
                    delay = self.config.retry_delay_base * (2 ** attempt)
                    delay += random.uniform(0, 1)  # Add jitter
                    
                    self.logger.warning(
                        f"Request failed for {request.url} (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"All retry attempts failed for {request.url}: {e}")
        
        # All retries failed
        return ScrapeResult(
            url=request.url,
            status_code=0,
            content=None,
            response_time=time.time() - start_time,
            timestamp=datetime.now(),
            error=last_error
        )
    
    def _get_rate_limiter(self, domain: str) -> RateLimiter:
        """Get rate limiter for domain"""
        if domain in self.rate_limiters:
            return self.rate_limiters[domain]
        else:
            # Use default rate limit
            default_rate = self.config.rate_limits.get('default', 10)
            self.rate_limiters[domain] = RateLimiter(default_rate, self.config.min_delay_between_requests)
            return self.rate_limiters[domain]
    
    def _store_result(self, result: ScrapeResult):
        """Store scrape result in database"""
        try:
            with sqlite3.connect(self.config.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO scrape_results
                    (url, status_code, response_time, timestamp, content_length, 
                     error, domain, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.url,
                    result.status_code,
                    result.response_time,
                    result.timestamp.isoformat(),
                    len(result.content) if result.content else 0,
                    result.error,
                    urlparse(result.url).netloc,
                    json.dumps(result.metadata)
                ))
        except Exception as e:
            self.logger.error(f"Error storing result for {result.url}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        return {
            'running': self.is_running,
            'uptime_seconds': elapsed,
            'queue_size': self.request_queue.qsize(),
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': (self.stats['successful_requests'] / max(1, self.stats['total_requests'])),
            'requests_per_hour': (self.stats['total_requests'] / elapsed * 3600) if elapsed > 0 else 0,
            'robots_blocked': self.stats['robots_blocked'],
            'rate_limited': self.stats['rate_limited']
        }
    
    def get_domain_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get per-domain statistics"""
        stats = {}
        
        with sqlite3.connect(self.config.db_path) as conn:
            rows = conn.execute("""
                SELECT domain, 
                       COUNT(*) as total_requests,
                       SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful,
                       AVG(response_time) as avg_response_time,
                       MIN(timestamp) as first_request,
                       MAX(timestamp) as last_request
                FROM scrape_results
                GROUP BY domain
            """).fetchall()
            
            for row in rows:
                domain = row[0]
                rate_limit = self.config.rate_limits.get(domain, self.config.rate_limits['default'])
                
                stats[domain] = {
                    'total_requests': row[1],
                    'successful_requests': row[2],
                    'success_rate': row[2] / row[1] if row[1] > 0 else 0,
                    'avg_response_time': row[3] or 0,
                    'first_request': row[4],
                    'last_request': row[5],
                    'configured_rate_limit': rate_limit,
                    'theoretical_max_per_hour': rate_limit * 60
                }
        
        return stats


def create_property_scraper() -> RateLimitedScraper:
    """Create scraper configured for property websites"""
    config = ScrapingConfig(
        rate_limits={
            'spitogatos.gr': 30,     # Conservative: ~1,800/hour max
            'xe.gr': 50,             # Conservative: ~3,000/hour max
            'tospitimou.gr': 20,     # Conservative: ~1,200/hour max
            'plot.gr': 25,           # Conservative: ~1,500/hour max
            'default': 10            # Very conservative default
        },
        min_delay_between_requests=2.0,  # 2 second minimum delay
        respect_robots_txt=True,
        max_retries=3,
        timeout_seconds=15
    )
    
    return RateLimitedScraper(config)