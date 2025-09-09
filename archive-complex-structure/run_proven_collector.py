#!/usr/bin/env python3
"""
🚀 Execute Proven Athens Center Collector
Quick execution script for the proven methodology collector

Usage:
    python run_proven_collector.py
    
or with custom target:
    python run_proven_collector.py --target 50
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add scripts to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from proven_athens_center_collector import collect_proven_athens_center_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Execute Proven Athens Center Collector')
    parser.add_argument('--target', '-t', type=int, default=100, 
                       help='Target number of properties to collect (default: 100)')
    parser.add_argument('--batch', '-b', type=int, default=50,
                       help='Batch size for incremental collection (default: 50)')
    return parser.parse_args()

async def main():
    """Execute proven collector with options"""
    
    args = parse_arguments()
    
    logger.info("🏛️ PROVEN ATHENS CENTER COLLECTOR - EXECUTION")
    logger.info(f"🎯 Target properties: {args.target}")
    logger.info("📊 Using 100% verified successful methodology")
    logger.info("🔒 Conservative rate limiting: 3-5 second delays")
    logger.info("🏠 Focus: Syntagma, Monastiraki, Thiseio, Psirri, Plaka, Exarchia, Pagrati")
    
    # Recommend incremental approach for large targets
    if args.target > 100:
        logger.info(f"💡 RECOMMENDATION: Consider running in batches of {args.batch} properties")
        logger.info("   This prevents timeouts and allows incremental validation")
        
        response = input(f"Continue with {args.target} properties in one run? (y/n): ")
        if response.lower() != 'y':
            logger.info("Switching to batch mode")
            args.target = args.batch
    
    try:
        # Execute collection
        json_file, csv_file = await collect_proven_athens_center_data(args.target)
        
        if json_file and csv_file:
            logger.info("\n🎉 COLLECTION COMPLETED SUCCESSFULLY!")
            logger.info(f"📁 JSON Data: {json_file}")
            logger.info(f"📊 CSV Summary: {csv_file}")
            logger.info("\n🔍 NEXT STEPS:")
            logger.info("1. Review the authenticated data in the JSON file")
            logger.info("2. Verify property URLs are accessible")
            logger.info("3. Check price and size ranges match expectations")
            logger.info("4. Run additional batches if needed")
            
        else:
            logger.error("❌ Collection failed - no properties extracted")
            logger.error("💡 Try reducing target number or checking network connection")
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ Collection interrupted by user")
        logger.info("Partial results may be available in data/processed/")
        
    except Exception as e:
        logger.error(f"❌ Collection failed with error: {e}")
        logger.error("💡 Check network connection and website availability")

if __name__ == "__main__":
    asyncio.run(main())