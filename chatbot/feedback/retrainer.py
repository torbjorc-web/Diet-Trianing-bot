"""Model retraining from user feedback."""

import logging

from chatbot.feedback.collector import FeedbackCollector

logger = logging.getLogger(__name__)


class ModelRetrainer:
    """Retrains ML models based on collected user feedback."""

    def __init__(self, planner):
        """Initialize retrainer with reference to planner.

        Args:
            planner: DietTrainingPlanner instance to retrain
        """
        self.planner = planner
        self.collector = FeedbackCollector()

    def retrain_from_feedback(self, min_feedback_count: int = 10) -> dict:
        """Retrain models using collected misclassified examples.

        Args:
            min_feedback_count: Minimum feedback samples required for retraining

        Returns:
            Dictionary with retraining results for each classifier
        """
        misclassified = self.collector.get_misclassified_examples()
        results = {}

        # Retrain goal classifier if we have enough feedback
        if len(misclassified["goal"]) >= min_feedback_count:
            results["goal"] = self._retrain_classifier(
                "goal",
                misclassified["goal"],
            )

        # Retrain diet_style classifier if we have enough feedback
        if len(misclassified["diet_style"]) >= min_feedback_count:
            results["diet_style"] = self._retrain_classifier(
                "diet_style",
                misclassified["diet_style"],
            )

        # Retrain training_level classifier if we have enough feedback
        if len(misclassified["training_level"]) >= min_feedback_count:
            results["training_level"] = self._retrain_classifier(
                "training_level",
                misclassified["training_level"],
            )

        if results:
            logger.info(f"Retrained models: {list(results.keys())}")
        else:
            logger.info(f"Not enough feedback for retraining. Need {min_feedback_count} samples per classifier.")

        return results

    def _retrain_classifier(self, classifier_type: str, misclassified: list[dict]) -> dict:
        """Retrain a specific classifier with correction examples.

        Args:
            classifier_type: Type of classifier to retrain
            misclassified: List of misclassified examples

        Returns:
            Dictionary with retraining statistics
        """
        try:
            texts = [item["prompt"] for item in misclassified]
            labels = [item["actual"] for item in misclassified]

            self.planner.train_classifier(classifier_type, texts, labels)

            return {
                "success": True,
                "examples_used": len(misclassified),
                "message": f"Successfully retrained {classifier_type} classifier"
            }
        except Exception as e:
            logger.error(f"Failed to retrain {classifier_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to retrain {classifier_type} classifier"
            }
