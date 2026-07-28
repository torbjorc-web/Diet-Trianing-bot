"""User feedback learning system for continuous model improvement.

Tracks user interactions and collects feedback to retrain ML classifiers.
Stores feedback data for analysis and model performance monitoring.
"""

import csv
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default feedback directory
FEEDBACK_DIR = Path(__file__).parent.parent / "data" / "feedback"


@dataclass
class UserFeedback:
    """Represents user feedback on a generated plan."""

    timestamp: str
    user_id: str
    prompt: str
    detected_goal: str
    user_goal: Optional[str]  # What user said goal should be
    detected_diet_style: str
    user_diet_style: Optional[str]
    detected_training_level: str
    user_training_level: Optional[str]
    plan_quality: int  # 1-5 rating
    specific_feedback: str  # Free text feedback
    helpful: bool  # Was the plan helpful?


class FeedbackCollector:
    """Collects and stores user feedback for model retraining."""

    def __init__(self):
        self.feedback_file = FEEDBACK_DIR / "user_feedback.jsonl"
        self.csv_file = FEEDBACK_DIR / "user_feedback.csv"
        FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

    def record_feedback(self, feedback: UserFeedback) -> None:
        """Record user feedback to disk.

        Args:
            feedback: UserFeedback object with user's assessment
        """
        try:
            # Append to JSONL file for easy streaming
            with open(self.feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(feedback)) + "\n")

            # Also append to CSV for analysis in Excel/Pandas
            self._append_to_csv(feedback)

            logger.info(f"Recorded feedback for user {feedback.user_id}")
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")

    def _append_to_csv(self, feedback: UserFeedback) -> None:
        """Append feedback to CSV file."""
        file_exists = self.csv_file.exists()

        with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(feedback).keys())

            if not file_exists:
                writer.writeheader()

            writer.writerow(asdict(feedback))

    def get_feedback_summary(self) -> dict:
        """Get summary statistics of collected feedback.

        Returns:
            Dictionary with feedback statistics
        """
        if not self.feedback_file.exists():
            return {"total_feedback": 0, "average_quality": 0, "helpful_rate": 0}

        feedbacks = []
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                for line in f:
                    feedbacks.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read feedback file: {e}")
            return {}

        if not feedbacks:
            return {"total_feedback": 0, "average_quality": 0, "helpful_rate": 0}

        total = len(feedbacks)
        avg_quality = sum(f.get("plan_quality", 0) for f in feedbacks) / total
        helpful_count = sum(1 for f in feedbacks if f.get("helpful", False))
        helpful_rate = helpful_count / total if total > 0 else 0

        return {
            "total_feedback": total,
            "average_quality": round(avg_quality, 2),
            "helpful_rate": round(helpful_rate, 2),
            "last_recorded": feedbacks[-1].get("timestamp"),
        }

    def get_misclassified_examples(self) -> dict[str, list[dict]]:
        """Extract examples where classifier predictions didn't match user feedback.

        Returns:
            Dictionary mapping classifier types to misclassified examples
        """
        if not self.feedback_file.exists():
            return {}

        misclassified = {
            "goal": [],
            "diet_style": [],
            "training_level": [],
        }

        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                for line in f:
                    feedback = json.loads(line)

                    if feedback.get("user_goal") and feedback.get("detected_goal") != feedback.get("user_goal"):
                        misclassified["goal"].append({
                            "prompt": feedback.get("prompt"),
                            "predicted": feedback.get("detected_goal"),
                            "actual": feedback.get("user_goal"),
                        })

                    if feedback.get("user_diet_style") and feedback.get("detected_diet_style") != feedback.get("user_diet_style"):
                        misclassified["diet_style"].append({
                            "prompt": feedback.get("prompt"),
                            "predicted": feedback.get("detected_diet_style"),
                            "actual": feedback.get("user_diet_style"),
                        })

                    if feedback.get("user_training_level") and feedback.get("detected_training_level") != feedback.get("user_training_level"):
                        misclassified["training_level"].append({
                            "prompt": feedback.get("prompt"),
                            "predicted": feedback.get("detected_training_level"),
                            "actual": feedback.get("user_training_level"),
                        })
        except Exception as e:
            logger.error(f"Failed to extract misclassified examples: {e}")

        return misclassified


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
                GoalClassifier
            )

        # Retrain diet_style classifier if we have enough feedback
        if len(misclassified["diet_style"]) >= min_feedback_count:
            results["diet_style"] = self._retrain_classifier(
                "diet_style",
                misclassified["diet_style"],
                DietStyleClassifier
            )

        # Retrain training_level classifier if we have enough feedback
        if len(misclassified["training_level"]) >= min_feedback_count:
            results["training_level"] = self._retrain_classifier(
                "training_level",
                misclassified["training_level"],
                TrainingLevelClassifier
            )

        if results:
            logger.info(f"Retrained models: {list(results.keys())}")
        else:
            logger.info(f"Not enough feedback for retraining. Need {min_feedback_count} samples per classifier.")

        return results

    def _retrain_classifier(self, classifier_type: str, misclassified: list[dict], classifier_class) -> dict:
        """Retrain a specific classifier with correction examples.

        Args:
            classifier_type: Type of classifier to retrain
            misclassified: List of misclassified examples
            classifier_class: The classifier class to instantiate

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


class FeedbackAPIHandler:
    """Handles feedback submission and retrieval via API."""

    def __init__(self, planner):
        """Initialize handler with planner and feedback collector.

        Args:
            planner: DietTrainingPlanner instance
        """
        self.planner = planner
        self.collector = FeedbackCollector()
        self.retrainer = ModelRetrainer(planner)

    def submit_feedback(
        self,
        user_id: str,
        prompt: str,
        detected_goal: str,
        user_goal: Optional[str],
        detected_diet_style: str,
        user_diet_style: Optional[str],
        detected_training_level: str,
        user_training_level: Optional[str],
        plan_quality: int,
        specific_feedback: str,
        helpful: bool,
    ) -> dict:
        """Submit user feedback for a generated plan.

        Args:
            user_id: User identifier
            prompt: Original user prompt
            detected_goal: Goal detected by system
            user_goal: Correct goal per user
            detected_diet_style: Diet style detected by system
            user_diet_style: Correct diet style per user
            detected_training_level: Training level detected by system
            user_training_level: Correct training level per user
            plan_quality: Quality rating 1-5
            specific_feedback: User's specific feedback text
            helpful: Whether plan was helpful

        Returns:
            Dictionary with feedback submission result
        """
        feedback = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            prompt=prompt,
            detected_goal=detected_goal,
            user_goal=user_goal,
            detected_diet_style=detected_diet_style,
            user_diet_style=user_diet_style,
            detected_training_level=detected_training_level,
            user_training_level=user_training_level,
            plan_quality=plan_quality,
            specific_feedback=specific_feedback,
            helpful=helpful,
        )

        self.collector.record_feedback(feedback)

        return {
            "success": True,
            "message": "Feedback recorded successfully",
            "feedback_summary": self.collector.get_feedback_summary()
        }

    def get_feedback_stats(self) -> dict:
        """Get statistics on collected feedback.

        Returns:
            Dictionary with feedback statistics
        """
        return self.collector.get_feedback_summary()

    def trigger_retraining(self, min_feedback_count: int = 10) -> dict:
        """Trigger model retraining if enough feedback is available.

        Args:
            min_feedback_count: Minimum feedback samples per classifier

        Returns:
            Dictionary with retraining results
        """
        return self.retrainer.retrain_from_feedback(min_feedback_count)
