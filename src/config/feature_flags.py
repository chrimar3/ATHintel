"""
Feature Flag Configuration for ATHintel Real Data Transformation
Enables gradual rollout and instant rollback capabilities
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class FeatureFlags:
    """
    Centralized feature flag management for safe deployment
    """
    
    # Default feature states - all disabled initially
    DEFAULT_FLAGS = {
        # Story 1.1: Data Authenticity Validator
        "data_validation_enabled": False,
        "multi_factor_validation": False,
        "validation_strict_mode": False,
        "validation_logging": True,
        
        # Story 1.3: Real Data Pipeline
        "real_data_pipeline": False,
        "reject_synthetic_data": False,
        "data_lineage_tracking": False,
        
        # Story 1.4: Value Assessment
        "enhanced_value_assessment": False,
        "market_comparables": False,
        "confidence_intervals": False,
        
        # Story 1.5: Reports
        "authenticity_indicators": False,
        "report_confidence_scores": False,
        
        # Story 1.6: Audit System
        "audit_logging": False,
        "sqlite_audit_db": False,
        "authenticity_alerts": False,
        
        # Story 1.7: Deployment
        "production_mode": False,
        "performance_monitoring": True,
        "rollback_enabled": True,
        
        # Sprint 2 Features
        "monitoring_enabled": False,
        "performance_mode": False
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize feature flags from file or defaults
        
        Args:
            config_file: Path to JSON config file (optional)
        """
        self.config_file = config_file or os.environ.get(
            'FEATURE_FLAGS_CONFIG',
            'config/feature_flags.json'
        )
        self.flags = self._load_flags()
        self.override_flags = {}  # Runtime overrides
        
    def _load_flags(self) -> Dict[str, bool]:
        """Load flags from file or use defaults"""
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_flags = json.load(f)
                    # Merge with defaults to ensure all flags exist
                    return {**self.DEFAULT_FLAGS, **loaded_flags}
            except Exception as e:
                print(f"Warning: Could not load feature flags: {e}")
                return self.DEFAULT_FLAGS.copy()
        return self.DEFAULT_FLAGS.copy()
    
    def save_flags(self) -> None:
        """Persist current flags to file"""
        try:
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.flags, f, indent=2)
        except Exception as e:
            print(f"Error saving feature flags: {e}")
    
    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            True if enabled, False otherwise
        """
        # Check runtime overrides first
        if flag_name in self.override_flags:
            return self.override_flags[flag_name]
        
        # Check environment variable override
        env_var = f"FF_{flag_name.upper()}"
        if env_var in os.environ:
            return os.environ[env_var].lower() in ('true', '1', 'yes')
        
        # Return configured value or False if not found
        return self.flags.get(flag_name, False)
    
    def enable(self, flag_name: str, save: bool = True) -> None:
        """Enable a feature flag"""
        if flag_name not in self.DEFAULT_FLAGS:
            raise ValueError(f"Unknown feature flag: {flag_name}")
        
        self.flags[flag_name] = True
        if save:
            self.save_flags()
        self._log_change(flag_name, True)
    
    def disable(self, flag_name: str, save: bool = True) -> None:
        """Disable a feature flag"""
        if flag_name not in self.DEFAULT_FLAGS:
            raise ValueError(f"Unknown feature flag: {flag_name}")
        
        self.flags[flag_name] = False
        if save:
            self.save_flags()
        self._log_change(flag_name, False)
    
    def set_override(self, flag_name: str, value: bool) -> None:
        """Set a runtime override (not persisted)"""
        self.override_flags[flag_name] = value
        self._log_change(flag_name, value, override=True)
    
    def clear_override(self, flag_name: str) -> None:
        """Clear a runtime override"""
        if flag_name in self.override_flags:
            del self.override_flags[flag_name]
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get current state of all flags"""
        result = self.flags.copy()
        result.update(self.override_flags)
        return result
    
    def get_enabled_features(self) -> list:
        """Get list of currently enabled features"""
        return [name for name, enabled in self.get_all_flags().items() if enabled]
    
    def _log_change(self, flag_name: str, value: bool, override: bool = False) -> None:
        """Log feature flag changes for audit trail"""
        change_type = "OVERRIDE" if override else "CHANGE"
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {change_type}: {flag_name} = {value}"
        
        # In production, this would write to audit log
        if self.is_enabled("audit_logging"):
            print(f"AUDIT: {log_entry}")
    
    def rollback_all(self) -> None:
        """Emergency rollback - disable all feature flags"""
        if not self.is_enabled("rollback_enabled"):
            raise RuntimeError("Rollback is disabled")
        
        print("EMERGENCY ROLLBACK: Disabling all features")
        for flag in self.DEFAULT_FLAGS:
            if flag not in ["rollback_enabled", "performance_monitoring", "validation_logging"]:
                self.flags[flag] = False
        self.save_flags()
        print("Rollback complete - all features disabled")


# Global instance
_feature_flags = None

def get_feature_flags() -> FeatureFlags:
    """Get or create the global feature flags instance"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


# Decorator for feature-flagged functions
def feature_flag(flag_name: str, default_return=None):
    """
    Decorator to conditionally execute functions based on feature flags
    
    Usage:
        @feature_flag("enhanced_value_assessment")
        def calculate_advanced_metrics():
            # This only runs if feature is enabled
            return complex_calculation()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if get_feature_flags().is_enabled(flag_name):
                return func(*args, **kwargs)
            else:
                if default_return is not None:
                    return default_return
                # Return None or empty result based on function name
                if 'calculate' in func.__name__ or 'get' in func.__name__:
                    return 0
                elif 'validate' in func.__name__ or 'check' in func.__name__:
                    return True
                return None
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# Command-line interface for managing flags
if __name__ == "__main__":
    import sys
    
    ff = get_feature_flags()
    
    if len(sys.argv) < 2:
        print("Feature Flags Status:")
        print("-" * 40)
        for name, enabled in ff.get_all_flags().items():
            status = "✅" if enabled else "❌"
            print(f"{status} {name}: {enabled}")
        print("-" * 40)
        print(f"Enabled features: {len(ff.get_enabled_features())}/{len(ff.DEFAULT_FLAGS)}")
    elif sys.argv[1] == "enable" and len(sys.argv) > 2:
        ff.enable(sys.argv[2])
        print(f"Enabled: {sys.argv[2]}")
    elif sys.argv[1] == "disable" and len(sys.argv) > 2:
        ff.disable(sys.argv[2])
        print(f"Disabled: {sys.argv[2]}")
    elif sys.argv[1] == "rollback":
        ff.rollback_all()
    else:
        print("Usage: python feature_flags.py [enable|disable|rollback] [flag_name]")