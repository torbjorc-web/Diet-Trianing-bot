# ML Package Structure

## Overview

The machine learning system is split into two specialized packages:

- **`ml/`** - Classification and intent detection
- **`feedback/`** - User feedback collection and model retraining

## ML Package (`chatbot/ml/`)

Handles all classification and intent detection logic.

### Modules

#### `base_classifier.py`
Base class for all ML classifiers. Provides:
- Model training and persistence
- Prediction with confidence scores
- Automatic model loading/saving

**Usage**:
```python
from chatbot.ml.base_classifier import MLClassifier

class MyClassifier(MLClassifier):
    CLASSES = ["class1", "class2"]
    
    def __init__(self):
        super().__init__("my_classifier", self.CLASSES)
```

#### `classifiers.py`
Five specialized classifier implementations:
- `GoalClassifier` - Fitness goals (fat loss, muscle gain, etc.)
- `DietStyleClassifier` - Diet preferences (vegan, keto, etc.)
- `MealPreferenceClassifier` - Dietary restrictions (halal, kosher, etc.)
- `TrainingLevelClassifier` - Experience levels (beginner, intermediate, advanced)
- `TrainingSettingClassifier` - Training environment (self, studio, group)

**Usage**:
```python
from chatbot.ml import GoalClassifier

classifier = GoalClassifier()
goal, confidence = classifier.predict("lose weight fast")
# Returns: ("fat loss", 0.92)

# Train on custom examples
classifier.train(["I want to gain muscle"], ["muscle gain"])
```

#### `intent_detection.py`
Fuzzy string matching for robust intent detection.

**Features**:
- Typo tolerance
- Partial phrase matching
- Configurable thresholds

**Usage**:
```python
from chatbot.ml import FuzzyMatcher

intent = FuzzyMatcher.match_intent("give me a meel plan")
# Returns: {"wants_meal_plan": True, "wants_training_plan": False}

# Match against options
best_match = FuzzyMatcher.match_value("vegn", ["vegan", "vegetarian"])
# Returns: "vegan"
```

#### `health_extractor.py`
Extracts health conditions and constraints from prompts.

**Features**:
- Pattern-based extraction (e.g., "health notes: ...")
- Keyword recognition (knee, diabetes, etc.)
- Normalized health notes

**Usage**:
```python
from chatbot.ml import HealthConditionExtractor

health = HealthConditionExtractor.extract("I have knee pain and asthma")
# Returns: "knee pain/issues, asthma"
```

### Package-Level Imports

```python
from chatbot.ml import (
    GoalClassifier,
    DietStyleClassifier,
    MealPreferenceClassifier,
    TrainingLevelClassifier,
    TrainingSettingClassifier,
    FuzzyMatcher,
    HealthConditionExtractor,
)
```

## Feedback Package (`chatbot/feedback/`)

Handles user feedback collection, analysis, and automatic model retraining.

### Modules

#### `models.py`
Data model for user feedback.

**Usage**:
```python
from chatbot.feedback import UserFeedback
from datetime import datetime

feedback = UserFeedback(
    timestamp=datetime.now().isoformat(),
    user_id="alice",
    prompt="lose weight fast",
    detected_goal="fat loss",
    user_goal=None,  # User confirmed correct
    detected_diet_style="balanced",
    user_diet_style="low-carb",  # User corrected
    detected_training_level="beginner",
    user_training_level=None,
    plan_quality=4,
    specific_feedback="Too intense",
    helpful=True
)
```

#### `collector.py`
Records and analyzes user feedback.

**Features**:
- JSONL storage for streaming
- CSV export for analysis
- Feedback statistics
- Misclassification detection

**Usage**:
```python
from chatbot.feedback import FeedbackCollector, UserFeedback

collector = FeedbackCollector()

# Record feedback
collector.record_feedback(feedback)

# Get statistics
stats = collector.get_feedback_summary()
# Returns: {
#     "total_feedback": 150,
#     "average_quality": 4.2,
#     "helpful_rate": 0.87,
#     "last_recorded": "2024-01-28T10:30:00"
# }

# Find misclassifications
misclassified = collector.get_misclassified_examples()
# Returns: {
#     "goal": [{"prompt": "...", "predicted": "...", "actual": "..."}],
#     "diet_style": [...],
#     "training_level": [...]
# }
```

#### `retrainer.py`
Automatically retrains models using collected feedback.

**Features**:
- Extracts learning examples from misclassifications
- Trains specific classifiers
- Threshold-based triggering

**Usage**:
```python
from chatbot.feedback import ModelRetrainer

retrainer = ModelRetrainer(planner)

# Retrain models when enough feedback collected
results = retrainer.retrain_from_feedback(min_feedback_count=10)
# Returns: {
#     "goal": {"success": True, "examples_used": 15},
#     "diet_style": {"success": True, "examples_used": 12}
# }
```

#### `api_handler.py`
API interface for feedback submission and retraining.

**Features**:
- Unified feedback submission
- Feedback statistics retrieval
- Programmatic retraining trigger

**Usage**:
```python
from chatbot.feedback import FeedbackAPIHandler

handler = FeedbackAPIHandler(planner)

# Submit feedback
result = handler.submit_feedback(
    user_id="alice",
    prompt="lose weight fast",
    detected_goal="fat loss",
    user_goal=None,
    detected_diet_style="balanced",
    user_diet_style="low-carb",
    detected_training_level="beginner",
    user_training_level=None,
    plan_quality=4,
    specific_feedback="Too intense",
    helpful=True
)

# Get stats
stats = handler.get_feedback_stats()

# Trigger retraining
retraining = handler.trigger_retraining(min_feedback_count=10)
```

### Package-Level Imports

```python
from chatbot.feedback import (
    UserFeedback,
    FeedbackCollector,
    ModelRetrainer,
    FeedbackAPIHandler,
)
```

## Integration with Planner

The `DietTrainingPlanner` integrates both packages:

```python
from chatbot.planner import DietTrainingPlanner
from chatbot.feedback import FeedbackAPIHandler

# Create planner with ML enabled
planner = DietTrainingPlanner(use_ml=True)

# Create feedback handler
feedback_handler = FeedbackAPIHandler(planner)

# Generate plan
prompt = "lose weight fast"
plan = planner.build_plan("alice", prompt)

# Collect feedback
feedback_handler.submit_feedback(
    user_id="alice",
    prompt=prompt,
    detected_goal="fat loss",  # From planner
    user_goal="fat loss",
    # ... other fields
    helpful=True
)

# Retrain models
feedback_handler.trigger_retraining()
```

## Data Storage

### ML Models
- **Location**: `data/ml_models/`
- **Format**: Pickle files
- **Files**: `{classifier_type}_model.pkl` and `{classifier_type}_vectorizer.pkl`

### User Feedback
- **JSONL**: `data/feedback/user_feedback.jsonl` (for ML processing)
- **CSV**: `data/feedback/user_feedback.csv` (for analysis)

## Architecture Benefits

1. **Modularity** - Each package has a single purpose
2. **Scalability** - Easy to add classifiers or feedback modules
3. **Testability** - Independent unit testing per module
4. **Reusability** - Use packages in other projects
5. **Maintainability** - Clear separation of concerns

## Adding Features

### New Classifier
1. Edit `chatbot/ml/classifiers.py`
2. Add class inheriting from `MLClassifier`
3. Export in `chatbot/ml/__init__.py`
4. Use in planner

### New Feedback Module
1. Create `chatbot/feedback/new_module.py`
2. Implement your logic
3. Export in `chatbot/feedback/__init__.py`
4. Integrate with planner or API handler

## Testing

Each module can be tested independently:

```python
# Test ML classifier
def test_goal_classifier():
    classifier = GoalClassifier()
    goal, conf = classifier.predict("lose weight")
    assert goal == "fat loss"

# Test feedback collector
def test_feedback_collector():
    collector = FeedbackCollector()
    feedback = UserFeedback(...)
    collector.record_feedback(feedback)
    assert collector.get_feedback_summary()["total_feedback"] > 0
```

See `tests/` directory for comprehensive test examples.
