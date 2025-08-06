#!/usr/bin/env python3
"""
🚀 SCALABLE ATHENS COLLECTION RUNNER
Simple interface to run the scalable property collector

USAGE MODES:
1. Single Session (recommended for initial run)
2. Multi-Session (spread collection over time)
3. Custom Parameters

Built on proven methodology that collected 100+ authentic properties
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from scalable_athens_collector import (
    run_scalable_collection, 
    run_multiple_sessions,
    ScalableAthensCollector
)

def main():
    """Main runner with different collection modes"""
    
    parser = argparse.ArgumentParser(description='Scalable Athens Property Collector')
    parser.add_argument('--mode', choices=['single', 'multi', 'custom'], default='single',
                       help='Collection mode (default: single)')
    parser.add_argument('--target', type=int, default=500,
                       help='Target number of properties (default: 500)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Properties per batch (default: 50)')
    parser.add_argument('--strategies', type=int, default=25,
                       help='Max search strategies (default: 25)')
    parser.add_argument('--timeout', type=int, default=180,
                       help='Session timeout in minutes (default: 180)')
    parser.add_argument('--sessions', type=int, default=5,
                       help='Number of sessions for multi mode (default: 5)')
    parser.add_argument('--break-time', type=int, default=30,
                       help='Break between sessions in minutes (default: 30)')
    
    args = parser.parse_args()
    
    print("🏛️ SCALABLE ATHENS PROPERTY COLLECTOR")
    print("=====================================")
    print("Built on proven methodology that extracted 100+ authentic properties")
    print(f"Mode: {args.mode.upper()}")
    print(f"Target: {args.target} properties")
    print()
    
    if args.mode == 'single':
        run_single_session(args)
    elif args.mode == 'multi':
        run_multi_session(args)
    elif args.mode == 'custom':
        run_custom_session(args)

def run_single_session(args):
    """Run single collection session"""
    
    print("🚀 SINGLE SESSION MODE")
    print(f"🎯 Target: {args.target} properties")
    print(f"📦 Batch size: {args.batch_size}")
    print(f"🔍 Max strategies: {args.strategies}")
    print(f"⏱️ Timeout: {args.timeout} minutes")
    print()
    
    try:
        properties, session_name = asyncio.run(
            run_scalable_collection(
                target_properties=args.target,
                batch_size=args.batch_size,
                max_strategies=args.strategies,
                session_timeout_minutes=args.timeout
            )
        )
        
        print()
        print("✅ SINGLE SESSION COMPLETE!")
        print(f"📊 Collected: {len(properties)} authentic properties")
        print(f"📁 Session: {session_name}")
        print(f"💾 Check data/processed/ for results")
        
    except KeyboardInterrupt:
        print("\n⏹️ Collection stopped by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")

def run_multi_session(args):
    """Run multiple collection sessions"""
    
    properties_per_session = args.target // args.sessions
    
    print("🚀 MULTI-SESSION MODE")
    print(f"🎯 Total target: {args.target} properties")
    print(f"📊 Sessions: {args.sessions}")
    print(f"🔢 Per session: {properties_per_session}")
    print(f"⏸️ Break time: {args.break_time} minutes")
    print()
    
    try:
        all_properties = run_multiple_sessions(
            target_per_session=properties_per_session,
            num_sessions=args.sessions,
            break_between_sessions_minutes=args.break_time
        )
        
        print()
        print("✅ MULTI-SESSION COLLECTION COMPLETE!")
        print(f"📊 Total collected: {len(all_properties)} authentic properties")
        print(f"💾 Check data/processed/ for results")
        
    except KeyboardInterrupt:
        print("\n⏹️ Collection stopped by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")

def run_custom_session(args):
    """Run with custom parameters"""
    
    print("🚀 CUSTOM SESSION MODE")
    print("All parameters as specified:")
    print(f"🎯 Target: {args.target}")
    print(f"📦 Batch: {args.batch_size}")
    print(f"🔍 Strategies: {args.strategies}")
    print(f"⏱️ Timeout: {args.timeout} minutes")
    print()
    
    try:
        properties, session_name = asyncio.run(
            run_scalable_collection(
                target_properties=args.target,
                batch_size=args.batch_size,
                max_strategies=args.strategies,
                session_timeout_minutes=args.timeout
            )
        )
        
        print()
        print("✅ CUSTOM SESSION COMPLETE!")
        print(f"📊 Collected: {len(properties)} authentic properties") 
        print(f"📁 Session: {session_name}")
        print(f"💾 Check data/processed/ for results")
        
    except KeyboardInterrupt:
        print("\n⏹️ Collection stopped by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")

def quick_modes():
    """Pre-configured quick modes"""
    
    print()
    print("🚀 QUICK START MODES:")
    print()
    print("1. DEMO MODE (Fast test)")
    print("   python run_scalable_collection.py --mode single --target 50 --timeout 30")
    print()
    print("2. STANDARD MODE (Recommended)")
    print("   python run_scalable_collection.py --mode single --target 500 --timeout 180")
    print()
    print("3. EXTENDED MODE (Maximum collection)")
    print("   python run_scalable_collection.py --mode single --target 1000 --timeout 300")
    print()
    print("4. MULTI-SESSION MODE (Spread over time)")
    print("   python run_scalable_collection.py --mode multi --target 500 --sessions 5 --break-time 30")
    print()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - show help and quick modes
        print("🏛️ SCALABLE ATHENS PROPERTY COLLECTOR")
        print("=====================================")
        print()
        print("Usage: python run_scalable_collection.py [options]")
        print()
        print("Options:")
        print("  --mode {single,multi,custom}  Collection mode (default: single)")
        print("  --target N                    Target properties (default: 500)")
        print("  --batch-size N               Properties per batch (default: 50)")
        print("  --strategies N               Max strategies (default: 25)")
        print("  --timeout N                  Session timeout minutes (default: 180)")
        print("  --sessions N                 Number of sessions for multi mode (default: 5)")
        print("  --break-time N               Break between sessions minutes (default: 30)")
        
        quick_modes()
    else:
        main()