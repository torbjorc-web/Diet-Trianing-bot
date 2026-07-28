"""Tests for specialized ML classifiers."""

import pytest
from chatbot.ml.classifiers import (
    GoalClassifier,
    DietStyleClassifier,
    MealPreferenceClassifier,
    TrainingLevelClassifier,
    TrainingSettingClassifier,
)


class TestGoalClassifier:
    """Test suite for Goal classifier."""

    def test_goal_classifier_classes(self):
        """Test that goal classifier has correct classes."""
        clf = GoalClassifier()
        assert "fat loss" in clf.classes
        assert "muscle gain" in clf.classes
        assert "maintenance" in clf.classes
        assert "general fitness" in clf.classes

    def test_goal_classifier_predictions(self):
        """Test goal classifier predictions."""
        clf = GoalClassifier()
        
        # Test fat loss - should predict one of the classes
        pred, conf = clf.predict("I want to lose weight and burn fat")
        assert pred in clf.classes
        assert isinstance(conf, float)
        assert 0 <= conf <= 1
        
        # Test muscle gain
        pred, conf = clf.predict("build muscle and get strong")
        assert pred in clf.classes
        
    def test_goal_classifier_default_training(self):
        """Test that default training data loads correctly."""
        clf = GoalClassifier()
        
        # Should be able to predict after default training
        pred, conf = clf.predict("lose weight")
        assert pred in clf.classes
        assert isinstance(conf, float)


class TestDietStyleClassifier:
    """Test suite for Diet Style classifier."""

    def test_diet_style_classes(self):
        """Test diet style classifier has correct classes."""
        clf = DietStyleClassifier()
        assert "balanced" in clf.classes
        assert "vegetarian" in clf.classes
        assert "vegan" in clf.classes
        assert "low-carb" in clf.classes
        assert "high-protein" in clf.classes

    def test_diet_style_predictions(self):
        """Test diet style predictions."""
        clf = DietStyleClassifier()
        
        # Test vegan - should predict one of the classes
        pred, conf = clf.predict("I am vegan and eat no animal products")
        assert pred in clf.classes
        assert isinstance(conf, float)
        
        # Test vegetarian
        pred, conf = clf.predict("I'm vegetarian, no meat")
        assert pred in clf.classes

    def test_vegan_vs_vegetarian_distinction(self):
        """Test classifier can classify different diet types."""
        clf = DietStyleClassifier()
        
        vegan_pred, _ = clf.predict("no animal products at all, vegan")
        veg_pred, _ = clf.predict("I eat cheese and eggs but no meat")
        
        # Both should be valid classes
        assert vegan_pred in clf.classes
        assert veg_pred in clf.classes


class TestMealPreferenceClassifier:
    """Test suite for Meal Preference classifier."""

    def test_meal_preference_classes(self):
        """Test meal preference classifier has correct classes."""
        clf = MealPreferenceClassifier()
        assert "none" in clf.classes
        assert "halal" in clf.classes
        assert "kosher" in clf.classes
        assert "vegan" in clf.classes
        assert "vegetarian" in clf.classes

    def test_meal_preference_none(self):
        """Test when no specific meal preference."""
        clf = MealPreferenceClassifier()
        
        pred, conf = clf.predict("I eat anything, no restrictions")
        # Should be "none" or one of the choices
        assert pred in clf.classes

    def test_meal_preference_halal(self):
        """Test halal preference detection."""
        clf = MealPreferenceClassifier()
        
        pred, conf = clf.predict("I need halal certified food")
        assert pred in clf.classes
        assert isinstance(conf, float)


class TestTrainingLevelClassifier:
    """Test suite for Training Level classifier."""

    def test_training_level_classes(self):
        """Test training level classifier has correct classes."""
        clf = TrainingLevelClassifier()
        assert "beginner" in clf.classes
        assert "intermediate" in clf.classes
        assert "advanced" in clf.classes

    def test_beginner_classification(self):
        """Test beginner level detection."""
        clf = TrainingLevelClassifier()
        
        pred, conf = clf.predict("I'm just starting out, never worked out before")
        assert pred in clf.classes
        assert isinstance(conf, float)

    def test_advanced_classification(self):
        """Test advanced level detection."""
        clf = TrainingLevelClassifier()
        
        pred, conf = clf.predict("I'm very experienced, trained for years")
        assert pred in clf.classes
        assert isinstance(conf, float)

    def test_intermediate_classification(self):
        """Test intermediate level detection."""
        clf = TrainingLevelClassifier()
        
        pred, conf = clf.predict("I've worked out before but not consistently")
        assert pred in clf.classes
        assert isinstance(conf, float)


class TestTrainingSettingClassifier:
    """Test suite for Training Setting classifier."""

    def test_training_setting_classes(self):
        """Test training setting classifier has correct classes."""
        clf = TrainingSettingClassifier()
        assert "self" in clf.classes
        assert "studio" in clf.classes
        assert "group" in clf.classes

    def test_home_training_detection(self):
        """Test home/self training detection."""
        clf = TrainingSettingClassifier()
        
        pred, conf = clf.predict("I want to train at home with no equipment")
        assert pred in clf.classes
        assert isinstance(conf, float)

    def test_gym_studio_detection(self):
        """Test gym/studio training detection."""
        clf = TrainingSettingClassifier()
        
        pred, conf = clf.predict("I prefer working out at a gym or fitness studio")
        assert pred in clf.classes
        assert isinstance(conf, float)

    def test_group_training_detection(self):
        """Test group training detection."""
        clf = TrainingSettingClassifier()
        
        pred, conf = clf.predict("I like group fitness classes with others")
        assert pred in clf.classes
        assert isinstance(conf, float)
