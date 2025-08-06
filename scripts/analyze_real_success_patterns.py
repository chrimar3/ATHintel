#!/usr/bin/env python3
"""
🔍 REAL SUCCESS PATTERN ANALYZER
Analyzes your actual 203 successful properties to extract optimal scaling patterns

This script processes your real data to provide actionable insights for scaling:
- Property ID distribution and patterns
- Neighborhood success rates
- Price/SQM ranges that work best
- Optimal batch sizes based on actual performance
- Recommended ID ranges for maximum success
"""

import json
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_real_success_patterns():
    """Analyze real success patterns from your actual data"""
    
    logger.info("🔍 Analyzing real success patterns from your authenticated properties...")
    
    # Load your actual successful data
    data_files = [
        'data/processed/scalable_athens_consolidated_scalable_300_20250806_103412.json',
        'data/processed/parallel_batch_consolidated_parallel_batch_10x50_20250806_105407_20250806_110243.json'
    ]
    
    all_properties = []
    
    for file_path in data_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_properties.extend(data)
                        logger.info(f"✅ Loaded {len(data)} properties from {file_path}")
                    else:
                        logger.warning(f"⚠️ Unexpected data format in {file_path}")
            except Exception as e:
                logger.error(f"❌ Error loading {file_path}: {e}")
        else:
            logger.warning(f"⚠️ File not found: {file_path}")
    
    if not all_properties:
        logger.error("❌ No property data found. Please check your data files.")
        return None
    
    # Extract successful properties (those with complete data)
    successful_properties = []
    for prop in all_properties:
        if all([
            prop.get('url'),
            prop.get('price'),
            prop.get('sqm'),
            prop.get('energy_class')
        ]):
            successful_properties.append(prop)
    
    logger.info(f"📊 Found {len(successful_properties)} properties with complete data")
    
    # Analyze patterns
    analysis = analyze_property_patterns(successful_properties)
    
    # Generate recommendations
    recommendations = generate_scaling_recommendations(analysis, successful_properties)
    
    # Save analysis results
    save_analysis_results(analysis, recommendations)
    
    return analysis, recommendations

def analyze_property_patterns(properties):
    """Analyze patterns in successful properties"""
    
    analysis = {}
    
    # Extract property IDs from URLs
    property_ids = []
    for prop in properties:
        url = prop.get('url', '')
        match = re.search(r'/property/(\d+)', url)
        if match:
            property_ids.append(int(match.group(1)))
    
    if property_ids:
        # ID Pattern Analysis
        analysis['property_ids'] = {
            'count': len(property_ids),
            'min': min(property_ids),
            'max': max(property_ids),
            'mean': np.mean(property_ids),
            'median': np.median(property_ids),
            'std': np.std(property_ids)
        }
        
        # Prefix Analysis
        prefixes_4 = [str(pid)[:4] for pid in property_ids]
        prefixes_6 = [str(pid)[:6] for pid in property_ids]
        
        analysis['prefixes'] = {
            '4_digit': Counter(prefixes_4).most_common(10),
            '6_digit': Counter(prefixes_6).most_common(15)
        }
        
        # Range Analysis (divide into buckets)
        id_range = max(property_ids) - min(property_ids)
        bucket_size = id_range // 20  # 20 buckets
        bucket_counts = Counter()
        
        for pid in property_ids:
            bucket = (pid - min(property_ids)) // bucket_size
            bucket_counts[bucket] += 1
        
        analysis['id_ranges'] = {
            'bucket_size': bucket_size,
            'hotspots': bucket_counts.most_common(10)
        }
    
    # Neighborhood Analysis
    neighborhoods = [prop.get('neighborhood', 'Unknown') for prop in properties if prop.get('neighborhood')]
    analysis['neighborhoods'] = Counter(neighborhoods).most_common(20)
    
    # Price Analysis
    prices = [prop.get('price') for prop in properties if prop.get('price')]
    if prices:
        analysis['prices'] = {
            'count': len(prices),
            'min': min(prices),
            'max': max(prices),
            'mean': np.mean(prices),
            'median': np.median(prices),
            'std': np.std(prices)
        }
    
    # SQM Analysis
    sqms = [prop.get('sqm') for prop in properties if prop.get('sqm')]
    if sqms:
        analysis['sqm'] = {
            'count': len(sqms),
            'min': min(sqms),
            'max': max(sqms),
            'mean': np.mean(sqms),
            'median': np.median(sqms),
            'std': np.std(sqms)
        }
    
    # Energy Class Analysis
    energy_classes = [prop.get('energy_class') for prop in properties if prop.get('energy_class')]
    analysis['energy_classes'] = Counter(energy_classes).most_common()
    
    # Strategy Analysis (if available)
    strategies = [prop.get('search_strategy', 'unknown') for prop in properties if prop.get('search_strategy')]
    if strategies:
        analysis['strategies'] = Counter(strategies).most_common()
    
    # Timestamp Analysis (to understand timing patterns)
    timestamps = [prop.get('timestamp') for prop in properties if prop.get('timestamp')]
    if timestamps:
        analysis['collection_timing'] = {
            'total_sessions': len(set([ts[:10] for ts in timestamps])),  # Unique dates
            'first_collection': min(timestamps),
            'last_collection': max(timestamps)
        }
    
    return analysis

def generate_scaling_recommendations(analysis, properties):
    """Generate actionable scaling recommendations"""
    
    recommendations = {
        'immediate_actions': [],
        'optimal_ranges': [],
        'batch_strategies': [],
        'success_predictions': {}
    }
    
    # ID Range Recommendations
    if 'property_ids' in analysis:
        id_stats = analysis['property_ids']
        
        # High-confidence ranges based on statistical analysis
        mean_id = int(id_stats['mean'])
        std_id = int(id_stats['std'])
        
        recommended_ranges = [
            (mean_id - std_id, mean_id + std_id, 'High Confidence'),
            (id_stats['min'] - 100000, id_stats['min'], 'Pre-successful Range'),
            (id_stats['max'], id_stats['max'] + 200000, 'Post-successful Range')
        ]
        
        # Add hotspot ranges
        if 'id_ranges' in analysis:
            bucket_size = analysis['id_ranges']['bucket_size']
            min_id = id_stats['min']
            
            for bucket, count in analysis['id_ranges']['hotspots'][:5]:
                start_id = min_id + (bucket * bucket_size)
                end_id = start_id + bucket_size
                confidence = 'High' if count > 3 else 'Medium'
                recommended_ranges.append((start_id, end_id, f'{confidence} (Hotspot: {count} properties)'))
        
        recommendations['optimal_ranges'] = recommended_ranges
    
    # Prefix-based recommendations
    if 'prefixes' in analysis:
        prefix_recs = []
        for prefix, count in analysis['prefixes']['4_digit'][:5]:
            confidence = 'High' if count >= 5 else 'Medium' if count >= 3 else 'Low'
            prefix_recs.append(f"Target {prefix}xxxxxx range ({count} successes, {confidence} confidence)")
        recommendations['prefix_strategies'] = prefix_recs
    
    # Neighborhood recommendations
    if 'neighborhoods' in analysis:
        top_neighborhoods = [hood for hood, count in analysis['neighborhoods'][:10]]
        recommendations['target_neighborhoods'] = top_neighborhoods
    
    # Batch size recommendations based on actual success rates
    total_properties = len(properties)
    if total_properties > 0:
        # Estimate success rate based on your data
        estimated_success_rate = total_properties / 1000  # Rough estimate
        
        # Optimal batch sizes based on success rate
        if estimated_success_rate > 0.15:
            recommendations['optimal_batch_size'] = 50
        elif estimated_success_rate > 0.10:
            recommendations['optimal_batch_size'] = 25
        else:
            recommendations['optimal_batch_size'] = 15
        
        recommendations['success_predictions'] = {
            'estimated_success_rate': f"{estimated_success_rate:.1%}",
            'properties_per_1000_attempts': int(estimated_success_rate * 1000),
            'recommended_daily_target': 100 if estimated_success_rate > 0.1 else 50
        }
    
    # Immediate action recommendations
    recommendations['immediate_actions'] = [
        f"Focus on property ID ranges: {analysis.get('property_ids', {}).get('min', 'N/A')} - {analysis.get('property_ids', {}).get('max', 'N/A')}",
        f"Target top neighborhoods: {', '.join([hood for hood, _ in analysis.get('neighborhoods', [])[:5]])}",
        f"Use batch size: {recommendations.get('optimal_batch_size', 25)}",
        "Implement duplicate detection before scaling",
        "Setup Athens Center geo-filtering validation"
    ]
    
    return recommendations

def save_analysis_results(analysis, recommendations):
    """Save analysis results to files"""
    
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    
    # Save detailed analysis
    analysis_file = f'real_success_pattern_analysis_{timestamp}.json'
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # Save recommendations
    rec_file = f'scaling_recommendations_{timestamp}.json'
    with open(rec_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, indent=2, default=str)
    
    logger.info(f"💾 Analysis saved to: {analysis_file}")
    logger.info(f"💾 Recommendations saved to: {rec_file}")
    
    # Create summary report
    create_summary_report(analysis, recommendations, timestamp)

def create_summary_report(analysis, recommendations, timestamp):
    """Create a human-readable summary report"""
    
    report_file = f'SUCCESS_PATTERN_SUMMARY_{timestamp}.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 🏛️ REAL SUCCESS PATTERN ANALYSIS SUMMARY\n\n")
        f.write(f"**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Property ID Analysis
        if 'property_ids' in analysis:
            id_stats = analysis['property_ids']
            f.write("## 📊 Property ID Analysis\n\n")
            f.write(f"- **Total Successful Properties:** {id_stats['count']}\n")
            f.write(f"- **ID Range:** {id_stats['min']:,} - {id_stats['max']:,}\n")
            f.write(f"- **Mean ID:** {int(id_stats['mean']):,}\n")
            f.write(f"- **Median ID:** {int(id_stats['median']):,}\n\n")
        
        # Top Prefixes
        if 'prefixes' in analysis:
            f.write("## 🎯 Most Successful Prefixes\n\n")
            for prefix, count in analysis['prefixes']['4_digit'][:5]:
                f.write(f"- **{prefix}xxxxxx**: {count} properties\n")
            f.write("\n")
        
        # Top Neighborhoods
        if 'neighborhoods' in analysis:
            f.write("## 🏘️ Top Neighborhoods\n\n")
            for neighborhood, count in analysis['neighborhoods'][:10]:
                f.write(f"- **{neighborhood}**: {count} properties\n")
            f.write("\n")
        
        # Recommendations
        f.write("## 🚀 Scaling Recommendations\n\n")
        f.write("### Immediate Actions\n")
        for action in recommendations['immediate_actions']:
            f.write(f"- {action}\n")
        f.write("\n")
        
        if 'optimal_ranges' in recommendations:
            f.write("### Recommended ID Ranges\n")
            for start, end, confidence in recommendations['optimal_ranges'][:5]:
                f.write(f"- **{int(start):,} - {int(end):,}** ({confidence})\n")
            f.write("\n")
        
        # Success Predictions
        if 'success_predictions' in recommendations:
            pred = recommendations['success_predictions']
            f.write("### Success Predictions\n")
            f.write(f"- **Estimated Success Rate:** {pred.get('estimated_success_rate', 'N/A')}\n")
            f.write(f"- **Properties per 1000 attempts:** {pred.get('properties_per_1000_attempts', 'N/A')}\n")
            f.write(f"- **Recommended daily target:** {pred.get('recommended_daily_target', 'N/A')} properties\n")
        
    logger.info(f"📄 Summary report saved to: {report_file}")

def main():
    """Main execution function"""
    try:
        analysis, recommendations = analyze_real_success_patterns()
        
        if analysis and recommendations:
            logger.info("\n" + "="*60)
            logger.info("🎯 ANALYSIS COMPLETE - KEY INSIGHTS:")
            logger.info("="*60)
            
            # Show key insights
            if 'property_ids' in analysis:
                id_stats = analysis['property_ids']
                logger.info(f"📊 Analyzed {id_stats['count']} successful properties")
                logger.info(f"🎯 ID Range: {id_stats['min']:,} - {id_stats['max']:,}")
                logger.info(f"📈 Mean: {int(id_stats['mean']):,}, Median: {int(id_stats['median']):,}")
            
            if 'prefixes' in analysis:
                top_prefix = analysis['prefixes']['4_digit'][0]
                logger.info(f"🏆 Top prefix: {top_prefix[0]}xxxx ({top_prefix[1]} properties)")
            
            if recommendations.get('optimal_batch_size'):
                logger.info(f"⚡ Recommended batch size: {recommendations['optimal_batch_size']}")
            
            logger.info("="*60)
            logger.info("✅ Ready to implement optimal scaling strategy!")
            
        else:
            logger.error("❌ Analysis failed. Please check your data files.")
            
    except Exception as e:
        logger.error(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()