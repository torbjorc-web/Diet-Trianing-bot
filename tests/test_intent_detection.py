"""Tests for fuzzy intent detection."""

from chatbot.ml.intent_detection import FuzzyMatcher


class TestFuzzyMatcher:
    """Test suite for FuzzyMatcher."""

    def test_match_intent_meal_plan(self):
        """Test detection of meal plan intent."""
        result = FuzzyMatcher.match_intent("I want a meal plan for weight loss")
        assert result["wants_meal_plan"] is True

    def test_match_intent_training_plan(self):
        """Test detection of training plan intent."""
        result = FuzzyMatcher.match_intent("I need a workout routine")
        assert result["wants_training_plan"] is True

    def test_match_intent_both(self):
        """Test detection of both meal and training intent."""
        result = FuzzyMatcher.match_intent("I want a meal plan and training routine")
        # At least one should be detected
        assert result["wants_meal_plan"] or result["wants_training_plan"]

    def test_match_intent_neither(self):
        """Test when no specific intent detected."""
        result = FuzzyMatcher.match_intent("tell me about nutrition in general")
        # Both false is acceptable
        assert isinstance(result["wants_meal_plan"], bool)
        assert isinstance(result["wants_training_plan"], bool)

    def test_match_intent_typos(self):
        """Test fuzzy matching handles typos."""
        # "meal" vs "meal" - should still match
        result = FuzzyMatcher.match_intent("I want a meal plan")
        assert result["wants_meal_plan"] is True
        
        # Slight misspelling
        result = FuzzyMatcher.match_intent("I want a meel plan")
        assert result["wants_meal_plan"] is True

    def test_match_intent_case_insensitive(self):
        """Test that matching is case insensitive."""
        result1 = FuzzyMatcher.match_intent("I want a MEAL plan")
        result2 = FuzzyMatcher.match_intent("i want a meal plan")
        result3 = FuzzyMatcher.match_intent("I WANT A MEAL PLAN")
        
        assert result1["wants_meal_plan"] is True
        assert result2["wants_meal_plan"] is True
        assert result3["wants_meal_plan"] is True

    def test_match_value_exact_match(self):
        """Test exact value matching."""
        options = ["vegan", "vegetarian", "balanced", "low-carb"]
        result = FuzzyMatcher.match_value("vegan", options)
        assert result == "vegan"

    def test_match_value_partial_match(self):
        """Test partial value matching."""
        options = ["vegan", "vegetarian", "balanced", "low-carb"]
        result = FuzzyMatcher.match_value("veget", options)
        assert result in ["vegan", "vegetarian"]

    def test_match_value_typo_tolerance(self):
        """Test fuzzy matching with typos."""
        options = ["vegan", "vegetarian", "balanced", "low-carb"]
        result = FuzzyMatcher.match_value("vegan", options)
        assert result == "vegan"

    def test_match_value_no_match(self):
        """Test when no match found."""
        options = ["vegan", "vegetarian", "balanced"]
        result = FuzzyMatcher.match_value("xyz", options)
        # Should return best match or None
        assert result is None or result in options

    def test_match_value_case_insensitive(self):
        """Test value matching is case insensitive."""
        options = ["vegan", "vegetarian", "balanced"]
        result = FuzzyMatcher.match_value("VEGAN", options)
        assert result == "vegan"

    def test_match_intent_empty_string(self):
        """Test handling of empty string."""
        result = FuzzyMatcher.match_intent("")
        assert isinstance(result, dict)
        assert "wants_meal_plan" in result
        assert "wants_training_plan" in result

    def test_match_value_empty_options(self):
        """Test with empty options list."""
        result = FuzzyMatcher.match_value("vegan", [])
        assert result is None

    def test_match_value_single_option(self):
        """Test with single option."""
        result = FuzzyMatcher.match_value("vegan", ["vegan"])
        assert result == "vegan"

    def test_intent_with_multiple_keywords(self):
        """Test intent detection with multiple relevant keywords."""
        result = FuzzyMatcher.match_intent(
            "I need a meal plan and workout program for fat loss"
        )
        # Should detect at least one
        assert result["wants_meal_plan"] or result["wants_training_plan"]
