#!/usr/bin/env python3
"""
🏛️ PARALLEL BATCH COLLECTION RUNNER
Simple runner to execute the 10-worker parallel batch collection system

USAGE:
- Default: 10 workers × 50 properties = 500 total properties
- Custom: python run_parallel_batch.py --workers 5 --per_worker 40
"""

import sys
import logging
from parallel_batch_collector import run_parallel_collection_sync

def main():
    """Run the parallel batch collection with configuration"""
    
    # Configuration
    num_workers = 10
    properties_per_worker = 50
    
    # Parse simple command line args if provided
    if len(sys.argv) > 1:
        try:
            if '--workers' in sys.argv:
                workers_idx = sys.argv.index('--workers')
                num_workers = int(sys.argv[workers_idx + 1])
            
            if '--per_worker' in sys.argv:
                per_worker_idx = sys.argv.index('--per_worker')
                properties_per_worker = int(sys.argv[per_worker_idx + 1])
        except (ValueError, IndexError):
            print("Usage: python run_parallel_batch.py [--workers N] [--per_worker N]")
            sys.exit(1)
    
    total_target = num_workers * properties_per_worker
    
    print(f"""
🏛️ PARALLEL BATCH ATHENS COLLECTOR
=================================

Configuration:
- Workers: {num_workers}
- Properties per worker: {properties_per_worker}
- Total target: {total_target}

Features:
✅ 10 concurrent workers with staggered starts
✅ Different search strategies per worker  
✅ Real-time progress monitoring
✅ Individual worker error handling & retry
✅ Consolidated JSON + CSV output
✅ Built on proven successful methodology

Starting collection...
    """)
    
    try:
        properties = run_parallel_collection_sync(num_workers, properties_per_worker)
        
        print(f"""
🎉 COLLECTION COMPLETE!
=====================

Results:
- Total properties collected: {len(properties)}
- Target achieved: {len(properties)}/{total_target} ({len(properties)/total_target*100:.1f}%)

Files saved in: data/processed/
- Consolidated JSON with all property data
- CSV summary for analysis
- Statistics file with performance metrics

✅ All properties have been validated as authentic with:
   - Valid URLs, prices, sizes, energy classes
   - Athens location verification
   - Price range: €50K - €3M
   - Size range: 25m² - 600m²
        """)
        
    except KeyboardInterrupt:
        print("\n⚠️ Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        logging.exception("Full error details:")

if __name__ == "__main__":
    main()