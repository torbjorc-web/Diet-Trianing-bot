"""Tests for feedback data models."""

import pytest
from datetime import datetime
from chatbot.feedback.models import UserFeedback


class TestUserFeedback:
    """Test suite for UserFeedback dataclass."""

    def test_user_feedback_creation(self, sample_feedback_data):
        """Test creating a UserFeedback object."""
        feedback = UserFeedback(**sample_feedback_data)
        
        assert feedback.user_id == "test_user"
        assert feedback.prompt == "lose weight, vegan, beginner"
        assert feedback.detected_goal == "fat loss"
        assert feedback.plan_quality == 5
        assert feedback.helpful is True

    def test_user_feedback_with_corrections(self):
        """Test UserFeedback with user corrections."""
        feedback = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id="alice",
            prompt="gain muscle",
            detected_goal="fat loss",
            user_goal="muscle gain",  # User corrected
            detected_diet_style="balanced",
            user_diet_style="high-protein",  # User corrected
            detected_training_level="beginner",
            user_training_level=None,
            plan_quality=3,
            specific_feedback="Good but need more protein focus",
            helpful=True
        )
        
        assert feedback.user_goal == "muscle gain"
        assert feedback.user_diet_style == "high-protein"

    def test_user_feedback_all_fields(self):
        """Test that all required fields can be set."""
        feedback = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id="test_user",
            prompt="test prompt",
            detected_goal="goal",
            user_goal=None,
            detected_diet_style="diet",
            user_diet_style=None,
            detected_training_level="level",
            user_training_level=None,
            plan_quality=4,
            specific_feedback="feedback",
            helpful=False
        )
        
        assert feedback.plan_quality == 4
        assert feedback.specific_feedback == "feedback"
        assert feedback.helpful is False

    def test_user_feedback_plan_quality_range(self):
        """Test plan quality rating values."""
        for quality in range(1, 6):
            feedback = UserFeedback(
                timestamp=datetime.now().isoformat(),
                user_id="user",
                prompt="test",
                detected_goal="goal",
                user_goal=None,
                detected_diet_style="diet",
                user_diet_style=None,
                detected_training_level="level",
                user_training_level=None,
                plan_quality=quality,
                specific_feedback="",
                helpful=True
            )
            assert feedback.plan_quality == quality

    def test_user_feedback_timestamp(self):
        """Test timestamp is stored correctly."""
        now = datetime.now().isoformat()
        feedback = UserFeedback(
            timestamp=now,
            user_id="user",
            prompt="test",
            detected_goal="goal",
            user_goal=None,
            detected_diet_style="diet",
            user_diet_style=None,
            detected_training_level="level",
            user_training_level=None,
            plan_quality=5,
            specific_feedback="",
            helpful=True
        )
        assert feedback.timestamp == now

    def test_user_feedback_helpful_variations(self):
        """Test helpful field with different values."""
        # Test True
        feedback_good = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id="user",
            prompt="test",
            detected_goal="goal",
            user_goal=None,
            detected_diet_style="diet",
            user_diet_style=None,
            detected_training_level="level",
            user_training_level=None,
            plan_quality=5,
            specific_feedback="Excellent!",
            helpful=True
        )
        
        # Test False
        feedback_bad = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id="user",
            prompt="test",
            detected_goal="goal",
            user_goal=None,
            detected_diet_style="diet",
            user_diet_style=None,
            detected_training_level="level",
            user_training_level=None,
            plan_quality=1,
            specific_feedback="Not helpful",
            helpful=False
        )
        
        assert feedback_good.helpful is True
        assert feedback_bad.helpful is False

    def test_user_feedback_user_corrections_logic(self):
        """Test logic of detecting when user corrected model."""
        # Case 1: User agreed with model (user_goal is None)
        feedback_agree = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id="alice",
            prompt="lose weight",
            detected_goal="fat loss",
            user_goal=None,  # Agreed
            detected_diet_style="balanced",
            user_diet_style=None,  # Agreed
            detected_training_level="beginner",
            user_training_level=None,  # Agreed
            plan_quality=5,
            specific_feedback="Perfect!",
            helpful=True
        )
        
        # All corrections should be None (agreed)
        assert feedback_agree.user_goal is None
        assert feedback_agree.user_diet_style is None
        
        # Case 2: User corrected the model
        feedback_correct = UserFeedback(
            timestamp=datetime.now().isoformat(),
            user_id="bob",
            prompt="lose weight",
            detected_goal="fat loss",
            user_goal="muscle gain",  # Corrected
            detected_diet_style="balanced",
            user_diet_style="high-protein",  # Corrected
            detected_training_level="beginner",
            user_training_level="advanced",  # Corrected
            plan_quality=2,
            specific_feedback="Wrong classifications",
            helpful=False
        )
        
        # Corrections should be set
        assert feedback_correct.user_goal == "muscle gain"
        assert feedback_correct.user_diet_style == "high-protein"
        assert feedback_correct.user_training_level == "advanced"
