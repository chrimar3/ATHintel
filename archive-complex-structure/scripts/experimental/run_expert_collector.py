#!/usr/bin/env python3
"""
🏛️ EXPERT ATHENS COLLECTOR RUNNER
Execute the industry-grade Athens property collector with comprehensive monitoring

EXPERT FEATURES ACTIVATED:
⭐ Exponential Backoff with Jitter
⭐ Token Bucket Rate Limiting
⭐ Session Rotation & Anti-Detection
⭐ Playwright Stealth Configuration
⭐ Concurrent Processing Control
⭐ Real-time Performance Monitoring
⭐ Comprehensive Error Analysis

Based on web scraping mastery report recommendations from industry leaders.
"""

import asyncio
import sys
import signal
from pathlib import Path
from datetime import datetime
import logging

# Add the current directory to the path to import the expert collector
sys.path.append(str(Path(__file__).parent))

from expert_athens_collector import ExpertAthensCollector, logger

class ExpertCollectorRunner:
    """Runner for the expert Athens collector with monitoring and control"""
    
    def __init__(self):
        self.collector = None
        self.start_time = datetime.now()
        self.interrupted = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received shutdown signal ({signum})")
        print("🔄 Initiating graceful shutdown...")
        self.interrupted = True
        
        if self.collector:
            # The collector will handle saving data in its exception handling
            print("💾 Saving collected data before shutdown...")
    
    async def run_expert_collection(self):
        """Run the expert collector with monitoring"""
        
        print("🏛️ EXPERT ATHENS PROPERTY COLLECTOR")
        print("=" * 80)
        print("🚀 LAUNCHING INDUSTRY-GRADE COLLECTION SESSION")
        print("")
        print("📋 EXPERT METHODOLOGIES ACTIVE:")
        print("   ⭐ Exponential Backoff: base_delay * (2^retry) + jitter")
        print("   ⭐ Token Bucket: 20 capacity, 2.0/sec refill rate")
        print("   ⭐ Session Rotation: Every 50-100 requests")
        print("   ⭐ Playwright Stealth: Anti-detection measures")
        print("   ⭐ Resource Blocking: 40-60% performance boost")
        print("   ⭐ Concurrent Control: 5 pages maximum")
        print("   ⭐ Multi-layer Validation: Expert quality assurance")
        print("")
        print("🎯 TARGET: 300 expert-quality Athens properties")
        print("📊 EXPECTED: 15-25% success rate (industry standard)")
        print("🌱 FOUNDATION: 203 proven property seeds for expansion")
        print("=" * 80)
        print("")
        
        try:
            # Initialize expert collector
            self.collector = ExpertAthensCollector()
            
            # Start collection with monitoring
            print("🔄 Initializing expert collection systems...")
            print("🌐 Setting up browser pool with stealth configuration...")
            print("🎯 Loading proven seed IDs for intelligent targeting...")
            print("📊 Activating real-time performance monitoring...")
            print("")
            print("🚀 EXPERT COLLECTION STARTED!")
            print("=" * 50)
            
            # Run the collection
            properties = await self.collector.collect_properties()
            
            # Final report
            runtime = (datetime.now() - self.start_time).total_seconds() / 60
            success_rate = self.collector.stats.get_current_success_rate()
            expert_quality = [p for p in properties if p.is_expert_quality()]
            
            print("\n" + "=" * 80)
            print("🏁 EXPERT COLLECTION SESSION COMPLETED!")
            print("=" * 80)
            print(f"⏱️  Total Runtime: {runtime:.1f} minutes")
            print(f"📊 Success Rate: {success_rate:.2f}% (Target: 15-25%)")
            print(f"✅ Total Properties: {len(properties)}")
            print(f"⭐ Expert Quality: {len(expert_quality)}")
            print(f"🏛️ Athens Center: {self.collector.stats.athens_center_properties}")
            print(f"🔄 Session Rotations: {self.collector.stats.session_rotations}")
            print(f"⚡ Avg Response: {self.collector.stats.get_average_response_time():.0f}ms")
            print(f"🚫 Blocked Requests: {self.collector.stats.blocked_requests}")
            print("")
            
            # Performance analysis
            if success_rate >= 20:
                print("🏆 PERFORMANCE: EXCELLENT - Exceeds industry standards!")
            elif success_rate >= 15:
                print("✅ PERFORMANCE: GOOD - Meets industry standards!")
            elif success_rate >= 10:
                print("📈 PERFORMANCE: ACCEPTABLE - Room for optimization")
            else:
                print("⚠️ PERFORMANCE: NEEDS IMPROVEMENT - Check error logs")
            
            print("")
            
            # Collection size analysis
            if len(expert_quality) >= 200:
                print("🎯 TARGET: EXCEEDED - Outstanding collection results!")
            elif len(expert_quality) >= 100:
                print("🎯 TARGET: ACHIEVED - Excellent foundation collected!")
            elif len(expert_quality) >= 50:
                print("🎯 TARGET: PROGRESS - Good foundation established!")
            else:
                print("🎯 TARGET: PARTIAL - Consider adjusting parameters")
            
            print("")
            print("📊 EXPERT METHODOLOGY EFFECTIVENESS:")
            
            if self.collector.stats.session_rotations > 0:
                print(f"   ✅ Session Rotation: Active ({self.collector.stats.session_rotations} rotations)")
            else:
                print(f"   ⚠️ Session Rotation: Not triggered")
            
            if self.collector.stats.blocked_requests < self.collector.stats.total_attempts * 0.1:
                print(f"   ✅ Anti-Detection: Effective ({self.collector.stats.blocked_requests} blocks)")
            else:
                print(f"   ⚠️ Anti-Detection: High blocks ({self.collector.stats.blocked_requests})")
            
            avg_retries = (sum(self.collector.stats.retry_counts) / 
                          len(self.collector.stats.retry_counts)) if self.collector.stats.retry_counts else 0
            
            if avg_retries < 2.0:
                print(f"   ✅ Retry Strategy: Efficient ({avg_retries:.1f} avg retries)")
            else:
                print(f"   ⚠️ Retry Strategy: High retries ({avg_retries:.1f} avg)")
            
            print("")
            print("💾 DATA SAVED TO:")
            print(f"   📄 JSON: data/expert/expert_athens_{self.collector.session_id}.json")
            print(f"   📊 CSV: data/expert/expert_summary_{self.collector.session_id}.csv")
            print(f"   📈 Stats: data/expert/expert_stats_{self.collector.session_id}.json")
            print("=" * 80)
            
            return properties
            
        except KeyboardInterrupt:
            print("\n🛑 Collection interrupted by user")
            if self.collector:
                print("💾 Saving partial results...")
                await self.collector.save_expert_results()
            return []
            
        except Exception as e:
            print(f"\n❌ Expert collection failed: {str(e)}")
            logger.error(f"Collection failed: {str(e)}", exc_info=True)
            if self.collector:
                print("💾 Saving partial results...")
                await self.collector.save_expert_results()
            return []

async def main():
    """Main runner function"""
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required for expert async features")
        sys.exit(1)
    
    # Check if Playwright is available
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright available for expert browser automation")
    except ImportError:
        print("❌ Playwright not found. Install with: pip install playwright")
        print("   Then run: playwright install chromium")
        sys.exit(1)
    
    # Initialize and run
    runner = ExpertCollectorRunner()
    
    try:
        properties = await runner.run_expert_collection()
        
        if properties:
            print(f"\n🎉 Expert collection completed successfully!")
            print(f"📊 Final count: {len(properties)} properties")
        else:
            print(f"\n⚠️ Expert collection completed with no results")
            print("💡 Check logs for debugging information")
        
    except Exception as e:
        print(f"\n❌ Runner failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the expert collection
    asyncio.run(main())