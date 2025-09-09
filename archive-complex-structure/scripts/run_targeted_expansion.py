#!/usr/bin/env python3
"""
🎯 TARGETED EXPANSION RUNNER
Launch the seed-based targeted property collector

WHAT THIS DOES:
✅ Loads 203 successful property IDs as seeds
✅ Generates nearby IDs using proven expansion strategies
✅ Collects properties with 15-25% expected success rate
✅ Saves results with comprehensive seed tracking
"""

import asyncio
import sys
from pathlib import Path

# Add the scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from targeted_expansion_collector import TargetedExpansionCollector

async def run_targeted_collection():
    """Execute the targeted expansion collection"""
    
    print("🚀 STARTING TARGETED EXPANSION COLLECTION")
    print("=" * 60)
    
    # Path to successful dataset (our seed source)
    successful_dataset_path = "/Users/chrism/spitogatos_premium_analysis/ATHintel/data/processed/athens_comprehensive_consolidated_authenticated_20250806_114015.json"
    
    # Verify seed dataset exists
    if not Path(successful_dataset_path).exists():
        print(f"❌ ERROR: Seed dataset not found at {successful_dataset_path}")
        print("Please ensure the successful dataset file exists.")
        return
    
    try:
        # Initialize collector
        collector = TargetedExpansionCollector(successful_dataset_path)
        
        print(f"🌱 Loaded {len(collector.id_generator.seed_ids)} seed properties")
        print(f"🎯 Target: {collector.target_properties} new properties")
        print(f"📊 Expected success rate: 15-25%")
        print("=" * 60)
        
        # Run collection
        properties = await collector.collect_properties()
        
        # Final summary
        print(f"\n🏁 COLLECTION SUMMARY")
        print("=" * 40)
        print(f"Total Properties: {len(properties)}")
        
        authentic = [p for p in properties if p.is_authentic_quality()]
        print(f"Authentic Quality: {len(authentic)}")
        
        success_rate = collector.stats.get_current_success_rate()
        print(f"Success Rate: {success_rate:.1f}%")
        
        runtime = collector.stats.get_runtime_minutes()
        print(f"Runtime: {runtime:.1f} minutes")
        
        if success_rate >= 15:
            print("✅ SUCCESS: Target performance achieved!")
        elif success_rate >= 10:
            print("🔶 GOOD: Significantly better than random!")
        else:
            print("⚠️ Needs refinement - but better than 0%!")
        
        # Show data locations
        print(f"\n📁 Data saved to: {collector.data_dir}")
        print(f"Main file: targeted_expansion_{collector.session_id}.json")
        print(f"Analysis: seed_analysis_{collector.session_id}.json")
        
    except Exception as e:
        print(f"❌ Error during collection: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_targeted_collection())