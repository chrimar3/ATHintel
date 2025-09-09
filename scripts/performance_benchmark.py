#!/usr/bin/env python3
"""
Performance Benchmark Script
Story 1.4: Test validation performance optimization
Target: 10M properties/minute
"""

import sys
import time
import json
import random
import psutil
import gc
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validators.property_validator import PropertyValidator
from optimizers.performance_optimizer import (
    OptimizedValidator, 
    MemoryOptimizer,
    create_optimized_validator
)
from config.feature_flags import FeatureFlags


def generate_property_batch(size: int, pattern: str = 'mixed') -> List[Dict[str, Any]]:
    """
    Generate batch of test properties
    
    Args:
        size: Batch size
        pattern: Data pattern ('uniform', 'diverse', 'mixed')
    """
    properties = []
    
    if pattern == 'uniform':
        # Similar properties (good for caching)
        base_locations = ['Kolonaki', 'Glyfada']
        for i in range(size):
            properties.append({
                'id': f'uniform_{i:06d}',
                'url': f'https://spitogatos.gr/property/{100000 + i}',
                'price': 350000 + (i % 10) * 10000,
                'size': 120 + (i % 5) * 10,
                'rooms': 3,
                'location': base_locations[i % 2],
                'listed_date': datetime.now().isoformat()
            })
    
    elif pattern == 'diverse':
        # Diverse properties (stress test)
        locations = ['Kolonaki', 'Glyfada', 'Kifisia', 'Exarchia', 'Piraeus', 
                    'Marousi', 'Chalandri', 'Psychiko', 'Voula', 'Alimos']
        for i in range(size):
            properties.append({
                'id': f'diverse_{i:06d}',
                'url': f'https://spitogatos.gr/property/{random.randint(10000, 999999)}',
                'price': random.randint(100000, 1000000),
                'size': random.randint(40, 300),
                'rooms': random.randint(1, 6),
                'location': random.choice(locations),
                'listed_date': datetime.now().isoformat(),
                'year_built': random.randint(1970, 2024)
            })
    
    else:  # mixed
        # Mix of patterns
        half = size // 2
        properties.extend(generate_property_batch(half, 'uniform'))
        properties.extend(generate_property_batch(size - half, 'diverse'))
    
    return properties


def benchmark_baseline(validator: PropertyValidator, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Benchmark baseline validator performance"""
    print("\n📊 Baseline Performance Test")
    print("-" * 40)
    
    # Warm up
    for p in properties[:10]:
        validator.validate_property(p)
    
    # Actual benchmark
    gc.collect()
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    results = []
    for p in properties:
        result = validator.validate_property(p)
        results.append(result)
    
    elapsed = time.time() - start_time
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    return {
        'method': 'baseline',
        'total_properties': len(properties),
        'elapsed_seconds': elapsed,
        'throughput_per_second': len(properties) / elapsed if elapsed > 0 else 0,
        'throughput_per_minute': (len(properties) / elapsed * 60) if elapsed > 0 else 0,
        'memory_used_mb': end_memory - start_memory,
        'avg_time_per_property_ms': (elapsed / len(properties) * 1000) if properties else 0
    }


def benchmark_optimized(optimizer: OptimizedValidator, 
                       properties: List[Dict[str, Any]],
                       use_parallel: bool = True) -> Dict[str, Any]:
    """Benchmark optimized validator performance"""
    method = "optimized_parallel" if use_parallel else "optimized_sequential"
    print(f"\n📊 {method.replace('_', ' ').title()} Performance Test")
    print("-" * 40)
    
    # Warm up cache
    for p in properties[:100]:
        optimizer.validate_property(p)
    
    # Actual benchmark
    gc.collect()
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    if use_parallel:
        results = optimizer.validate_batch_optimized(properties)
    else:
        results = [optimizer.validate_property(p) for p in properties]
    
    elapsed = time.time() - start_time
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    # Get cache stats
    cache_stats = optimizer.cache.get_stats()
    
    return {
        'method': method,
        'total_properties': len(properties),
        'elapsed_seconds': elapsed,
        'throughput_per_second': len(properties) / elapsed if elapsed > 0 else 0,
        'throughput_per_minute': (len(properties) / elapsed * 60) if elapsed > 0 else 0,
        'memory_used_mb': end_memory - start_memory,
        'avg_time_per_property_ms': (elapsed / len(properties) * 1000) if properties else 0,
        'cache_hit_rate': cache_stats['hit_rate'],
        'cache_size': cache_stats['size']
    }


def run_scaling_test(optimizer: OptimizedValidator) -> List[Dict[str, Any]]:
    """Test scaling from 1K to 1M properties"""
    print("\n🚀 Scaling Test")
    print("=" * 60)
    
    test_sizes = [1000, 10000, 100000, 1000000]
    results = []
    
    for size in test_sizes:
        print(f"\n📏 Testing with {size:,} properties...")
        
        # Generate properties
        properties = generate_property_batch(min(size, 100000), 'mixed')
        
        # For very large tests, reuse properties
        if size > 100000:
            multiplier = size // 100000
            properties = properties * multiplier
            properties = properties[:size]
        
        # Memory estimate
        mem_estimate = MemoryOptimizer.estimate_memory_usage(size)
        print(f"  💾 Estimated memory: {mem_estimate['total_mb']:.1f} MB")
        
        # Run benchmark
        gc.collect()
        start_time = time.time()
        
        # Process in optimal batches for memory
        batch_size = MemoryOptimizer.optimize_batch_size(500, size)
        print(f"  📦 Using batch size: {batch_size:,}")
        
        total_processed = 0
        for i in range(0, size, batch_size):
            batch = properties[i:i+batch_size]
            optimizer.validate_batch_optimized(batch)
            total_processed += len(batch)
            
            # Progress indicator for large batches
            if size >= 100000 and total_processed % 100000 == 0:
                elapsed = time.time() - start_time
                rate = total_processed / elapsed if elapsed > 0 else 0
                print(f"    Processed {total_processed:,}/{size:,} "
                      f"({rate:.0f}/sec)")
        
        elapsed = time.time() - start_time
        throughput_per_min = (size / elapsed * 60) if elapsed > 0 else 0
        
        result = {
            'size': size,
            'elapsed_seconds': elapsed,
            'throughput_per_minute': throughput_per_min,
            'throughput_per_second': size / elapsed if elapsed > 0 else 0,
            'can_achieve_10m': throughput_per_min >= 10_000_000
        }
        
        results.append(result)
        
        print(f"  ⏱️  Elapsed: {elapsed:.2f}s")
        print(f"  🎯 Throughput: {throughput_per_min:,.0f}/min")
        print(f"  ✅ 10M target: {'ACHIEVED' if result['can_achieve_10m'] else 'NOT MET'}")
    
    return results


def main():
    """Run performance benchmarks"""
    print("=" * 80)
    print("🚀 ATHintel Performance Benchmark")
    print("🎯 Target: 10,000,000 properties/minute")
    print("=" * 80)
    
    # Enable feature flags
    ff = FeatureFlags()
    ff.enable("performance_mode")
    ff.enable("multi_factor_validation")
    print("✅ Feature flags enabled")
    
    # Create validators
    base_validator = PropertyValidator()
    optimizer = OptimizedValidator(base_validator, cache_size=50000)
    print("✅ Validators initialized")
    
    # System info
    print(f"\n💻 System Information:")
    print(f"  CPU Cores: {psutil.cpu_count()}")
    print(f"  Memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
    print(f"  Available: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
    
    # Test 1: Baseline vs Optimized (10K properties)
    print("\n" + "=" * 60)
    print("TEST 1: Baseline vs Optimized (10,000 properties)")
    print("=" * 60)
    
    test_properties = generate_property_batch(10000, 'mixed')
    
    baseline_result = benchmark_baseline(base_validator, test_properties)
    optimized_seq = benchmark_optimized(optimizer, test_properties, use_parallel=False)
    optimized_par = benchmark_optimized(optimizer, test_properties, use_parallel=True)
    
    # Compare results
    print("\n📊 Comparison Results:")
    print("-" * 60)
    print(f"{'Method':<25} {'Time (s)':<12} {'Throughput/min':<20} {'Memory (MB)':<12}")
    print("-" * 60)
    
    for result in [baseline_result, optimized_seq, optimized_par]:
        print(f"{result['method']:<25} "
              f"{result['elapsed_seconds']:<12.2f} "
              f"{result['throughput_per_minute']:<20,.0f} "
              f"{result.get('memory_used_mb', 0):<12.1f}")
    
    # Calculate speedup
    baseline_throughput = baseline_result['throughput_per_minute']
    optimized_throughput = optimized_par['throughput_per_minute']
    speedup = optimized_throughput / baseline_throughput if baseline_throughput > 0 else 0
    
    print(f"\n🚀 Speedup: {speedup:.1f}x")
    print(f"📈 Cache hit rate: {optimized_par.get('cache_hit_rate', 0):.1%}")
    
    # Test 2: Workload optimization
    print("\n" + "=" * 60)
    print("TEST 2: Workload Optimization Analysis")
    print("=" * 60)
    
    sample = generate_property_batch(1000, 'uniform')
    recommendations = optimizer.optimize_for_workload(sample)
    
    print("\n🔧 Optimization Recommendations:")
    for key, value in recommendations.items():
        print(f"  {key}: {value}")
    
    # Test 3: Scaling test
    print("\n" + "=" * 60)
    print("TEST 3: Scaling Test (1K → 1M properties)")
    print("=" * 60)
    
    scaling_results = run_scaling_test(optimizer)
    
    # Test 4: Memory efficiency
    print("\n" + "=" * 60)
    print("TEST 4: Memory Efficiency Test")
    print("=" * 60)
    
    # Test with 1M properties constraint
    mem_test_size = 1_000_000
    mem_estimate = MemoryOptimizer.estimate_memory_usage(mem_test_size)
    optimal_batch = MemoryOptimizer.optimize_batch_size(500, mem_test_size)
    
    print(f"\n📊 Memory Analysis for {mem_test_size:,} properties:")
    print(f"  Input data: {mem_estimate['input_data_mb']:.1f} MB")
    print(f"  Output data: {mem_estimate['output_data_mb']:.1f} MB")
    print(f"  Cache: {mem_estimate['cache_mb']:.1f} MB")
    print(f"  Total estimate: {mem_estimate['total_mb']:.1f} MB")
    print(f"  Optimal batch size: {optimal_batch:,}")
    print(f"  ✅ Meets <500MB requirement: {mem_estimate['total_mb'] < 500}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL PERFORMANCE SUMMARY")
    print("=" * 80)
    
    # Get final stats
    perf_stats = optimizer.get_performance_stats()
    
    print(f"\n🎯 Performance Metrics:")
    print(f"  Total Processed: {perf_stats['total_processed']:,}")
    print(f"  Overall Throughput: {perf_stats['throughput_per_minute']:,.0f}/min")
    print(f"  Cache Hit Rate: {perf_stats['cache_hit_rate']:.1%}")
    print(f"  Parallel Batches: {perf_stats['parallel_batches']}")
    print(f"  Worker Processes: {perf_stats['workers']}")
    
    # Check if we can achieve 10M/min
    max_throughput = max(r['throughput_per_minute'] for r in scaling_results)
    print(f"\n🏆 Maximum Achieved Throughput: {max_throughput:,.0f}/min")
    
    if max_throughput >= 10_000_000:
        print("✅ SUCCESS: 10M properties/minute target ACHIEVED!")
    else:
        shortfall = 10_000_000 - max_throughput
        print(f"⚠️  Target not met. Shortfall: {shortfall:,.0f}/min")
        print(f"   Achieved: {(max_throughput/10_000_000)*100:.1f}% of target")
    
    # Export results
    results_file = Path('performance_results.json')
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'baseline': baseline_result,
            'optimized_sequential': optimized_seq,
            'optimized_parallel': optimized_par,
            'scaling_test': scaling_results,
            'memory_analysis': mem_estimate,
            'performance_stats': perf_stats,
            'max_throughput': max_throughput,
            'target_achieved': max_throughput >= 10_000_000
        }, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to {results_file}")
    
    # Cleanup
    optimizer.shutdown()
    print("\n✅ Benchmark completed!")


if __name__ == "__main__":
    main()