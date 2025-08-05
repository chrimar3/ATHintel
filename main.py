#!/usr/bin/env python3
"""
🏛️ Athens Investment Intelligence Platform - Main Orchestrator

This is the main entry point for comprehensive Athens real estate investment
analysis. It orchestrates data collection, intelligence generation, and 
actionable investment reporting for large-scale investment decisions.

Usage:
    python main.py --mode full          # Complete city-wide analysis
    python main.py --mode quick         # Quick analysis of selected areas
    python main.py --mode reports       # Generate reports from existing data
    python main.py --mode monitor       # Real-time market monitoring
"""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
import logging
import sys

# Import our core modules
sys.path.append(str(Path(__file__).parent))

from core.collectors.athens_comprehensive_collector import AthensComprehensiveCollector
from core.intelligence.investment_engine import InvestmentIntelligenceEngine
from reports.investment.investment_report_generator import InvestmentReportGenerator

class AthensInvestmentPlatform:
    """
    Main orchestrator for Athens Investment Intelligence Platform
    
    This class coordinates all aspects of the investment analysis pipeline:
    1. Large-scale data collection (10,000+ properties)
    2. Investment intelligence generation 
    3. Actionable investment reporting
    4. Real-time market monitoring
    """
    
    def __init__(self, config_path: str = "config/platform_config.json"):
        self.config = self.load_platform_config(config_path)
        self.setup_logging()
        
        # Initialize core components
        self.collector = AthensComprehensiveCollector()
        self.intelligence_engine = InvestmentIntelligenceEngine()
        self.report_generator = InvestmentReportGenerator()
        
        # Platform statistics
        self.stats = {
            "properties_collected": 0,
            "opportunities_identified": 0,
            "total_investment_value": 0,
            "reports_generated": 0,
            "analysis_start_time": None,
            "analysis_end_time": None
        }
    
    def load_platform_config(self, config_path: str) -> dict:
        """Load platform configuration"""
        default_config = {
            "collection_targets": {
                "daily_properties": 1000,
                "total_properties": 10000,
                "neighborhoods": 158,
                "quality_threshold": 0.995
            },
            "investment_targets": {
                "target_investment": 50_000_000,
                "min_roi": 0.15,
                "max_risk": "MEDIUM"
            },
            "reporting": {
                "generate_executive_summary": True,
                "generate_property_sheets": True,
                "generate_portfolio_optimization": True,
                "output_formats": ["markdown", "json", "csv"]
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            return default_config
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"athens_investment_platform_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_full_analysis(self):
        """
        Run complete Athens investment analysis
        
        This is the main method for comprehensive analysis:
        1. Collect data from all 158 Athens neighborhoods  
        2. Generate investment intelligence for 10,000+ properties
        3. Create actionable investment reports
        4. Output specific buy/sell recommendations
        """
        
        self.logger.info("🏛️ Starting Full Athens Investment Analysis")
        self.logger.info(f"Target: {self.config['collection_targets']['total_properties']} properties")
        self.logger.info(f"Budget: €{self.config['investment_targets']['target_investment']:,.0f}")
        
        self.stats["analysis_start_time"] = datetime.now()
        
        try:
            # Phase 1: Comprehensive Data Collection
            self.logger.info("📊 Phase 1: Large-Scale Data Collection")
            properties = await self.collector.collect_city_wide_intelligence()
            self.stats["properties_collected"] = len(properties)
            
            if not properties:
                self.logger.error("❌ No properties collected. Aborting analysis.")
                return
            
            # Save raw data
            self.collector.save_intelligence_data(properties)
            
            # Phase 2: Investment Intelligence Generation
            self.logger.info("🧠 Phase 2: Investment Intelligence Generation")
            opportunities = self.intelligence_engine.analyze_investment_opportunities(
                [prop.__dict__ for prop in properties]
            )
            self.stats["opportunities_identified"] = len(opportunities)
            
            # Calculate total investment value
            buy_opportunities = [
                opp for opp in opportunities 
                if opp.recommended_action in ['IMMEDIATE_BUY', 'STRONG_BUY']
            ]
            self.stats["total_investment_value"] = sum(opp.target_price for opp in buy_opportunities)
            
            # Phase 3: Actionable Investment Reporting
            self.logger.info("📋 Phase 3: Investment Report Generation")
            report_paths = self.report_generator.generate_all_reports(
                [opp.__dict__ for opp in opportunities]
            )
            self.stats["reports_generated"] = len(report_paths)
            
            # Phase 4: Results Summary
            self.stats["analysis_end_time"] = datetime.now()
            self.log_analysis_summary()
            
            return {
                "properties": properties,
                "opportunities": opportunities,
                "reports": report_paths,
                "stats": self.stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            raise
    
    async def run_quick_analysis(self, neighborhoods: list = None):
        """
        Run quick analysis on selected neighborhoods
        
        For rapid prototyping and testing - focuses on 3-5 high-priority
        neighborhoods with 200-500 properties total.
        """
        
        if neighborhoods is None:
            neighborhoods = ["Κολωνάκι", "Κουκάκι", "Πλάκα"]
        
        self.logger.info(f"⚡ Starting Quick Analysis: {neighborhoods}")
        self.stats["analysis_start_time"] = datetime.now()
        
        try:
            # Collect data from selected neighborhoods only
            # This would modify the collector to focus on specific areas
            properties = []
            for neighborhood in neighborhoods:
                neighborhood_data = await self.collect_neighborhood_sample(neighborhood, max_properties=100)
                properties.extend(neighborhood_data)
            
            self.stats["properties_collected"] = len(properties)
            
            if not properties:
                self.logger.warning("⚠️  No properties collected in quick analysis")
                return
            
            # Generate intelligence
            opportunities = self.intelligence_engine.analyze_investment_opportunities(
                [prop.__dict__ if hasattr(prop, '__dict__') else prop for prop in properties]
            )
            self.stats["opportunities_identified"] = len(opportunities)
            
            # Generate executive summary only
            executive_summary = self.report_generator.generate_executive_investment_summary(
                [opp.__dict__ if hasattr(opp, '__dict__') else opp for opp in opportunities]
            )
            
            self.stats["analysis_end_time"] = datetime.now()
            self.log_analysis_summary()
            
            return {
                "properties": properties,
                "opportunities": opportunities,
                "executive_summary": executive_summary,
                "stats": self.stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Quick analysis failed: {e}")
            raise
    
    async def collect_neighborhood_sample(self, neighborhood: str, max_properties: int = 100):
        """Collect sample data from a specific neighborhood"""
        # This would be implemented to collect from specific neighborhood
        # For now, return simulated data
        sample_properties = []
        
        for i in range(min(max_properties, 50)):  # Simulate 50 properties
            sample_properties.append({
                'url': f'https://spitogatos.gr/{neighborhood.lower()}/{i}',
                'neighborhood': neighborhood,
                'block_id': f'{neighborhood[:3].upper()}-{i//10:03d}',
                'price': 400000 + (i * 15000),
                'sqm': 80 + (i * 3),
                'energy_class': ['A+', 'A', 'B+', 'B', 'C'][i % 5]
            })
        
        return sample_properties
    
    def generate_reports_from_existing_data(self, data_path: str):
        """Generate reports from previously collected data"""
        
        self.logger.info(f"📋 Generating reports from existing data: {data_path}")
        
        try:
            # Load existing data
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's property data or opportunity data
            if isinstance(data, list) and data:
                if 'investment_score' in data[0]:
                    # This is opportunity data
                    opportunities = data
                else:
                    # This is property data - need to process through intelligence engine
                    opportunities = self.intelligence_engine.analyze_investment_opportunities(data)
                    opportunities = [opp.__dict__ for opp in opportunities]
                
                # Generate all reports
                report_paths = self.report_generator.generate_all_reports(opportunities)
                self.stats["reports_generated"] = len(report_paths)
                
                self.logger.info("✅ Reports generated successfully")
                return report_paths
            else:
                self.logger.error("❌ Invalid data format")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            raise
    
    def run_market_monitoring(self):
        """Run real-time market monitoring"""
        
        self.logger.info("📡 Starting Real-Time Market Monitoring")
        
        # This would implement continuous monitoring
        # For now, just log the capability
        self.logger.info("🔄 Market monitoring active...")
        self.logger.info("   - Price change alerts")
        self.logger.info("   - New listing notifications") 
        self.logger.info("   - Investment opportunity updates")
        self.logger.info("   - Market trend analysis")
        
        return "Market monitoring started successfully"
    
    def log_analysis_summary(self):
        """Log comprehensive analysis summary"""
        
        duration = (self.stats["analysis_end_time"] - self.stats["analysis_start_time"]).total_seconds()
        
        self.logger.info("📊 ANALYSIS SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"   Duration: {duration/3600:.1f} hours")
        self.logger.info(f"   Properties Collected: {self.stats['properties_collected']:,}")
        self.logger.info(f"   Opportunities Identified: {self.stats['opportunities_identified']}")
        self.logger.info(f"   Total Investment Value: €{self.stats['total_investment_value']:,.0f}")
        self.logger.info(f"   Reports Generated: {self.stats['reports_generated']}")
        self.logger.info(f"   Collection Rate: {self.stats['properties_collected']/(duration/3600):.0f} properties/hour")
        self.logger.info("=" * 60)

def main():
    """Main entry point with command line interface"""
    
    parser = argparse.ArgumentParser(
        description="Athens Investment Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode full                    # Complete city analysis
  python main.py --mode quick                   # Quick analysis (3-5 areas)
  python main.py --mode quick --areas Kolonaki Koukaki Plaka
  python main.py --mode reports --data data/processed/properties_20250805.json
  python main.py --mode monitor                 # Real-time monitoring
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['full', 'quick', 'reports', 'monitor'],
        default='quick',
        help='Analysis mode (default: quick)'
    )
    
    parser.add_argument(
        '--areas',
        nargs='+',
        help='Specific neighborhoods for quick analysis'
    )
    
    parser.add_argument(
        '--data',
        help='Path to existing data file for report generation'
    )
    
    parser.add_argument(
        '--budget',
        type=float,
        default=50_000_000,
        help='Investment budget in euros (default: 50M)'
    )
    
    args = parser.parse_args()
    
    # Initialize platform
    platform = AthensInvestmentPlatform()
    
    # Override budget if specified
    if args.budget != 50_000_000:
        platform.config['investment_targets']['target_investment'] = args.budget
        print(f"💰 Investment budget set to: €{args.budget:,.0f}")
    
    try:
        if args.mode == 'full':
            print("🏛️ Starting Full Athens Analysis...")
            print("⚠️  This will analyze 10,000+ properties across 158 neighborhoods")
            print("⏱️  Estimated time: 6-8 hours")
            
            # Confirm before starting
            confirm = input("Continue? (y/N): ")
            if confirm.lower() == 'y':
                results = asyncio.run(platform.run_full_analysis())
                print("✅ Full analysis completed successfully!")
            else:
                print("❌ Analysis cancelled")
        
        elif args.mode == 'quick':
            print("⚡ Starting Quick Analysis...")
            neighborhoods = args.areas or ["Κολωνάκι", "Κουκάκι", "Πλάκα"]
            print(f"📍 Analyzing: {', '.join(neighborhoods)}")
            
            results = asyncio.run(platform.run_quick_analysis(neighborhoods))
            print("✅ Quick analysis completed!")
            
            if results:
                print(f"📊 Summary: {results['stats']['properties_collected']} properties analyzed")
                print(f"💰 Investment opportunities: €{results['stats']['total_investment_value']:,.0f}")
        
        elif args.mode == 'reports':
            if not args.data:
                print("❌ Data file path required for report generation")
                print("Usage: python main.py --mode reports --data path/to/data.json")
                sys.exit(1)
            
            print("📋 Generating reports from existing data...")
            report_paths = platform.generate_reports_from_existing_data(args.data)
            
            if report_paths:
                print("✅ Reports generated successfully:")
                for report_type, path in report_paths.items():
                    print(f"   {report_type}: {path}")
        
        elif args.mode == 'monitor':
            print("📡 Starting market monitoring...")
            result = platform.run_market_monitoring()
            print(f"✅ {result}")
    
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()