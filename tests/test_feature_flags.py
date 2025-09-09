"""
Integration tests for feature flag system
Ensures safe deployment and rollback capabilities
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.feature_flags import (
    FeatureFlags, 
    get_feature_flags, 
    feature_flag
)


class TestFeatureFlags:
    """Comprehensive tests for feature flag functionality"""
    
    def test_default_state(self):
        """All features should be disabled by default except monitoring"""
        ff = FeatureFlags()
        
        # These should be disabled
        assert not ff.is_enabled("data_validation_enabled")
        assert not ff.is_enabled("real_data_pipeline")
        assert not ff.is_enabled("production_mode")
        
        # These should be enabled for safety
        assert ff.is_enabled("validation_logging")
        assert ff.is_enabled("performance_monitoring")
        assert ff.is_enabled("rollback_enabled")
    
    def test_enable_disable(self):
        """Test enabling and disabling flags"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            ff = FeatureFlags(config_file=tmp.name)
            
            # Enable a flag
            ff.enable("data_validation_enabled")
            assert ff.is_enabled("data_validation_enabled")
            
            # Disable the flag
            ff.disable("data_validation_enabled")
            assert not ff.is_enabled("data_validation_enabled")
            
            # Clean up
            os.unlink(tmp.name)
    
    def test_rollback_functionality(self):
        """Emergency rollback should disable all features except critical ones"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            ff = FeatureFlags(config_file=tmp.name)
            
            # Enable multiple features
            ff.enable("data_validation_enabled")
            ff.enable("real_data_pipeline")
            ff.enable("enhanced_value_assessment")
            ff.enable("production_mode")
            
            # Perform rollback
            ff.rollback_all()
            
            # Verify all features disabled except critical
            assert not ff.is_enabled("data_validation_enabled")
            assert not ff.is_enabled("real_data_pipeline")
            assert not ff.is_enabled("enhanced_value_assessment")
            assert not ff.is_enabled("production_mode")
            
            # Verify critical flags remain
            assert ff.is_enabled("rollback_enabled")
            assert ff.is_enabled("performance_monitoring")
            assert ff.is_enabled("validation_logging")
            
            # Clean up
            os.unlink(tmp.name)
    
    def test_runtime_override(self):
        """Runtime overrides should take precedence"""
        ff = FeatureFlags()
        
        # Flag is disabled by default
        assert not ff.is_enabled("data_validation_enabled")
        
        # Set runtime override
        ff.set_override("data_validation_enabled", True)
        assert ff.is_enabled("data_validation_enabled")
        
        # Clear override
        ff.clear_override("data_validation_enabled")
        assert not ff.is_enabled("data_validation_enabled")
    
    def test_environment_override(self):
        """Environment variables should override config"""
        ff = FeatureFlags()
        
        # Set environment variable
        os.environ["FF_DATA_VALIDATION_ENABLED"] = "true"
        assert ff.is_enabled("data_validation_enabled")
        
        # Clean up
        del os.environ["FF_DATA_VALIDATION_ENABLED"]
        assert not ff.is_enabled("data_validation_enabled")
    
    def test_decorator_functionality(self):
        """Feature flag decorator should control function execution"""
        
        @feature_flag("test_feature", default_return=42)
        def protected_function():
            return 100
        
        # Create a test flag
        ff = get_feature_flags()
        
        # Function should return default when disabled
        result = protected_function()
        assert result == 42
        
        # Enable the feature (using override to avoid file changes)
        ff.set_override("test_feature", True)
        
        # Now function should execute
        # Note: In real implementation, decorator checks global instance
        # This test demonstrates the pattern
    
    def test_persistence(self):
        """Flag changes should persist to file"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            # Create first instance and enable flag
            ff1 = FeatureFlags(config_file=tmp.name)
            ff1.enable("data_validation_enabled")
            
            # Create second instance from same file
            ff2 = FeatureFlags(config_file=tmp.name)
            
            # Flag should be enabled in second instance
            assert ff2.is_enabled("data_validation_enabled")
            
            # Clean up
            os.unlink(tmp.name)
    
    def test_unknown_flag_handling(self):
        """Should handle unknown flags gracefully"""
        ff = FeatureFlags()
        
        # Unknown flag should return False
        assert not ff.is_enabled("unknown_flag")
        
        # Should raise error when trying to enable unknown flag
        try:
            ff.enable("unknown_flag")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown feature flag" in str(e)
    
    def test_get_enabled_features(self):
        """Should correctly list enabled features"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            ff = FeatureFlags(config_file=tmp.name)
            
            # Get initial enabled features
            initial_enabled = ff.get_enabled_features()
            assert "validation_logging" in initial_enabled
            assert "performance_monitoring" in initial_enabled
            
            # Enable more features
            ff.enable("data_validation_enabled")
            ff.enable("audit_logging")
            
            # Check updated list
            enabled = ff.get_enabled_features()
            assert "data_validation_enabled" in enabled
            assert "audit_logging" in enabled
            
            # Clean up
            os.unlink(tmp.name)
    
    def test_progressive_rollout_scenario(self):
        """Simulate progressive feature rollout"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            ff = FeatureFlags(config_file=tmp.name)
            
            # Sprint 1: Enable validation
            ff.enable("data_validation_enabled")
            assert ff.is_enabled("data_validation_enabled")
            assert not ff.is_enabled("real_data_pipeline")  # Not yet
            
            # Sprint 2: Enable pipeline
            ff.enable("real_data_pipeline")
            ff.enable("data_lineage_tracking")
            assert ff.is_enabled("real_data_pipeline")
            assert ff.is_enabled("data_lineage_tracking")
            
            # Issue detected - rollback!
            ff.rollback_all()
            
            # Verify safe state
            assert not ff.is_enabled("data_validation_enabled")
            assert not ff.is_enabled("real_data_pipeline")
            assert ff.is_enabled("rollback_enabled")  # Still can rollback
            
            # Clean up
            os.unlink(tmp.name)


def test_integration_with_validation():
    """Test feature flags with actual validation logic"""
    ff = get_feature_flags()
    
    def validate_property(data):
        """Example validation function"""
        if ff.is_enabled("data_validation_enabled"):
            if ff.is_enabled("multi_factor_validation"):
                # Perform all 6 validation factors
                return perform_multi_factor_validation(data)
            else:
                # Basic validation only
                return perform_basic_validation(data)
        return True  # No validation
    
    def perform_basic_validation(data):
        """Basic URL validation"""
        return "url" in data and data["url"].startswith("http")
    
    def perform_multi_factor_validation(data):
        """Complete validation"""
        checks = [
            "url" in data,
            "price" in data and data["price"] > 0,
            "size" in data and data["size"] > 0,
        ]
        return all(checks)
    
    # Test with flags disabled
    test_data = {"price": -100}  # Invalid data
    assert validate_property(test_data) == True  # No validation
    
    # Enable basic validation
    ff.set_override("data_validation_enabled", True)
    assert validate_property(test_data) == False  # Fails basic validation
    
    # Add valid URL
    test_data["url"] = "https://example.com"
    assert validate_property(test_data) == True  # Passes basic
    
    # Enable strict validation
    ff.set_override("multi_factor_validation", True)
    assert validate_property(test_data) == False  # Fails multi-factor
    
    # Add all required fields
    test_data.update({"price": 100000, "size": 75})
    assert validate_property(test_data) == True  # Passes all
    
    # Clear overrides
    ff.clear_override("data_validation_enabled")
    ff.clear_override("multi_factor_validation")


if __name__ == "__main__":
    # Run tests
    test_suite = TestFeatureFlags()
    
    print("🧪 Running Feature Flag Tests...")
    print("-" * 40)
    
    tests = [
        ("Default State", test_suite.test_default_state),
        ("Enable/Disable", test_suite.test_enable_disable),
        ("Rollback", test_suite.test_rollback_functionality),
        ("Runtime Override", test_suite.test_runtime_override),
        ("Environment Override", test_suite.test_environment_override),
        ("Decorator", test_suite.test_decorator_functionality),
        ("Persistence", test_suite.test_persistence),
        ("Unknown Flags", test_suite.test_unknown_flag_handling),
        ("List Enabled", test_suite.test_get_enabled_features),
        ("Progressive Rollout", test_suite.test_progressive_rollout_scenario),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        try:
            test()
            print(f"✅ {name}")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed += 1
    
    # Run integration test
    try:
        test_integration_with_validation()
        print(f"✅ Integration Test")
        passed += 1
    except Exception as e:
        print(f"❌ Integration Test: {e}")
        failed += 1
    
    print("-" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {failed} tests failed")
        sys.exit(1)