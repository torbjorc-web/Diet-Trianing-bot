"""Shared test fixtures and configuration."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(autouse=True)
def cleanup_feedback_files():
    """Auto-cleanup feedback files before each test."""
    # Cleanup before test
    feedback_dir = Path(__file__).parent.parent / "data" / "feedback"
    if feedback_dir.exists():
        shutil.rmtree(feedback_dir)
    
    yield
    
    # Cleanup after test
    if feedback_dir.exists():
        shutil.rmtree(feedback_dir)


@pytest.fixture
def temp_model_dir():
    """Create temporary directory for test models."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_feedback_dir():
    """Create temporary directory for feedback files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_training_data():
    """Sample training data for classifiers."""
    return {
        "goal": [
            ("I want to lose weight fast", "fat loss"),
            ("help me burn fat", "fat loss"),
            ("I need to get lean", "fat loss"),
            ("build muscle and get strong", "muscle gain"),
            ("increase muscle mass", "muscle gain"),
            ("stay at same weight", "maintenance"),
            ("general fitness routine", "general fitness"),
        ],
        "diet_style": [
            ("I eat balanced meals", "balanced"),
            ("I'm vegetarian", "vegetarian"),
            ("I'm vegan no animal products", "vegan"),
            ("low carb diet", "low-carb"),
            ("high protein meals", "high-protein"),
        ],
        "training_level": [
            ("I'm a beginner", "beginner"),
            ("I've worked out before", "intermediate"),
            ("I'm very experienced", "advanced"),
        ],
    }


@pytest.fixture
def sample_feedback_data():
    """Sample feedback data for testing feedback collection."""
    from datetime import datetime
    return {
        "timestamp": datetime.now().isoformat(),
        "user_id": "test_user",
        "prompt": "lose weight, vegan, beginner",
        "detected_goal": "fat loss",
        "user_goal": None,
        "detected_diet_style": "vegan",
        "user_diet_style": None,
        "detected_training_level": "beginner",
        "user_training_level": None,
        "plan_quality": 5,
        "specific_feedback": "Great plan!",
        "helpful": True,
    }

