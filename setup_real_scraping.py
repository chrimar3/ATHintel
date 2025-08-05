#!/usr/bin/env python3
"""
🔧 Setup Script for Real Data Scraping
Install dependencies and test scraping capabilities
"""

import subprocess
import sys
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages"""
    
    logger.info("📦 Installing requirements...")
    
    try:
        # Install Python requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        logger.info("✅ Python packages installed")
        
        # Install Playwright browsers
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])
        logger.info("✅ Playwright browsers installed")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Installation failed: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    
    logger.info("📁 Creating directories...")
    
    directories = [
        'data/raw/logs',
        'data/processed',
        'reports/athens_center',
        'reports/validation'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created: {directory}")

async def test_small_sample():
    """Test scraping with a small sample"""
    
    logger.info("🧪 Testing scraping with small sample...")
    
    try:
        # Import after installation
        from core.collectors.professional_real_estate_scraper import ProfessionalRealEstateScraper
        
        # Test with just 2 blocks, 2 properties each
        test_blocks = ["Syntagma", "Plaka"]
        scraper = ProfessionalRealEstateScraper(test_blocks)
        
        # Run small test
        properties = await scraper.scrape_athens_center_blocks(properties_per_block=2)
        
        if properties:
            logger.info(f"✅ Test successful: {len(properties)} properties extracted")
            
            # Save test results
            scraper.save_results(properties, 'data/processed/test')
            
            # Show sample property
            sample = properties[0]
            logger.info(f"📋 Sample property: {sample.title[:50]}...")
            logger.info(f"   Price: €{sample.price:,} | Size: {sample.sqm}m² | Source: {sample.source}")
            
            return True
        else:
            logger.warning("⚠️ Test returned no properties")
            return False
    
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    
    print("🏛️ ATHintel Real Data Scraping Setup")
    print("=" * 50)
    
    # Step 1: Install requirements
    print("\n1️⃣ Installing Dependencies...")
    if not install_requirements():
        print("❌ Setup failed at dependency installation")
        return
    
    # Step 2: Create directories
    print("\n2️⃣ Setting up Directories...")
    create_directories()
    
    # Step 3: Test scraping
    print("\n3️⃣ Testing Scraping Capabilities...")
    test_successful = asyncio.run(test_small_sample())
    
    # Final status
    print("\n" + "=" * 50)
    if test_successful:
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("\n📋 Next Steps:")
        print("   1. Run: python scripts/run_real_data_extraction.py")
        print("   2. Choose number of properties per block (10-20 recommended)")
        print("   3. Wait for extraction to complete")
        print("   4. Check reports in reports/athens_center/")
        print("\n⚠️  IMPORTANT:")
        print("   - Use respectful delays (already implemented)")
        print("   - Monitor for rate limiting")
        print("   - Start with small samples")
    else:
        print("❌ Setup completed but testing failed")
        print("   Check logs and try running test manually")

if __name__ == "__main__":
    main()