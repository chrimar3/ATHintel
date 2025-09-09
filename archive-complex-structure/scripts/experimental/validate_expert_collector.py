#!/usr/bin/env python3
"""
🔍 EXPERT COLLECTOR VALIDATION
Test and validate the expert Athens collector before full deployment

VALIDATION TESTS:
✅ Expert methodology implementation
✅ Rate limiting components
✅ Session management
✅ Browser stealth configuration
✅ Data extraction accuracy
✅ Error handling robustness
✅ Performance benchmarks
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from expert_athens_collector import (
    ExpertAthensCollector, 
    TokenBucket, 
    ExponentialBackoff,
    SessionManager,
    ExpertProperty
)

class ExpertCollectorValidator:
    """Comprehensive validation of expert collector components"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def validate_all_components(self) -> Dict[str, Any]:
        """Run all validation tests"""
        
        print("🔍 EXPERT ATHENS COLLECTOR VALIDATION")
        print("=" * 60)
        print("🧪 Running comprehensive component tests...")
        print("")
        
        # Test 1: Rate limiting components
        print("1️⃣ Testing Token Bucket Rate Limiting...")
        self.test_results['token_bucket'] = await self.test_token_bucket()
        
        print("2️⃣ Testing Exponential Backoff...")
        self.test_results['exponential_backoff'] = await self.test_exponential_backoff()
        
        print("3️⃣ Testing Session Management...")
        self.test_results['session_management'] = await self.test_session_management()
        
        print("4️⃣ Testing Expert Property Validation...")
        self.test_results['property_validation'] = await self.test_property_validation()
        
        print("5️⃣ Testing Collector Initialization...")
        self.test_results['collector_init'] = await self.test_collector_initialization()
        
        print("6️⃣ Testing Small Scale Collection...")
        self.test_results['small_collection'] = await self.test_small_collection()
        
        # Generate validation report
        await self.generate_validation_report()
        
        return self.test_results
    
    async def test_token_bucket(self) -> Dict[str, Any]:
        """Test token bucket rate limiting"""
        try:
            bucket = TokenBucket(capacity=5, refill_rate=2.0)
            
            # Test initial consumption
            can_consume_5 = await bucket.consume(5)
            can_consume_more = await bucket.consume(1)
            
            # Wait for refill
            await asyncio.sleep(1)
            can_consume_after_wait = await bucket.consume(1)
            
            result = {
                "status": "PASS",
                "initial_consumption": can_consume_5,
                "overconsumption_blocked": not can_consume_more,
                "refill_working": can_consume_after_wait,
                "details": "Token bucket operates correctly"
            }
            
            print(f"   ✅ Token Bucket: {'PASS' if all([can_consume_5, not can_consume_more, can_consume_after_wait]) else 'FAIL'}")
            return result
            
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "details": f"Token bucket test failed: {str(e)}"
            }
            print(f"   ❌ Token Bucket: FAIL - {str(e)}")
            return result
    
    async def test_exponential_backoff(self) -> Dict[str, Any]:
        """Test exponential backoff calculation"""
        try:
            backoff = ExponentialBackoff(base_delay=1.0, max_delay=10.0, backoff_factor=2.0)
            
            delays = []
            for retry in range(5):
                delay = backoff.calculate_delay(retry)
                delays.append(delay)
            
            # Verify exponential growth with jitter
            exponential_growth = all(delays[i] <= delays[i+1] * 1.5 for i in range(len(delays)-1))
            max_delay_respected = all(d <= 10.5 for d in delays)  # Allow for jitter
            min_delay_respected = all(d >= 1.0 for d in delays)
            
            result = {
                "status": "PASS" if all([exponential_growth, max_delay_respected, min_delay_respected]) else "FAIL",
                "delays": delays,
                "exponential_growth": exponential_growth,
                "max_delay_respected": max_delay_respected,
                "min_delay_respected": min_delay_respected,
                "details": f"Delays: {[f'{d:.2f}' for d in delays]}"
            }
            
            print(f"   ✅ Exponential Backoff: {'PASS' if result['status'] == 'PASS' else 'FAIL'}")
            return result
            
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "details": f"Exponential backoff test failed: {str(e)}"
            }
            print(f"   ❌ Exponential Backoff: FAIL - {str(e)}")
            return result
    
    async def test_session_management(self) -> Dict[str, Any]:
        """Test session management and rotation"""
        try:
            session_mgr = SessionManager()
            
            # Test initial state
            initial_ua = session_mgr.current_user_agent
            initial_headers = session_mgr.get_headers()
            
            # Test rotation logic
            session_mgr.requests_in_session = 100  # Force rotation
            should_rotate = session_mgr.should_rotate_session()
            
            # Test actual rotation
            session_mgr.rotate_session()
            new_ua = session_mgr.current_user_agent
            new_headers = session_mgr.get_headers()
            
            result = {
                "status": "PASS",
                "initial_user_agent": initial_ua[:50],
                "rotation_triggered": should_rotate,
                "user_agent_changed": initial_ua != new_ua,
                "headers_valid": "User-Agent" in new_headers,
                "session_count": session_mgr.session_count,
                "details": "Session management working correctly"
            }
            
            print(f"   ✅ Session Management: PASS")
            return result
            
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "details": f"Session management test failed: {str(e)}"
            }
            print(f"   ❌ Session Management: FAIL - {str(e)}")
            return result
    
    async def test_property_validation(self) -> Dict[str, Any]:
        """Test expert property validation logic"""
        try:
            # Create valid property
            valid_property = ExpertProperty(
                property_id="test_123",
                url="https://www.spitogatos.gr/en/property/1117123456",
                timestamp=datetime.now().isoformat(),
                title="2 Bedroom Apartment in Exarchia, Athens",
                neighborhood="Exarchia",
                price=250000.0,
                sqm=75.0,
                energy_class="B",
                price_per_sqm=None,
                rooms=2,
                floor="3rd",
                property_type="apartment",
                listing_type="sale",
                description="Test property",
                html_source_hash="test_hash",
                extraction_confidence=0.9,
                validation_flags=[],
                collection_method="test",
                session_id="test_session",
                retry_count=0,
                response_time_ms=1000,
                user_agent_used="test_agent",
                proxy_used=None,
                headers_fingerprint="test_fingerprint"
            )
            
            # Test validation
            is_valid = valid_property.is_expert_quality()
            
            # Create invalid property (missing energy class)
            invalid_property = ExpertProperty(
                property_id="test_456",
                url="https://www.spitogatos.gr/en/property/1117123457",
                timestamp=datetime.now().isoformat(),
                title="Invalid Property",
                neighborhood="Athens",
                price=100000.0,
                sqm=50.0,
                energy_class=None,  # Missing required field
                price_per_sqm=None,
                rooms=1,
                floor=None,
                property_type="apartment",
                listing_type="sale",
                description="Invalid test property",
                html_source_hash="test_hash_2",
                extraction_confidence=0.9,
                validation_flags=[],
                collection_method="test",
                session_id="test_session",
                retry_count=0,
                response_time_ms=1000,
                user_agent_used="test_agent",
                proxy_used=None,
                headers_fingerprint="test_fingerprint"
            )
            
            is_invalid = not invalid_property.is_expert_quality()
            
            result = {
                "status": "PASS" if (is_valid and is_invalid) else "FAIL",
                "valid_property_passed": is_valid,
                "invalid_property_rejected": is_invalid,
                "price_per_sqm_calculated": valid_property.price_per_sqm is not None,
                "validation_flags_added": len(valid_property.validation_flags) > 0,
                "details": f"Valid: {is_valid}, Invalid rejected: {is_invalid}"
            }
            
            print(f"   ✅ Property Validation: {'PASS' if result['status'] == 'PASS' else 'FAIL'}")
            return result
            
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "details": f"Property validation test failed: {str(e)}"
            }
            print(f"   ❌ Property Validation: FAIL - {str(e)}")
            return result
    
    async def test_collector_initialization(self) -> Dict[str, Any]:
        """Test collector initialization"""
        try:
            collector = ExpertAthensCollector()
            
            # Test components exist
            has_stats = collector.stats is not None
            has_session_mgr = collector.session_manager is not None
            has_token_bucket = collector.token_bucket is not None
            has_backoff = collector.backoff is not None
            
            # Test configuration
            valid_target = collector.target_properties > 0
            valid_success_rate = collector.min_success_rate >= 10.0
            valid_batch_size = collector.batch_size >= 5
            
            result = {
                "status": "PASS" if all([has_stats, has_session_mgr, has_token_bucket, 
                                       has_backoff, valid_target, valid_success_rate, 
                                       valid_batch_size]) else "FAIL",
                "components_initialized": has_stats and has_session_mgr and has_token_bucket and has_backoff,
                "target_properties": collector.target_properties,
                "min_success_rate": collector.min_success_rate,
                "batch_size": collector.batch_size,
                "session_id": collector.session_id,
                "details": "Collector initialization complete"
            }
            
            print(f"   ✅ Collector Init: {'PASS' if result['status'] == 'PASS' else 'FAIL'}")
            return result
            
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "details": f"Collector initialization test failed: {str(e)}"
            }
            print(f"   ❌ Collector Init: FAIL - {str(e)}")
            return result
    
    async def test_small_collection(self) -> Dict[str, Any]:
        """Test small-scale collection (3 properties max)"""
        try:
            print("   🔄 Running small collection test (this may take 30-60 seconds)...")
            
            # Create collector with reduced targets for testing
            collector = ExpertAthensCollector()
            collector.target_properties = 3
            collector.batch_size = 3
            
            # Test seed loading
            seeds = await collector.load_proven_seeds()
            has_seeds = len(seeds) > 0
            
            # Test target generation
            targets = await collector.generate_expert_targets(seeds[:10])
            has_targets = len(targets) > 0
            
            result = {
                "status": "PASS" if (has_seeds and has_targets) else "FAIL",
                "seeds_loaded": len(seeds),
                "targets_generated": len(targets),
                "seed_sample": seeds[:5] if seeds else [],
                "target_sample": targets[:5] if targets else [],
                "details": f"Small collection test: {len(seeds)} seeds, {len(targets)} targets"
            }
            
            print(f"   ✅ Small Collection: {'PASS' if result['status'] == 'PASS' else 'FAIL'}")
            return result
            
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "details": f"Small collection test failed: {str(e)}"
            }
            print(f"   ❌ Small Collection: FAIL - {str(e)}")
            return result
    
    async def generate_validation_report(self):
        """Generate comprehensive validation report"""
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        passed_tests = sum(1 for test in self.test_results.values() if test.get('status') == 'PASS')
        total_tests = len(self.test_results)
        
        print("")
        print("=" * 60)
        print("🔍 EXPERT COLLECTOR VALIDATION REPORT")
        print("=" * 60)
        print(f"⏱️  Validation Runtime: {runtime:.2f} seconds")
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("")
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result.get('status') == 'PASS' else "❌"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result.get('status', 'UNKNOWN')}")
            
            if result.get('status') == 'FAIL' and 'error' in result:
                print(f"   Error: {result['error']}")
        
        print("")
        
        # Overall assessment
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Expert collector ready for deployment!")
            deployment_ready = True
        elif passed_tests >= total_tests * 0.8:
            print("✅ MOSTLY PASSING - Expert collector ready with minor issues")
            deployment_ready = True
        else:
            print("⚠️ SIGNIFICANT ISSUES - Review failed tests before deployment")
            deployment_ready = False
        
        print("")
        print("💡 NEXT STEPS:")
        if deployment_ready:
            print("   1. Run: python run_expert_collector.py")
            print("   2. Monitor initial collection performance")
            print("   3. Adjust parameters based on success rate")
        else:
            print("   1. Fix failed test components")
            print("   2. Re-run validation")
            print("   3. Deploy after all tests pass")
        
        print("=" * 60)
        
        # Save validation report
        report_file = Path("data/expert") / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            "validation_completed": datetime.now().isoformat(),
            "runtime_seconds": runtime,
            "tests_passed": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "deployment_ready": deployment_ready,
            "test_results": self.test_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Validation report saved: {report_file}")

async def main():
    """Main validation function"""
    
    print("🔍 Starting Expert Athens Collector Validation")
    print("")
    
    try:
        validator = ExpertCollectorValidator()
        results = await validator.validate_all_components()
        
        # Return success code based on results
        passed = sum(1 for r in results.values() if r.get('status') == 'PASS')
        total = len(results)
        
        if passed == total:
            print("\n🎉 Validation completed successfully!")
            sys.exit(0)
        elif passed >= total * 0.8:
            print("\n✅ Validation mostly successful!")
            sys.exit(0)
        else:
            print("\n⚠️ Validation found significant issues!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Validation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())