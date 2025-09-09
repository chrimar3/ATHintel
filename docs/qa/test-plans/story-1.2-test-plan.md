# 🧪 Test Plan - Story 1.2: Repository Structure Reorganization

**Story:** 1.2 - Repository Structure Reorganization  
**Risk Level:** 🟡 **MEDIUM**  
**Test Coverage Target:** 80%  
**QA Owner:** QA Engineer 2

---

## 📋 Story Overview

**User Story:**  
As a **development team lead**,  
I want **a clean separation between production and experimental code**,  
so that **real data processing is isolated from any synthetic data contamination**.

**Acceptance Criteria:**
1. Production code moved to `src/production/` with real-data-only modules
2. Fake/synthetic data relocated to `test/fixtures/` or separate repository
3. Clear directory structure: `realdata/`, `src/`, `scripts/production/`, `docs/`
4. Migration script successfully moves all existing code to new structure
5. Git history preserved for all moved files
6. README updated with new structure documentation

---

## 🎯 Test Strategy

### Test Approach
- **Regression Testing** - Ensure no functionality breaks
- **Migration Testing** - Validate file movements
- **Integration Testing** - Verify import paths
- **Build Testing** - Confirm package structure
- **Documentation Testing** - Validate README updates

### Test Levels
| Level | Coverage | Focus |
|-------|----------|-------|
| Unit | 70% | Migration scripts, path utilities |
| Integration | 80% | Import resolution, module loading |
| Build | 100% | Package installation, dependencies |
| Regression | 100% | Existing functionality preservation |
| Documentation | 100% | README accuracy |

---

## 🔍 Test Scenarios

### 1. File Structure Testing

#### Test Case 1.2.1: Directory Structure Validation
```yaml
Test ID: TC-1.2.1
Priority: HIGH
Type: Structural

Expected Structure:
  ATHintel/
  ├── src/
  │   ├── production/     # Real data only
  │   ├── config/         # Configuration
  │   └── utils/          # Shared utilities
  ├── test/
  │   ├── fixtures/       # Test data (including fake)
  │   └── unit/           # Unit tests
  ├── realdata/           # Production data
  ├── scripts/
  │   └── production/     # Production scripts
  └── docs/               # Documentation

Validation:
  - All directories exist
  - No fakedata/ in root
  - No synthetic data in src/production/
  - Clear separation verified
```

#### Test Case 1.2.2: File Migration Verification
```yaml
Test ID: TC-1.2.2
Priority: CRITICAL
Type: Migration

Test Steps:
  1. Record file checksums before migration
  2. Run migration script
  3. Verify file checksums after migration
  4. Check no files lost
  5. Verify no duplicates created

Expected:
  - All files accounted for
  - Content unchanged (checksum match)
  - Proper categorization
```

### 2. Import Path Testing

#### Test Case 1.2.3: Python Import Resolution
```yaml
Test ID: TC-1.2.3
Priority: CRITICAL
Type: Integration

Test Scenarios:
  - Old: from src.core.analytics import *
  - New: from src.production.analytics import *

Validation:
  - All imports resolve
  - No import errors
  - Circular dependencies resolved
  - __init__.py files updated
```

#### Test Case 1.2.4: Cross-Module Dependencies
```yaml
Test ID: TC-1.2.4
Priority: HIGH
Type: Integration

Test Matrix:
  - production → utils: ✓
  - production → config: ✓
  - production → test: ✗ (should fail)
  - test → production: ✓
  - scripts → production: ✓
```

### 3. Git History Testing

#### Test Case 1.2.5: History Preservation
```yaml
Test ID: TC-1.2.5
Priority: HIGH
Type: Version Control

Validation Steps:
  1. Check git log for moved files
  2. Verify commit history intact
  3. Blame annotations preserved
  4. Branch history maintained

Commands:
  git log --follow src/production/analytics.py
  git blame src/production/analytics.py
```

#### Test Case 1.2.6: Git Operations
```yaml
Test ID: TC-1.2.6
Priority: MEDIUM
Type: Version Control

Test Operations:
  - Checkout previous commits
  - Cherry-pick across reorganization
  - Merge branches post-reorg
  - Rebase operations

Expected:
  - All operations successful
  - No conflicts from structure
```

### 4. Build and Package Testing

#### Test Case 1.2.7: Package Installation
```yaml
Test ID: TC-1.2.7
Priority: HIGH
Type: Build

Test Scenarios:
  - pip install -e .
  - python setup.py install
  - pip install -r requirements.txt

Validation:
  - Installation successful
  - All modules importable
  - Dependencies resolved
```

#### Test Case 1.2.8: CI/CD Pipeline
```yaml
Test ID: TC-1.2.8
Priority: HIGH
Type: Build

Pipeline Stages:
  - Lint check: Pass
  - Unit tests: Pass
  - Integration tests: Pass
  - Build artifacts: Success
  - Deployment: Ready
```

### 5. Regression Testing

#### Test Case 1.2.9: Core Functionality
```yaml
Test ID: TC-1.2.9
Priority: CRITICAL
Type: Regression

Test Areas:
  - Data collection: Working
  - Analytics processing: Working
  - Report generation: Working
  - API endpoints: Responding
  - Database operations: Functional

Validation:
  - All 75 properties process
  - Reports generate correctly
  - No functionality lost
```

#### Test Case 1.2.10: Performance Baseline
```yaml
Test ID: TC-1.2.10
Priority: HIGH
Type: Performance

Metrics:
  - Import time: <2 seconds
  - Module loading: <1 second
  - First operation: <5 seconds
  - Memory usage: No increase

Comparison:
  - Before reorg: X seconds
  - After reorg: Y seconds
  - Degradation: <5%
```

### 6. Migration Script Testing

#### Test Case 1.2.11: Script Execution
```yaml
Test ID: TC-1.2.11
Priority: HIGH
Type: Functional

Test Scenarios:
  - Dry run mode: Preview changes
  - Actual run: Execute migration
  - Rollback: Undo changes
  - Idempotency: Run twice safely

Validation:
  - Script completes without errors
  - Logs all actions
  - Handles edge cases
```

#### Test Case 1.2.12: Error Handling
```yaml
Test ID: TC-1.2.12
Priority: MEDIUM
Type: Negative

Error Scenarios:
  - Permission denied: Graceful failure
  - Disk full: Rollback
  - File in use: Retry logic
  - Network path: Skip with warning
  - Symbolic links: Handle correctly
```

### 7. Documentation Testing

#### Test Case 1.2.13: README Updates
```yaml
Test ID: TC-1.2.13
Priority: MEDIUM
Type: Documentation

Validation:
  - New structure documented
  - Import examples updated
  - Setup instructions current
  - Migration guide included
  - Troubleshooting section
```

#### Test Case 1.2.14: Code Comments
```yaml
Test ID: TC-1.2.14
Priority: LOW
Type: Documentation

Check:
  - File headers updated
  - Import comments accurate
  - TODO items reviewed
  - Deprecated markers added
```

---

## 📊 Test Data Requirements

### Pre-Migration Snapshot
```bash
# Capture current state
find . -type f -name "*.py" | xargs md5sum > pre_migration.md5
tree -I '__pycache__|*.pyc' > pre_migration_structure.txt
git rev-parse HEAD > pre_migration_commit.txt
```

### Post-Migration Validation
```bash
# Verify migration success
find . -type f -name "*.py" | xargs md5sum > post_migration.md5
diff pre_migration.md5 post_migration.md5
```

### Test Fixtures
```
test/fixtures/
├── fake_properties.json      # Synthetic test data
├── invalid_data.json         # Malformed data
├── edge_cases.json          # Boundary conditions
└── performance_dataset.json  # Large dataset
```

---

## 🛠️ Test Automation

### Migration Tests
```python
# tests/test_migration.py

def test_directory_structure():
    """Verify new directory structure exists"""
    assert os.path.exists("src/production")
    assert os.path.exists("test/fixtures")
    assert not os.path.exists("fakedata")
    
def test_import_resolution():
    """Test all imports work after migration"""
    try:
        from src.production.analytics import analyze
        assert analyze is not None
    except ImportError:
        pytest.fail("Import failed after migration")
```

### Regression Tests
```python
# tests/regression/test_functionality.py

def test_core_functionality_preserved():
    """Ensure no functionality lost"""
    # Process test dataset
    result = process_properties("test_data.json")
    assert result.success == True
    assert len(result.properties) == 75
```

### Performance Tests
```python
# tests/performance/test_import_time.py

def test_import_performance():
    """Ensure no significant performance degradation"""
    start = time.time()
    import src.production.analytics
    duration = time.time() - start
    assert duration < 2.0  # Less than 2 seconds
```

---

## 🐛 Bug Categories

### Expected Issues
1. **Import Errors** - Path resolution failures
2. **Missing Files** - Migration script gaps
3. **Permission Issues** - File access problems
4. **Git Conflicts** - Merge issues post-reorg
5. **Build Failures** - Package structure problems

### Priority Levels
- **P1:** Complete failure, no workaround
- **P2:** Major functionality broken
- **P3:** Minor issues, workaround exists
- **P4:** Cosmetic, documentation

---

## ✅ Exit Criteria

### Story Completion Requirements
- [ ] All files successfully migrated
- [ ] Zero import errors
- [ ] Git history preserved
- [ ] CI/CD pipeline green
- [ ] Documentation updated
- [ ] No regression in functionality
- [ ] Performance within 5% of baseline

### Quality Gates
| Gate | Requirement | Status |
|------|------------|--------|
| Migration | 100% files moved | Pending |
| Imports | 0 errors | Pending |
| Regression | 0 failures | Pending |
| Performance | <5% degradation | Pending |
| Documentation | Updated | Pending |

---

## 📅 Test Execution Timeline

### Sprint 1, Week 1
- Day 1: Pre-migration snapshot
- Day 2: Migration execution
- Day 3: Import testing
- Day 4: Regression testing
- Day 5: Documentation review

### Rollback Plan
```bash
# If migration fails
git reset --hard pre_migration_commit
git clean -fd
pip install -e . --force-reinstall
```

---

## 🚨 Risk Mitigation

### High-Risk Areas
1. **Import path changes** - Automated find/replace
2. **Git history loss** - Use git mv exclusively
3. **CI/CD breakage** - Test in branch first
4. **Production impact** - Feature flag protection

### Mitigation Strategies
- Complete backup before migration
- Dry run in test environment
- Incremental migration option
- Automated rollback script
- Parallel old/new structure temporarily

---

## 📝 Test Reports

### Migration Report Format
```
Migration Summary:
- Files moved: X
- Directories created: Y
- Import updates: Z
- Git operations: Successful
- Build status: Green
- Regression tests: X/Y passed
```

### Daily Status
- Files migrated today
- Issues encountered
- Fixes applied
- Tomorrow's plan

---

**Test Plan Status:** APPROVED  
**Created by:** QA Engineer 2  
**Reviewed by:** PM (John)  
**Last Updated:** 2025-09-08

---

## 🔗 Related Documents
- Story 1.2 Requirements (PRD)
- Repository Structure Design
- Migration Script Documentation
- Git Best Practices Guide