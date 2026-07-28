"""Tests for feedback collection and storage."""

import pytest
import json
from pathlib import Path
from datetime import datetime
from chatbot.feedback.collector import FeedbackCollector
from chatbot.feedback.models import UserFeedback


class TestFeedbackCollector:
    """Test suite for FeedbackCollector."""

    def test_collector_initialization(self):
        """Test FeedbackCollector initializes correctly."""
        collector = FeedbackCollector()
        assert collector.feedback_file is not None

    def test_record_single_feedback(self, sample_feedback_data):
        """Test recording a single feedback entry."""
        collector = FeedbackCollector()
        
        feedback = UserFeedback(**sample_feedback_data)
        collector.record_feedback(feedback)
        
        # Check JSONL file exists
        assert collector.feedback_file.exists()

    def test_record_multiple_feedback(self):
        """Test recording multiple feedback entries."""
        collector = FeedbackCollector()
        
        for i in range(5):
            feedback = UserFeedback(
                timestamp=datetime.now().isoformat(),
                user_id=f"user_{i}",
                prompt=f"test prompt {i}",
                detected_goal="fat loss",
                user_goal=None,
                detected_diet_style="vegan",
                user_diet_style=None,
                detected_training_level="beginner",
                user_training_level=None,
                plan_quality=4,
                specific_feedback=f"Feedback {i}",
                helpful=True
            )
            collector.record_feedback(feedback)
        
        # Check JSONL file exists
        assert collector.feedback_file.exists()

    def test_feedback_stored_as_jsonl(self, sample_feedback_data):
        """Test that feedback is stored in JSONL format."""
        collector = FeedbackCollector()
        
        feedback = UserFeedback(**sample_feedback_data)
        collector.record_feedback(feedback)
        
        jsonl_file = collector.feedback_file
        
        with open(jsonl_file) as f:
            for line in f:
                data = json.loads(line)
                assert data["user_id"] == "test_user"
                assert data["plan_quality"] == 5

    def test_feedback_stored_as_csv(self, sample_feedback_data):
        """Test that feedback is stored in CSV format."""
        collector = FeedbackCollector()
        
        feedback = UserFeedback(**sample_feedback_data)
        collector.record_feedback(feedback)
        
        csv_file = collector.csv_file
        assert csv_file.exists()
        
        with open(csv_file) as f:
            lines = f.readlines()
        
        # Header + at least 1 data line
        assert len(lines) >= 2

    def test_get_feedback_summary(self):
        """Test getting feedback summary statistics."""
        collector = FeedbackCollector()
        
        # Record some feedback
        for i in range(3):
            feedback = UserFeedback(
                timestamp=datetime.now().isoformat(),
                user_id=f"user_{i}",
                prompt="test",
                detected_goal="fat loss",
                user_goal=None,
                detected_diet_style="vegan",
                user_diet_style=None,
                detected_training_level="beginner",
                user_training_level=None,
                plan_quality=i + 3,  # 3, 4, 5
                specific_feedback="test",
                helpful=True
            )
            collector.record_feedback(feedback)
        
        summary = collector.get_feedback_summary()
        
        assert summary["total_feedback"] == 3
        assert summary["average_quality"] > 0

    def test_get_misclassified_examples(self):
        """Test extracting misclassified examples from feedback."""
        collector = FeedbackCollector()
        
        # Record feedback with corrections
        for i in range(3):
            feedback = UserFeedback(
                timestamp=datetime.now().isoformat(),
                user_id=f"user_{i}",
                prompt="lose weight",
                detected_goal="fat loss",
                user_goal="muscle gain" if i == 0 else None,  # First one is wrong
                detected_diet_style="balanced",
                user_diet_style="vegan" if i == 1 else None,  # Second one is wrong
                detected_training_level="beginner",
                user_training_level="advanced" if i == 2 else None,  # Third one is wrong
                plan_quality=5,
                specific_feedback="test",
                helpful=True
            )
            collector.record_feedback(feedback)
        
        misclassified = collector.get_misclassified_examples()
        
        assert isinstance(misclassified, dict)
        assert "goal" in misclassified
        assert "diet_style" in misclassified
        assert "training_level" in misclassified

    def test_empty_feedback_summary(self):
        """Test summary when no feedback collected yet."""
        collector = FeedbackCollector()
        
        summary = collector.get_feedback_summary()
        
        assert summary["total_feedback"] == 0
        assert summary["average_quality"] == 0

    def test_helpful_rate_calculation(self):
        """Test calculation of helpful rate."""
        collector = FeedbackCollector()
        
        # Record 4 helpful, 1 not helpful
        for i in range(5):
            feedback = UserFeedback(
                timestamp=datetime.now().isoformat(),
                user_id=f"user_{i}",
                prompt="test",
                detected_goal="goal",
                user_goal=None,
                detected_diet_style="diet",
                user_diet_style=None,
                detected_training_level="level",
                user_training_level=None,
                plan_quality=4,
                specific_feedback="test",
                helpful=i < 4  # Last one is not helpful
            )
            collector.record_feedback(feedback)
        
        summary = collector.get_feedback_summary()
        assert 0 <= summary["helpful_rate"] <= 1
