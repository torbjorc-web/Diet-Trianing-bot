"""Base classifier class for ML-based preference extraction."""

import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# Default model directory
MODELS_DIR = Path(__file__).parent.parent.parent / "data" / "ml_models"


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
        except (OSError, pickle.PickleError, EOFError, AttributeError, ValueError) as e:
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
        if not self.model:
            return self.classes[0], 0.0

        # Pass raw text to Pipeline (it will handle vectorization)
        probabilities = self.model.predict_proba([text])[0]
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
