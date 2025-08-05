#!/usr/bin/env python3
"""
🧪 Test Proven Scrapers - Case Study Methodology
Test both Spitogatos and XE.gr scrapers using exact proven approaches
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from core.collectors.proven_spitogatos_scraper import ProvenSpitogatosScraper, test_proven_scraper
from core.collectors.proven_xe_scraper import ProvenXEScraper, test_proven_xe_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_both_proven_scrapers():
    """Test both scrapers using proven case study methodologies"""
    
    print("🧪 TESTING PROVEN SCRAPERS - CASE STUDY METHODOLOGY")
    print("=" * 70)
    
    # Test 1: Spitogatos (proven working)
    print("\n1️⃣ Testing Proven Spitogatos Scraper...")
    print("-" * 40)
    
    try:
        spitogatos_file = await test_proven_scraper()
        if spitogatos_file:
            print(f"✅ Spitogatos test successful: {spitogatos_file}")
        else:
            print("❌ Spitogatos test failed")
    except Exception as e:
        print(f"❌ Spitogatos test error: {e}")
    
    # Break between tests
    print("\n⏳ Waiting 10 seconds between tests...")
    await asyncio.sleep(10)
    
    # Test 2: XE.gr (proven working)
    print("\n2️⃣ Testing Proven XE.gr Scraper...")
    print("-" * 40)
    
    try:
        xe_file = await test_proven_xe_scraper()
        if xe_file:
            print(f"✅ XE.gr test successful: {xe_file}")
        else:
            print("❌ XE.gr test failed")
    except Exception as e:
        print(f"❌ XE.gr test error: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 PROVEN SCRAPER TESTING COMPLETED")
    print("\nNext steps:")
    print("1. Check debug screenshots for visual confirmation")
    print("2. Review extracted data files")
    print("3. If tests successful, run full extraction")

async def run_small_combined_extraction():
    """Run small combined extraction from both sources"""
    
    print("🚀 SMALL COMBINED EXTRACTION - PROVEN METHODS")
    print("=" * 60)
    
    # Initialize both scrapers
    spitogatos_scraper = ProvenSpitogatosScraper()
    xe_scraper = ProvenXEScraper()
    
    all_results = []
    
    # Extract from Spitogatos (5 properties)
    print("\n📍 Extracting from Spitogatos...")
    try:
        spitogatos_properties = await spitogatos_scraper.scrape_proven_athens_properties(max_properties_total=5)
        
        if spitogatos_properties:
            spitogatos_file = spitogatos_scraper.save_proven_results(spitogatos_properties)
            all_results.extend([
                {"source": "spitogatos", "property": prop} for prop in spitogatos_properties
            ])
            print(f"✅ Spitogatos: {len(spitogatos_properties)} properties")
        else:
            print("⚠️ No Spitogatos properties extracted")
    
    except Exception as e:
        print(f"❌ Spitogatos extraction failed: {e}")
    
    # Break between sources
    await asyncio.sleep(15)
    
    # Extract from XE.gr (5 properties)
    print("\n📍 Extracting from XE.gr...")
    try:
        xe_properties = await xe_scraper.scrape_proven_xe_athens(max_properties_total=5)
        
        if xe_properties:
            xe_file = xe_scraper.save_proven_xe_results(xe_properties)
            all_results.extend([
                {"source": "xe", "property": prop} for prop in xe_properties
            ])
            print(f"✅ XE.gr: {len(xe_properties)} properties")
        else:
            print("⚠️ No XE.gr properties extracted")
    
    except Exception as e:
        print(f"❌ XE.gr extraction failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 COMBINED EXTRACTION COMPLETED")
    print(f"📊 Total properties: {len(all_results)}")
    
    if all_results:
        spitogatos_count = len([r for r in all_results if r["source"] == "spitogatos"])
        xe_count = len([r for r in all_results if r["source"] == "xe"])
        
        print(f"   Spitogatos: {spitogatos_count} properties")
        print(f"   XE.gr: {xe_count} properties")
        
        # Show sample from each source
        if spitogatos_count > 0:
            spito_sample = next(r["property"] for r in all_results if r["source"] == "spitogatos")
            print(f"\n📋 Spitogatos Sample:")
            print(f"   Title: {spito_sample.title}")
            print(f"   Price: €{spito_sample.price:,}")
            print(f"   Size: {spito_sample.sqm}m²")
        
        if xe_count > 0:
            xe_sample = next(r["property"] for r in all_results if r["source"] == "xe")
            print(f"\n📋 XE.gr Sample:")
            print(f"   Neighborhood: {xe_sample.neighborhood}")
            print(f"   Price: {xe_sample.price}")
            print(f"   Size: {xe_sample.sqm}m²")
    
    else:
        print("❌ No properties extracted from either source")
        print("\nDebugging suggestions:")
        print("1. Check debug screenshots")
        print("2. Verify website accessibility")
        print("3. Check network connectivity")

def main():
    """Main test function"""
    
    print("🏛️ ATHintel Proven Scrapers Test Suite")
    print("Based on spitogatos_premium_analysis case study")
    print("=" * 60)
    
    # Ask user what to test
    print("\nChoose test mode:")
    print("1. Quick test (small samples)")
    print("2. Small combined extraction")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
        return
    
    if choice == "1":
        asyncio.run(test_both_proven_scrapers())
    elif choice == "2":
        asyncio.run(run_small_combined_extraction())
    else:
        print("Invalid choice. Running quick test...")
        asyncio.run(test_both_proven_scrapers())

if __name__ == "__main__":
    main()