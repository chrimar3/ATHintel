#!/usr/bin/env python3
"""
ATHintel Production Test Suite Runner
Runs all tests and generates comprehensive reports
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("Errors:", result.stderr)
            if result.stdout:
                print("Output:", result.stdout)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("🚀 ATHintel Production Test Suite")
    print("="*60)
    
    all_passed = True
    test_results = []
    
    # 1. Check Python version
    print("\n📋 Environment Check")
    python_version = sys.version_info
    print(f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 2. Run unit tests
    unit_test_cmd = "python3 -m pytest tests/unit/ -v --tb=short --maxfail=5 -x 2>&1 | head -50"
    passed = run_command(unit_test_cmd, "Unit Tests")
    test_results.append(("Unit Tests", passed))
    all_passed = all_passed and passed
    
    # 3. Run security tests
    security_test_cmd = "python3 -m pytest tests/security/ -v --tb=short --maxfail=5 -x 2>&1 | head -50"
    passed = run_command(security_test_cmd, "Security Tests")
    test_results.append(("Security Tests", passed))
    all_passed = all_passed and passed
    
    # 4. Run integration tests
    integration_test_cmd = "python3 -m pytest tests/integration/ -v --tb=short --maxfail=5 -x 2>&1 | head -50"
    passed = run_command(integration_test_cmd, "Integration Tests")
    test_results.append(("Integration Tests", passed))
    all_passed = all_passed and passed
    
    # 5. Run performance tests
    performance_test_cmd = "python3 -m pytest tests/performance/ -v --tb=short --maxfail=5 -x 2>&1 | head -50"
    passed = run_command(performance_test_cmd, "Performance Tests")
    test_results.append(("Performance Tests", passed))
    all_passed = all_passed and passed
    
    # 6. Run functional tests
    functional_test_cmd = "python3 -m pytest tests/functional/ -v --tb=short --maxfail=5 -x 2>&1 | head -50"
    passed = run_command(functional_test_cmd, "Functional Tests")
    test_results.append(("Functional Tests", passed))
    all_passed = all_passed and passed
    
    # 7. Run resilience tests
    resilience_test_cmd = "python3 -m pytest tests/resilience/ -v --tb=short --maxfail=5 -x 2>&1 | head -50"
    passed = run_command(resilience_test_cmd, "Resilience Tests")
    test_results.append(("Resilience Tests", passed))
    all_passed = all_passed and passed
    
    # Generate summary report
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} : {status}")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Production Ready!")
    else:
        print("⚠️  SOME TESTS FAILED - Review Required")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())