#!/usr/bin/env python3
"""
🔍 Data Authenticity Verification - Comprehensive Analysis
Verify the authenticity of all 987 properties claimed in the analysis
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAuthenticityVerifier:
    """Comprehensive verification of property data authenticity"""
    
    def __init__(self):
        self.verification_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.project_root = Path(__file__).parent.parent
        
        logger.info("🔍 Data Authenticity Verification - Comprehensive Analysis")
        logger.info(f"📅 Verification ID: {self.verification_timestamp}")
    
    def load_all_data_files(self) -> Dict[str, Any]:
        """Load and analyze all data files in the project"""
        
        logger.info("📊 Loading All Data Files...")
        
        all_files_analysis = {
            'files_found': [],
            'total_properties': 0,
            'properties_by_file': {},
            'data_quality_analysis': {},
            'authenticity_indicators': {}
        }
        
        # Search directories for data files
        search_dirs = [
            self.project_root / "data/processed",
            self.project_root / "data/raw",
            self.project_root / "reports"
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            # Find all JSON files
            json_files = list(search_dir.glob("*.json"))
            
            for file_path in json_files:
                try:
                    logger.info(f"🔍 Analyzing: {file_path.name}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    file_analysis = self._analyze_single_file(file_path, data)
                    
                    all_files_analysis['files_found'].append(file_path.name)
                    all_files_analysis['properties_by_file'][file_path.name] = file_analysis
                    all_files_analysis['total_properties'] += file_analysis['property_count']
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error analyzing {file_path}: {e}")
                    continue
        
        logger.info(f"📊 Analysis Complete:")
        logger.info(f"   📁 Files Analyzed: {len(all_files_analysis['files_found'])}")
        logger.info(f"   🏠 Total Properties Found: {all_files_analysis['total_properties']}")
        
        return all_files_analysis
    
    def _analyze_single_file(self, file_path: Path, data: Any) -> Dict[str, Any]:
        """Analyze a single data file for authenticity indicators"""
        
        file_analysis = {
            'file_name': file_path.name,
            'file_size_mb': file_path.stat().st_size / (1024 * 1024),
            'property_count': 0,
            'data_structure': 'unknown',
            'authenticity_score': 0.0,
            'authenticity_indicators': [],
            'synthetic_patterns': [],
            'sample_properties': []
        }
        
        # Determine data structure and extract properties
        properties = []
        
        if isinstance(data, list):
            properties = data
            file_analysis['data_structure'] = 'list'
        elif isinstance(data, dict):
            if 'properties' in data:
                properties = data['properties']
                file_analysis['data_structure'] = 'object_with_properties'
            elif 'data' in data:
                properties = data['data'] if isinstance(data['data'], list) else [data['data']]
                file_analysis['data_structure'] = 'object_with_data'
            elif any(key in data for key in ['price', 'sqm', 'title', 'url']):
                properties = [data]
                file_analysis['data_structure'] = 'single_property'
            else:
                # Check if it contains metadata about properties
                if 'total_properties' in data or 'authentic_properties' in data:
                    file_analysis['data_structure'] = 'metadata_only'
                    file_analysis['property_count'] = data.get('total_properties', 0)
                    return file_analysis
        
        file_analysis['property_count'] = len(properties)
        
        # Analyze properties for authenticity
        if properties:
            authenticity_analysis = self._analyze_properties_authenticity(properties)
            file_analysis.update(authenticity_analysis)
        
        return file_analysis
    
    def _analyze_properties_authenticity(self, properties: List[Dict]) -> Dict[str, Any]:
        """Analyze properties for authenticity indicators"""
        
        analysis = {
            'authenticity_score': 0.0,
            'authenticity_indicators': [],
            'synthetic_patterns': [],
            'sample_properties': []
        }
        
        if not properties:
            return analysis
        
        # Take sample of properties for detailed analysis
        sample_size = min(10, len(properties))
        sample_properties = properties[:sample_size]
        
        # Analyze for synthetic patterns
        synthetic_indicators = self._detect_synthetic_patterns(properties)
        analysis['synthetic_patterns'] = synthetic_indicators
        
        # Analyze for authentic indicators
        authentic_indicators = self._detect_authentic_indicators(properties)
        analysis['authenticity_indicators'] = authentic_indicators
        
        # Calculate authenticity score
        authenticity_score = len(authentic_indicators) * 0.1 - len(synthetic_indicators) * 0.2
        authenticity_score = max(0.0, min(1.0, authenticity_score + 0.5))  # Normalize to 0-1
        analysis['authenticity_score'] = authenticity_score
        
        # Store sample properties for review
        for prop in sample_properties:
            sample = {
                'title': prop.get('title', 'N/A')[:50],
                'price': prop.get('price'),
                'sqm': prop.get('sqm'),
                'url': prop.get('url', 'N/A'),
                'neighborhood': prop.get('neighborhood', 'N/A')
            }
            analysis['sample_properties'].append(sample)
        
        return analysis
    
    def _detect_synthetic_patterns(self, properties: List[Dict]) -> List[str]:
        """Detect patterns that indicate synthetic/generated data"""
        
        synthetic_patterns = []
        
        if not properties:
            return synthetic_patterns
        
        # Check for repeated synthetic values
        prices = [p.get('price') for p in properties if p.get('price')]
        sqms = [p.get('sqm') for p in properties if p.get('sqm')]
        titles = [p.get('title', '') for p in properties if p.get('title')]
        
        # Known synthetic price patterns
        synthetic_prices = {740.0, 3000.0, 740, 3000, 100000.0, 250000.0, 500000.0, 1000000.0}
        price_matches = sum(1 for price in prices if price in synthetic_prices)
        if price_matches > len(prices) * 0.1:  # More than 10%
            synthetic_patterns.append(f"Synthetic price patterns: {price_matches}/{len(prices)} properties")
        
        # Known synthetic SQM patterns
        synthetic_sqms = {63.0, 270.0, 63, 270, 100.0, 150.0, 200.0}
        sqm_matches = sum(1 for sqm in sqms if sqm in synthetic_sqms)
        if sqm_matches > len(sqms) * 0.1:
            synthetic_patterns.append(f"Synthetic SQM patterns: {sqm_matches}/{len(sqms)} properties")
        
        # Check for generic/template titles
        generic_titles = ['Property', 'Listing', 'Advertisement', 'Sample', 'Test', 'Example', 'Demo']
        generic_title_count = sum(1 for title in titles if any(generic in title for generic in generic_titles))
        if generic_title_count > len(titles) * 0.05:  # More than 5%
            synthetic_patterns.append(f"Generic titles: {generic_title_count}/{len(titles)} properties")
        
        # Check for unrealistic price ranges
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            if min_price < 1000 or max_price > 50000000:  # Unrealistic ranges
                synthetic_patterns.append(f"Unrealistic price range: €{min_price:,} - €{max_price:,}")
        
        # Check for perfect round numbers (indication of generation)
        if prices:
            round_prices = sum(1 for price in prices if price % 10000 == 0 and price > 50000)
            if round_prices > len(prices) * 0.3:  # More than 30% are round numbers
                synthetic_patterns.append(f"Too many round prices: {round_prices}/{len(prices)} properties")
        
        # Check for duplicate entries
        if len(properties) > 1:
            # Check for duplicate URLs
            urls = [p.get('url') for p in properties if p.get('url')]
            unique_urls = set(urls)
            if len(urls) > 0 and len(unique_urls) < len(urls) * 0.95:  # Less than 95% unique
                duplicates = len(urls) - len(unique_urls)
                synthetic_patterns.append(f"Duplicate URLs detected: {duplicates} duplicates")
        
        return synthetic_patterns
    
    def _detect_authentic_indicators(self, properties: List[Dict]) -> List[str]:
        """Detect patterns that indicate authentic real data"""
        
        authentic_indicators = []
        
        if not properties:
            return authentic_indicators
        
        # Check for authentic URL patterns
        urls = [p.get('url', '') for p in properties if p.get('url')]
        spitogatos_urls = sum(1 for url in urls if 'spitogatos.gr' in url and '/property/' in url)
        if spitogatos_urls > len(urls) * 0.8:  # More than 80% are Spitogatos URLs
            authentic_indicators.append(f"Authentic Spitogatos URLs: {spitogatos_urls}/{len(urls)}")
        
        # Check for realistic price distribution
        prices = [p.get('price') for p in properties if p.get('price')]
        if prices and len(prices) > 10:
            # Check if prices follow realistic distribution
            price_std = pd.Series(prices).std()
            price_mean = pd.Series(prices).mean()
            if price_std / price_mean > 0.3:  # Reasonable variation
                authentic_indicators.append(f"Realistic price variation (CV: {price_std/price_mean:.2f})")
        
        # Check for authentic Greek neighborhoods
        neighborhoods = [p.get('neighborhood', '') for p in properties if p.get('neighborhood')]
        greek_neighborhoods = ['Exarchia', 'Syntagma', 'Psirri', 'Kolonaki', 'Pangrati', 'Plaka', 'Monastiraki']
        greek_matches = sum(1 for n in neighborhoods if any(greek in n for greek in greek_neighborhoods))
        if greek_matches > 0:
            authentic_indicators.append(f"Greek neighborhoods: {greek_matches} properties")
        
        # Check for realistic SQM distribution
        sqms = [p.get('sqm') for p in properties if p.get('sqm')]
        if sqms and len(sqms) > 10:
            sqm_series = pd.Series(sqms)
            if 20 <= sqm_series.median() <= 300:  # Realistic apartment sizes
                authentic_indicators.append(f"Realistic property sizes (median: {sqm_series.median():.0f}m²)")
        
        # Check for property ID patterns (should be varied)
        prop_ids = [p.get('property_id', '') for p in properties if p.get('property_id')]
        if len(prop_ids) > 10 and len(set(prop_ids)) == len(prop_ids):  # All unique
            authentic_indicators.append(f"Unique property IDs: {len(prop_ids)} properties")
        
        # Check for extraction timestamps (indicates recent scraping)
        timestamps = [p.get('source_timestamp') or p.get('timestamp') for p in properties if p.get('source_timestamp') or p.get('timestamp')]
        if timestamps:
            authentic_indicators.append(f"Extraction timestamps present: {len(timestamps)} properties")
        
        # Check for HTML source hashes (indicates real scraping)
        html_hashes = [p.get('html_source_hash') for p in properties if p.get('html_source_hash')]
        if html_hashes and len(set(html_hashes)) > len(html_hashes) * 0.8:  # Mostly unique
            authentic_indicators.append(f"Unique HTML source hashes: {len(html_hashes)} properties")
        
        return authentic_indicators
    
    def generate_authenticity_report(self, files_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive authenticity report"""
        
        logger.info("📋 Generating Authenticity Report...")
        
        # Calculate overall statistics
        total_files = len(files_analysis['files_found'])
        total_properties = files_analysis['total_properties']
        
        # Analyze authenticity across all files
        high_authenticity_files = []
        medium_authenticity_files = []
        low_authenticity_files = []
        suspicious_files = []
        
        for file_name, file_data in files_analysis['properties_by_file'].items():
            auth_score = file_data.get('authenticity_score', 0)
            
            if auth_score >= 0.7:
                high_authenticity_files.append((file_name, auth_score))
            elif auth_score >= 0.5:
                medium_authenticity_files.append((file_name, auth_score))
            elif auth_score >= 0.3:
                low_authenticity_files.append((file_name, auth_score))
            else:
                suspicious_files.append((file_name, auth_score))
        
        # Count authentic properties
        authentic_property_count = 0
        for file_data in files_analysis['properties_by_file'].values():
            if file_data.get('authenticity_score', 0) >= 0.6:
                authentic_property_count += file_data.get('property_count', 0)
        
        # Generate final verdict
        authenticity_percentage = (authentic_property_count / max(total_properties, 1)) * 100
        
        if authenticity_percentage >= 90:
            overall_verdict = "HIGHLY AUTHENTIC"
            verdict_confidence = "High"
        elif authenticity_percentage >= 70:
            overall_verdict = "MOSTLY AUTHENTIC"
            verdict_confidence = "Medium-High"
        elif authenticity_percentage >= 50:
            overall_verdict = "MIXED AUTHENTICITY"
            verdict_confidence = "Medium"
        elif authenticity_percentage >= 30:
            overall_verdict = "QUESTIONABLE AUTHENTICITY"
            verdict_confidence = "Low"
        else:
            overall_verdict = "LIKELY SYNTHETIC/GENERATED"
            verdict_confidence = "Very Low"
        
        authenticity_report = {
            'report_metadata': {
                'verification_timestamp': self.verification_timestamp,
                'total_files_analyzed': total_files,
                'total_properties_claimed': 987,
                'total_properties_found': total_properties,
                'discrepancy': 987 - total_properties
            },
            'authenticity_assessment': {
                'overall_verdict': overall_verdict,
                'authenticity_percentage': authenticity_percentage,
                'authentic_property_count': authentic_property_count,
                'verdict_confidence': verdict_confidence
            },
            'file_analysis': {
                'high_authenticity_files': high_authenticity_files,
                'medium_authenticity_files': medium_authenticity_files,
                'low_authenticity_files': low_authenticity_files,
                'suspicious_files': suspicious_files
            },
            'detailed_findings': {
                'files_analysis': files_analysis['properties_by_file']
            },
            'recommendations': self._generate_authenticity_recommendations(
                authenticity_percentage, total_properties, files_analysis
            )
        }
        
        return authenticity_report
    
    def _generate_authenticity_recommendations(self, auth_percentage: float, 
                                             total_properties: int, files_analysis: Dict) -> List[str]:
        """Generate recommendations based on authenticity analysis"""
        
        recommendations = []
        
        if auth_percentage >= 90:
            recommendations.append("✅ Data appears highly authentic - proceed with confidence")
            recommendations.append("📊 Consider this a strong foundation for business decisions")
        elif auth_percentage >= 70:
            recommendations.append("✅ Data is mostly authentic with some concerns")
            recommendations.append("🔍 Review low-authenticity files for data quality issues")
        elif auth_percentage >= 50:
            recommendations.append("⚠️ Mixed authenticity - proceed with caution")
            recommendations.append("🧹 Data cleaning and validation recommended")
        else:
            recommendations.append("❌ Significant authenticity concerns detected")
            recommendations.append("🚨 Data verification and re-collection recommended")
        
        if total_properties < 987:
            shortage = 987 - total_properties
            recommendations.append(f"📉 Property count discrepancy: {shortage} properties missing from claimed 987")
        
        # Check for suspicious patterns
        suspicious_files = [f for f, data in files_analysis['properties_by_file'].items() 
                          if data.get('authenticity_score', 1) < 0.3]
        if suspicious_files:
            recommendations.append(f"🔍 Review suspicious files: {', '.join(suspicious_files)}")
        
        return recommendations
    
    def save_authenticity_report(self, report: Dict[str, Any]):
        """Save authenticity verification report"""
        
        # Create analysis directory
        analysis_dir = self.project_root / "analysis"
        analysis_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        json_file = analysis_dir / f'data_authenticity_verification_{self.verification_timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Create markdown summary
        markdown_content = self._create_authenticity_markdown(report)
        markdown_file = analysis_dir / f'Data_Authenticity_Report_{self.verification_timestamp}.md'
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"💾 Authenticity report saved:")
        logger.info(f"   📄 JSON: {json_file}")
        logger.info(f"   📝 Report: {markdown_file}")
    
    def _create_authenticity_markdown(self, report: Dict[str, Any]) -> str:
        """Create markdown authenticity report"""
        
        metadata = report['report_metadata']
        assessment = report['authenticity_assessment']
        file_analysis = report['file_analysis']
        
        markdown = f"""# 🔍 Data Authenticity Verification Report

**Verification Date:** {metadata['verification_timestamp']}  
**Files Analyzed:** {metadata['total_files_analyzed']}  
**Properties Claimed:** {metadata['total_properties_claimed']}  
**Properties Found:** {metadata['total_properties_found']}

## 🎯 Overall Assessment

### Final Verdict: {assessment['overall_verdict']}
- **Authenticity Percentage:** {assessment['authenticity_percentage']:.1f}%
- **Authentic Properties:** {assessment['authentic_property_count']} / {metadata['total_properties_found']}
- **Confidence Level:** {assessment['verdict_confidence']}

"""
        
        if metadata['discrepancy'] != 0:
            markdown += f"⚠️ **Property Count Discrepancy:** {abs(metadata['discrepancy'])} properties {'missing' if metadata['discrepancy'] > 0 else 'excess'}\n\n"
        
        markdown += "## 📊 File Analysis\n\n"
        
        if file_analysis['high_authenticity_files']:
            markdown += "### ✅ High Authenticity Files\n"
            for file_name, score in file_analysis['high_authenticity_files']:
                markdown += f"- **{file_name}** (Score: {score:.2f})\n"
            markdown += "\n"
        
        if file_analysis['medium_authenticity_files']:
            markdown += "### 📊 Medium Authenticity Files\n"
            for file_name, score in file_analysis['medium_authenticity_files']:
                markdown += f"- **{file_name}** (Score: {score:.2f})\n"
            markdown += "\n"
        
        if file_analysis['low_authenticity_files']:
            markdown += "### ⚠️ Low Authenticity Files\n"
            for file_name, score in file_analysis['low_authenticity_files']:
                markdown += f"- **{file_name}** (Score: {score:.2f})\n"
            markdown += "\n"
        
        if file_analysis['suspicious_files']:
            markdown += "### 🚨 Suspicious Files\n"
            for file_name, score in file_analysis['suspicious_files']:
                markdown += f"- **{file_name}** (Score: {score:.2f})\n"
            markdown += "\n"
        
        markdown += "## 💡 Recommendations\n\n"
        for recommendation in report['recommendations']:
            markdown += f"- {recommendation}\n"
        
        markdown += """
---

*Authenticity verification powered by ATHintel Enhanced 2025 Platform*
"""
        
        return markdown
    
    def print_authenticity_summary(self, report: Dict[str, Any]):
        """Print authenticity verification summary"""
        
        logger.info("=" * 80)
        logger.info("🔍 DATA AUTHENTICITY VERIFICATION COMPLETE")
        logger.info("=" * 80)
        
        metadata = report['report_metadata']
        assessment = report['authenticity_assessment']
        
        logger.info("📊 VERIFICATION RESULTS:")
        logger.info(f"   📁 Files Analyzed: {metadata['total_files_analyzed']}")
        logger.info(f"   🏠 Properties Claimed: {metadata['total_properties_claimed']}")
        logger.info(f"   🏠 Properties Found: {metadata['total_properties_found']}")
        
        if metadata['discrepancy'] != 0:
            logger.info(f"   ⚠️ Discrepancy: {abs(metadata['discrepancy'])} properties {'missing' if metadata['discrepancy'] > 0 else 'excess'}")
        
        logger.info("🎯 AUTHENTICITY ASSESSMENT:")
        logger.info(f"   📊 Overall Verdict: {assessment['overall_verdict']}")
        logger.info(f"   📈 Authenticity: {assessment['authenticity_percentage']:.1f}%")
        logger.info(f"   ✅ Authentic Properties: {assessment['authentic_property_count']}")
        logger.info(f"   🎯 Confidence: {assessment['verdict_confidence']}")
        
        logger.info("💡 KEY RECOMMENDATIONS:")
        for rec in report['recommendations'][:3]:
            logger.info(f"   {rec}")
        
        logger.info("=" * 80)

# Main execution
def main():
    """Execute comprehensive authenticity verification"""
    
    verifier = DataAuthenticityVerifier()
    
    # Load and analyze all data files
    files_analysis = verifier.load_all_data_files()
    
    # Generate authenticity report
    authenticity_report = verifier.generate_authenticity_report(files_analysis)
    
    # Save report
    verifier.save_authenticity_report(authenticity_report)
    
    # Print summary
    verifier.print_authenticity_summary(authenticity_report)
    
    return authenticity_report

if __name__ == "__main__":
    result = main()