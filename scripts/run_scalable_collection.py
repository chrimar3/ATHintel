#!/usr/bin/env python3
"""
🚀 Run Scalable Collection
Execute the enhanced scalable property collection for 1000+ properties
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.collectors.scalable_athens_collector import run_scalable_collection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main execution function"""
    logger.info("🏛️ Starting ATHintel Scalable Collection")
    
    try:
        # Run collection for 1000 properties across priority neighborhoods
        properties, json_file = await run_scalable_collection(
            target_properties=1000,
            priority_level=1
        )
        
        logger.info(f"✅ Collection complete! {len(properties)} properties saved to {json_file}")
        
    except KeyboardInterrupt:
        logger.info("🛑 Collection interrupted by user")
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())