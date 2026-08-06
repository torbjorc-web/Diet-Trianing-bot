"""Feedback collection and storage."""

import csv
import json
import logging
from dataclasses import asdict
from pathlib import Path

from chatbot.feedback.models import UserFeedback

logger = logging.getLogger(__name__)

# Default feedback directory
FEEDBACK_DIR = Path(__file__).parent.parent.parent / "data" / "feedback"


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
        except (OSError, TypeError, ValueError) as e:
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
        except (OSError, json.JSONDecodeError, TypeError) as e:
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
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to extract misclassified examples: {e}")

        return misclassified
