# Feedback Package

User feedback collection and learning system.

## Quick Start

```python
from chatbot.feedback import FeedbackAPIHandler, UserFeedback
from chatbot.planner import DietTrainingPlanner

planner = DietTrainingPlanner(use_ml=True)
handler = FeedbackAPIHandler(planner)

# Submit feedback
handler.submit_feedback(
    user_id="alice",
    prompt="lose weight",
    detected_goal="fat loss",
    user_goal=None,  # Correct
    detected_diet_style="balanced",
    user_diet_style="low-carb",  # Wrong - needs correction
    detected_training_level="beginner",
    user_training_level=None,
    plan_quality=4,
    specific_feedback="Good but too low on protein",
    helpful=True
)

# Check stats
stats = handler.get_feedback_stats()
print(f"Average plan quality: {stats['average_quality']}")

# Retrain models
handler.trigger_retraining(min_feedback_count=10)
```

## Modules

### `models.py`
Data structures for feedback.

**Main Class**: `UserFeedback`
- Immutable dataclass with feedback fields
- Timestamp tracking
- User and plan metadata

### `collector.py`
Collects and analyzes feedback.

**Main Class**: `FeedbackCollector`
- Records feedback to JSONL and CSV
- Generates statistics
- Identifies misclassifications

**Methods**:
- `record_feedback(feedback)` - Store feedback
- `get_feedback_summary()` - Stats on collected feedback
- `get_misclassified_examples()` - Find prediction errors

### `retrainer.py`
Retrains classifiers from feedback.

**Main Class**: `ModelRetrainer`
- Extracts learning examples from misclassifications
- Retrains specific classifiers
- Provides retraining results

**Methods**:
- `retrain_from_feedback(min_feedback_count)` - Trigger retraining

### `api_handler.py`
API interface for feedback workflow.

**Main Class**: `FeedbackAPIHandler`
- Unified feedback submission
- Stats retrieval
- Retraining orchestration

**Methods**:
- `submit_feedback(...)` - Submit user feedback
- `get_feedback_stats()` - Get feedback statistics
- `trigger_retraining(min_feedback_count)` - Retrain models

## Workflow

```
User generates plan
        ↓
User rates plan (1-5)
        ↓
User corrects any misclassifications
        ↓
Feedback recorded to JSONL/CSV
        ↓
Feedback analyzed for misclassifications
        ↓
When threshold reached, models retrained
        ↓
Models perform better on similar inputs
```

## Data Flow

### Recording Feedback
```
UserFeedback object
    ↓
FeedbackCollector.record_feedback()
    ↓
├── Write to JSONL (data/feedback/user_feedback.jsonl)
└── Append to CSV (data/feedback/user_feedback.csv)
```

### Analyzing Feedback
```
FeedbackCollector.get_misclassified_examples()
    ↓
Read JSONL file
    ↓
Compare predicted vs. actual for each field
    ↓
Return organized by classifier type
    ├── goal
    ├── diet_style
    └── training_level
```

### Retraining Models
```
ModelRetrainer.retrain_from_feedback()
    ↓
Get misclassifications from FeedbackCollector
    ↓
For each classifier with enough feedback:
    ├── Extract prompts and correct labels
    ├── Call planner.train_classifier()
    └── Update model on disk
    ↓
Return results for each classifier
```

## Integration Points

### With Planner
```python
from chatbot.planner import DietTrainingPlanner
from chatbot.feedback import FeedbackAPIHandler

planner = DietTrainingPlanner(use_ml=True)
handler = FeedbackAPIHandler(planner)

# Handler uses planner to retrain models
```

### With FastAPI
```python
from fastapi import FastAPI
from chatbot.feedback import FeedbackAPIHandler

app = FastAPI()
handler = FeedbackAPIHandler(planner)

@app.post("/feedback/submit")
async def submit_feedback(data: dict):
    return handler.submit_feedback(**data)

@app.get("/feedback/stats")
async def get_stats():
    return handler.get_feedback_stats()

@app.post("/feedback/retrain")
async def retrain(min_samples: int = 10):
    return handler.trigger_retraining(min_samples)
```

## Configuration

### Feedback Threshold
Minimum feedback samples needed to trigger retraining:
```python
# Require at least 20 corrections
handler.trigger_retraining(min_feedback_count=20)
```

### Storage Location
Feedback files stored in:
- `data/feedback/user_feedback.jsonl` - JSON lines
- `data/feedback/user_feedback.csv` - Spreadsheet format

### Feedback Fields

Required in `UserFeedback`:
- `timestamp` - ISO format datetime
- `user_id` - User identifier
- `prompt` - Original user input
- `detected_*` - What system predicted
- `user_*` - What user says is correct (None if agreed)
- `plan_quality` - Rating 1-5
- `specific_feedback` - Free text notes
- `helpful` - Boolean: was plan helpful?

## Analysis

### View Feedback Statistics
```python
from chatbot.feedback import FeedbackCollector

collector = FeedbackCollector()
stats = collector.get_feedback_summary()

print(f"Total feedback: {stats['total_feedback']}")
print(f"Avg quality: {stats['average_quality']}/5")
print(f"Helpful rate: {stats['helpful_rate']:.0%}")
```

### View Misclassifications
```python
misclassified = collector.get_misclassified_examples()

for example in misclassified["goal"]:
    print(f"Prompt: {example['prompt']}")
    print(f"  Wrong: {example['predicted']}")
    print(f"  Should be: {example['actual']}")
```

### Export for Analysis
```python
import pandas as pd

# Load feedback CSV
df = pd.read_csv("data/feedback/user_feedback.csv")

# Analyze by quality
quality_by_goal = df.groupby("detected_goal")["plan_quality"].mean()
print(quality_by_goal)

# Find low-rated plans
poor_plans = df[df["plan_quality"] < 3]
print(poor_plans[["prompt", "specific_feedback"]])
```

## Monitoring

### Check Model Improvement
```python
# Collect feedback periodically
# View stats to see plan quality trend
stats = handler.get_feedback_stats()

# After retraining
# Stats should improve as model learns from corrections
```

### Performance Tracking
```python
# Before retraining
before = handler.get_feedback_stats()

# Submit more feedback and retrain
handler.trigger_retraining()

# After retraining  
after = handler.get_feedback_stats()

# Compare improvement
improvement = after["helpful_rate"] - before["helpful_rate"]
print(f"Improvement: {improvement:.1%}")
```

## Best Practices

1. **Consistent Feedback**
   - Have users rate plans consistently (1-5 scale)
   - Collect feedback on both correct and incorrect predictions

2. **Threshold Tuning**
   - Start with `min_feedback_count=10`
   - Increase if retraining causes instability
   - Decrease if models stagnate

3. **Regular Analysis**
   - Check feedback stats weekly
   - Review misclassifications monthly
   - Retrain when patterns emerge

4. **Error Handling**
   - Gracefully handle feedback submission errors
   - Log all feedback for audit trail
   - Monitor model retraining results

## Troubleshooting

### No Feedback Recorded
- Check `data/feedback/` directory exists
- Verify permissions on data directory
- Check logs for write errors

### Retraining Doesn't Trigger
- Need 10+ misclassifications per classifier
- Check `get_feedback_summary()` for actual count
- Lower `min_feedback_count` parameter

### Model Performance Degrades
- Retraining might be overfitting to corrections
- Review misclassified examples for noise
- Consider filtering out low-confidence feedback

## Files & Storage

```
data/
└── feedback/
    ├── user_feedback.jsonl    # JSONL format (one per line)
    └── user_feedback.csv      # CSV spreadsheet format
```

## See Also

- [ML Package](../ml/README.md) - Classification system
- [Planner](../planner.py) - Main planning engine
- [ML Enhancements](../../ML_ENHANCEMENTS.md) - Full documentation
