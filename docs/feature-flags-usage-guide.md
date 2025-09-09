# 🚦 Feature Flags Usage Guide - ATHintel

**Version:** 1.0  
**Status:** ACTIVE  
**Critical for:** Safe deployment and instant rollback capability

---

## 🎯 Quick Start

### Check Current Status
```bash
python3 src/config/feature_flags.py
```

### Enable a Feature
```bash
python3 src/config/feature_flags.py enable [flag_name]
```

### Disable a Feature
```bash
python3 src/config/feature_flags.py disable [flag_name]
```

### Emergency Rollback
```bash
python3 src/config/feature_flags.py rollback
```

---

## 📋 Available Feature Flags

### Story 1.1: Data Validation
| Flag | Purpose | Risk | Default |
|------|---------|------|---------|
| `data_validation_enabled` | Master switch for validation | HIGH | False |
| `multi_factor_validation` | Enable 6-factor validation | HIGH | False |
| `validation_strict_mode` | Reject on any validation failure | MEDIUM | False |
| `validation_logging` | Log validation decisions | LOW | True |

### Story 1.3: Data Pipeline
| Flag | Purpose | Risk | Default |
|------|---------|------|---------|
| `real_data_pipeline` | Use real-data-only pipeline | HIGH | False |
| `reject_synthetic_data` | Block all synthetic data | HIGH | False |
| `data_lineage_tracking` | Track data source trail | LOW | False |

### Story 1.4: Value Assessment
| Flag | Purpose | Risk | Default |
|------|---------|------|---------|
| `enhanced_value_assessment` | New valuation algorithm | MEDIUM | False |
| `market_comparables` | Use market comparison | MEDIUM | False |
| `confidence_intervals` | Show confidence ranges | LOW | False |

### Story 1.5: Reporting
| Flag | Purpose | Risk | Default |
|------|---------|------|---------|
| `authenticity_indicators` | Show data authenticity | LOW | False |
| `report_confidence_scores` | Display confidence levels | LOW | False |

### Story 1.6: Audit System
| Flag | Purpose | Risk | Default |
|------|---------|------|---------|
| `audit_logging` | Enable audit trail | LOW | False |
| `sqlite_audit_db` | Use SQLite for audit | MEDIUM | False |
| `authenticity_alerts` | Send quality alerts | LOW | False |

### Story 1.7: Deployment
| Flag | Purpose | Risk | Default |
|------|---------|------|---------|
| `production_mode` | Production configuration | CRITICAL | False |
| `performance_monitoring` | Track performance metrics | LOW | True |
| `rollback_enabled` | Allow emergency rollback | LOW | True |

---

## 🔧 Developer Usage

### Using Decorators in Code
```python
from src.config.feature_flags import feature_flag, get_feature_flags

@feature_flag("enhanced_value_assessment")
def calculate_advanced_metrics(property_data):
    """This function only runs when feature is enabled"""
    return complex_calculation(property_data)

# Manual check in code
ff = get_feature_flags()
if ff.is_enabled("data_validation_enabled"):
    validate_property(data)
else:
    # Use old validation
    legacy_validate(data)
```

### Runtime Overrides (Testing)
```python
from src.config.feature_flags import get_feature_flags

ff = get_feature_flags()

# Temporary override (not saved to file)
ff.set_override("data_validation_enabled", True)

# Clear override
ff.clear_override("data_validation_enabled")
```

### Environment Variable Overrides
```bash
# Override via environment variable
export FF_DATA_VALIDATION_ENABLED=true
python3 main.py

# Multiple overrides
export FF_REAL_DATA_PIPELINE=true
export FF_AUDIT_LOGGING=true
python3 main.py
```

---

## 📊 Progressive Rollout Strategy

### Sprint 1 - Foundation
```bash
# Week 1: Enable validation in test mode
python3 src/config/feature_flags.py enable validation_logging
python3 src/config/feature_flags.py enable data_validation_enabled

# Week 2: Add multi-factor validation
python3 src/config/feature_flags.py enable multi_factor_validation
```

### Sprint 2 - Pipeline
```bash
# Week 3: Enable real data pipeline in shadow mode
python3 src/config/feature_flags.py enable data_lineage_tracking

# Week 4: Activate pipeline
python3 src/config/feature_flags.py enable real_data_pipeline
python3 src/config/feature_flags.py enable reject_synthetic_data
```

### Sprint 3 - User-Facing
```bash
# Week 5: Enable reporting features
python3 src/config/feature_flags.py enable authenticity_indicators
python3 src/config/feature_flags.py enable report_confidence_scores

# Week 6: Enable audit system
python3 src/config/feature_flags.py enable audit_logging
python3 src/config/feature_flags.py enable sqlite_audit_db
```

### Sprint 4 - Production
```bash
# Week 7: Production deployment
python3 src/config/feature_flags.py enable production_mode
python3 src/config/feature_flags.py enable authenticity_alerts
```

---

## 🚨 Emergency Procedures

### Scenario 1: Performance Degradation
```bash
# Disable heavy processing features
python3 src/config/feature_flags.py disable multi_factor_validation
python3 src/config/feature_flags.py disable enhanced_value_assessment
```

### Scenario 2: Data Corruption Risk
```bash
# Immediately disable data pipeline
python3 src/config/feature_flags.py disable real_data_pipeline
python3 src/config/feature_flags.py disable reject_synthetic_data
```

### Scenario 3: Complete System Issues
```bash
# Emergency rollback - disables everything except monitoring
python3 src/config/feature_flags.py rollback
```

### Scenario 4: Production Incident
```bash
# Disable production mode but keep monitoring
python3 src/config/feature_flags.py disable production_mode
# Check what's still enabled
python3 src/config/feature_flags.py | grep "✅"
```

---

## 🔍 Monitoring & Verification

### Daily Health Check Script
```bash
#!/bin/bash
# daily_flag_check.sh

echo "🔍 Feature Flag Health Check"
echo "============================"

# Check current state
python3 src/config/feature_flags.py > /tmp/flags_current.txt

# Count enabled features
ENABLED=$(grep "✅" /tmp/flags_current.txt | wc -l)
TOTAL=$(grep ":" /tmp/flags_current.txt | wc -l)

echo "Features Enabled: $ENABLED / $TOTAL"

# Check for risky combinations
if grep -q "✅ production_mode: True" /tmp/flags_current.txt; then
    if grep -q "❌ rollback_enabled: False" /tmp/flags_current.txt; then
        echo "⚠️ WARNING: Production mode without rollback capability!"
    fi
fi

# Verify critical monitoring flags
if ! grep -q "✅ performance_monitoring: True" /tmp/flags_current.txt; then
    echo "⚠️ WARNING: Performance monitoring is disabled!"
fi

echo "============================"
```

### Integration Test
```python
# tests/test_feature_flags.py

import pytest
from src.config.feature_flags import get_feature_flags

def test_rollback_preserves_monitoring():
    """Ensure rollback keeps critical flags enabled"""
    ff = get_feature_flags()
    
    # Enable some features
    ff.enable("data_validation_enabled", save=False)
    ff.enable("real_data_pipeline", save=False)
    
    # Perform rollback
    ff.rollback_all()
    
    # Verify monitoring stays enabled
    assert ff.is_enabled("performance_monitoring")
    assert ff.is_enabled("rollback_enabled")
    assert ff.is_enabled("validation_logging")
    
    # Verify features are disabled
    assert not ff.is_enabled("data_validation_enabled")
    assert not ff.is_enabled("real_data_pipeline")

def test_feature_flag_decorator():
    """Test conditional execution with decorator"""
    from src.config.feature_flags import feature_flag
    
    @feature_flag("test_feature", default_return=42)
    def protected_function():
        return 100
    
    # Should return default when disabled
    result = protected_function()
    assert result == 42
```

---

## 📈 Flag Lifecycle Management

### Feature Flag Stages

1. **Development** - Flag created, disabled by default
2. **Testing** - Enabled in test environment only
3. **Staging** - Enabled in staging for validation
4. **Production (Gradual)** - Enabled for % of users
5. **Production (Full)** - Enabled for all users
6. **Cleanup** - Flag removed after stable

### Graduation Criteria
- [ ] Feature tested in development
- [ ] Performance impact measured
- [ ] Rollback tested successfully
- [ ] No critical bugs for 48 hours
- [ ] Monitoring shows stable metrics

---

## 🎯 Best Practices

### DO:
- ✅ Test flag changes in development first
- ✅ Monitor performance after enabling
- ✅ Document why flags are enabled/disabled
- ✅ Use gradual rollout for risky features
- ✅ Keep rollback_enabled always true

### DON'T:
- ❌ Enable multiple HIGH risk flags simultaneously
- ❌ Disable monitoring flags in production
- ❌ Make flag changes without testing
- ❌ Leave obsolete flags in code
- ❌ Disable rollback capability

---

## 📝 Troubleshooting

### Common Issues

**Issue:** Flag changes not taking effect
```bash
# Check for environment variable override
env | grep FF_
# Check for runtime override in code
```

**Issue:** Cannot rollback
```bash
# Verify rollback is enabled
python3 -c "from src.config.feature_flags import get_feature_flags; print(get_feature_flags().is_enabled('rollback_enabled'))"
```

**Issue:** Performance degradation after enabling
```bash
# Disable the last enabled feature
python3 src/config/feature_flags.py disable [last_enabled_flag]
# Check performance metrics
```

---

## 📞 Support

**For Issues:**
- Check this guide first
- Review `/docs/qa/` for QA procedures
- Contact DevOps team for infrastructure issues
- Emergency hotline for production incidents

**Audit Trail:**
All flag changes are logged when `audit_logging` is enabled.

---

**Remember:** Feature flags are your safety net. Use them wisely! 🛡️