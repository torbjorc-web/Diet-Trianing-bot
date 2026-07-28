# ML System Data Flow Diagram

## Complete Request-Response Flow

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         INCOMING USER REQUEST                              ║
║           "lose weight fast, vegan, I weigh 78kg, beginner level"         ║
║                  prompt: str, user_id: str                                 ║
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    1. INTENT DETECTION                                     ║
║               chatbot/ml/intent_detection.py                               ║
║                      FuzzyMatcher                                           ║
├────────────────────────────────────────────────────────────────────────────┤
│ Input:  "lose weight fast, vegan, I weigh 78kg, beginner level"           │
│ Process: Fuzzy string matching (fuzzywuzzy library)                       │
│   - "weight" matches "weight" keyword (100%)                              │
│   - "lose" matches "meal" keyword (partial, ~50%)                         │
│   - "training" not in text                                                │
│ Output: wants_meal_plan=False, wants_training_plan=False                  │
│         → Guidance response                                               │
│                                                                            │
│ OR if "training" detected:                                               │
│   Output: wants_meal_plan=True, wants_training_plan=False                │
│           → Generate meal plan                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                   2. PREFERENCE EXTRACTION                                 ║
║            chatbot/ml/classifiers.py + base_classifier.py                 ║
│                        (5 ML Classifiers)                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│ ┌─────────────────────┐  ┌─────────────────────┐                          │
│ │ GOAL CLASSIFIER     │  │ INPUT: "lose weight │                          │
│ │ GoalClassifier      │  │ fast, vegan, etc."  │                          │
│ ├─────────────────────┤  └─────────────────────┘                          │
│ │ Classes:            │          │                                        │
│ │ • fat loss          │          ▼                                        │
│ │ • muscle gain       │  TF-IDF Vectorizer                                │
│ │ • maintenance       │  [0.2, 0.5, 0.1, ..., 0.0]                       │
│ │ • general fitness   │          │                                        │
│ │                     │          ▼                                        │
│ │ Prediction:         │  Logistic Regression                              │
│ │ "fat loss"          │  fat loss:        0.92 ←── HIGHEST                │
│ │ confidence: 0.92    │  muscle gain:     0.05                            │
│ │                     │  maintenance:     0.02                            │
│ │ ✓ Use ML (0.92 >    │  general fitness: 0.01                            │
│ │   threshold 0.20)   │                                                    │
│ └─────────────────────┘                                                    │
│                                                                            │
│ ┌─────────────────────┐  ┌─────────────────────┐                          │
│ │ DIET STYLE          │  │ INPUT: Same prompt  │                          │
│ │ CLASSIFIER          │  └─────────────────────┘                          │
│ ├─────────────────────┤          │                                        │
│ │ Classes:            │          ▼                                        │
│ │ • balanced          │  [vectorized features]                            │
│ │ • vegetarian        │          │                                        │
│ │ • vegan             │          ▼                                        │
│ │ • low-carb          │  vegan: 0.88 ←── HIGHEST                         │
│ │ • high-protein      │                                                    │
│ │                     │  ✓ Use ML                                         │
│ │ Prediction: "vegan" │                                                    │
│ │ confidence: 0.88    │                                                    │
│ └─────────────────────┘                                                    │
│                                                                            │
│ ┌─────────────────────┐                                                    │
│ │ MEAL PREFERENCE     │  Input: Same  [Vectorize]  [Classify]             │
│ │ CLASSIFIER          │  → "vegan", 0.91 ✓                                │
│ ├─────────────────────┤                                                    │
│ │ Classes:            │                                                    │
│ │ • none              │                                                    │
│ │ • halal             │                                                    │
│ │ • kosher            │  ALL 5 CLASSIFIERS RUN INDEPENDENTLY               │
│ │ • vegan             │  ┌─────────────────┐ ┌──────────────┐             │
│ │ • vegetarian        │  │ TRAINING LEVEL  │ │ TRAINING     │             │
│ │                     │  │ → "beginner"    │ │ SETTING      │             │
│ │ Prediction: "vegan" │  │ 0.85 ✓          │ │ → "self"     │             │
│ │ confidence: 0.91    │  │                 │ │ 0.92 ✓       │             │
│ └─────────────────────┘  └─────────────────┘ └──────────────┘             │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    3. HEALTH EXTRACTION                                    ║
║              chatbot/ml/health_extractor.py                                ║
│                    HealthConditionExtractor                                │
├────────────────────────────────────────────────────────────────────────────┤
│ Input: "lose weight fast, vegan, I weigh 78kg, beginner level"           │
│                                                                            │
│ Pattern Matching:                                                          │
│ - "health notes: ..." → Extract                                           │
│ - "health issues: ..." → Extract                                          │
│ - "injuries: ..." → Extract                                               │
│                                                                            │
│ Keyword Matching:                                                          │
│ - "knee" → "knee pain/issues"                                             │
│ - "diabetes" → "diabetes"                                                 │
│ - "back pain" → "back pain"                                               │
│ - ... (20 conditions recognized)                                          │
│                                                                            │
│ Output: "none" (no conditions detected)                                   │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    4. REGEX EXTRACTION                                     ║
║              (Non-ML features)                                             ║
├────────────────────────────────────────────────────────────────────────────┤
│ Training Days:                                                             │
│ - Regex: r"(\d)\s*(day|days)"                                             │
│ - "5 days" → 5 → clamped to 2-6 → 5                                      │
│                                                                            │
│ Weight:                                                                    │
│ - Regex: r"(\d{2,3}(?:\.\d+)?)\s*(kg|kilograms)"                         │
│ - "78kg" → 78.0                                                           │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    5. COMBINE ALL INPUTS                                   ║
║              chatbot/planner.py                                            ║
├────────────────────────────────────────────────────────────────────────────┤
│ UserPreferences Object:                                                    │
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │ goal: "fat loss"           (from GoalClassifier)                  │   │
│ │ diet_style: "vegan"        (from DietStyleClassifier)             │   │
│ │ meal_preference: "vegan"   (from MealPreferenceClassifier)        │   │
│ │ training_level: "beginner" (from TrainingLevelClassifier)         │   │
│ │ training_setting: "self"   (from TrainingSettingClassifier)       │   │
│ │ training_days: 3           (from regex extraction, default)       │   │
│ │ weight_kg: 78.0            (from regex extraction)                │   │
│ │ health_notes: "none"       (from HealthConditionExtractor)        │   │
│ └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    6. PLAN GENERATION                                      ║
║              chatbot/planner.py                                            ║
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│ If wants_meal_plan:                                                       │
│   _build_meal_plan(preferences)                                           │
│   ├─ Goal: "fat loss" → Calorie deficit (300-400 kcal)                  │
│   ├─ Style: "vegan" → Plant-based proteins (tofu, lentils, etc.)       │
│   ├─ Preference: "vegan" → No animal products                           │
│   └─ Output: Meal plan text                                             │
│                                                                            │
│ If wants_training_plan:                                                   │
│   _build_training_plan(preferences)                                       │
│   ├─ Level: "beginner" → 2-3 sets x 8-12 reps                          │
│   ├─ Days: 3 → Full-body split                                          │
│   ├─ Setting: "self" → Bodyweight + bands                               │
│   └─ Output: Training plan text                                          │
│                                                                            │
│ Result:                                                                    │
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │ Hi [user_id]. Here is your tailored plan:                         │   │
│ │                                                                    │   │
│ │ Meal plan:                                                         │   │
│ │ - Goal: fat loss | Style: vegan                                   │   │
│ │ - Meal preference: vegan                                          │   │
│ │ - Calorie target: slight deficit (300-400 kcal/day)              │   │
│ │ - Protein: Aim for plant-based sources (tofu, tempeh, lentils)   │   │
│ │ - Meal structure: 3 meals + snacks with plant protein each       │   │
│ │ - Carbs: Include whole grains (oats, brown rice, quinoa)         │   │
│ │ - Fats: Use plant oils (olive, coconut, avocado)                 │   │
│ │ - Hydration: 2.5-3L water daily                                  │   │
│ │ - Progress tracking: Weigh weekly, adjust if < 0.5kg/week loss   │   │
│ │                                                                    │   │
│ │ Safety note: this is educational guidance, not medical advice.   │   │
│ │ If you have medical conditions, consult a qualified professional.│   │
│ └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    7. USER RATES PLAN & FEEDBACK                           ║
║              (Optional - collected via FeedbackAPIHandler)                 ║
├────────────────────────────────────────────────────────────────────────────┤
│ User Rating: 5/5 ⭐                                                       │
│ Feedback: "Perfect! Exactly what I needed"                               │
│                                                                            │
│ UserFeedback Object Created:                                              │
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │ timestamp: "2024-01-28T15:30:00"                                  │   │
│ │ user_id: "alice"                                                  │   │
│ │ prompt: "lose weight fast, vegan, ..."                            │   │
│ │ detected_goal: "fat loss"                                         │   │
│ │ user_goal: None  (user confirmed correct ✓)                       │   │
│ │ detected_diet_style: "vegan"                                      │   │
│ │ user_diet_style: None  (user confirmed correct ✓)                 │   │
│ │ detected_training_level: "beginner"                               │   │
│ │ user_training_level: None  (user confirmed correct ✓)             │   │
│ │ plan_quality: 5                                                   │   │
│ │ specific_feedback: "Perfect! Exactly what I needed"               │   │
│ │ helpful: True                                                     │   │
│ └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    8. STORE FEEDBACK                                       ║
║              chatbot/feedback/collector.py                                 ║
├────────────────────────────────────────────────────────────────────────────┤
│ FeedbackCollector.record_feedback(feedback)                               │
│                                                                            │
│ Save to two formats:                                                      │
│                                                                            │
│ 1. JSONL (data/feedback/user_feedback.jsonl)                              │
│    {"timestamp":"...", "user_id":"alice", "prompt":"...", ...}           │
│    {"timestamp":"...", "user_id":"bob", "prompt":"...", ...}             │
│    ... (one per line)                                                     │
│                                                                            │
│ 2. CSV (data/feedback/user_feedback.csv)                                  │
│    timestamp,user_id,prompt,detected_goal,user_goal,...                  │
│    2024-01-28T15:30:00,alice,"lose weight",...                           │
│    2024-01-28T15:35:00,bob,"gain muscle",...                             │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    9. ANALYZE FEEDBACK                                     ║
║              chatbot/feedback/collector.py                                 ║
├────────────────────────────────────────────────────────────────────────────┤
│ After 150+ feedback samples collected:                                    │
│                                                                            │
│ FeedbackCollector.get_feedback_summary():                                 │
│ {                                                                          │
│     "total_feedback": 150,                                                │
│     "average_quality": 4.2,                                               │
│     "helpful_rate": 0.87,                                                 │
│     "last_recorded": "2024-01-28T16:00:00"                                │
│ }                                                                          │
│                                                                            │
│ FeedbackCollector.get_misclassified_examples():                           │
│ {                                                                          │
│     "goal": [],                                                           │
│     "diet_style": [                                                       │
│         {                                                                 │
│             "prompt": "I want vegan diet",                                │
│             "predicted": "balanced",  ← WRONG                             │
│             "actual": "vegan"         ← CORRECT                           │
│         },                                                                │
│         ... (11 more examples)                                            │
│     ],                                                                    │
│     "training_level": []                                                 │
│ }                                                                          │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    10. RETRAIN MODELS                                      ║
║              chatbot/feedback/retrainer.py                                 ║
├────────────────────────────────────────────────────────────────────────────┤
│ Threshold reached: 12+ misclassifications in "diet_style"                │
│                                                                            │
│ ModelRetrainer.retrain_from_feedback(min_feedback_count=10):             │
│                                                                            │
│ For "diet_style" classifier:                                              │
│   1. Extract 12 examples from misclassifications                          │
│   2. Texts = ["I want vegan diet", "vegan only", ...]                    │
│   3. Labels = ["vegan", "vegan", ...]                                    │
│   4. Call planner.train_classifier("diet_style", texts, labels)          │
│                                                                            │
│        Diet Style Classifier:                                             │
│        ├─ Load existing model                                             │
│        ├─ Add new training examples                                       │
│        ├─ Retrain: 12 new + original examples                            │
│        ├─ Evaluate on new examples                                        │
│        └─ Save updated model to disk                                      │
│           (data/ml_models/diet_style_model.pkl)                          │
│                                                                            │
│ Return:                                                                    │
│ {                                                                          │
│     "diet_style": {                                                       │
│         "success": True,                                                  │
│         "examples_used": 12,                                              │
│         "message": "Successfully retrained diet_style classifier"         │
│     }                                                                      │
│ }                                                                          │
│                                                                            │
│ ✓ Model saved and ready for next inference                               │
│                                                                            │
╚════════════════════════════════════════════════════════════════════════════╝
                                     │
                                     ▼
╔════════════════════════════════════════════════════════════════════════════╗
║                    CYCLE REPEATS                                           ║
║                                                                            ║
║ New users generate plans → Better models from feedback → More accurate    ║
║ preferences → Better plans → Higher quality ratings                       ║
║                                                                            ║
║ Continuous improvement loop! 🔄                                           ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## Key Insights

### Why This Architecture?

1. **Modularity**: Each component does one thing well
2. **Robustness**: Falls back to rules if ML confidence is low
3. **Self-Learning**: Improves from real user feedback
4. **Transparency**: Each step logged and traceable
5. **Scalability**: Easy to add new classifiers or feedback types

### Performance Characteristics

- **Inference**: 60-70ms per request (5 classifiers + extraction)
- **Storage**: ~1KB per feedback record
- **Retraining**: 100-500ms (depends on feedback volume)
- **Accuracy**: ~85% baseline, improves with feedback

### Data Flow Summary

```
Request → Intent Detection → 5 Classifiers → Health Extract → Regex
    ↓              ↓                ↓              ↓            ↓
  Input        Fuzzy Match     ML Predictions  Pattern Matching Regex
                             (with fallback)
                    ↓
              UserPreferences
                    ↓
            Plan Generation
                    ↓
            Feedback Collection (optional)
                    ↓
            Model Retraining (if 10+ errors)
                    ↓
            Continuous Improvement
```

---

See [ML_ENHANCEMENTS.md](ML_ENHANCEMENTS.md) and [HOW_ML_WORKS.md](HOW_ML_WORKS.md) for detailed documentation.
