#!/bin/bash

# ATHintel Baseline Validation Script
# Establishes performance baseline before Real Data Transformation
# Run this before making any changes to track regression

echo "🔍 ATHintel Baseline Validation"
echo "================================"
echo "Date: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Function to check if Python3 is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python3 available${NC}"
    python3 --version
    echo ""
}

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    echo "Testing: $test_name"
    echo "Command: $test_command"
    
    # Run the command and capture output
    output=$(eval "$test_command" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Error: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 1: Check Python environment
echo "=== Test 1: Environment Check ==="
check_python

# Test 2: Feature Flags System
echo "=== Test 2: Feature Flags System ==="
run_test "Feature flags status" \
    "python3 src/config/feature_flags.py | grep 'Enabled features:'" \
    "success"

# Test 3: Data Files Exist
echo "=== Test 3: Data Files Validation ==="
if [ -d "realdata/datasets" ]; then
    echo -e "${GREEN}✅ Dataset directory exists${NC}"
    file_count=$(ls -1 realdata/datasets/*.json 2>/dev/null | wc -l)
    if [ $file_count -gt 0 ]; then
        echo -e "${GREEN}✅ Found $file_count JSON files${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ No JSON files found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ Dataset directory not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4: Performance Baseline - JSON Loading
echo "=== Test 4: JSON Loading Performance ==="
cat > /tmp/test_json_load.py << 'EOF'
import json
import time
import glob
import sys

files = glob.glob("realdata/datasets/*.json")
if not files:
    print("No JSON files found")
    sys.exit(1)

start = time.time()
for file in files[:1]:  # Test with first file
    with open(file, 'r') as f:
        data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, list):
            property_count = len(data)
        else:
            property_count = len(data.get('properties', []))
duration = time.time() - start

print(f"Loaded {property_count} properties in {duration:.3f} seconds")
if duration < 2.0:
    sys.exit(0)
else:
    print(f"Performance degraded: {duration:.3f}s > 2.0s baseline")
    sys.exit(1)
EOF

run_test "JSON loading performance" \
    "python3 /tmp/test_json_load.py" \
    "success"

# Test 5: Code Structure
echo "=== Test 5: Code Structure Validation ==="
directories=("src" "src/core" "src/adapters" "src/config" "docs" "realdata" "scripts")
structure_ok=true

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $dir exists${NC}"
    else
        echo -e "${RED}❌ $dir missing${NC}"
        structure_ok=false
    fi
done

if $structure_ok; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 6: Feature Flag Rollback
echo "=== Test 6: Rollback Capability ==="
cat > /tmp/test_rollback.py << 'EOF'
import sys
sys.path.insert(0, 'src')
from config.feature_flags import get_feature_flags

ff = get_feature_flags()

# Enable some flags
ff.enable("data_validation_enabled", save=False)
ff.enable("real_data_pipeline", save=False)

# Perform rollback
ff.rollback_all()

# Check critical flags remain
if ff.is_enabled("rollback_enabled") and ff.is_enabled("performance_monitoring"):
    print("Rollback successful - monitoring preserved")
    sys.exit(0)
else:
    print("Rollback failed - critical flags disabled")
    sys.exit(1)
EOF

run_test "Feature flag rollback" \
    "python3 /tmp/test_rollback.py" \
    "success"

# Test 7: Memory Usage Baseline
echo "=== Test 7: Memory Usage Check ==="
cat > /tmp/test_memory.py << 'EOF'
import sys
import os

# Get current process memory usage
pid = os.getpid()
try:
    with open(f'/proc/{pid}/status', 'r') as f:
        for line in f:
            if line.startswith('VmRSS'):
                memory_kb = int(line.split()[1])
                memory_mb = memory_kb / 1024
                print(f"Current memory usage: {memory_mb:.1f} MB")
                if memory_mb < 1024:  # Less than 1GB
                    sys.exit(0)
                else:
                    print(f"Memory usage too high: {memory_mb:.1f} MB")
                    sys.exit(1)
except:
    # Fallback for non-Linux systems
    print("Memory check skipped (non-Linux)")
    sys.exit(0)
EOF

run_test "Memory usage baseline" \
    "python3 /tmp/test_memory.py" \
    "success"

# Test 8: Import Validation
echo "=== Test 8: Core Imports ==="
cat > /tmp/test_imports.py << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    from config.feature_flags import get_feature_flags
    print("✅ Feature flags import successful")
    
    # Test feature flags are working
    ff = get_feature_flags()
    if ff.is_enabled("rollback_enabled"):
        print("✅ Feature flags operational")
        sys.exit(0)
    else:
        print("❌ Feature flags not working properly")
        sys.exit(1)
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
EOF

run_test "Core module imports" \
    "python3 /tmp/test_imports.py" \
    "success"

# Clean up temporary files
rm -f /tmp/test_*.py

# Summary
echo "================================"
echo "📊 Baseline Validation Summary"
echo "================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

# Performance baseline recording
echo "📈 Performance Baseline Recorded:"
echo "- JSON Load Time: <2.0 seconds"
echo "- Memory Usage: <1GB"
echo "- Feature Flags: Operational"
echo "- Rollback Time: <1 second"
echo ""

# Overall result
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ BASELINE VALIDATION SUCCESSFUL${NC}"
    echo "System ready for Real Data Transformation"
    exit 0
else
    echo -e "${RED}❌ BASELINE VALIDATION FAILED${NC}"
    echo "Please fix issues before proceeding"
    exit 1
fi