# libs/ Consistency Improvement Plan

## Executive Summary

This document outlines the comprehensive plan to improve consistency across all device driver files in the `libs/` directory. After analyzing 14 driver files, we identified significant inconsistencies in code quality, API design, error handling, and documentation.

**Key Findings:**
- **9 PyVISA-based drivers** and **4 PySerial-based drivers**
- Quality scores range from **15/100 (DAC.py)** to **95/100 (DMM6500.py)**
- **7 files** require major refactoring (Tier 3, score <40)
- **5 files** need moderate updates (Tier 2, score 70-85)
- **2 files** serve as excellent templates (Tier 1, score >85)

**Impact:**
- Improved maintainability and code reuse
- Reduced bugs from inconsistent error handling
- Easier onboarding for new contributors
- Better integration with data_logger.py

---

## Current State Analysis

### Device Driver Inventory

| File | Type | Lines | Score | Status | Priority |
|------|------|-------|-------|--------|----------|
| DMM6500.py | VISA | 417 | 95 | ✅ Excellent | Template |
| StanfordPS310.py | VISA | ~800 | 90 | ✅ Very Good | Template |
| KeysightMSOX4154A.py | VISA | ~1000 | 85 | 🟡 Good | Low |
| Keysight34460A.py | VISA | 347 | 75 | 🟡 Fair | Medium |
| RigolDS7034.py | VISA | ~900 | 72 | 🟡 Fair | Medium |
| RigolDP832.py | VISA | ~650 | 70 | 🟡 Fair | Medium |
| U1233A.py | Serial | 141 | 45 | 🟠 Poor | Medium |
| KS33500B.py | VISA | 70 | 35 | 🔴 Very Poor | High |
| DL3021.py | VISA | 253 | 30 | 🔴 Very Poor | High |
| EPS.py | Serial | 105 | 25 | 🔴 Very Poor | High |
| FLUKE45.py | Serial | 60 | 20 | 🔴 Very Poor | High |
| KA3010P.py | Serial | 104 | 20 | 🔴 Very Poor | High |
| DAC.py | Serial | 55 | 15 | 🔴 Very Poor | High |
| DP832.py | VISA | 154 | 15 | 🔴 Very Poor | High |

### Major Issues by Category

#### 1. Connection Management
**Problems:**
- ❌ 5 files have hardcoded COM ports (DAC: COM10, EPS: COM16, FLUKE45: COM7, KA3010P: COM19)
- ❌ 4 files lack `auto_connect` parameter
- ❌ Inconsistent address detection strategies

**Goal:** All drivers support both auto-detection and explicit addressing

#### 2. Error Handling
**Problems:**
- ❌ KeysightMSOX4154A.py has **39 bare except blocks**
- ❌ StanfordPS310.py has **19 bare except blocks**
- ❌ RigolDP832.py has **20 bare except blocks**
- ❌ 8 files use `except:` without specifying exception type

**Goal:** Replace all bare except with specific exception types

#### 3. API Consistency
**Problems:**
- ❌ Inconsistent `get()` return types:
  - DMM6500: Returns `float` directly
  - DAC/KA3010P: Returns `(value, 0)` tuple
  - DL3021: Returns either `(value, 0)` or `(mean, stdev)` inconsistently
  - RigolDS7034: Returns `float` or `List[float]` depending on item
- ❌ Method naming: `meas()` vs `measure()` vs `measure_voltage()`

**Goal:** Standardize return types and method naming across all drivers

#### 4. Documentation
**Problems:**
- ❌ 3 files have 0% docstring coverage (DP832, KS33500B, FLUKE45)
- ❌ 7 files lack type hints completely
- ❌ Inconsistent docstring styles

**Goal:** 100% docstring coverage and type hints for all public methods

#### 5. Disconnect Handling
**Problems:**
- ❌ 5 files lack `disconnect()` method (DAC, DP832, DL3021, KS33500B, KA3010P)

**Goal:** All drivers implement proper resource cleanup

---

## Gold Standard Definition

We have created a comprehensive gold standard documented in:
- **[DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)** - Complete reference

**Key Standards:**
1. **File Structure**: Header, imports, constants, class, tests
2. **Imports**: `from __future__ import annotations`, proper typing
3. **Connection**: `auto_connect` parameter, address fallback, auto-detection
4. **Error Handling**: Specific exceptions only, no bare except
5. **Console Output**: Standardized `_ERROR_STYLE`, `_SUCCESS_STYLE`, `_WARNING_STYLE`
6. **API**: Standard `get()` method with consistent returns
7. **Type Hints**: All public methods must have type hints
8. **Documentation**: Docstrings for all classes and public methods
9. **Disconnect**: Proper resource cleanup with status update

**Template Files:**
- Primary: `DMM6500.py` (95/100 score)
- Secondary: `StanfordPS310.py` (90/100 score)

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal:** Establish standards and templates

- [x] Create DEVICE_DRIVER_STANDARD.md documentation
- [x] Create LIBS_CONSISTENCY_PLAN.md roadmap
- [ ] Review and finalize standards with team
- [ ] Create abstract BaseDevice class (optional, if team agrees)
- [ ] Create migration guide for developers
- [ ] Set up pre-commit hooks for style enforcement

**Deliverables:**
- Complete documentation
- Team approval on standards
- Migration guidelines

### Phase 2: High-Priority Refactoring (Weeks 2-4)
**Goal:** Fix Tier 3 files (score <40)

#### Week 2: Serial Devices
- [ ] **DAC.py** (Score: 15)
  - Remove hardcoded COM10
  - Add `auto_connect` parameter with port selection
  - Add `disconnect()` method
  - Add type hints and docstrings
  - Replace bare except with specific exceptions
  
- [ ] **FLUKE45.py** (Score: 20)
  - Remove hardcoded COM7
  - Rename `meas()` to `measure_voltage()`
  - Add comprehensive docstrings
  - Add type hints

- [ ] **KA3010P.py** (Score: 20)
  - Remove hardcoded COM19
  - Add `disconnect()` method
  - Standardize return types in `get()`
  - Add docstrings and type hints

- [ ] **EPS.py** (Score: 25)
  - Remove hardcoded COM16
  - Fix commented-out interpolation (line 68)
  - Add comprehensive docstrings
  - Improve error handling

#### Week 3: VISA Devices Part 1
- [ ] **DP832.py** (Score: 15)
  - Add `disconnect()` method
  - Replace bare except with specific exceptions
  - Add comprehensive docstrings
  - Add type hints
  - Improve connection detection

- [ ] **KS33500B.py** (Score: 35)
  - Add comprehensive error handling
  - Add `disconnect()` method
  - Add docstrings and type hints
  - Improve auto-detection

#### Week 4: VISA Devices Part 2
- [ ] **DL3021.py** (Score: 30)
  - Fix inconsistent `get()` return types (lines 52, 55)
  - Add `disconnect()` method
  - Add comprehensive docstrings
  - Add type hints
  - Improve error handling

**Testing:**
- [ ] Create test suite for each updated driver
- [ ] Verify backward compatibility with data_logger.py
- [ ] Test with actual hardware (if available)

### Phase 3: Medium-Priority Updates (Weeks 5-7)
**Goal:** Update Tier 2 files (score 70-85)

#### Week 5: Major Updates
- [ ] **KeysightMSOX4154A.py** (Score: 85)
  - **Critical:** Reduce 39 bare except blocks to specific exceptions
  - Improve error messages
  - Add debug logging for troubleshooting

- [ ] **RigolDP832.py** (Score: 70)
  - Add type hints throughout
  - Simplify voltage/current configuration state tracking
  - Improve docstrings

#### Week 6: Type Hints
- [ ] **RigolDS7034.py** (Score: 72)
  - Add comprehensive type hints
  - Reduce bare except blocks
  - Improve screenshot handling documentation

- [ ] **Keysight34460A.py** (Score: 75)
  - Add type hints to all methods
  - Replace generic `except:` with specific exceptions
  - Improve docstrings

#### Week 7: Serial Device
- [ ] **U1233A.py** (Score: 45)
  - Simplify COM port selection logic
  - Add type hints
  - Improve error messages
  - Better environment variable handling

**Testing:**
- [ ] Regression tests for all updated drivers
- [ ] Performance benchmarks
- [ ] Documentation review

### Phase 4: Low-Priority Polish (Week 8)
**Goal:** Minor improvements to Tier 1 files

- [ ] **StanfordPS310.py** (Score: 90)
  - Reduce 19 bare except blocks
  - Review and optimize glitch filtering
  - Minor documentation improvements

- [ ] **DMM6500.py** (Score: 95)
  - Review for any minor improvements
  - Ensure it serves as best-practice template

**Testing:**
- [ ] Final integration tests
- [ ] Code quality metrics
- [ ] Documentation completeness

### Phase 5: Validation & Documentation (Week 9)
**Goal:** Finalize and document all changes

- [ ] Update main README.md
- [ ] Create driver development guide
- [ ] Document breaking changes (if any)
- [ ] Create migration guide for existing code
- [ ] Add examples demonstrating best practices
- [ ] Final code review with team
- [ ] Create release notes

---

## Breaking Changes

### Potential Breaking Changes
The following changes may affect existing code:

1. **get() Return Type Standardization**
   - **Current:** Some drivers return `(value, 0)`, others return `float` or `List[float]`
   - **Proposed:** Standardize to return `float` for single values, `Tuple[float, float, float, float]` for statistics
   - **Migration:** Update data_logger.py to handle both old and new patterns during transition

2. **Method Renaming**
   - **Current:** `meas()` in FLUKE45, DAC
   - **Proposed:** Rename to `measure_voltage()`, `measure_current()`, etc.
   - **Migration:** Add deprecated wrapper methods for backward compatibility

3. **Connection Parameters**
   - **Current:** Some __init__ methods have no parameters
   - **Proposed:** Add `auto_connect` and `address` parameters
   - **Migration:** Default `auto_connect=True` maintains backward compatibility

### Backward Compatibility Strategy

To maintain compatibility during transition:

```python
# Option 1: Dual return support
def get(self, item: str) -> Union[float, Tuple[float, float]]:
    """Support both old and new return types."""
    value = self.measure_voltage()
    if os.environ.get('LAB_DATA_LOGGING_LEGACY_MODE') == '1':
        return (value, 0)  # Old format
    return value  # New format

# Option 2: Deprecated method warnings
def meas(self):
    """Deprecated: Use measure_voltage() instead."""
    import warnings
    warnings.warn("meas() is deprecated, use measure_voltage()", DeprecationWarning)
    return self.measure_voltage()
```

---

## Testing Strategy

### Unit Tests
- [ ] Connection handling (auto-detect, explicit address, failure cases)
- [ ] Error handling (specific exceptions, error messages)
- [ ] Measurement methods (return types, ranges)
- [ ] Disconnect handling (resource cleanup)
- [ ] get() method interface (all valid items)

### Integration Tests
- [ ] data_logger.py integration
- [ ] Multi-device scenarios
- [ ] Error propagation to calling code

### Hardware Tests (if available)
- [ ] Real device connections
- [ ] Measurement accuracy
- [ ] Performance benchmarks
- [ ] Long-running stability

### Test Coverage Goals
- **Minimum:** 80% code coverage
- **Target:** 90% code coverage for new/updated code

---

## Success Metrics

### Code Quality Metrics
- **All files score ≥70/100** on modernization scale
- **Zero bare except blocks** in production code
- **100% docstring coverage** for public APIs
- **100% type hint coverage** for public methods

### Consistency Metrics
- **Standardized connection handling** across all drivers
- **Consistent get() return types** documented and tested
- **Uniform error handling** patterns
- **Common console output styles**

### Documentation Metrics
- **Complete API documentation** for all drivers
- **Migration guide** for existing code
- **Examples** for each driver pattern
- **Developer onboarding guide**

---

## Risk Assessment

### High Risk
- **Breaking existing integrations** with data_logger.py
  - Mitigation: Maintain backward compatibility wrappers
  - Testing: Comprehensive integration tests

- **Hardware unavailability** for testing
  - Mitigation: Mock testing + community validation
  - Fallback: Phased rollout by device availability

### Medium Risk
- **Team disagreement** on standards
  - Mitigation: Early review and feedback cycles
  - Fallback: Vote on controversial decisions

- **Scope creep** beyond consistency improvements
  - Mitigation: Strict adherence to roadmap phases
  - Monitoring: Weekly progress reviews

### Low Risk
- **Performance degradation** from type checking
  - Note: Type hints have no runtime cost in Python
  - Monitoring: Benchmark critical paths

---

## Resources Required

### Developer Time
- **Phase 1:** 20 hours (documentation, standards)
- **Phase 2:** 60 hours (7 high-priority files)
- **Phase 3:** 40 hours (5 medium-priority files)
- **Phase 4:** 10 hours (2 low-priority files)
- **Phase 5:** 20 hours (testing, documentation)
- **Total:** ~150 hours (~4 weeks full-time)

### Hardware Access
- Keysight 34460A Multimeter
- Keysight MSOX4154A Oscilloscope
- Keithley DMM6500
- Rigol DP832 Power Supply
- Rigol DS7034 Oscilloscope
- Stanford PS310 Power Supply
- Various serial devices (if available)

### Tools & Infrastructure
- Python 3.8+ environment
- PyVISA library and drivers
- Pre-commit hooks for style enforcement
- CI/CD pipeline for automated testing
- Documentation hosting (GitHub Pages or similar)

---

## Long-Term Maintenance

### Post-Implementation
1. **Enforce standards** for all new drivers
2. **Code review checklist** based on DEVICE_DRIVER_STANDARD.md
3. **Automated linting** to catch common issues
4. **Quarterly review** of driver quality metrics
5. **Community contribution guide** for external developers

### Continuous Improvement
- Collect feedback from driver users
- Monitor error rates and common issues
- Update standards based on lessons learned
- Maintain compatibility with new PyVISA/pyserial versions

---

## Approval & Sign-off

**Document Author:** GitHub Copilot Agent  
**Date:** January 27, 2026  
**Status:** Draft - Pending Review

**Reviewers:**
- [ ] Project Lead
- [ ] Lead Developer
- [ ] Hardware Lab Manager
- [ ] Documentation Lead

**Approvals:**
- [ ] Technical Review Complete
- [ ] Resource Allocation Approved
- [ ] Timeline Approved
- [ ] Standards Finalized

---

## Appendix A: File-by-File Analysis

See individual file analysis in the initial assessment (available on request).

## Appendix B: Code Examples

See DEVICE_DRIVER_STANDARD.md for comprehensive code examples.

## Appendix C: Migration Guide

To be created in Phase 1 after standards approval.

---

**Questions or Feedback?**
- Create an issue on GitHub
- Contact the maintainers
- Review DEVICE_DRIVER_STANDARD.md for technical details
