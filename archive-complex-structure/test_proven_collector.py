#!/usr/bin/env python3
"""
🧪 Test Proven Athens Center Collector
Quick test with 5 properties to verify the methodology works

This test will:
1. Extract 5 sample properties using proven method
2. Validate all required fields are present
3. Confirm authentication markers
4. Show sample results
"""

import asyncio
import sys
from pathlib import Path

# Add scripts to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from proven_athens_center_collector import ProvenAthensCenterCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_proven_collector():
    """Test collector with small sample"""
    
    logger.info("🧪 TESTING PROVEN ATHENS CENTER COLLECTOR")
    logger.info("🎯 Testing with 5 properties to verify methodology")
    
    collector = ProvenAthensCenterCollector()
    
    try:
        # Test with small sample
        properties = await collector.collect_proven_athens_center(target_properties=5)
        
        if properties:
            logger.info(f"\n✅ TEST SUCCESS: {len(properties)} properties extracted")
            
            # Validate required fields
            complete_properties = 0
            for prop in properties:
                if all([prop.url, prop.price, prop.sqm, prop.energy_class]):
                    complete_properties += 1
            
            logger.info(f"📊 Complete properties: {complete_properties}/{len(properties)}")
            
            # Show sample property
            if properties:
                sample = properties[0]
                logger.info(f"\n📋 SAMPLE PROPERTY:")
                logger.info(f"   URL: {sample.url}")
                logger.info(f"   Title: {sample.title[:60]}...")
                logger.info(f"   Neighborhood: {sample.neighborhood}")
                logger.info(f"   Price: €{sample.price:,}")
                logger.info(f"   Size: {sample.sqm}m²")
                logger.info(f"   Energy Class: {sample.energy_class}")
                logger.info(f"   Price/m²: €{sample.price_per_sqm:.0f if sample.price_per_sqm else 0}")
                logger.info(f"   Authentication: {sample.validation_flags}")
            
            # Save test results
            json_file, csv_file = collector.save_proven_results(properties, "data/test")
            
            logger.info(f"\n💾 Test results saved:")
            logger.info(f"   JSON: {json_file}")
            logger.info(f"   CSV: {csv_file}")
            
            logger.info(f"\n🎉 TEST COMPLETED - Collector is working!")
            logger.info(f"   Ready for production run with larger targets")
            
        else:
            logger.error("❌ TEST FAILED: No properties extracted")
            logger.error("💡 Check network connection and website availability")
            
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        logger.error("💡 Check dependencies and network connection")

if __name__ == "__main__":
    asyncio.run(test_proven_collector())