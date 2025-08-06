#!/usr/bin/env python3
"""
🔍 Athens Center Blocks Search Script

Execute comprehensive search and analysis of Athens center blocks
for investment opportunities with detailed property-by-property analysis.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.analyzers.athens_center_blocks_analyzer import AthensCenterBlocksAnalyzer
from reports.investment.investment_report_generator import InvestmentReportGenerator

async def search_athens_center_blocks():
    """Main search and analysis function"""
    
    print("🏛️ ATHintel - Athens Center Blocks Search")
    print("=" * 70)
    print("🎯 Analyzing prime Athens center blocks for investment opportunities")
    print("📍 Focus Areas: Syntagma, Plaka, Monastiraki, Psyrri, Koukaki, Exarchia, Kolonaki")
    print()
    
    # Initialize analyzer
    analyzer = AthensCenterBlocksAnalyzer()
    
    # Run comprehensive center blocks analysis
    print("🔍 Starting comprehensive center blocks analysis...")
    properties = await analyzer.analyze_center_blocks()
    
    # Save detailed results
    results_path = analyzer.save_analysis_results(properties)
    
    # Generate investment summary
    generate_investment_summary(properties)
    
    # Generate detailed reports
    await generate_detailed_reports(properties)
    
    print(f"\n💾 Complete analysis saved to: {results_path}")
    print("✅ Athens center blocks search completed successfully!")
    
    return properties

def generate_investment_summary(properties):
    """Generate comprehensive investment summary"""
    
    print("\n" + "=" * 70)
    print("💰 INVESTMENT OPPORTUNITIES SUMMARY")
    print("=" * 70)
    
    # Overall statistics
    total_properties = len(properties)
    avg_score = sum(p.investment_score for p in properties) / total_properties
    
    print(f"📊 Properties Analyzed: {total_properties}")
    print(f"📈 Average Investment Score: {avg_score:.1f}/10")
    print(f"🏙️ Blocks Covered: {len(set(p.block_id for p in properties))}")
    
    # Investment recommendations breakdown
    recommendations = {}
    total_investment_value = 0
    
    for prop in properties:
        action = prop.recommended_action
        recommendations[action] = recommendations.get(action, 0) + 1
        
        if action in ["IMMEDIATE_BUY", "STRONG_BUY"]:
            total_investment_value += prop.target_price
    
    print(f"\n📋 Investment Recommendations:")
    for action, count in sorted(recommendations.items()):
        print(f"   {action}: {count} properties")
    
    print(f"\n💰 Total Investment Value: €{total_investment_value:,.0f}")
    
    # District analysis
    print(f"\n🏘️ DISTRICT ANALYSIS")
    print("-" * 50)
    
    district_analysis = {}
    for prop in properties:
        district = prop.district_zone
        if district not in district_analysis:
            district_analysis[district] = {
                'count': 0,
                'avg_score': 0,
                'investment_value': 0,
                'properties': []
            }
        
        district_analysis[district]['count'] += 1
        district_analysis[district]['avg_score'] += prop.investment_score
        district_analysis[district]['properties'].append(prop)
        
        if prop.recommended_action in ["IMMEDIATE_BUY", "STRONG_BUY"]:
            district_analysis[district]['investment_value'] += prop.target_price
    
    # Calculate averages and display
    for district, data in district_analysis.items():
        data['avg_score'] /= data['count']
        
        print(f"{district}:")
        print(f"   Properties: {data['count']}")
        print(f"   Avg Score: {data['avg_score']:.1f}/10")
        print(f"   Investment Value: €{data['investment_value']:,.0f}")
        print()
    
    # Top investment opportunities
    print("🏆 TOP 10 INVESTMENT OPPORTUNITIES")
    print("-" * 50)
    
    top_opportunities = sorted(properties, key=lambda x: x.investment_score, reverse=True)[:10]
    
    for i, prop in enumerate(top_opportunities, 1):
        print(f"{i:2d}. {prop.neighborhood} ({prop.block_id}) - Score: {prop.investment_score:.1f}/10")
        print(f"    Action: {prop.recommended_action} | Strategy: {prop.investment_strategy}")
        print(f"    Price: €{prop.price:,} → Target: €{prop.target_price:,}")
        print(f"    ROI (24m): {prop.expected_roi_24m:.1%} | Risk: {prop.overall_risk}")
        print(f"    Energy: {prop.energy_class} | Tourism: {prop.tourism_score}/10")
        print()
    
    # Strategic insights
    print("🎯 STRATEGIC INSIGHTS")
    print("-" * 50)
    
    # Energy arbitrage opportunities
    energy_arbitrage = [p for p in properties if p.investment_strategy == "ENERGY_RETROFIT"]
    tourism_rental = [p for p in properties if p.investment_strategy == "TOURISM_RENTAL"]
    gentrification = [p for p in properties if p.investment_strategy == "GENTRIFICATION_PLAY"]
    
    print(f"⚡ Energy Arbitrage Opportunities: {len(energy_arbitrage)} properties")
    if energy_arbitrage:
        avg_roi = sum(p.expected_roi_24m for p in energy_arbitrage) / len(energy_arbitrage)
        total_value = sum(p.target_price for p in energy_arbitrage if p.recommended_action in ["IMMEDIATE_BUY", "STRONG_BUY"])
        print(f"   Average ROI (24m): {avg_roi:.1%}")
        print(f"   Investment Value: €{total_value:,.0f}")
    
    print(f"\n🏨 Tourism Rental Opportunities: {len(tourism_rental)} properties")
    if tourism_rental:
        avg_roi = sum(p.expected_roi_24m for p in tourism_rental) / len(tourism_rental)
        total_value = sum(p.target_price for p in tourism_rental if p.recommended_action in ["IMMEDIATE_BUY", "STRONG_BUY"])
        print(f"   Average ROI (24m): {avg_roi:.1%}")
        print(f"   Investment Value: €{total_value:,.0f}")
    
    print(f"\n🏗️ Gentrification Opportunities: {len(gentrification)} properties")
    if gentrification:
        avg_roi = sum(p.expected_roi_24m for p in gentrification) / len(gentrification)
        total_value = sum(p.target_price for p in gentrification if p.recommended_action in ["IMMEDIATE_BUY", "STRONG_BUY"])
        print(f"   Average ROI (24m): {avg_roi:.1%}")
        print(f"   Investment Value: €{total_value:,.0f}")

async def generate_detailed_reports(properties):
    """Generate detailed investment reports"""
    
    print("\n📋 Generating detailed investment reports...")
    
    # Convert properties to dictionary format for report generator
    properties_data = []
    for prop in properties:
        properties_data.append({
            'property_id': prop.property_id,
            'property_url': prop.url,
            'neighborhood': prop.neighborhood,
            'block_id': prop.block_id,
            'price': prop.price,
            'sqm': prop.sqm,
            'energy_class': prop.energy_class,
            'investment_score': prop.investment_score,
            'investment_grade': 'A+' if prop.investment_score >= 9 else 'A' if prop.investment_score >= 8 else 'B+',
            'risk_level': prop.overall_risk,
            'estimated_roi': prop.expected_roi_24m,
            'monthly_rental_yield': prop.rental_yield_estimate / 12,
            'break_even_months': int(1 / (prop.rental_yield_estimate / 12)) if prop.rental_yield_estimate > 0 else 24,
            'five_year_appreciation': prop.appreciation_potential * 5,
            'strategy': prop.investment_strategy,
            'recommended_action': prop.recommended_action,
            'target_price': prop.target_price,
            'max_offer_price': prop.max_bid,
            'current_value_per_sqm': prop.price_per_sqm,
            'post_improvement_value_per_sqm': prop.post_renovation_value / prop.sqm,
            'improvement_cost': prop.renovation_cost_estimate,
            'net_value_increase': prop.post_renovation_value - prop.price,
            'comparable_sales_median': prop.price_per_sqm,
            'days_on_market_average': prop.days_on_market,
            'market_trend': prop.price_trend,
            'competition_level': prop.market_activity,
            'market_risk': prop.market_risk,
            'liquidity_risk': prop.liquidity_risk,
            'renovation_risk': prop.renovation_risk,
            'regulatory_risk': 'MEDIUM',
            'overall_risk_score': {'LOW': 3, 'MEDIUM': 6, 'HIGH': 9}.get(prop.overall_risk, 6),
            'optimal_purchase_window': 'IMMEDIATE_3_MONTHS' if prop.recommended_action == 'IMMEDIATE_BUY' else 'WITHIN_6_MONTHS',
            'recommended_hold_period': '18_24_MONTHS',
            'optimal_exit_window': 'POST_IMPROVEMENT'
        })
    
    # Generate reports
    try:
        report_generator = InvestmentReportGenerator(output_dir="reports/athens_center")
        report_paths = report_generator.generate_all_reports(properties_data)
        
        print("✅ Investment reports generated:")
        for report_type, path in report_paths.items():
            print(f"   {report_type}: {path}")
    
    except Exception as e:
        print(f"⚠️ Report generation failed: {e}")
        print("   Property data analysis completed successfully")

if __name__ == "__main__":
    # Run the Athens center blocks search
    asyncio.run(search_athens_center_blocks())