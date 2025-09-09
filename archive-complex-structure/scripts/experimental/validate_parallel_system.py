#!/usr/bin/env python3
"""
🔍 PARALLEL BATCH SYSTEM VALIDATOR
Quick validation script to ensure the parallel batch collector is properly configured
"""

import sys
import logging
from pathlib import Path

def validate_system():
    """Validate the parallel batch collection system"""
    
    print("🔍 PARALLEL BATCH SYSTEM VALIDATOR")
    print("=" * 40)
    
    validation_results = []
    
    # Test 1: Check file existence
    print("\n📁 Checking system files...")
    
    required_files = [
        "parallel_batch_collector.py",
        "run_parallel_batch.py", 
        "PARALLEL_BATCH_README.md"
    ]
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"   ✅ {file_name}")
            validation_results.append(True)
        else:
            print(f"   ❌ {file_name} - MISSING")
            validation_results.append(False)
    
    # Test 2: Check imports
    print("\n🐍 Testing imports...")
    
    try:
        from parallel_batch_collector import (
            BatchCoordinator, BatchWorker, WorkerAgent, 
            ProgressMonitor, ResultsConsolidator, 
            ParallelBatchProperty, run_parallel_collection_sync
        )
        print("   ✅ All core classes imported successfully")
        validation_results.append(True)
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        validation_results.append(False)
    
    # Test 3: Check dependencies
    print("\n📦 Checking dependencies...")
    
    dependencies = [
        ('asyncio', 'asyncio'),
        ('playwright', 'playwright.async_api'),
        ('pathlib', 'pathlib'),
        ('dataclasses', 'dataclasses')
    ]
    
    for dep_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"   ✅ {dep_name}")
            validation_results.append(True)
        except ImportError:
            print(f"   ❌ {dep_name} - Install with: pip install {dep_name}")
            validation_results.append(False)
    
    # Test 4: Check system configuration
    print("\n⚙️ Validating system configuration...")
    
    try:
        from parallel_batch_collector import BatchCoordinator
        
        # Test coordinator initialization
        coordinator = BatchCoordinator(num_workers=3, properties_per_worker=10)
        
        # Check strategies built
        if len(coordinator.search_strategies) >= 3:
            print(f"   ✅ Search strategies: {len(coordinator.search_strategies)} generated")
            validation_results.append(True)
        else:
            print(f"   ❌ Search strategies: Only {len(coordinator.search_strategies)} generated")
            validation_results.append(False)
        
        # Check progress monitor
        if coordinator.progress_monitor:
            print("   ✅ Progress monitor initialized")
            validation_results.append(True)
        else:
            print("   ❌ Progress monitor not initialized")
            validation_results.append(False)
            
        # Check consolidator
        if coordinator.consolidator:
            print("   ✅ Results consolidator initialized")
            validation_results.append(True)
        else:
            print("   ❌ Results consolidator not initialized") 
            validation_results.append(False)
            
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        validation_results.extend([False, False, False])
    
    # Test 5: Check data directory
    print("\n📂 Checking output directory...")
    
    data_dir = Path("data/processed")
    if data_dir.exists():
        print(f"   ✅ Output directory exists: {data_dir}")
        validation_results.append(True)
    else:
        print(f"   ⚠️ Output directory will be created: {data_dir}")
        validation_results.append(True)  # This is fine, it gets created
    
    # Summary
    passed = sum(validation_results)
    total = len(validation_results)
    success_rate = (passed / total) * 100
    
    print(f"\n📊 VALIDATION SUMMARY")
    print(f"   Tests passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("   🎉 System ready for parallel collection!")
        print("\n🚀 To start collecting:")
        print("   python3 run_parallel_batch.py")
        return True
    elif success_rate >= 70:
        print("   ⚠️ System mostly ready, but check failed tests above")
        return False
    else:
        print("   ❌ System has significant issues - check errors above")
        return False

def check_system_requirements():
    """Check additional system requirements"""
    
    print("\n🔧 SYSTEM REQUIREMENTS CHECK")
    print("-" * 30)
    
    # Check Python version
    if sys.version_info >= (3, 7):
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    else:
        print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} - Need 3.7+")
        
    # Check if we can import asyncio
    try:
        import asyncio
        print("   ✅ Asyncio support available")
    except:
        print("   ❌ Asyncio not available")
    
    # Playwright check
    try:
        from playwright.async_api import async_playwright
        print("   ✅ Playwright available")
        print("   💡 If browsers not installed: playwright install")
    except:
        print("   ❌ Playwright missing - Install: pip install playwright")

if __name__ == "__main__":
    try:
        check_system_requirements()
        success = validate_system()
        
        if success:
            print(f"\n✅ Validation complete - System ready!")
            sys.exit(0)
        else:
            print(f"\n⚠️ Validation complete - Issues found")  
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        logging.exception("Full error details:")
        sys.exit(1)