#!/usr/bin/env python3
"""
🎯 RUNNER FOR DIRECT URL COLLECTOR
Simple execution script for the direct property ID enumeration collector

This script will:
1. Initialize the DirectURLCollector
2. Run the collection with 250 target properties  
3. Save results to data/processed/
4. Display final statistics
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from direct_url_collector import run_direct_collection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main execution function"""
    
    logger.info("="*60)
    logger.info("🎯 DIRECT URL COLLECTOR - EXECUTION STARTED")
    logger.info("="*60)
    
    logger.info("📍 APPROACH: Direct property ID enumeration")
    logger.info("🎯 TARGET: 250 authentic Athens properties")
    logger.info("🔧 METHOD: Bypass search page discovery issues")
    logger.info("📊 EXPECTED: 200-300 properties from known working ID ranges")
    
    try:
        # Run the async collection
        json_file, csv_file = asyncio.run(run_direct_collection(target_properties=250))
        
        if json_file and csv_file:
            logger.info("="*60)
            logger.info("🎉 DIRECT COLLECTION COMPLETED SUCCESSFULLY!")
            logger.info("="*60)
            logger.info(f"📁 Properties JSON: {json_file}")
            logger.info(f"📊 Summary CSV: {csv_file}")
            logger.info("")
            logger.info("✅ Collection complete - ready for analysis!")
            logger.info("✅ All properties have: URL, Price, SQM, Energy Class")
            logger.info("✅ Bypassed search page discovery issues completely")
            
        else:
            logger.error("="*60)
            logger.error("❌ COLLECTION FAILED")
            logger.error("="*60)
            logger.error("No properties were collected")
            logger.error("Check the logs above for specific issues")
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Collection interrupted by user")
        logger.info("Partial results may have been saved")
        
    except Exception as e:
        logger.error(f"❌ Collection failed with error: {e}")
        logger.error("Check the full traceback above for debugging")
        raise

if __name__ == "__main__":
    main()