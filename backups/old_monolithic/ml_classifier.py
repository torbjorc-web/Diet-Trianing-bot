"""Machine learning classifiers for diet and training preferences extraction.

Uses scikit-learn for intent classification and preference extraction.
Supports model persistence and retraining from user feedback.
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

# Default model directory
MODELS_DIR = Path(__file__).parent.parent / "data" / "ml_models"
TRAINING_DATA_DIR = Path(__file__).parent.parent / "data" / "training_data"


class MLClassifier:
    """Base classifier with model persistence and training capabilities."""

    def __init__(self, model_name: str, classes: list[str]):
        self.model_name = model_name
        self.classes = classes
        self.model_path = MODELS_DIR / f"{model_name}_model.pkl"
        self.vectorizer_path = MODELS_DIR / f"{model_name}_vectorizer.pkl"
        self.model = None
        self.vectorizer = None
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load existing model or create new one."""
        try:
            if self.model_path.exists() and self.vectorizer_path.exists():
                with open(self.vectorizer_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"Loaded {self.model_name} model from disk")
            else:
                self._create_default_model()
                logger.info(f"Created new {self.model_name} model")
        except Exception as e:
            logger.warning(f"Failed to load {self.model_name} model: {e}. Creating new.")
            self._create_default_model()

    def _create_default_model(self) -> None:
        """Create a new default model."""
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            max_features=100,
            ngram_range=(1, 2),
        )
        self.model = Pipeline([
            ("vectorizer", self.vectorizer),
            ("classifier", OneVsRestClassifier(LogisticRegression(max_iter=200))),
        ])

    def train(self, texts: list[str], labels: list[str]) -> None:
        """Train the classifier on provided examples.

        Args:
            texts: List of training texts
            labels: List of corresponding labels (must be in self.classes)
        """
        if not all(label in self.classes for label in labels):
            raise ValueError(f"Labels must be one of {self.classes}")

        self.model.fit(texts, labels)
        self._save()
        logger.info(f"Trained {self.model_name} model with {len(texts)} examples")

    def predict(self, text: str, confidence_threshold: float = 0.3) -> tuple[str, float]:
        """Predict the class for given text.

        Args:
            text: Input text
            confidence_threshold: Minimum confidence to return prediction

        Returns:
            Tuple of (predicted_class, confidence_score)
        """
        if not self.model or not self.vectorizer:
            return self.classes[0], 0.0

        X = self.vectorizer.transform([text])
        probabilities = self.model.predict_proba(X)[0]
        max_prob_idx = np.argmax(probabilities)
        max_prob = probabilities[max_prob_idx]

        if max_prob < confidence_threshold:
            return self.classes[0], max_prob

        return self.classes[max_prob_idx], float(max_prob)

    def _save(self) -> None:
        """Save model and vectorizer to disk."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)


class GoalClassifier(MLClassifier):
    """Classify fitness goal from user input."""

    CLASSES = ["fat loss", "muscle gain", "maintenance", "general fitness"]

    def __init__(self):
        super().__init__("goal", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        if self.model.get_params()["classifier"].coef_ is None:
            training_examples = [
                ("lose weight fat loss", "fat loss"),
                ("weight loss diet", "fat loss"),
                ("cut down calories", "fat loss"),
                ("reduce body fat", "fat loss"),
                ("get lean", "fat loss"),
                ("build muscle gain mass", "muscle gain"),
                ("bulk up strength", "muscle gain"),
                ("gain muscle size", "muscle gain"),
                ("increase muscle", "muscle gain"),
                ("stay fit maintain", "maintenance"),
                ("maintain weight", "maintenance"),
                ("keep current fitness", "maintenance"),
                ("general fitness", "general fitness"),
                ("get fit healthy", "general fitness"),
                ("improve fitness", "general fitness"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class DietStyleClassifier(MLClassifier):
    """Classify diet style preference."""

    CLASSES = ["balanced", "vegetarian", "vegan", "low-carb", "high-protein"]

    def __init__(self):
        super().__init__("diet_style", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        if self.model.get_params()["classifier"].coef_ is None:
            training_examples = [
                ("normal balanced diet", "balanced"),
                ("all foods", "balanced"),
                ("omnivore", "balanced"),
                ("vegetarian diet no meat", "vegetarian"),
                ("no meat", "vegetarian"),
                ("vegan diet no animal", "vegan"),
                ("plant based only", "vegan"),
                ("low carb keto", "low-carb"),
                ("minimal carbs", "low-carb"),
                ("high protein diet", "high-protein"),
                ("protein focused", "high-protein"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class MealPreferenceClassifier(MLClassifier):
    """Classify meal preference/dietary restrictions."""

    CLASSES = ["none", "halal", "kosher", "vegan", "vegetarian"]

    def __init__(self):
        super().__init__("meal_preference", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        if self.model.get_params()["classifier"].coef_ is None:
            training_examples = [
                ("any food", "none"),
                ("no restrictions", "none"),
                ("halal certified", "halal"),
                ("halal only", "halal"),
                ("kosher certified", "kosher"),
                ("kosher diet", "kosher"),
                ("vegan only", "vegan"),
                ("no animal products", "vegan"),
                ("vegetarian only", "vegetarian"),
                ("no meat", "vegetarian"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class TrainingLevelClassifier(MLClassifier):
    """Classify training experience level."""

    CLASSES = ["beginner", "intermediate", "advanced"]

    def __init__(self):
        super().__init__("training_level", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        if self.model.get_params()["classifier"].coef_ is None:
            training_examples = [
                ("never trained", "beginner"),
                ("just starting", "beginner"),
                ("new to gym", "beginner"),
                ("beginner level", "beginner"),
                ("some experience", "intermediate"),
                ("trained for years", "intermediate"),
                ("intermediate level", "intermediate"),
                ("several years experience", "intermediate"),
                ("expert lifter", "advanced"),
                ("advanced athlete", "advanced"),
                ("competitive", "advanced"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class TrainingSettingClassifier(MLClassifier):
    """Classify training environment/setting."""

    CLASSES = ["self", "studio", "group"]

    def __init__(self):
        super().__init__("training_setting", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        if self.model.get_params()["classifier"].coef_ is None:
            training_examples = [
                ("home training", "self"),
                ("at home", "self"),
                ("solo training", "self"),
                ("self guided", "self"),
                ("gym training", "studio"),
                ("studio gym", "studio"),
                ("fitness studio", "studio"),
                ("personal trainer", "studio"),
                ("group class", "group"),
                ("team training", "group"),
                ("group fitness", "group"),
                ("class training", "group"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class HealthConditionExtractor:
    """Extract and recognize health conditions from text."""

    # Common health keywords mapped to descriptions
    HEALTH_KEYWORDS = {
        "knee": "knee pain/issues",
        "back pain": "back pain",
        "lower back": "lower back pain",
        "upper back": "upper back pain",
        "shoulder": "shoulder issues",
        "elbow": "elbow pain",
        "wrist": "wrist pain",
        "ankle": "ankle issues",
        "arthritis": "arthritis",
        "diabetes": "diabetes",
        "asthma": "asthma",
        "hypertension": "high blood pressure",
        "high blood pressure": "hypertension",
        "heart": "heart condition",
        "cardiac": "cardiac issues",
        "respiratory": "respiratory issues",
        "pregnancy": "pregnancy",
        "osteoporosis": "osteoporosis",
        "injury": "injury",
        "injured": "injured",
    }

    @staticmethod
    def extract(prompt: str) -> str:
        """Extract health conditions from prompt.

        Args:
            prompt: User prompt text

        Returns:
            Extracted health notes or "none"
        """
        lowered = prompt.lower()
        found_conditions = []

        # Check for explicit health notes format
        import re
        health_patterns = [
            r"health notes?:\s*(.+?)(?:\.|,|$)",
            r"health issues?:\s*(.+?)(?:\.|,|$)",
            r"injur(?:y|ies):\s*(.+?)(?:\.|,|$)",
        ]

        for pattern in health_patterns:
            match = re.search(pattern, lowered)
            if match:
                return match.group(1).strip()

        # Check for keyword matches
        for keyword, condition in HealthConditionExtractor.HEALTH_KEYWORDS.items():
            if keyword in lowered:
                found_conditions.append(condition)

        if found_conditions:
            return ", ".join(set(found_conditions))  # Remove duplicates

        return "none"


class FuzzyMatcher:
    """Fuzzy matching for improved intent and preference detection."""

    @staticmethod
    def match_intent(prompt: str, threshold: int = 70) -> dict[str, bool]:
        """Fuzzy match against meal and training keywords.

        Args:
            prompt: User prompt
            threshold: Fuzzy match threshold (0-100)

        Returns:
            Dict with wants_meal_plan and wants_training_plan booleans
        """
        lowered = prompt.lower()

        meal_keywords = ["meal", "diet", "nutrition", "calorie", "food", "eating"]
        training_keywords = ["training", "workout", "exercise", "gym", "program", "fitness"]

        wants_meal = any(
            fuzz.partial_ratio(keyword, lowered) > threshold
            for keyword in meal_keywords
        )
        wants_training = any(
            fuzz.partial_ratio(keyword, lowered) > threshold
            for keyword in training_keywords
        )

        # Explicit both patterns
        if fuzz.partial_ratio("both", lowered) > 80:
            wants_meal = True
            wants_training = True

        return {"wants_meal_plan": wants_meal, "wants_training_plan": wants_training}

    @staticmethod
    def match_value(text: str, options: list[str], threshold: int = 60) -> str:
        """Fuzzy match text against a list of options.

        Args:
            text: Input text
            options: List of valid options
            threshold: Match threshold (0-100)

        Returns:
            Best matching option or first option if no good match
        """
        if not text or not options:
            return options[0]

        best_match = options[0]
        best_score = 0

        for option in options:
            score = fuzz.token_set_ratio(text.lower(), option.lower())
            if score > best_score:
                best_score = score
                best_match = option

        if best_score >= threshold:
            return best_match
        return options[0]
