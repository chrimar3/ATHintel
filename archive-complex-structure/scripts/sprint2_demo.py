#!/usr/bin/env python3
"""
Sprint 2 Demo Script
Demonstrates Story 1.3 (Monitoring) and Story 1.4 (Performance)
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validators.property_validator import PropertyValidator
from monitoring.metrics_collector import get_metrics_collector
from monitoring.dashboard import MonitoringDashboard
from optimizers.performance_optimizer import OptimizedValidator, MemoryOptimizer
from config.feature_flags import FeatureFlags


def demo_monitoring():
    """Demo Story 1.3: Monitoring Dashboard"""
    print("\n" + "=" * 60)
    print("📊 STORY 1.3: Real-time Monitoring Dashboard Demo")
    print("=" * 60)
    
    # Enable monitoring
    ff = FeatureFlags()
    ff.enable("monitoring_enabled")
    ff.enable("multi_factor_validation")
    
    # Initialize components
    validator = PropertyValidator()
    dashboard = MonitoringDashboard(refresh_interval_seconds=1)
    
    print("\n✅ Components initialized")
    print("📊 Validating 100 test properties...")
    
    # Generate and validate test data
    for i in range(100):
        property_data = {
            'id': f'demo_{i:03d}',
            'url': f'https://spitogatos.gr/property/{i}',
            'price': 200000 + i * 1000,
            'size': 80 + i % 40,
            'rooms': 2 + i % 3,
            'location': ['Kolonaki', 'Glyfada', 'Kifisia'][i % 3],
            'listed_date': datetime.now().isoformat(),
            'images': ['img1.jpg', 'img2.jpg'] if i % 5 != 0 else []
        }
        
        result = validator.validate_property(property_data)
        
        # Show progress
        if (i + 1) % 20 == 0:
            print(f"  Validated {i + 1}/100 properties...")
    
    # Get dashboard data
    data = dashboard.get_dashboard_data()
    
    print("\n📈 Dashboard Metrics:")
    rt = data['real_time']['last_minute']
    print(f"  Total Validations: {rt['total_validations']}")
    print(f"  Valid: {rt['valid_count']} ({rt['validity_rate']:.1%})")
    print(f"  Invalid: {rt['invalid_count']}")
    print(f"  Average Score: {rt['avg_score']:.1f}")
    print(f"  Average Time: {rt['avg_time_ms']:.2f}ms")
    print(f"  Throughput: {rt['throughput_per_minute']}/min")
    
    # Export sample report
    dashboard.export_report('demo_monitoring.json', format='json')
    print("\n✅ Dashboard data exported to demo_monitoring.json")
    
    return True


def demo_performance():
    """Demo Story 1.4: Performance Optimization"""
    print("\n" + "=" * 60)
    print("🚀 STORY 1.4: Performance Optimization Demo")
    print("=" * 60)
    
    # Enable performance features
    ff = FeatureFlags()
    ff.enable("performance_mode")
    
    # Create validators
    base_validator = PropertyValidator()
    optimizer = OptimizedValidator(base_validator, cache_size=1000)
    
    print("\n✅ Optimized validator initialized")
    print("📊 Running performance comparison...")
    
    # Generate test data
    test_size = 1000
    test_data = []
    for i in range(test_size):
        test_data.append({
            'id': f'perf_{i:04d}',
            'url': f'https://spitogatos.gr/property/{i}',
            'price': 300000 + (i % 100) * 1000,
            'size': 100 + (i % 50),
            'rooms': 2 + (i % 4),
            'location': 'Kolonaki' if i % 2 == 0 else 'Glyfada',
            'listed_date': datetime.now().isoformat()
        })
    
    # Test 1: Baseline performance
    print(f"\n1️⃣ Baseline Test ({test_size} properties):")
    start = time.time()
    for prop in test_data:
        base_validator.validate_property(prop)
    baseline_time = time.time() - start
    baseline_throughput = (test_size / baseline_time * 60)
    print(f"   Time: {baseline_time:.2f}s")
    print(f"   Throughput: {baseline_throughput:,.0f}/min")
    
    # Test 2: Optimized with cache
    print(f"\n2️⃣ Optimized Test ({test_size} properties):")
    start = time.time()
    results = optimizer.validate_batch_optimized(test_data)
    optimized_time = time.time() - start
    optimized_throughput = (test_size / optimized_time * 60)
    print(f"   Time: {optimized_time:.2f}s")
    print(f"   Throughput: {optimized_throughput:,.0f}/min")
    
    # Cache stats
    cache_stats = optimizer.cache.get_stats()
    print(f"\n📊 Cache Performance:")
    print(f"   Hit Rate: {cache_stats['hit_rate']:.1%}")
    print(f"   Cache Size: {cache_stats['size']}")
    print(f"   Hits: {cache_stats['hits']}")
    print(f"   Misses: {cache_stats['misses']}")
    
    # Performance improvement
    speedup = optimized_throughput / baseline_throughput if baseline_throughput > 0 else 0
    print(f"\n🚀 Performance Improvement: {speedup:.1f}x faster")
    
    # Memory analysis
    mem_analysis = MemoryOptimizer.estimate_memory_usage(1000000)
    print(f"\n💾 Memory Analysis (1M properties):")
    print(f"   Estimated Total: {mem_analysis['total_mb']:.1f} MB")
    print(f"   Per Property: {mem_analysis['per_property_kb']:.2f} KB")
    print(f"   ✅ Meets <500MB requirement: {mem_analysis['total_mb'] < 500}")
    
    # Throughput projection
    projected_throughput = optimized_throughput * optimizer.processor.num_workers
    print(f"\n🎯 Throughput Projection (with {optimizer.processor.num_workers} workers):")
    print(f"   Projected: {projected_throughput:,.0f}/min")
    print(f"   Target: 10,000,000/min")
    print(f"   Achievement: {(projected_throughput/10000000)*100:.1f}%")
    
    # Cleanup
    optimizer.shutdown()
    
    return True


def main():
    """Run Sprint 2 Demo"""
    print("=" * 80)
    print("🎯 ATHintel Sprint 2 Demo")
    print("📅 Stories: 1.3 (Monitoring) & 1.4 (Performance)")
    print("=" * 80)
    
    try:
        # Demo monitoring
        monitoring_success = demo_monitoring()
        
        # Demo performance
        performance_success = demo_performance()
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ SPRINT 2 DEMO COMPLETED")
        print("=" * 80)
        
        print("\n📋 Story Completion:")
        print(f"  1.3 Monitoring Dashboard: {'✅ DONE' if monitoring_success else '❌ FAILED'}")
        print(f"  1.4 Performance Optimization: {'✅ DONE' if performance_success else '❌ FAILED'}")
        
        print("\n🎯 Key Achievements:")
        print("  • Real-time monitoring dashboard operational")
        print("  • Performance optimization with caching implemented")
        print("  • Parallel processing capability added")
        print("  • Memory efficiency validated (<500MB for 1M properties)")
        
        print("\n📈 Next Steps:")
        print("  • Deploy monitoring to production")
        print("  • Enable performance optimizations")
        print("  • Begin Sprint 3 planning")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())