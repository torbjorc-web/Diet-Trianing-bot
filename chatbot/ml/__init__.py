"""Machine Learning package for preference extraction and classification."""

from chatbot.ml.classifiers import (
    DietStyleClassifier,
    GoalClassifier,
    MealPreferenceClassifier,
    TrainingLevelClassifier,
    TrainingSettingClassifier,
)
from chatbot.ml.health_extractor import HealthConditionExtractor
from chatbot.ml.intent_detection import FuzzyMatcher

__all__ = [
    "GoalClassifier",
    "DietStyleClassifier",
    "MealPreferenceClassifier",
    "TrainingLevelClassifier",
    "TrainingSettingClassifier",
    "FuzzyMatcher",
    "HealthConditionExtractor",
]
