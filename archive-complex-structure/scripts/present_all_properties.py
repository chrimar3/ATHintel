#!/usr/bin/env python3
"""
📋 Present All Individual Properties
Display complete data for each and every property extracted
"""

import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def present_all_properties():
    """Present complete data for every single property"""
    
    # Find latest data file
    data_files = list(Path("data/processed").glob("athens_large_scale_real_data_*.json"))
    if not data_files:
        logger.error("❌ No data files found")
        return
    
    latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        properties = json.load(f)
    
    print("🏛️ ATHENS REAL ESTATE - COMPLETE PROPERTY DATABASE")
    print("=" * 100)
    print(f"📊 Total Properties: {len(properties)}")
    print(f"📁 Data Source: {latest_file.name}")
    print(f"🕒 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Sort properties by price (high to low) for better presentation
    properties_sorted = sorted(properties, key=lambda x: x.get('price', 0), reverse=True)
    
    for i, prop in enumerate(properties_sorted, 1):
        print(f"\n🏠 PROPERTY #{i:03d}")
        print("─" * 80)
        
        # Essential Information
        print(f"🔗 URL: {prop.get('url', 'N/A')}")
        print(f"💰 PRICE: €{prop.get('price', 0):,.0f}")
        print(f"📐 SIZE: {prop.get('sqm', 0)}m²")
        print(f"⚡ ENERGY CLASS: {prop.get('energy_class', 'N/A')}")
        print(f"💸 PRICE/m²: €{prop.get('price_per_sqm', 0):,.0f}")
        
        # Location Information
        print(f"📍 NEIGHBORHOOD: {prop.get('neighborhood', 'N/A')}")
        print(f"🏘️ TITLE: {prop.get('title', 'N/A')[:100]}...")
        
        # Property Details
        print(f"🛏️ ROOMS: {prop.get('rooms', 'N/A')}")
        print(f"🏢 TYPE: {prop.get('property_type', 'N/A').title()}")
        print(f"📋 LISTING: {prop.get('listing_type', 'N/A').title()}")
        
        # Data Quality
        print(f"🎯 CONFIDENCE: {prop.get('extraction_confidence', 0):.0%}")
        print(f"✅ VALIDATION: {', '.join(prop.get('validation_flags', []))}")
        print(f"🕐 EXTRACTED: {prop.get('timestamp', 'N/A')[:19]}")
        
        # Additional Information
        if prop.get('description'):
            print(f"📝 DESCRIPTION: {prop.get('description', '')[:150]}...")
        
        print(f"🔑 PROPERTY ID: {prop.get('property_id', 'N/A')}")
        print(f"#️⃣ HTML HASH: {prop.get('html_source_hash', 'N/A')}")
    
    print("\n" + "=" * 100)
    print("📊 SUMMARY STATISTICS")
    print("=" * 100)
    
    # Calculate statistics
    prices = [p.get('price', 0) for p in properties if p.get('price')]
    sqms = [p.get('sqm', 0) for p in properties if p.get('sqm')]
    price_per_sqms = [p.get('price_per_sqm', 0) for p in properties if p.get('price_per_sqm')]
    
    # Energy class distribution
    energy_classes = {}
    for prop in properties:
        energy = prop.get('energy_class')
        if energy:
            energy_classes[energy] = energy_classes.get(energy, 0) + 1
    
    # Neighborhood distribution
    neighborhoods = {}
    for prop in properties:
        neighborhood = prop.get('neighborhood')
        if neighborhood:
            neighborhoods[neighborhood] = neighborhoods.get(neighborhood, 0) + 1
    
    print(f"💰 PRICE STATISTICS:")
    print(f"   Total Properties: {len(prices)}")
    print(f"   Average Price: €{sum(prices)/len(prices):,.0f}")
    print(f"   Minimum Price: €{min(prices):,.0f}")
    print(f"   Maximum Price: €{max(prices):,.0f}")
    print(f"   Total Value: €{sum(prices):,.0f}")
    
    print(f"\n📐 SIZE STATISTICS:")
    print(f"   Total Properties: {len(sqms)}")
    print(f"   Average Size: {sum(sqms)/len(sqms):.0f}m²")
    print(f"   Minimum Size: {min(sqms):.0f}m²")
    print(f"   Maximum Size: {max(sqms):.0f}m²")
    print(f"   Total Area: {sum(sqms):,.0f}m²")
    
    print(f"\n💸 PRICE PER m² STATISTICS:")
    print(f"   Average Price/m²: €{sum(price_per_sqms)/len(price_per_sqms):,.0f}")
    print(f"   Minimum Price/m²: €{min(price_per_sqms):,.0f}")
    print(f"   Maximum Price/m²: €{max(price_per_sqms):,.0f}")
    
    print(f"\n⚡ ENERGY CLASS DISTRIBUTION:")
    for energy_class in sorted(energy_classes.keys()):
        count = energy_classes[energy_class]
        percentage = (count / len(properties)) * 100
        print(f"   {energy_class}: {count} properties ({percentage:.1f}%)")
    
    print(f"\n📍 NEIGHBORHOOD DISTRIBUTION:")
    for neighborhood in sorted(neighborhoods.keys(), key=lambda x: neighborhoods[x], reverse=True):
        count = neighborhoods[neighborhood]
        percentage = (count / len(properties)) * 100
        print(f"   {neighborhood}: {count} properties ({percentage:.1f}%)")
    
    print("\n" + "=" * 100)
    print("✅ COMPLETE PROPERTY DATABASE PRESENTED")
    print("🎯 All individual properties with complete data shown above")
    print("📊 Ready for investment analysis and decision making")
    print("=" * 100)

def export_individual_properties_csv():
    """Export individual properties to detailed CSV"""
    
    # Find latest data file
    data_files = list(Path("data/processed").glob("athens_large_scale_real_data_*.json"))
    if not data_files:
        return None
    
    latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        properties = json.load(f)
    
    # Create detailed CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = Path("data/processed") / f"all_individual_properties_{timestamp}.csv"
    
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("Property_Number,URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Rooms,Title,Property_Type,Listing_Type,Confidence,Validation_Flags,Timestamp,Property_ID,Description\n")
        
        properties_sorted = sorted(properties, key=lambda x: x.get('price', 0), reverse=True)
        
        for i, prop in enumerate(properties_sorted, 1):
            # Escape commas and quotes in text fields
            title = prop.get('title', '').replace('"', '""').replace(',', ';')
            description = prop.get('description', '').replace('"', '""').replace(',', ';')
            validation = ';'.join(prop.get('validation_flags', []))
            
            f.write(f'{i},"{prop.get("url", "")}",{prop.get("price", 0)},{prop.get("sqm", 0)},"{prop.get("energy_class", "")}",{prop.get("price_per_sqm", 0):.0f},"{prop.get("neighborhood", "")}",{prop.get("rooms", "") or ""},"{title}","{prop.get("property_type", "")}","{prop.get("listing_type", "")}",{prop.get("extraction_confidence", 0):.2f},"{validation}","{prop.get("timestamp", "")[:19]}","{prop.get("property_id", "")}","{description[:200]}"\n')
    
    print(f"📊 Individual properties exported to: {csv_file}")
    return str(csv_file)

if __name__ == "__main__":
    # Present all properties
    present_all_properties()
    
    # Export to CSV
    csv_file = export_individual_properties_csv()
    
    print(f"\n📁 CSV Export: {csv_file}")
    print("🎯 Complete individual property data ready for analysis!")