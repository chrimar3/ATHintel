"""
Performance Optimizer
Story 1.4: Optimize validation for 10M properties/minute
Implements caching, parallel processing, and algorithm optimization
"""

import time
import hashlib
import json
import pickle
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, List, Any, Optional, Tuple, Callable
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        return self.hits / self.total_requests if self.total_requests > 0 else 0


class LRUCache:
    """
    Least Recently Used cache for validation results
    Thread-safe implementation with size limits
    """
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum cache entries
            ttl_seconds: Time to live for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.stats = CacheStats()
    
    def _make_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from property data"""
        # Create deterministic key from relevant fields
        key_data = {
            'id': data.get('id'),
            'price': data.get('price'),
            'size': data.get('size'),
            'location': data.get('location'),
            'rooms': data.get('rooms')
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, data: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached validation result
        
        Args:
            data: Property data
            
        Returns:
            Cached result or None
        """
        key = self._make_key(data)
        
        with self.lock:
            self.stats.total_requests += 1
            
            if key not in self.cache:
                self.stats.misses += 1
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                del self.cache[key]
                del self.timestamps[key]
                self.stats.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.stats.hits += 1
            return self.cache[key]
    
    def put(self, data: Dict[str, Any], result: Any) -> None:
        """
        Store validation result in cache
        
        Args:
            data: Property data
            result: Validation result
        """
        key = self._make_key(data)
        
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                del self.timestamps[oldest]
                self.stats.evictions += 1
            
            self.cache[key] = result
            self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'evictions': self.stats.evictions,
                'hit_rate': self.stats.hit_rate,
                'total_requests': self.stats.total_requests
            }


class ParallelProcessor:
    """
    Parallel processing for batch validations
    Uses multiprocessing for CPU-bound operations
    """
    
    def __init__(self, num_workers: Optional[int] = None):
        """
        Initialize parallel processor
        
        Args:
            num_workers: Number of worker processes (None for CPU count)
        """
        self.num_workers = num_workers or multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.num_workers * 2)
        self.process_pool = ProcessPoolExecutor(max_workers=self.num_workers)
    
    def process_batch_threaded(self, 
                              func: Callable,
                              items: List[Any],
                              chunk_size: int = 100) -> List[Any]:
        """
        Process batch using threads (for I/O-bound operations)
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            chunk_size: Size of chunks for processing
            
        Returns:
            List of results
        """
        if len(items) <= chunk_size:
            # Small batch, process directly
            return [func(item) for item in items]
        
        # Split into chunks and process in parallel
        chunks = [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]
        
        def process_chunk(chunk):
            return [func(item) for item in chunk]
        
        futures = [self.thread_pool.submit(process_chunk, chunk) for chunk in chunks]
        
        results = []
        for future in futures:
            results.extend(future.result())
        
        return results
    
    def process_batch_multiprocess(self,
                                  func: Callable,
                                  items: List[Any],
                                  chunk_size: int = 1000) -> List[Any]:
        """
        Process batch using processes (for CPU-bound operations)
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            chunk_size: Size of chunks for processing
            
        Returns:
            List of results
        """
        if len(items) <= chunk_size:
            # Small batch, process directly
            return [func(item) for item in items]
        
        # Use process pool for large batches
        try:
            return list(self.process_pool.map(func, items, chunksize=chunk_size))
        except Exception as e:
            logger.error(f"Multiprocessing failed: {e}, falling back to sequential")
            return [func(item) for item in items]
    
    def shutdown(self):
        """Shutdown executor pools"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


class OptimizedValidator:
    """
    Optimized property validator with caching and parallel processing
    Target: 10M properties/minute throughput
    """
    
    def __init__(self, base_validator, cache_size: int = 50000):
        """
        Initialize optimized validator
        
        Args:
            base_validator: Base PropertyValidator instance
            cache_size: Maximum cache size
        """
        self.base_validator = base_validator
        self.cache = LRUCache(max_size=cache_size)
        self.processor = ParallelProcessor()
        
        # Performance tracking
        self.start_time = time.time()
        self.total_processed = 0
        self.cache_hits = 0
        self.parallel_batches = 0
    
    def validate_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate single property with caching
        
        Args:
            property_data: Property to validate
            
        Returns:
            Validation result
        """
        # Check cache first
        cached_result = self.cache.get(property_data)
        if cached_result is not None:
            self.cache_hits += 1
            return cached_result
        
        # Validate and cache result
        result = self.base_validator.validate_property(property_data)
        result_dict = result.to_dict() if hasattr(result, 'to_dict') else result
        self.cache.put(property_data, result_dict)
        
        self.total_processed += 1
        return result_dict
    
    def validate_batch_parallel(self, 
                               properties: List[Dict[str, Any]],
                               use_multiprocess: bool = False) -> List[Dict[str, Any]]:
        """
        Validate batch of properties in parallel
        
        Args:
            properties: List of properties to validate
            use_multiprocess: Use multiprocessing instead of threading
            
        Returns:
            List of validation results
        """
        self.parallel_batches += 1
        
        if use_multiprocess:
            # For CPU-intensive validation
            results = self.processor.process_batch_multiprocess(
                self.validate_property,
                properties,
                chunk_size=1000
            )
        else:
            # For I/O-bound validation
            results = self.processor.process_batch_threaded(
                self.validate_property,
                properties,
                chunk_size=100
            )
        
        self.total_processed += len(properties)
        return results
    
    def validate_batch_optimized(self,
                                properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimized batch validation with intelligent processing
        
        Args:
            properties: List of properties to validate
            
        Returns:
            List of validation results
        """
        batch_size = len(properties)
        
        # Strategy selection based on batch size
        if batch_size < 10:
            # Small batch: sequential processing
            return [self.validate_property(p) for p in properties]
        
        elif batch_size < 100:
            # Medium batch: threaded processing
            return self.validate_batch_parallel(properties, use_multiprocess=False)
        
        elif batch_size < 10000:
            # Large batch: check cache first, then parallel process remainder
            results = []
            to_process = []
            
            for prop in properties:
                cached = self.cache.get(prop)
                if cached:
                    results.append(cached)
                    self.cache_hits += 1
                else:
                    to_process.append(prop)
            
            if to_process:
                processed = self.validate_batch_parallel(to_process, use_multiprocess=False)
                results.extend(processed)
            
            return results
        
        else:
            # Very large batch: multiprocessing
            return self.validate_batch_parallel(properties, use_multiprocess=True)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        elapsed = time.time() - self.start_time
        throughput = (self.total_processed / elapsed * 60) if elapsed > 0 else 0
        
        return {
            'total_processed': self.total_processed,
            'elapsed_seconds': elapsed,
            'throughput_per_minute': throughput,
            'cache_stats': self.cache.get_stats(),
            'cache_hit_rate': self.cache_hits / self.total_processed if self.total_processed > 0 else 0,
            'parallel_batches': self.parallel_batches,
            'workers': self.processor.num_workers
        }
    
    def optimize_for_workload(self, sample_properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Auto-tune optimization parameters based on workload
        
        Args:
            sample_properties: Sample of properties to analyze
            
        Returns:
            Optimization recommendations
        """
        recommendations = {
            'cache_size': self.cache.max_size,
            'ttl_seconds': self.cache.ttl_seconds,
            'parallel_threshold': 100,
            'use_multiprocess': False
        }
        
        # Analyze sample for patterns
        unique_locations = len(set(p.get('location', '') for p in sample_properties))
        avg_validation_time = 0
        
        # Test validation time
        start = time.time()
        for p in sample_properties[:10]:
            self.validate_property(p)
        avg_validation_time = (time.time() - start) / min(10, len(sample_properties))
        
        # Recommendations based on analysis
        if unique_locations < 50:
            # High locality, increase cache
            recommendations['cache_size'] = min(100000, self.cache.max_size * 2)
            recommendations['ttl_seconds'] = 7200  # 2 hours
        
        if avg_validation_time > 0.01:  # >10ms per validation
            # CPU-intensive, use multiprocessing
            recommendations['use_multiprocess'] = True
            recommendations['parallel_threshold'] = 50
        
        # Calculate expected throughput
        if recommendations['use_multiprocess']:
            expected_throughput = (self.processor.num_workers / avg_validation_time) * 60
        else:
            expected_throughput = (self.processor.num_workers * 2 / avg_validation_time) * 60
        
        recommendations['expected_throughput'] = expected_throughput
        recommendations['can_achieve_10m'] = expected_throughput >= 10_000_000
        
        return recommendations
    
    def shutdown(self):
        """Cleanup resources"""
        self.processor.shutdown()
        self.cache.clear()


class MemoryOptimizer:
    """
    Memory optimization for large-scale processing
    Ensures memory usage stays under 500MB for 1M properties
    """
    
    @staticmethod
    def estimate_memory_usage(num_properties: int) -> Dict[str, float]:
        """
        Estimate memory usage for given number of properties
        
        Args:
            num_properties: Number of properties to process
            
        Returns:
            Memory estimates in MB
        """
        # Average sizes (bytes)
        property_size = 500  # JSON property data
        result_size = 200    # Validation result
        cache_entry = 250    # Cached result
        
        # Calculate estimates
        input_memory = (num_properties * property_size) / (1024 * 1024)
        output_memory = (num_properties * result_size) / (1024 * 1024)
        cache_memory = (min(50000, num_properties) * cache_entry) / (1024 * 1024)
        overhead = 50  # Python overhead, libraries, etc.
        
        return {
            'input_data_mb': input_memory,
            'output_data_mb': output_memory,
            'cache_mb': cache_memory,
            'overhead_mb': overhead,
            'total_mb': input_memory + output_memory + cache_memory + overhead,
            'per_property_kb': ((input_memory + output_memory) * 1024) / num_properties
        }
    
    @staticmethod
    def optimize_batch_size(available_memory_mb: int = 500,
                           num_properties: int = 1_000_000) -> int:
        """
        Calculate optimal batch size for memory constraints
        
        Args:
            available_memory_mb: Available memory in MB
            num_properties: Total properties to process
            
        Returns:
            Optimal batch size
        """
        # Reserve memory for system and cache
        usable_memory = available_memory_mb * 0.7  # Use 70% of available
        
        # Calculate memory per property (conservative estimate)
        memory_per_property_kb = 1.5  # 1.5KB per property (input + output)
        
        # Calculate batch size
        batch_size = int((usable_memory * 1024) / memory_per_property_kb)
        
        # Apply reasonable limits
        batch_size = max(1000, min(batch_size, 100000))
        
        return batch_size


def create_optimized_validator(base_validator_class, config_path: Optional[str] = None):
    """
    Factory function to create optimized validator
    
    Args:
        base_validator_class: Base validator class
        config_path: Optional config file path
        
    Returns:
        OptimizedValidator instance
    """
    # Create base validator
    base = base_validator_class(config_path) if config_path else base_validator_class()
    
    # Wrap with optimizer
    optimized = OptimizedValidator(base, cache_size=50000)
    
    return optimized