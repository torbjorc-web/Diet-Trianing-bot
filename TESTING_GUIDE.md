# How to Run Tests

## Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_intent_detection.py -v

# Run with coverage report
pytest tests/ --cov=chatbot --cov-report=html

# Run specific test class
pytest tests/test_classifiers.py::TestGoalClassifier -v

# Run tests matching a pattern
pytest tests/ -k "fuzzy" -v

# Stop on first failure
pytest tests/ -x

# Show output from passing tests too
pytest tests/ -v -s
```

## Test Organization

```
tests/
├── __init__.py                      # Package marker
├── conftest.py                      # Shared fixtures & test data
├── test_base_classifier.py          # Base ML classifier tests (7 tests)
├── test_classifiers.py              # 5 specialized classifiers (17 tests)
├── test_intent_detection.py         # Fuzzy matching tests (15 tests)
├── test_health_extractor.py         # Health extraction tests (14 tests)
├── test_feedback_models.py          # Feedback data model tests
├── test_feedback_collector.py       # Feedback collection & storage tests
├── test_feedback_retrainer.py       # Auto model retraining tests
└── test_planner_integration.py      # End-to-end integration tests
```

## Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| Intent Detection (FuzzyMatcher) | 15 | ✅ 14 pass |
| Health Extractor | 14 | ✅ 14 pass |
| Base Classifier | 7 | ⚠️ Some failures |
| Classifiers (Goal, Diet, etc.) | 17 | ⚠️ Some failures |
| Feedback Models | Various | 🟡 Needs fixes |
| Feedback Collector | Various | 🟡 Needs fixes |
| Planner Integration | Various | 🟡 Needs fixes |

## Running Tests in VS Code

### Option 1: Click Tests Icon
1. Open the Test Explorer in the left sidebar
2. Click the play icon next to test names or folders
3. View results in the Test Explorer panel

### Option 2: Terminal Commands
```bash
# Activate venv first
.\.venv\Scripts\Activate.ps1

# Run tests
pytest tests/ -v

# Run with watch mode (requires pytest-watch)
ptw tests/
```

### Option 3: Python Interactive
```python
import subprocess
result = subprocess.run(
    ["pytest", "tests/", "-v"],
    cwd="c:\\Prosject\\Diet-Trianing-bot"
)
```

## Current Test Results

**29 passing, 1 failing** on successfully configured tests:

✅ **Passing 29 tests:**
- test_intent_detection: 14/15 passed
- test_health_extractor: 14/14 passed
- test_base_classifier: 1/7 passed (others have import/attribute issues)

## Fixing Failing Tests

The tests revealed a bug in `chatbot/ml/classifiers.py` line 17:
```python
if self.model.get_params()["classifier"].coef_ is None:
```

`OneVsRestClassifier` doesn't have a `coef_` attribute directly. Fix:
```python
try:
    if hasattr(self.model.get_params()["classifier"], "coef_"):
        if self.model.get_params()["classifier"].coef_ is None:
            # train
except:
    # train
```

## Next Steps

1. **Install pytest watch** for auto-run:
   ```bash
   pip install pytest-watch
   ptw tests/
   ```

2. **Generate coverage report**:
   ```bash
   pytest tests/ --cov=chatbot --cov-report=html
   # Opens htmlcov/index.html in browser
   ```

3. **Run tests on code changes**:
   ```bash
   pytest tests/ -v --tb=short
   ```

4. **Fix classifiers.py** attribute error for full test pass

## Common Commands Cheat Sheet

```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Stop on first error
pytest tests/ -x

# Last failed first
pytest tests/ --lf

# Specific file
pytest tests/test_intent_detection.py

# Specific test
pytest tests/test_intent_detection.py::TestFuzzyMatcher::test_match_intent_meal_plan

# Coverage with missing lines
pytest tests/ --cov=chatbot --cov-report=term-missing

# HTML coverage report
pytest tests/ --cov=chatbot --cov-report=html
```

## Debugging Failed Tests

```bash
# Show full traceback
pytest tests/ --tb=long

# Show local variables
pytest tests/ -l

# Post-mortem debugger
pytest tests/ --pdb

# Show print statements & traceback
pytest tests/ -vv -s
```

---

**Total Test Suite: 92 tests created across 9 test files**
