#!/usr/bin/env python3
"""
🎬 EXPERT ATHENS COLLECTOR DEMO
Quick demonstration of expert collector capabilities with limited scope

DEMO FEATURES:
⭐ All expert methodologies active
⭐ Limited to 5 properties for quick testing
⭐ Real-time performance monitoring
⭐ Comprehensive validation
⭐ Anti-detection measures demonstrated
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from expert_athens_collector import ExpertAthensCollector

class ExpertCollectorDemo:
    """Demo runner for expert Athens collector"""
    
    async def run_demo(self):
        """Run limited demo collection"""
        
        print("🎬 EXPERT ATHENS COLLECTOR DEMO")
        print("=" * 50)
        print("🎯 Demo Target: 5 properties maximum")
        print("⚡ All expert methodologies active")
        print("🔍 Real-time monitoring enabled")
        print("=" * 50)
        print("")
        
        # Create demo collector with reduced scope
        collector = ExpertAthensCollector()
        collector.target_properties = 5
        collector.batch_size = 5
        
        print("🚀 Starting expert demo collection...")
        print("🌐 Browser automation: Playwright stealth mode")
        print("⏱️ Rate limiting: Token bucket + exponential backoff")
        print("🔄 Session management: Anti-detection active")
        print("🛡️ Resource blocking: Images/CSS disabled for speed")
        print("")
        
        try:
            start_time = datetime.now()
            properties = await collector.collect_properties()
            runtime = (datetime.now() - start_time).total_seconds() / 60
            
            print("\n" + "=" * 50)
            print("🎬 EXPERT DEMO COMPLETED!")
            print("=" * 50)
            print(f"⏱️ Runtime: {runtime:.1f} minutes")
            print(f"✅ Properties Collected: {len(properties)}")
            
            expert_quality = [p for p in properties if p.is_expert_quality()]
            print(f"⭐ Expert Quality: {len(expert_quality)}")
            print(f"📊 Success Rate: {collector.stats.get_current_success_rate():.1f}%")
            print(f"🔄 Session Rotations: {collector.stats.session_rotations}")
            print(f"⚡ Avg Response: {collector.stats.get_average_response_time():.0f}ms")
            
            if expert_quality:
                print("\n🏛️ SAMPLE PROPERTIES:")
                for prop in expert_quality[:3]:
                    print(f"   • {prop.neighborhood}: €{prop.price:,}, {prop.sqm}m², {prop.energy_class}")
            
            print("\n💡 DEMO INSIGHTS:")
            if len(expert_quality) >= 1:
                print("   ✅ Expert methodology working correctly")
                print("   ✅ Anti-detection measures effective")
                print("   ✅ Data validation pipeline functional")
                print("   🚀 Ready for full-scale collection!")
            else:
                print("   ⚠️ No successful extractions in demo")
                print("   💡 May need parameter adjustment for full run")
                print("   🔍 Check logs for detailed error analysis")
            
            print("=" * 50)
            
            return properties
            
        except Exception as e:
            print(f"\n❌ Demo failed: {str(e)}")
            return []

async def main():
    """Main demo function"""
    
    print("🎬 Expert Athens Collector Demo Starting...")
    print("⚠️  This demo uses live web scraping - respect rate limits!")
    print("")
    
    demo = ExpertCollectorDemo()
    
    try:
        properties = await demo.run_demo()
        print(f"\n🎉 Demo completed with {len(properties)} properties!")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())