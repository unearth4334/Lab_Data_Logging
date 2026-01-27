# Device Driver Documentation

This directory contains comprehensive documentation for maintaining and developing device drivers in the `libs/` directory.

## 📚 Documentation Index

### 1. [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
**The Gold Standard Reference**

Complete technical specification for all device drivers including:
- File structure and imports
- Connection management patterns
- Error handling requirements
- Console output standards
- Measurement method conventions
- API interface design
- Type hints and documentation
- Complete code examples

**Use this when:**
- Creating a new device driver
- Need detailed technical specifications
- Looking for best practices and patterns
- Want comprehensive code examples

---

### 2. [LIBS_CONSISTENCY_PLAN.md](./LIBS_CONSISTENCY_PLAN.md)
**Implementation Roadmap**

Comprehensive plan for improving consistency across all existing drivers:
- Current state analysis with file scores
- Phased implementation roadmap (9 weeks)
- Breaking changes documentation
- Testing strategy
- Success metrics
- Risk assessment

**Use this when:**
- Planning driver refactoring work
- Need to understand project scope
- Want to track improvement progress
- Looking for testing requirements

---

### 3. [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md)
**Quick Lookup Guide**

Fast reference for common patterns and issues:
- Quick comparison table (bad vs. good)
- Common code patterns
- Most frequent issues and fixes
- Checklist for new drivers
- Priority order for fixes

**Use this when:**
- Need a quick answer
- Fixing a specific issue
- Want to see before/after examples
- Creating a driver checklist

---

## 🎯 Quick Start

### For New Drivers
1. Read [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md) checklist
2. Copy template from [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
3. Reference `libs/DMM6500.py` as example
4. Test with hardware

### For Updating Existing Drivers
1. Check your file's score in [LIBS_CONSISTENCY_PLAN.md](./LIBS_CONSISTENCY_PLAN.md)
2. Review priority issues in [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md)
3. Follow patterns in [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
4. Test backward compatibility

### For Code Reviews
1. Use checklist from [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md)
2. Verify compliance with [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
3. Check for common issues in [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md)

---

## 📊 Current Status

### Driver Quality Overview

| Status | Count | Files |
|--------|-------|-------|
| ✅ Excellent (90-100) | 2 | DMM6500, StanfordPS310 |
| 🟡 Good (70-89) | 4 | KeysightMSOX4154A, Keysight34460A, RigolDS7034, RigolDP832 |
| 🟠 Fair (40-69) | 1 | U1233A |
| 🔴 Needs Work (0-39) | 7 | KS33500B, DL3021, EPS, FLUKE45, KA3010P, DAC, DP832 |

### Top Priorities
1. **Remove hardcoded COM ports** (DAC, EPS, FLUKE45, KA3010P)
2. **Add disconnect() methods** (5 files missing)
3. **Replace bare except blocks** (39 in KeysightMSOX4154A alone!)
4. **Add type hints** (7 files have none)
5. **Add docstrings** (3 files have 0% coverage)

See [LIBS_CONSISTENCY_PLAN.md](./LIBS_CONSISTENCY_PLAN.md) for detailed roadmap.

---

## 🏆 Best Practice Examples

### Excellent Examples (Use as Templates)
- **`libs/DMM6500.py`** (Score: 95/100)
  - Full type hints with future annotations
  - Comprehensive docstrings
  - Proper exception handling
  - Auto-connect + explicit addressing
  - Statistics support
  
- **`libs/StanfordPS310.py`** (Score: 90/100)
  - Excellent logging and debug mode
  - Environment variable configuration
  - Glitch filtering
  - Detailed documentation

### Good Examples (Follow Most Patterns)
- **`libs/KeysightMSOX4154A.py`** - Complex oscilloscope with waveform capture
- **`libs/Keysight34460A.py`** - Good docstrings, needs type hints
- **`libs/RigolDS7034.py`** - Excellent docstrings, needs type hints

---

## 🔧 Common Issues and Solutions

### Issue: Bare Except Blocks
**Current state:** 11/14 files have bare `except:` blocks  
**Solution:** Use specific exceptions (`pyvisa.VisaIOError`, `serial.SerialException`)  
**Reference:** [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md) - Error Handling section

### Issue: Hardcoded Ports
**Current state:** 4 serial drivers have hardcoded COM ports  
**Solution:** Add `com_port` parameter with auto-detection  
**Reference:** [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md) - Connection Management section

### Issue: Missing Type Hints
**Current state:** 7/14 files have no type hints  
**Solution:** Add `from __future__ import annotations` and type all public methods  
**Reference:** [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md) - Type Hints section

### Issue: Inconsistent Returns
**Current state:** `get()` returns `float`, `(value, 0)`, or `List[float]` inconsistently  
**Solution:** Standardize return types per measurement type  
**Reference:** [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md) - API Interface section

---

## 📝 Contributing

When contributing driver code:

1. **Read the Standard** - Review [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
2. **Use the Checklist** - Follow [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md)
3. **Test Thoroughly** - Verify with hardware if possible
4. **Document Changes** - Update docstrings and examples
5. **Maintain Compatibility** - Ensure data_logger.py still works

### Code Review Checklist
- [ ] Type hints on all public methods
- [ ] Docstrings on class and public methods
- [ ] No bare `except:` blocks
- [ ] `disconnect()` method present
- [ ] No hardcoded addresses/ports
- [ ] Standard console output styles
- [ ] Standard method naming
- [ ] Backward compatibility verified

---

## 📈 Metrics and Goals

### Current Metrics (as of Jan 2026)
- **Average file score:** 54/100
- **Files with type hints:** 7/14 (50%)
- **Files with 100% docstrings:** 4/14 (29%)
- **Files with disconnect():** 9/14 (64%)
- **Files with hardcoded ports:** 4/14 (29%)

### Goals (End of Q1 2026)
- **Average file score:** ≥70/100
- **Files with type hints:** 14/14 (100%)
- **Files with 100% docstrings:** 14/14 (100%)
- **Files with disconnect():** 14/14 (100%)
- **Files with hardcoded ports:** 0/14 (0%)

---

## 🎓 Learning Path

### For New Contributors
1. **Week 1:** Read [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md)
2. **Week 2:** Study `libs/DMM6500.py` and `libs/StanfordPS310.py`
3. **Week 3:** Read full [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
4. **Week 4:** Update one low-priority driver (follow [LIBS_CONSISTENCY_PLAN.md](./LIBS_CONSISTENCY_PLAN.md))

### For Experienced Developers
1. Review [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md) for patterns
2. Check [LIBS_CONSISTENCY_PLAN.md](./LIBS_CONSISTENCY_PLAN.md) for priorities
3. Pick high-priority refactoring tasks
4. Use [DEVICE_DRIVER_QUICK_REFERENCE.md](./DEVICE_DRIVER_QUICK_REFERENCE.md) as reference

---

## 🔗 Related Resources

### Internal
- **Main README:** `../README.md`
- **Driver Source:** `../libs/`
- **Data Logger:** `../data_logger.py`

### External
- [PyVISA Documentation](https://pyvisa.readthedocs.io/)
- [PySerial Documentation](https://pyserial.readthedocs.io/)
- [Python Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Python Docstrings (PEP 257)](https://www.python.org/dev/peps/pep-0257/)
- [Python Style Guide (PEP 8)](https://pep8.org/)

---

## 📞 Support

- **Questions:** Open an issue on GitHub
- **Bugs:** Report in issue tracker with driver name
- **Feature Requests:** Discuss in issues before implementing

---

**Last Updated:** January 27, 2026  
**Maintained By:** Lab Data Logging Team  
**Version:** 1.0
