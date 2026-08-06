"""API handlers for feedback submission and retrieval."""

from datetime import datetime, timezone

from chatbot.feedback.collector import FeedbackCollector
from chatbot.feedback.models import UserFeedback
from chatbot.feedback.retrainer import ModelRetrainer


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
        user_goal: str | None,
        detected_diet_style: str,
        user_diet_style: str | None,
        detected_training_level: str,
        user_training_level: str | None,
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
            timestamp=datetime.now(timezone.utc).isoformat(),
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
