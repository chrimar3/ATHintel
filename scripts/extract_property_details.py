#!/usr/bin/env python3
"""
📋 Property Details Extractor

Extract and display URLs, SQM, and energy class for all scanned properties
in Athens center blocks analysis.
"""

import json
import pandas as pd
from pathlib import Path
import sys

def extract_property_details():
    """Extract and display property details from latest analysis"""
    
    # Find the latest analysis file
    data_dir = Path("data/processed")
    analysis_files = list(data_dir.glob("athens_center_blocks_analysis_*.json"))
    
    if not analysis_files:
        print("❌ No Athens center blocks analysis files found!")
        return
    
    # Get the most recent file
    latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
    print(f"📊 Reading analysis from: {latest_file.name}")
    
    # Load the analysis data
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    properties = data.get('properties', [])
    
    if not properties:
        print("❌ No properties found in analysis file!")
        return
    
    print(f"\n🏠 ATHENS CENTER BLOCKS - ALL PROPERTIES SCANNED")
    print("=" * 100)
    print(f"📈 Total Properties: {len(properties)}")
    print(f"🏛️ Analysis Date: {data['analysis_metadata']['timestamp']}")
    print("=" * 100)
    
    # Sort properties by block and investment score
    properties_sorted = sorted(properties, key=lambda x: (x['block_id'], -x['investment_score']))
    
    # Group by block for better organization
    current_block = None
    block_count = 0
    property_count = 0
    
    for prop in properties_sorted:
        # Block header
        if prop['block_id'] != current_block:
            current_block = prop['block_id']
            block_count += 1
            
            print(f"\n📍 BLOCK {block_count}: {prop['block_id']} - {prop['neighborhood']}")
            print(f"   District: {prop['district_zone']} | Tourism Score: {prop['tourism_score']}/10")
            print("-" * 100)
            print(f"{'No.':<4} {'URL':<50} {'SQM':<6} {'Energy':<8} {'Score':<6} {'Action':<15} {'Price':<12}")
            print("-" * 100)
        
        property_count += 1
        
        # Property details
        url = prop['url']
        sqm = prop['sqm']
        energy_class = prop['energy_class']
        score = prop['investment_score']
        action = prop['recommended_action']
        price = prop['price']
        
        # Truncate URL if too long
        display_url = url if len(url) <= 48 else url[:45] + "..."
        
        print(f"{property_count:<4} {display_url:<50} {sqm:<6} {energy_class:<8} {score:<6.1f} {action:<15} €{price:<11,}")
    
    print("\n" + "=" * 100)
    print(f"✅ Complete Property List: {property_count} properties across {block_count} blocks")
    
    # Summary statistics
    print(f"\n📊 PROPERTY SUMMARY STATISTICS")
    print("-" * 50)
    
    # Energy class distribution
    energy_distribution = {}
    sqm_stats = []
    price_stats = []
    
    for prop in properties:
        energy_class = prop['energy_class']
        energy_distribution[energy_class] = energy_distribution.get(energy_class, 0) + 1
        sqm_stats.append(prop['sqm'])
        price_stats.append(prop['price'])
    
    print(f"🔋 Energy Class Distribution:")
    for energy_class in sorted(energy_distribution.keys()):
        count = energy_distribution[energy_class]
        percentage = (count / len(properties)) * 100
        print(f"   {energy_class}: {count} properties ({percentage:.1f}%)")
    
    print(f"\n📏 Size Statistics:")
    print(f"   Average SQM: {sum(sqm_stats) / len(sqm_stats):.1f}")
    print(f"   Min SQM: {min(sqm_stats)}")
    print(f"   Max SQM: {max(sqm_stats)}")
    
    print(f"\n💰 Price Statistics:")
    print(f"   Average Price: €{sum(price_stats) / len(price_stats):,.0f}")
    print(f"   Min Price: €{min(price_stats):,}")
    print(f"   Max Price: €{max(price_stats):,}")
    
    # Investment recommendations summary
    print(f"\n🎯 Investment Recommendations:")
    recommendations = {}
    for prop in properties:
        action = prop['recommended_action']
        recommendations[action] = recommendations.get(action, 0) + 1
    
    for action, count in sorted(recommendations.items()):
        percentage = (count / len(properties)) * 100
        print(f"   {action}: {count} properties ({percentage:.1f}%)")

def export_to_csv():
    """Export property details to CSV for spreadsheet analysis"""
    
    # Find the latest analysis file
    data_dir = Path("data/processed")
    analysis_files = list(data_dir.glob("athens_center_blocks_analysis_*.json"))
    
    if not analysis_files:
        print("❌ No analysis files found for CSV export!")
        return
    
    latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
    
    # Load the analysis data
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    properties = data.get('properties', [])
    
    if not properties:
        print("❌ No properties found for CSV export!")
        return
    
    # Create DataFrame with key property details
    df_data = []
    for prop in properties:
        df_data.append({
            'Property_ID': prop['property_id'],
            'Block_ID': prop['block_id'],
            'Neighborhood': prop['neighborhood'],
            'District_Zone': prop['district_zone'],
            'URL': prop['url'],
            'SQM': prop['sqm'],
            'Energy_Class': prop['energy_class'],
            'Price': prop['price'],
            'Price_per_SQM': prop['price_per_sqm'],
            'Investment_Score': prop['investment_score'],
            'Recommended_Action': prop['recommended_action'],
            'Investment_Strategy': prop['investment_strategy'],
            'Target_Price': prop['target_price'],
            'Expected_ROI_24m': prop['expected_roi_24m'],
            'Tourism_Score': prop['tourism_score'],
            'Commercial_Score': prop['commercial_score'],
            'Metro_Distance': prop['metro_distance'],
            'Overall_Risk': prop['overall_risk']
        })
    
    df = pd.DataFrame(df_data)
    
    # Sort by investment score (highest first)
    df = df.sort_values('Investment_Score', ascending=False)
    
    # Export to CSV
    csv_filename = f"athens_center_properties_{data['analysis_metadata']['timestamp']}.csv"
    csv_path = Path("reports/athens_center") / csv_filename
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    print(f"📊 Property details exported to CSV: {csv_path}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Rows: {len(df)}")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--csv":
        export_to_csv()
    else:
        extract_property_details()
        print(f"\n💡 Tip: Use 'python scripts/extract_property_details.py --csv' to export to spreadsheet")