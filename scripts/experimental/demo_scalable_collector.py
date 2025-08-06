#!/usr/bin/env python3
"""
🧪 DEMO SCALABLE ATHENS COLLECTOR
Quick test of the scalable methodology with 25 properties

This demonstrates the scalable collector on a small scale to verify:
- Proven methodology works at scale
- Multiple search strategies function correctly
- Batch processing and incremental saving
- URL deduplication
- Proper rate limiting

Run this before launching full 500+ property collection.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from scalable_athens_collector import run_scalable_collection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_collection():
    """Demo collection with 25 properties"""
    
    logger.info("🧪 DEMO SCALABLE ATHENS COLLECTION")
    logger.info("=================================")
    logger.info("Testing scalable methodology with 25 properties")
    logger.info("Built on proven collector that extracted 100+ authentic properties")
    logger.info()
    
    try:
        # Run small-scale test
        properties, session_name = await run_scalable_collection(
            target_properties=25,      # Small target for demo
            batch_size=10,            # Small batches
            max_strategies=5,         # Limited strategies
            session_timeout_minutes=15 # Short timeout
        )
        
        logger.info("✅ DEMO COLLECTION COMPLETE!")
        logger.info(f"📊 Collected: {len(properties)} authentic properties")
        logger.info(f"📁 Session: {session_name}")
        logger.info(f"💾 Check data/processed/ for results")
        
        # Show sample results
        if properties:
            logger.info("\n🏆 SAMPLE PROPERTIES:")
            for i, prop in enumerate(properties[:5], 1):
                logger.info(f"{i}. {prop.neighborhood}: €{prop.price:,} - {prop.sqm}m² - {prop.energy_class}")
                logger.info(f"   Strategy: {prop.search_strategy}")
                logger.info(f"   €{prop.price_per_sqm:.0f}/m² - {prop.url}")
                logger.info("")
        
        # Validation summary
        authentic_count = len([p for p in properties if "SCALED_AUTHENTIC_DATA" in p.validation_flags])
        logger.info(f"🔍 VALIDATION SUMMARY:")
        logger.info(f"   Total properties: {len(properties)}")
        logger.info(f"   Authenticated: {authentic_count} ({authentic_count/len(properties)*100:.1f}%)")
        
        if properties:
            prices = [p.price for p in properties if p.price]
            sqms = [p.sqm for p in properties if p.sqm]
            energy_classes = [p.energy_class for p in properties if p.energy_class]
            
            logger.info(f"   Price range: €{min(prices):,.0f} - €{max(prices):,.0f}")
            logger.info(f"   Size range: {min(sqms):.0f}m² - {max(sqms):.0f}m²")
            logger.info(f"   Energy classes: {sorted(set(energy_classes))}")
        
        logger.info("\n🚀 Ready for full-scale collection!")
        logger.info("Next: python run_scalable_collection.py --mode single --target 500")
        
        return properties
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Demo stopped by user")
        return []
    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        raise

if __name__ == "__main__":
    # Run the demo
    properties = asyncio.run(demo_collection())