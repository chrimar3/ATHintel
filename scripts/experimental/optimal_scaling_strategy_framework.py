#!/usr/bin/env python3
"""
🏛️ OPTIMAL SCALING STRATEGY FRAMEWORK
Built upon proven 203 authenticated properties with 13.8% success rate

CURRENT SUCCESS ANALYSIS:
✅ 203 properties with 100% complete data (URL, SQM, Price, Energy Class)
✅ Direct URL collector: 13.8% success rate (much better than search pages)
✅ Proven property ID ranges: 1114000000 - 1118000000
✅ Athens Center focus with high-value neighborhoods
✅ Robust validation ensuring data quality

SCALING STRATEGY FRAMEWORK:
🎯 TARGET: 500-1000+ unique Athens Center properties
🚀 Multi-pronged approach using proven methodologies
📈 Predictive scaling based on successful patterns
⚡ Micro-batch processing for optimal reliability
🔄 Adaptive systems responding to real-time success rates
"""

import asyncio
import json
import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple, Generator
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright
import random
import statistics
import math
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, PriorityQueue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 1. SMART ID GENERATION STRATEGY
# ============================================================================

class PropertyIDAnalyzer:
    """Analyzes successful property ID patterns for predictive generation"""
    
    def __init__(self, successful_urls: List[str]):
        self.successful_ids = self._extract_ids_from_urls(successful_urls)
        self.analysis = self._analyze_patterns()
        
        logger.info(f"🔍 Analyzed {len(self.successful_ids)} successful property IDs")
        logger.info(f"📊 ID range: {min(self.successful_ids)} - {max(self.successful_ids)}")
        
    def _extract_ids_from_urls(self, urls: List[str]) -> List[int]:
        """Extract numerical property IDs from URLs"""
        ids = []
        for url in urls:
            match = re.search(r'/property/(\d+)', url)
            if match:
                ids.append(int(match.group(1)))
        return sorted(ids)
    
    def _analyze_patterns(self) -> Dict:
        """Analyze patterns in successful property IDs"""
        if not self.successful_ids:
            return {}
            
        # Statistical analysis
        mean_id = statistics.mean(self.successful_ids)
        median_id = statistics.median(self.successful_ids)
        stdev_id = statistics.stdev(self.successful_ids) if len(self.successful_ids) > 1 else 0
        
        # Range analysis
        min_id = min(self.successful_ids)
        max_id = max(self.successful_ids)
        range_span = max_id - min_id
        
        # Prefix analysis (first 4-6 digits)
        prefix_4 = Counter([str(id)[:4] for id in self.successful_ids])
        prefix_6 = Counter([str(id)[:6] for id in self.successful_ids])
        
        # Density analysis (gaps between IDs)
        gaps = [self.successful_ids[i+1] - self.successful_ids[i] 
                for i in range(len(self.successful_ids)-1)]
        avg_gap = statistics.mean(gaps) if gaps else 0
        
        # Most common ranges (divide into 10 buckets)
        bucket_size = range_span // 10
        bucket_counts = defaultdict(int)
        for id_val in self.successful_ids:
            bucket = (id_val - min_id) // bucket_size
            bucket_counts[bucket] += 1
        
        return {
            'statistical': {
                'mean': mean_id,
                'median': median_id,
                'stdev': stdev_id,
                'min': min_id,
                'max': max_id,
                'count': len(self.successful_ids)
            },
            'prefixes': {
                'top_4_digit': prefix_4.most_common(5),
                'top_6_digit': prefix_6.most_common(10)
            },
            'density': {
                'avg_gap': avg_gap,
                'gaps': sorted(gaps)[:20] if gaps else []  # Show 20 smallest gaps
            },
            'hotspots': {
                'bucket_size': bucket_size,
                'top_buckets': sorted(bucket_counts.items(), 
                                    key=lambda x: x[1], reverse=True)[:5]
            }
        }
    
    def generate_smart_id_ranges(self, target_count: int = 1000) -> List[Tuple[int, int]]:
        """Generate ID ranges based on successful patterns"""
        if not self.analysis:
            # Fallback to basic ranges if no analysis available
            return [(1114000000, 1118000000)]
        
        ranges = []
        stat = self.analysis['statistical']
        
        # Strategy 1: High-density ranges based on hotspots
        for bucket, count in self.analysis['hotspots']['top_buckets']:
            bucket_start = stat['min'] + (bucket * self.analysis['hotspots']['bucket_size'])
            bucket_end = bucket_start + self.analysis['hotspots']['bucket_size']
            ranges.append((bucket_start, bucket_end))
        
        # Strategy 2: Around successful prefixes
        for prefix, count in self.analysis['prefixes']['top_4_digit']:
            prefix_num = int(prefix) * (10 ** (10 - len(prefix)))  # Scale to 10 digits
            ranges.append((prefix_num, prefix_num + 999999))  # 1M range
        
        # Strategy 3: Statistical expansion around mean/median
        mean_range = 500000
        ranges.extend([
            (int(stat['mean'] - mean_range), int(stat['mean'] + mean_range)),
            (int(stat['median'] - mean_range), int(stat['median'] + mean_range))
        ])
        
        # Strategy 4: Recent property ranges (assuming higher IDs are newer)
        recent_threshold = stat['max'] - (stat['stdev'] * 2)
        ranges.append((int(recent_threshold), stat['max'] + 100000))
        
        # Remove duplicates and sort
        unique_ranges = []
        for start, end in ranges:
            if not any(abs(start - s) < 50000 and abs(end - e) < 50000 
                      for s, e in unique_ranges):
                unique_ranges.append((start, end))
        
        return sorted(unique_ranges)[:10]  # Limit to top 10 ranges

# ============================================================================
# 2. MICRO-BATCH PROCESSING OPTIMIZATION
# ============================================================================

@dataclass
class BatchConfig:
    """Configuration for optimized batch processing"""
    size: int
    delay_seconds: float
    retry_count: int
    success_threshold: float  # Minimum success rate to continue
    
class MicroBatchProcessor:
    """Optimized batch processing based on real-time success rates"""
    
    def __init__(self, initial_batch_size: int = 25):
        self.current_batch_size = initial_batch_size
        self.success_history = []
        self.performance_metrics = {
            'batch_sizes_tested': [],
            'success_rates': [],
            'optimal_size': initial_batch_size,
            'adaptive_adjustments': 0
        }
        
        logger.info(f"🔄 MicroBatchProcessor initialized with batch size: {initial_batch_size}")
    
    def record_batch_result(self, batch_size: int, successful_count: int, total_count: int):
        """Record results of a batch for adaptive optimization"""
        success_rate = successful_count / total_count if total_count > 0 else 0
        
        self.success_history.append({
            'batch_size': batch_size,
            'success_rate': success_rate,
            'successful_count': successful_count,
            'total_count': total_count,
            'timestamp': datetime.now()
        })
        
        self.performance_metrics['batch_sizes_tested'].append(batch_size)
        self.performance_metrics['success_rates'].append(success_rate)
        
        # Adaptive batch size adjustment
        self._adapt_batch_size()
        
        logger.info(f"📊 Batch result: {successful_count}/{total_count} = {success_rate:.2%} (size: {batch_size})")
    
    def _adapt_batch_size(self):
        """Adaptively adjust batch size based on performance"""
        if len(self.success_history) < 3:
            return  # Need more data
        
        recent_batches = self.success_history[-5:]  # Last 5 batches
        
        # Calculate average success rate for different batch sizes
        size_performance = defaultdict(list)
        for batch in recent_batches:
            size_performance[batch['batch_size']].append(batch['success_rate'])
        
        # Find optimal batch size
        avg_performance = {}
        for size, rates in size_performance.items():
            avg_performance[size] = statistics.mean(rates)
        
        if avg_performance:
            optimal_size = max(avg_performance, key=avg_performance.get)
            
            if optimal_size != self.current_batch_size:
                old_size = self.current_batch_size
                self.current_batch_size = optimal_size
                self.performance_metrics['adaptive_adjustments'] += 1
                self.performance_metrics['optimal_size'] = optimal_size
                
                logger.info(f"🎯 Batch size adapted: {old_size} → {optimal_size} "
                           f"(avg success rate: {avg_performance[optimal_size]:.2%})")
    
    def get_next_batch_config(self) -> BatchConfig:
        """Get optimized configuration for next batch"""
        # Adaptive delay based on recent success rates
        recent_success = statistics.mean([b['success_rate'] for b in self.success_history[-3:]]) \
                        if len(self.success_history) >= 3 else 0.1
        
        # Lower success rate = longer delay to avoid rate limiting
        base_delay = 2.0
        adaptive_delay = base_delay * (1.5 - recent_success)  # 0.5s - 3.0s range
        
        return BatchConfig(
            size=self.current_batch_size,
            delay_seconds=adaptive_delay,
            retry_count=3 if recent_success > 0.1 else 2,  # More retries if we're succeeding
            success_threshold=0.05  # Stop if success rate drops below 5%
        )

# ============================================================================
# 3. MULTI-STRATEGY PARALLEL PROCESSING
# ============================================================================

class CollectionStrategy:
    """Individual collection strategy with specific parameters"""
    
    def __init__(self, name: str, id_ranges: List[Tuple[int, int]], 
                 priority: int = 1, athens_filter: bool = True):
        self.name = name
        self.id_ranges = id_ranges
        self.priority = priority  # 1 = highest
        self.athens_filter = athens_filter
        self.success_count = 0
        self.attempt_count = 0
        self.last_success = None
        
    @property
    def success_rate(self) -> float:
        return self.success_count / self.attempt_count if self.attempt_count > 0 else 0
        
    def record_attempt(self, successful: bool):
        self.attempt_count += 1
        if successful:
            self.success_count += 1
            self.last_success = datetime.now()

class MultiStrategyCoordinator:
    """Coordinates multiple collection strategies in parallel"""
    
    def __init__(self, analyzer: PropertyIDAnalyzer):
        self.analyzer = analyzer
        self.strategies = self._create_strategies()
        self.active_workers = {}
        self.results_queue = PriorityQueue()
        self.coordination_lock = threading.Lock()
        
        logger.info(f"🎯 MultiStrategyCoordinator initialized with {len(self.strategies)} strategies")
    
    def _create_strategies(self) -> List[CollectionStrategy]:
        """Create collection strategies based on analysis"""
        smart_ranges = self.analyzer.generate_smart_id_ranges()
        
        strategies = [
            # High-priority: Proven successful ranges
            CollectionStrategy("hotspot_ranges", smart_ranges[:3], priority=1),
            
            # Medium-priority: Statistical expansion
            CollectionStrategy("statistical_expansion", smart_ranges[3:6], priority=2),
            
            # Lower-priority: Exploration ranges
            CollectionStrategy("exploration_ranges", smart_ranges[6:], priority=3),
            
            # Specialized: Recent properties (likely higher IDs)
            CollectionStrategy("recent_properties", 
                             [(max(self.analyzer.successful_ids), 
                               max(self.analyzer.successful_ids) + 200000)], 
                             priority=1),
            
            # Specialized: Gap filling between known successful IDs
            CollectionStrategy("gap_filling", self._create_gap_filling_ranges(), priority=2)
        ]
        
        return strategies
    
    def _create_gap_filling_ranges(self) -> List[Tuple[int, int]]:
        """Create ranges to fill gaps between known successful IDs"""
        gaps = []
        sorted_ids = sorted(self.analyzer.successful_ids)
        
        for i in range(len(sorted_ids) - 1):
            gap_size = sorted_ids[i+1] - sorted_ids[i]
            if gap_size > 1000:  # Only fill significant gaps
                gaps.append((sorted_ids[i], sorted_ids[i+1]))
        
        return gaps[:10]  # Limit to 10 largest gaps

# ============================================================================
# 4. QUALITY ASSURANCE PIPELINE
# ============================================================================

class PropertyValidator:
    """Advanced validation and quality assurance for properties"""
    
    def __init__(self):
        self.seen_urls = set()
        self.seen_properties = set()  # Based on price+sqm+neighborhood combo
        self.athens_center_neighborhoods = {
            'Syntagma', 'Plaka', 'Monastiraki', 'Psyrri', 'Exarchia', 
            'Kolonaki', 'Koukaki', 'Pagkrati', 'Mets', 'Petralona',
            'Thission', 'Gazi', 'Kerameikos', 'Metaxourgeio'
        }
        
        logger.info(f"🔍 PropertyValidator initialized with {len(self.athens_center_neighborhoods)} Athens Center neighborhoods")
    
    def is_duplicate(self, property_data: Dict) -> Tuple[bool, str]:
        """Check if property is a duplicate using multiple methods"""
        
        # Method 1: URL-based duplicate detection
        if property_data.get('url') in self.seen_urls:
            return True, "DUPLICATE_URL"
        
        # Method 2: Property signature (price + sqm + neighborhood)
        signature = f"{property_data.get('price')}_{property_data.get('sqm')}_{property_data.get('neighborhood')}"
        if signature in self.seen_properties:
            return True, "DUPLICATE_SIGNATURE"
        
        # Method 3: Near-duplicate detection (similar price + sqm in same neighborhood)
        if self._is_near_duplicate(property_data):
            return True, "NEAR_DUPLICATE"
        
        # Not a duplicate - record for future checks
        if property_data.get('url'):
            self.seen_urls.add(property_data['url'])
        self.seen_properties.add(signature)
        
        return False, "UNIQUE"
    
    def _is_near_duplicate(self, property_data: Dict) -> bool:
        """Check for near-duplicates (very similar properties)"""
        # For now, use simple signature approach
        # Could be enhanced with fuzzy matching algorithms
        return False
    
    def is_athens_center(self, neighborhood: str) -> bool:
        """Check if property is in Athens Center"""
        if not neighborhood:
            return False
        
        # Exact match
        if neighborhood in self.athens_center_neighborhoods:
            return True
        
        # Fuzzy matching for common variations
        neighborhood_lower = neighborhood.lower()
        for ac_neighborhood in self.athens_center_neighborhoods:
            if ac_neighborhood.lower() in neighborhood_lower or \
               neighborhood_lower in ac_neighborhood.lower():
                return True
        
        return False
    
    def validate_complete_data(self, property_data: Dict) -> Tuple[bool, List[str]]:
        """Validate that property has complete required data"""
        required_fields = ['url', 'price', 'sqm', 'energy_class']
        missing_fields = []
        
        for field in required_fields:
            if not property_data.get(field):
                missing_fields.append(field)
        
        # Additional validation
        issues = []
        
        # Price validation
        price = property_data.get('price')
        if price and (price < 50000 or price > 3000000):
            issues.append("PRICE_OUT_OF_RANGE")
        
        # SQM validation
        sqm = property_data.get('sqm')
        if sqm and (sqm < 25 or sqm > 600):
            issues.append("SQM_OUT_OF_RANGE")
        
        # Energy class validation
        energy_class = property_data.get('energy_class')
        valid_energy_classes = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'E', 'F', 'G']
        if energy_class and energy_class not in valid_energy_classes:
            issues.append("INVALID_ENERGY_CLASS")
        
        is_valid = len(missing_fields) == 0 and len(issues) == 0
        all_issues = [f"MISSING_{field.upper()}" for field in missing_fields] + issues
        
        return is_valid, all_issues

# ============================================================================
# 5. PERFORMANCE OPTIMIZATION
# ============================================================================

class AdaptiveRateLimiter:
    """Smart rate limiting based on success rates and server response"""
    
    def __init__(self, initial_delay: float = 2.0):
        self.base_delay = initial_delay
        self.current_delay = initial_delay
        self.success_window = []  # Rolling window of recent success rates
        self.error_counts = defaultdict(int)
        self.last_adjustment = datetime.now()
        
    def record_request(self, successful: bool, response_time: float = None, error_type: str = None):
        """Record request result for adaptive rate limiting"""
        
        # Update success window (keep last 20 requests)
        self.success_window.append(successful)
        if len(self.success_window) > 20:
            self.success_window.pop(0)
        
        # Track error types
        if error_type:
            self.error_counts[error_type] += 1
        
        # Adapt delay based on recent performance
        self._adapt_delay(response_time)
    
    def _adapt_delay(self, response_time: float = None):
        """Adaptively adjust delay based on performance indicators"""
        if len(self.success_window) < 10:
            return  # Need more data
        
        recent_success_rate = sum(self.success_window[-10:]) / 10
        overall_success_rate = sum(self.success_window) / len(self.success_window)
        
        # Adjustment factors
        delay_multiplier = 1.0
        
        # Factor 1: Success rate
        if recent_success_rate < 0.05:  # Very low success rate
            delay_multiplier *= 2.0  # Double the delay
        elif recent_success_rate < 0.1:  # Low success rate  
            delay_multiplier *= 1.5
        elif recent_success_rate > 0.2:  # Good success rate
            delay_multiplier *= 0.8  # Slightly faster
        
        # Factor 2: Error patterns
        if self.error_counts.get('RATE_LIMITED', 0) > 2:
            delay_multiplier *= 2.5
        elif self.error_counts.get('TIMEOUT', 0) > 3:
            delay_multiplier *= 1.8
        
        # Factor 3: Response time (if available)
        if response_time and response_time > 10.0:  # Slow responses
            delay_multiplier *= 1.3
        
        # Apply adjustment with bounds
        new_delay = self.base_delay * delay_multiplier
        self.current_delay = max(0.5, min(10.0, new_delay))  # 0.5s - 10s bounds
        
        # Reset error counts periodically
        if datetime.now() - self.last_adjustment > timedelta(minutes=10):
            self.error_counts.clear()
            self.last_adjustment = datetime.now()
    
    def get_delay(self) -> float:
        """Get current adaptive delay"""
        return self.current_delay

# ============================================================================
# 6. MAIN SCALING FRAMEWORK
# ============================================================================

class OptimalScalingFramework:
    """Main framework orchestrating all scaling strategies"""
    
    def __init__(self, successful_property_urls: List[str]):
        # Initialize components
        self.id_analyzer = PropertyIDAnalyzer(successful_property_urls)
        self.batch_processor = MicroBatchProcessor()
        self.strategy_coordinator = MultiStrategyCoordinator(self.id_analyzer)
        self.validator = PropertyValidator()
        self.rate_limiter = AdaptiveRateLimiter()
        
        # Scaling metrics
        self.target_properties = 1000
        self.collected_properties = []
        self.session_stats = {
            'start_time': datetime.now(),
            'strategies_used': 0,
            'batches_processed': 0,
            'total_attempts': 0,
            'unique_properties': 0,
            'athens_center_properties': 0
        }
        
        logger.info("🏛️ OptimalScalingFramework initialized successfully")
        self._log_initialization_summary()
    
    def _log_initialization_summary(self):
        """Log initialization summary"""
        logger.info("=" * 60)
        logger.info("🎯 OPTIMAL SCALING FRAMEWORK SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📊 Successful IDs analyzed: {len(self.id_analyzer.successful_ids)}")
        logger.info(f"🎯 Target properties: {self.target_properties}")
        logger.info(f"🚀 Collection strategies: {len(self.strategy_coordinator.strategies)}")
        logger.info(f"🔍 Athens Center neighborhoods: {len(self.validator.athens_center_neighborhoods)}")
        
        # Show ID analysis summary
        analysis = self.id_analyzer.analysis
        if analysis:
            stats = analysis['statistical']
            logger.info(f"📈 ID Range: {stats['min']:,} - {stats['max']:,}")
            logger.info(f"📈 Mean ID: {int(stats['mean']):,}")
            
            top_prefixes = analysis['prefixes']['top_4_digit'][:3]
            logger.info(f"🎯 Top prefixes: {', '.join([f'{p}xx ({c})' for p, c in top_prefixes])}")
        
        logger.info("=" * 60)
    
    async def execute_scaling_strategy(self) -> Dict:
        """Execute the complete scaling strategy"""
        logger.info("🚀 Starting optimal scaling strategy execution...")
        
        # TODO: This would contain the actual implementation
        # For now, return the framework configuration
        
        framework_config = {
            'id_analysis': self.id_analyzer.analysis,
            'strategies': [
                {
                    'name': s.name,
                    'priority': s.priority,
                    'ranges': s.id_ranges,
                    'athens_filter': s.athens_filter
                }
                for s in self.strategy_coordinator.strategies
            ],
            'batch_config': asdict(self.batch_processor.get_next_batch_config()),
            'validation_config': {
                'athens_center_neighborhoods': list(self.validator.athens_center_neighborhoods),
                'required_fields': ['url', 'price', 'sqm', 'energy_class']
            },
            'rate_limiting': {
                'current_delay': self.rate_limiter.current_delay,
                'base_delay': self.rate_limiter.base_delay
            }
        }
        
        return framework_config

# ============================================================================
# DEMO USAGE AND TESTING
# ============================================================================

def demo_scaling_framework():
    """Demonstrate the scaling framework with sample data"""
    
    # Sample successful URLs (based on your data patterns)
    sample_urls = [
        "https://www.spitogatos.gr/en/property/1117849708",
        "https://www.spitogatos.gr/en/property/1116810667", 
        "https://www.spitogatos.gr/en/property/1117677094",
        "https://www.spitogatos.gr/en/property/1116800081",
        "https://www.spitogatos.gr/en/property/1117819845",
        "https://www.spitogatos.gr/en/property/1117238428",
        "https://www.spitogatos.gr/en/property/1115970691",
        "https://www.spitogatos.gr/en/property/1116349256",
        "https://www.spitogatos.gr/en/property/1116740967",
        "https://www.spitogatos.gr/en/property/1117858511"
    ]
    
    # Initialize framework
    framework = OptimalScalingFramework(sample_urls)
    
    # Demo batch processing adaptation
    batch_processor = framework.batch_processor
    
    # Simulate some batch results
    batch_processor.record_batch_result(25, 3, 25)  # 12% success
    batch_processor.record_batch_result(25, 4, 25)  # 16% success  
    batch_processor.record_batch_result(25, 2, 25)  # 8% success
    batch_processor.record_batch_result(50, 5, 50)  # 10% success
    batch_processor.record_batch_result(10, 2, 10)  # 20% success
    
    logger.info(f"📊 Optimal batch size after adaptation: {batch_processor.current_batch_size}")
    
    # Demo rate limiter adaptation
    rate_limiter = framework.rate_limiter
    
    # Simulate some request patterns
    for _ in range(5):
        rate_limiter.record_request(False, error_type='TIMEOUT')
    for _ in range(3):
        rate_limiter.record_request(True, 2.5)
    rate_limiter.record_request(False, error_type='RATE_LIMITED')
    
    logger.info(f"⏱️ Adaptive delay after simulation: {rate_limiter.get_delay():.2f}s")
    
    # Demo property validation
    validator = framework.validator
    
    test_property = {
        'url': 'https://www.spitogatos.gr/en/property/1234567890',
        'price': 250000,
        'sqm': 85,
        'energy_class': 'B',
        'neighborhood': 'Syntagma'
    }
    
    is_duplicate, dup_reason = validator.is_duplicate(test_property)
    is_athens = validator.is_athens_center(test_property['neighborhood'])
    is_valid, issues = validator.validate_complete_data(test_property)
    
    logger.info(f"🔍 Property validation: Duplicate={is_duplicate}, Athens={is_athens}, Valid={is_valid}")
    
    return framework

if __name__ == "__main__":
    demo_scaling_framework()