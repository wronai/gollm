# TODO List - Updated: 2025-06-01 14:23:15

## 🔴 HIGH Priority (Auto-generated by goLLM)

### Code Quality Violations - `examples/bad_code.py`
- [ ] **CRITICAL: Function `process_user_data()` has 10 parameters (max: 5)**
  - **Created:** 2025-06-01 14:23:15
  - **Source:** goLLM Auto-validation
  - **Impact:** Maintainability Risk
  - **Suggested Fix:** Use dataclass or configuration object
  - **Estimated Effort:** 5-10 minutes

- [ ] **Remove global variable usage (2 instances)**
  - **Created:** 2025-06-01 14:23:15
  - **Location:** `examples/bad_code.py:17, 28`
  - **Suggested Fix:** Use class attributes or pass as parameters
  - **Estimated Effort:** 30-60 minutes

- [ ] **Fix naming convention violations (CamelCase → snake_case)**
  - **Created:** 2025-06-01 14:23:15
  - **Functions:** `processDataAndReturnResults`, variables in function
  - **Estimated Effort:** 15-30 minutes

## 🟢 LOW Priority

### Documentation Improvements
- [ ] **Add docstrings to functions missing documentation**
  - **Created:** 2025-06-01 14:23:15
  - **Functions:** `process_user_data()`, `another_long_function()`, `processDataAndReturnResults()`
  - **Template Available:** ✅ `gollm generate-docstring`
  - **Estimated Effort:** 15-30 minutes per function

- [ ] **Add class documentation for `ExampleClass`**
  - **Created:** 2025-06-01 14:23:15
  - **Location:** `examples/bad_code.py:89`
  - **Estimated Effort:** 10-15 minutes

### Refactoring Opportunities
- [ ] **Extract complex logic in `another_long_function()` to separate methods**
  - **Created:** 2025-06-01 14:23:15
  - **Benefit:** Improved testability and readability
  - **Estimated Effort:** 45-60 minutes

---
*This file is automatically managed by goLLM*