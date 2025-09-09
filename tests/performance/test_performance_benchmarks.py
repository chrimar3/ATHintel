"""
Performance Testing Suite for ATHintel Platform
Tests load handling, response times, memory usage, and scalability
"""

import pytest
import asyncio
import time
import psutil
import gc
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime
import numpy as np
from dataclasses import dataclass

from src.core.services.investment_analysis import InvestmentAnalysisService
from src.core.analytics.market_segmentation import MarketSegmentationAnalytics
from src.core.scrapers.crawlee_scraper import CrawleePropertyScraper


@dataclass
class PerformanceMetrics:
    """Performance measurement results"""
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    throughput: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float


class PerformanceTester:
    """Utility class for performance testing"""
    
    def __init__(self):
        self.metrics = []
        self.errors = []
        self.start_memory = None
        self.start_cpu_times = None

    def start_monitoring(self):
        """Start system resource monitoring"""
        process = psutil.Process()
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu_times = process.cpu_times()
        gc.collect()  # Clean start

    def record_metric(self, response_time: float, error: bool = False):
        """Record performance metric"""
        self.metrics.append(response_time)
        if error:
            self.errors.append(response_time)

    def get_performance_summary(self) -> PerformanceMetrics:
        """Calculate performance summary"""
        if not self.metrics:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 100.0, 0, 0)
        
        sorted_metrics = sorted(self.metrics)
        
        # Calculate percentiles
        avg_time = sum(self.metrics) / len(self.metrics)
        p95_time = sorted_metrics[int(0.95 * len(sorted_metrics))]
        p99_time = sorted_metrics[int(0.99 * len(sorted_metrics))]
        max_time = max(self.metrics)
        min_time = min(self.metrics)
        
        # Calculate throughput (operations per second)
        total_time = sum(self.metrics)
        throughput = len(self.metrics) / total_time if total_time > 0 else 0
        
        # Calculate error rate
        error_rate = (len(self.errors) / len(self.metrics)) * 100
        
        # Get current resource usage
        process = psutil.Process()
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = current_memory - (self.start_memory or 0)
        
        cpu_usage = process.cpu_percent()
        
        return PerformanceMetrics(
            avg_response_time=avg_time,
            p95_response_time=p95_time,
            p99_response_time=p99_time,
            max_response_time=max_time,
            min_response_time=min_time,
            throughput=throughput,
            error_rate=error_rate,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )


class TestInvestmentAnalysisPerformance:
    """Performance tests for investment analysis service"""

    @pytest.fixture
    async def investment_service(self, mock_property_repository, mock_market_data_service):
        """Investment analysis service with mocked dependencies"""
        return InvestmentAnalysisService(
            property_repo=mock_property_repository,
            market_service=mock_market_data_service
        )

    @pytest.fixture
    def performance_test_properties(self, property_data_generator):
        """Generate properties for performance testing"""
        return property_data_generator(count=100)

    async def test_single_property_analysis_performance(self, investment_service, sample_property):
        """Test single property analysis performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Warm up
        for _ in range(5):
            await investment_service.analyze_investment_potential(sample_property)
        
        # Actual test
        test_iterations = 50
        
        for i in range(test_iterations):
            start_time = time.perf_counter()
            
            try:
                await investment_service.analyze_investment_potential(sample_property)
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed)
            except Exception:
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed, error=True)
        
        metrics = tester.get_performance_summary()
        
        # Performance assertions
        assert metrics.avg_response_time < 0.5, f"Average response time too high: {metrics.avg_response_time:.3f}s"
        assert metrics.p95_response_time < 1.0, f"95th percentile response time too high: {metrics.p95_response_time:.3f}s"
        assert metrics.error_rate < 1.0, f"Error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.memory_usage_mb < 100, f"Memory usage too high: {metrics.memory_usage_mb:.1f}MB"

    async def test_batch_analysis_performance(self, investment_service, performance_test_properties):
        """Test batch property analysis performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        batch_sizes = [10, 25, 50, 100]
        results = {}
        
        for batch_size in batch_sizes:
            batch_properties = performance_test_properties[:batch_size]
            
            start_time = time.perf_counter()
            
            try:
                # Analyze batch
                analyses = []
                for prop in batch_properties:
                    analysis = await investment_service.analyze_investment_potential(prop)
                    analyses.append(analysis)
                
                elapsed = time.perf_counter() - start_time
                throughput = batch_size / elapsed
                
                results[batch_size] = {
                    'elapsed': elapsed,
                    'throughput': throughput,
                    'avg_per_property': elapsed / batch_size
                }
                
            except Exception as e:
                results[batch_size] = {'error': str(e)}

        # Verify throughput scales reasonably
        for batch_size, result in results.items():
            if 'error' not in result:
                assert result['throughput'] > 1.0, f"Low throughput for batch size {batch_size}: {result['throughput']:.2f} props/sec"
                assert result['avg_per_property'] < 2.0, f"High per-property time for batch {batch_size}: {result['avg_per_property']:.3f}s"

    async def test_concurrent_analysis_performance(self, investment_service, performance_test_properties):
        """Test concurrent property analysis performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        concurrent_levels = [5, 10, 20]
        
        for concurrency in concurrent_levels:
            properties_subset = performance_test_properties[:concurrency]
            
            start_time = time.perf_counter()
            
            # Run concurrent analyses
            tasks = [
                investment_service.analyze_investment_potential(prop)
                for prop in properties_subset
            ]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                elapsed = time.perf_counter() - start_time
                
                # Count errors
                errors = sum(1 for r in results if isinstance(r, Exception))
                success_rate = ((len(results) - errors) / len(results)) * 100
                
                # Performance assertions
                assert success_rate > 95, f"Low success rate with {concurrency} concurrent requests: {success_rate:.1f}%"
                
                throughput = len(properties_subset) / elapsed
                assert throughput > concurrency * 0.3, f"Low concurrent throughput: {throughput:.2f} props/sec with {concurrency} concurrent"
                
            except Exception as e:
                pytest.fail(f"Concurrent analysis failed at {concurrency} concurrent requests: {e}")

    @pytest.mark.slow
    async def test_sustained_load_performance(self, investment_service, performance_test_properties):
        """Test performance under sustained load"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Run for extended period
        test_duration = 60  # 1 minute
        start_time = time.time()
        analyses_completed = 0
        
        while time.time() - start_time < test_duration:
            prop = performance_test_properties[analyses_completed % len(performance_test_properties)]
            
            analysis_start = time.perf_counter()
            try:
                await investment_service.analyze_investment_potential(prop)
                elapsed = time.perf_counter() - analysis_start
                tester.record_metric(elapsed)
                analyses_completed += 1
            except Exception:
                elapsed = time.perf_counter() - analysis_start
                tester.record_metric(elapsed, error=True)
        
        metrics = tester.get_performance_summary()
        
        # Sustained load assertions
        assert analyses_completed > 50, f"Too few analyses completed: {analyses_completed}"
        assert metrics.error_rate < 5.0, f"High error rate under sustained load: {metrics.error_rate:.1f}%"
        assert metrics.avg_response_time < 1.0, f"Response time degraded under load: {metrics.avg_response_time:.3f}s"
        
        # Check for memory leaks
        assert metrics.memory_usage_mb < 200, f"Potential memory leak detected: {metrics.memory_usage_mb:.1f}MB"

    async def test_memory_efficiency(self, investment_service, performance_test_properties):
        """Test memory efficiency of investment analysis"""
        import tracemalloc
        
        # Start memory tracing
        tracemalloc.start()
        gc.collect()
        
        # Baseline memory
        baseline = tracemalloc.take_snapshot()
        
        # Run multiple analyses
        for i in range(50):
            prop = performance_test_properties[i % len(performance_test_properties)]
            await investment_service.analyze_investment_potential(prop)
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        # Final memory snapshot
        final = tracemalloc.take_snapshot()
        
        # Calculate memory growth
        top_stats = final.compare_to(baseline, 'lineno')
        total_memory_growth = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        
        # Memory growth should be reasonable (< 50MB)
        memory_growth_mb = total_memory_growth / 1024 / 1024
        assert memory_growth_mb < 50, f"Excessive memory growth: {memory_growth_mb:.1f}MB"
        
        tracemalloc.stop()

    async def test_cpu_efficiency(self, investment_service, performance_test_properties):
        """Test CPU efficiency of investment analysis"""
        # Monitor CPU usage during intensive processing
        process = psutil.Process()
        cpu_samples = []
        
        async def cpu_monitor():
            """Monitor CPU usage in background"""
            for _ in range(30):  # Monitor for 30 seconds
                cpu_samples.append(process.cpu_percent())
                await asyncio.sleep(1.0)
        
        # Start CPU monitoring
        monitor_task = asyncio.create_task(cpu_monitor())
        
        # Run intensive analysis workload
        start_time = time.perf_counter()
        analyses_completed = 0
        
        try:
            while time.perf_counter() - start_time < 25:  # Run for 25 seconds
                prop = performance_test_properties[analyses_completed % len(performance_test_properties)]
                await investment_service.analyze_investment_potential(prop)
                analyses_completed += 1
        finally:
            monitor_task.cancel()
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # CPU usage should be reasonable
            assert max_cpu < 90, f"CPU usage too high: {max_cpu:.1f}%"
            assert avg_cpu < 70, f"Average CPU usage too high: {avg_cpu:.1f}%"
            
            # Should maintain reasonable throughput
            throughput = analyses_completed / 25
            assert throughput > 1.0, f"Low throughput under CPU monitoring: {throughput:.2f} analyses/sec"


class TestScrapingPerformance:
    """Performance tests for web scraping operations"""

    @pytest.fixture
    async def scraper_service(self, mock_browser_context):
        """Scraper service with mocked browser"""
        scraper = CrawleePropertyScraper()
        scraper.browser_context = mock_browser_context
        return scraper

    async def test_single_page_scraping_performance(self, scraper_service, mock_playwright_page):
        """Test single page scraping performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Mock page content
        mock_playwright_page.content.return_value = """
        <div class="property-listing">
            <h2>Test Property</h2>
            <div class="price">€250,000</div>
            <div class="area">75 m²</div>
        </div>
        """
        
        test_urls = [f"https://example.com/property/{i}" for i in range(20)]
        
        for url in test_urls:
            start_time = time.perf_counter()
            
            try:
                await scraper_service.scrape_single_property(url)
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed)
            except Exception:
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed, error=True)
        
        metrics = tester.get_performance_summary()
        
        # Scraping performance assertions
        assert metrics.avg_response_time < 2.0, f"Average scraping time too high: {metrics.avg_response_time:.3f}s"
        assert metrics.error_rate < 10.0, f"High scraping error rate: {metrics.error_rate:.1f}%"
        assert metrics.throughput > 0.5, f"Low scraping throughput: {metrics.throughput:.2f} pages/sec"

    async def test_batch_scraping_performance(self, scraper_service):
        """Test batch scraping performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Test different batch sizes
        batch_sizes = [10, 25, 50]
        
        for batch_size in batch_sizes:
            test_urls = [f"https://example.com/property/{i}" for i in range(batch_size)]
            
            start_time = time.perf_counter()
            
            try:
                results = await scraper_service.scrape_multiple_properties(test_urls)
                elapsed = time.perf_counter() - start_time
                
                success_count = len([r for r in results if r is not None])
                success_rate = (success_count / batch_size) * 100
                throughput = batch_size / elapsed
                
                # Batch performance assertions
                assert success_rate > 70, f"Low success rate for batch size {batch_size}: {success_rate:.1f}%"
                assert throughput > 0.3, f"Low batch throughput for size {batch_size}: {throughput:.2f} pages/sec"
                
            except Exception as e:
                pytest.fail(f"Batch scraping failed for size {batch_size}: {e}")

    @pytest.mark.slow
    async def test_scraping_rate_limiting(self, scraper_service):
        """Test scraping with rate limiting compliance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Configure rate limiting (1 request per second)
        scraper_service.rate_limit_delay = 1.0
        
        urls = [f"https://example.com/property/{i}" for i in range(10)]
        
        start_time = time.perf_counter()
        
        for url in urls:
            await scraper_service.scrape_single_property(url)
        
        total_time = time.perf_counter() - start_time
        
        # Should respect rate limiting (approximately 1 request per second)
        expected_min_time = len(urls) * scraper_service.rate_limit_delay * 0.8  # Allow 20% variance
        assert total_time >= expected_min_time, f"Rate limiting not respected: {total_time:.2f}s < {expected_min_time:.2f}s"

    async def test_scraping_memory_efficiency(self, scraper_service):
        """Test memory efficiency during scraping operations"""
        # Monitor memory during scraping
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        urls = [f"https://example.com/property/{i}" for i in range(100)]
        
        for i, url in enumerate(urls):
            await scraper_service.scrape_single_property(url)
            
            # Check memory every 10 requests
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be controlled
                assert memory_growth < 200, f"Excessive memory growth during scraping: {memory_growth:.1f}MB"
                
                # Force garbage collection
                gc.collect()


class TestDatabasePerformance:
    """Performance tests for database operations"""

    @pytest.fixture
    async def populated_db_repository(self, mock_property_repository, property_data_generator):
        """Database repository with test data"""
        # Generate large dataset
        properties = property_data_generator(count=1000)
        
        # Configure mock to simulate database operations
        mock_property_repository.find_all.return_value = properties
        mock_property_repository.count_total.return_value = len(properties)
        
        async def mock_find_by_criteria(**criteria):
            # Simulate filtering
            filtered = properties
            if 'neighborhood' in criteria:
                filtered = [p for p in filtered if p.location.neighborhood == criteria['neighborhood']]
            if 'min_price' in criteria:
                filtered = [p for p in filtered if p.price >= criteria['min_price']]
            return filtered[:50]  # Limit results
        
        mock_property_repository.find_by_criteria = mock_find_by_criteria
        
        return mock_property_repository

    async def test_property_query_performance(self, populated_db_repository):
        """Test property query performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Test various query patterns
        queries = [
            {'neighborhood': 'Kolonaki'},
            {'min_price': Decimal('200000')},
            {'neighborhood': 'Glyfada', 'min_price': Decimal('300000')},
            {},  # All properties
        ]
        
        for query in queries:
            start_time = time.perf_counter()
            
            try:
                results = await populated_db_repository.find_by_criteria(**query)
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed)
                
                # Verify results are reasonable
                assert len(results) >= 0, "Query should return results"
                
            except Exception:
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed, error=True)
        
        metrics = tester.get_performance_summary()
        
        # Database query performance assertions
        assert metrics.avg_response_time < 0.1, f"Average query time too high: {metrics.avg_response_time:.3f}s"
        assert metrics.error_rate < 1.0, f"High database error rate: {metrics.error_rate:.1f}%"

    async def test_bulk_insert_performance(self, populated_db_repository, property_data_generator):
        """Test bulk insert performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Test different batch sizes
        batch_sizes = [10, 50, 100, 500]
        
        for batch_size in batch_sizes:
            new_properties = property_data_generator(count=batch_size)
            
            start_time = time.perf_counter()
            
            try:
                await populated_db_repository.bulk_save(new_properties)
                elapsed = time.perf_counter() - start_time
                
                throughput = batch_size / elapsed
                
                # Bulk insert performance assertions
                assert throughput > 10, f"Low bulk insert throughput for batch {batch_size}: {throughput:.2f} records/sec"
                assert elapsed < batch_size * 0.01, f"Bulk insert too slow for batch {batch_size}: {elapsed:.3f}s"
                
            except Exception as e:
                pytest.fail(f"Bulk insert failed for batch size {batch_size}: {e}")

    async def test_concurrent_database_access(self, populated_db_repository):
        """Test concurrent database access performance"""
        concurrent_operations = 20
        
        async def db_operation():
            """Simulate database operation"""
            await populated_db_repository.find_by_criteria(neighborhood='Kolonaki')
            await asyncio.sleep(0.01)  # Simulate processing
            return True
        
        start_time = time.perf_counter()
        
        # Run concurrent operations
        tasks = [db_operation() for _ in range(concurrent_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.perf_counter() - start_time
        
        # Check results
        success_count = sum(1 for r in results if r is True)
        success_rate = (success_count / concurrent_operations) * 100
        
        # Concurrent access assertions
        assert success_rate > 95, f"Low success rate for concurrent access: {success_rate:.1f}%"
        assert elapsed < 2.0, f"Concurrent operations took too long: {elapsed:.3f}s"


class TestSystemIntegrationPerformance:
    """Performance tests for full system integration"""

    @pytest.mark.slow
    async def test_end_to_end_pipeline_performance(self, investment_analysis_service, sample_properties):
        """Test end-to-end pipeline performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        pipeline_steps = [
            'data_validation',
            'energy_assessment',
            'investment_analysis',
            'market_comparison',
            'report_generation'
        ]
        
        step_times = {step: [] for step in pipeline_steps}
        
        for prop in sample_properties[:10]:
            pipeline_start = time.perf_counter()
            
            # Simulate full pipeline
            for step in pipeline_steps:
                step_start = time.perf_counter()
                
                if step == 'investment_analysis':
                    await investment_analysis_service.analyze_investment_potential(prop)
                else:
                    await asyncio.sleep(0.01)  # Simulate other operations
                
                step_elapsed = time.perf_counter() - step_start
                step_times[step].append(step_elapsed)
            
            pipeline_elapsed = time.perf_counter() - pipeline_start
            tester.record_metric(pipeline_elapsed)
        
        metrics = tester.get_performance_summary()
        
        # End-to-end performance assertions
        assert metrics.avg_response_time < 3.0, f"Pipeline too slow: {metrics.avg_response_time:.3f}s average"
        assert metrics.error_rate < 5.0, f"High pipeline error rate: {metrics.error_rate:.1f}%"
        
        # Check individual step performance
        for step, times in step_times.items():
            avg_time = sum(times) / len(times)
            assert avg_time < 1.0, f"Step {step} too slow: {avg_time:.3f}s average"

    async def test_system_resource_utilization(self, investment_analysis_service, property_data_generator):
        """Test overall system resource utilization"""
        properties = property_data_generator(count=50)
        
        # Monitor system resources
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        resource_samples = []
        
        # Background resource monitoring
        async def monitor_resources():
            for _ in range(30):
                cpu = process.cpu_percent()
                memory = process.memory_info().rss / 1024 / 1024
                resource_samples.append((cpu, memory))
                await asyncio.sleep(1.0)
        
        monitor_task = asyncio.create_task(monitor_resources())
        
        try:
            # Run intensive workload
            start_time = time.perf_counter()
            
            # Process multiple properties concurrently
            batch_size = 5
            for i in range(0, len(properties), batch_size):
                batch = properties[i:i + batch_size]
                tasks = [
                    investment_analysis_service.analyze_investment_potential(prop)
                    for prop in batch
                ]
                await asyncio.gather(*tasks)
            
            elapsed = time.perf_counter() - start_time
            
        finally:
            monitor_task.cancel()
        
        # Analyze resource usage
        if resource_samples:
            cpu_values = [sample[0] for sample in resource_samples]
            memory_values = [sample[1] for sample in resource_samples]
            
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_memory = max(memory_values)
            memory_growth = max_memory - initial_memory
            
            # Resource utilization assertions
            assert avg_cpu < 80, f"High average CPU usage: {avg_cpu:.1f}%"
            assert memory_growth < 300, f"Excessive memory growth: {memory_growth:.1f}MB"
            
            # Performance should be maintained
            throughput = len(properties) / elapsed
            assert throughput > 2.0, f"Low system throughput: {throughput:.2f} properties/sec"


# Performance benchmark utilities
class PerformanceBenchmark:
    """Utility for running performance benchmarks"""
    
    @staticmethod
    async def benchmark_function(func: Callable, iterations: int = 100, warmup: int = 5) -> PerformanceMetrics:
        """Benchmark a function's performance"""
        tester = PerformanceTester()
        tester.start_monitoring()
        
        # Warmup runs
        for _ in range(warmup):
            try:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            except Exception:
                pass
        
        # Actual benchmark
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed)
            except Exception:
                elapsed = time.perf_counter() - start_time
                tester.record_metric(elapsed, error=True)
        
        return tester.get_performance_summary()
    
    @staticmethod
    def compare_performance(baseline: PerformanceMetrics, current: PerformanceMetrics, tolerance: float = 0.1) -> Dict[str, Any]:
        """Compare performance metrics with baseline"""
        comparison = {}
        
        # Response time comparison
        time_change = (current.avg_response_time - baseline.avg_response_time) / baseline.avg_response_time
        comparison['response_time_change'] = time_change
        comparison['response_time_degraded'] = time_change > tolerance
        
        # Throughput comparison
        throughput_change = (current.throughput - baseline.throughput) / baseline.throughput if baseline.throughput > 0 else 0
        comparison['throughput_change'] = throughput_change
        comparison['throughput_improved'] = throughput_change > tolerance
        
        # Error rate comparison
        comparison['error_rate_change'] = current.error_rate - baseline.error_rate
        comparison['error_rate_increased'] = comparison['error_rate_change'] > 1.0
        
        # Memory usage comparison
        memory_change = current.memory_usage_mb - baseline.memory_usage_mb
        comparison['memory_change_mb'] = memory_change
        comparison['memory_increased'] = memory_change > 50  # 50MB threshold
        
        return comparison


# Performance regression tests
@pytest.mark.performance
class TestPerformanceRegression:
    """Tests to detect performance regression"""
    
    # Store baseline metrics (in real implementation, would load from file)
    BASELINE_METRICS = {
        'investment_analysis': PerformanceMetrics(
            avg_response_time=0.3,
            p95_response_time=0.5,
            p99_response_time=0.8,
            max_response_time=1.0,
            min_response_time=0.1,
            throughput=3.0,
            error_rate=1.0,
            memory_usage_mb=50.0,
            cpu_usage_percent=40.0
        )
    }
    
    async def test_investment_analysis_regression(self, investment_analysis_service, sample_property):
        """Test for investment analysis performance regression"""
        
        async def analysis_operation():
            await investment_analysis_service.analyze_investment_potential(sample_property)
        
        current_metrics = await PerformanceBenchmark.benchmark_function(
            analysis_operation, iterations=50
        )
        
        baseline = self.BASELINE_METRICS['investment_analysis']
        comparison = PerformanceBenchmark.compare_performance(baseline, current_metrics)
        
        # Regression assertions
        assert not comparison['response_time_degraded'], f"Response time regressed by {comparison['response_time_change']:.1%}"
        assert not comparison['error_rate_increased'], f"Error rate increased by {comparison['error_rate_change']:.1f}%"
        
        # Allow some memory growth but not excessive
        assert not comparison['memory_increased'], f"Memory usage increased by {comparison['memory_change_mb']:.1f}MB"


# Load testing utilities  
@pytest.mark.load
class TestLoadCapacity:
    """Load testing to determine system capacity"""
    
    async def test_find_breaking_point(self, investment_analysis_service, property_data_generator):
        """Find the breaking point of the system"""
        properties = property_data_generator(count=200)
        
        # Gradually increase load until system breaks
        concurrent_levels = [1, 5, 10, 20, 50, 100]
        breaking_point = None
        
        for concurrency in concurrent_levels:
            success_count = 0
            total_time = 0
            
            start_time = time.perf_counter()
            
            # Create concurrent tasks
            tasks = []
            for i in range(concurrency):
                prop = properties[i % len(properties)]
                task = investment_analysis_service.analyze_investment_potential(prop)
                tasks.append(task)
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                elapsed = time.perf_counter() - start_time
                
                success_count = sum(1 for r in results if not isinstance(r, Exception))
                success_rate = (success_count / concurrency) * 100
                avg_response_time = elapsed / concurrency
                
                if success_rate < 90 or avg_response_time > 5.0:
                    breaking_point = concurrency
                    break
                
            except Exception:
                breaking_point = concurrency
                break
        
        # Report capacity findings
        if breaking_point:
            print(f"\nSystem breaking point: {breaking_point} concurrent requests")
        else:
            print(f"\nSystem handled up to {concurrent_levels[-1]} concurrent requests successfully")
        
        # System should handle at least 10 concurrent requests
        assert breaking_point is None or breaking_point >= 10, f"System capacity too low: breaks at {breaking_point} concurrent requests"