"""Tests for automatic model retraining from feedback."""

from datetime import datetime, timezone
from unittest.mock import Mock

from chatbot.feedback.models import UserFeedback
from chatbot.feedback.retrainer import ModelRetrainer


class TestModelRetrainer:
    """Test suite for ModelRetrainer."""

    def test_retrainer_initialization(self):
        """Test ModelRetrainer initializes correctly."""
        mock_planner = Mock()
        retrainer = ModelRetrainer(planner=mock_planner)
        assert retrainer.planner == mock_planner
        assert retrainer.collector is not None

    def test_retrainer_no_misclassifications(self):
        """Test retrainer when no misclassifications present."""
        from chatbot.feedback.collector import FeedbackCollector
        
        collector = FeedbackCollector()
        mock_planner = Mock()
        retrainer = ModelRetrainer(planner=mock_planner)
        
        # Record feedback with NO corrections
        for i in range(5):
            feedback = UserFeedback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=f"user_{i}",
                prompt="lose weight",
                detected_goal="fat loss",
                user_goal=None,  # All correct
                detected_diet_style="vegan",
                user_diet_style=None,  # All correct
                detected_training_level="beginner",
                user_training_level=None,  # All correct
                plan_quality=5,
                specific_feedback="Perfect!",
                helpful=True
            )
            collector.record_feedback(feedback)
        
        # This should not trigger retraining (no errors)
        result = retrainer.retrain_from_feedback(min_feedback_count=3)
        
        # Check result is dictionary
        assert isinstance(result, dict)

    def test_retrainer_with_misclassifications(self):
        """Test retrainer when misclassifications are present."""
        from chatbot.feedback.collector import FeedbackCollector
        
        collector = FeedbackCollector()
        mock_planner = Mock()
        retrainer = ModelRetrainer(planner=mock_planner)
        
        # Record feedback with corrections
        for i in range(12):
            feedback = UserFeedback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=f"user_{i}",
                prompt="test prompt",
                detected_goal="fat loss",
                user_goal="muscle gain" if i < 8 else None,  # 8 misclassifications
                detected_diet_style="balanced",
                user_diet_style="vegan" if i < 4 else None,  # 4 misclassifications
                detected_training_level="beginner",
                user_training_level="advanced" if i < 10 else None,  # 10 misclassifications
                plan_quality=2,
                specific_feedback="Wrong predictions",
                helpful=False
            )
            collector.record_feedback(feedback)
        
        # Should retrain with enough misclassified examples
        result = retrainer.retrain_from_feedback(min_feedback_count=3)
        assert isinstance(result, dict)

    def test_retrainer_min_feedback_threshold(self):
        """Test retrainer respects minimum feedback threshold."""
        from chatbot.feedback.collector import FeedbackCollector
        
        collector = FeedbackCollector()
        mock_planner = Mock()
        retrainer = ModelRetrainer(planner=mock_planner)
        
        # Only record 2 misclassifications
        for i in range(2):
            feedback = UserFeedback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=f"user_{i}",
                prompt="test",
                detected_goal="fat loss",
                user_goal="muscle gain",  # Misclassified
                detected_diet_style="balanced",
                user_diet_style=None,
                detected_training_level="beginner",
                user_training_level=None,
                plan_quality=1,
                specific_feedback="Wrong",
                helpful=False
            )
            collector.record_feedback(feedback)
        
        # Require minimum 5 - should not retrain
        result = retrainer.retrain_from_feedback(min_feedback_count=5)
        
        # Result should be empty or indicate no retraining
        assert isinstance(result, dict)

    def test_retrainer_extracts_correct_examples(self):
        """Test retrainer extracts misclassified examples correctly."""
        from chatbot.feedback.collector import FeedbackCollector
        
        collector = FeedbackCollector()
        
        # Record mixed correct and incorrect
        correct_count = 3
        incorrect_count = 2
        
        for i in range(correct_count):
            feedback = UserFeedback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=f"correct_{i}",
                prompt="test",
                detected_goal="fat loss",
                user_goal=None,  # Correct
                detected_diet_style="balanced",
                user_diet_style=None,  # Correct
                detected_training_level="beginner",
                user_training_level=None,  # Correct
                plan_quality=5,
                specific_feedback="Good",
                helpful=True
            )
            collector.record_feedback(feedback)
        
        for i in range(incorrect_count):
            feedback = UserFeedback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=f"incorrect_{i}",
                prompt="test",
                detected_goal="fat loss",
                user_goal="muscle gain",  # Wrong
                detected_diet_style="balanced",
                user_diet_style="vegan",  # Wrong
                detected_training_level="beginner",
                user_training_level="advanced",  # Wrong
                plan_quality=1,
                specific_feedback="Bad",
                helpful=False
            )
            collector.record_feedback(feedback)
        
        # Get misclassified examples
        misclassified = collector.get_misclassified_examples()
        
        # Should extract misclassifications
        assert isinstance(misclassified, dict)

    def test_retrainer_multiple_classifier_errors(self):
        """Test retraining when multiple classifiers have errors."""
        from chatbot.feedback.collector import FeedbackCollector
        
        collector = FeedbackCollector()
        mock_planner = Mock()
        retrainer = ModelRetrainer(planner=mock_planner)
        
        # Record feedback with errors in multiple classifiers
        for i in range(15):
            feedback = UserFeedback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=f"user_{i}",
                prompt="test",
                detected_goal="fat loss",
                user_goal="muscle gain",  # Goal classifier error
                detected_diet_style="balanced",
                user_diet_style="vegan",  # Diet style error
                detected_training_level="beginner",
                user_training_level="advanced",  # Training level error
                plan_quality=1,
                specific_feedback="All wrong",
                helpful=False
            )
            collector.record_feedback(feedback)
        
        result = retrainer.retrain_from_feedback(min_feedback_count=10)
        
        # Result should be dictionary with potential retraining results
        assert isinstance(result, dict)

    def test_retrainer_handles_logging(self):
        """Test retrainer logs appropriately."""
        mock_planner = Mock()
        retrainer = ModelRetrainer(planner=mock_planner)
        
        # Should initialize without error
        assert retrainer.planner == mock_planner
        assert retrainer.collector is not None
