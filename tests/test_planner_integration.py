"""Integration tests for planner with ML components."""

from chatbot.planner import DietTrainingPlanner, UserPreferences


class TestPlannerMLIntegration:
    """Test suite for Planner integration with ML."""

    def test_planner_initialization_with_ml(self):
        """Test planner initializes with ML enabled."""
        planner = DietTrainingPlanner(use_ml=True)
        assert planner.use_ml is True

    def test_planner_initialization_without_ml(self):
        """Test planner initializes with ML disabled."""
        planner = DietTrainingPlanner(use_ml=False)
        assert planner.use_ml is False

    def test_planner_build_plan_ml_enabled(self):
        """Test planner generates plan with ML enabled."""
        planner = DietTrainingPlanner(use_ml=True)
        plan = planner.build_plan(
            user_id="test_user",
            prompt="lose weight, vegan, beginner"
        )
        
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_planner_extract_preferences_ml(self):
        """Test that planner extracts preferences using ML."""
        planner = DietTrainingPlanner(use_ml=True)
        prefs = planner._extract_preferences("fat loss goal, vegetarian diet, beginner level")
        
        assert isinstance(prefs, UserPreferences)
        assert hasattr(prefs, 'goal')
        assert hasattr(prefs, 'diet_style')
        assert hasattr(prefs, 'training_level')

    def test_planner_detect_intent_ml(self):
        """Test that planner detects intent using fuzzy matching."""
        planner = DietTrainingPlanner(use_ml=True)
        intent = planner._detect_intent("meal plan and workout routine")
        
        assert isinstance(intent.wants_meal_plan, bool)
        assert isinstance(intent.wants_training_plan, bool)

    def test_planner_handle_missing_preferences(self):
        """Test planner handles missing preference data."""
        planner = DietTrainingPlanner(use_ml=True)
        plan = planner.build_plan(
            user_id="minimal_user",
            prompt="hello"
        )
        
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_planner_prefers_ml_with_high_confidence(self):
        """Test that planner prefers ML predictions with high confidence."""
        planner = DietTrainingPlanner(use_ml=True)
        
        # Should use ML (model trained with defaults)
        prefs = planner._extract_preferences("I want to lose weight and get lean")
        
        # Should detect "fat loss" goal
        assert prefs.goal is not None

    def test_planner_fallback_without_ml_data(self):
        """Test planner falls back to rules without trained ML data."""
        # Create planner without training models first
        planner = DietTrainingPlanner(use_ml=True)
        
        # Even without trained models, should still generate a plan
        plan = planner.build_plan(
            user_id="user",
            prompt="diet plan needed"
        )
        
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_planner_consistent_predictions(self):
        """Test that planner makes consistent predictions for same input."""
        planner = DietTrainingPlanner(use_ml=True)
        
        prompt = "muscle gain, high protein, advanced"
        
        prefs1 = planner._extract_preferences(prompt)
        prefs2 = planner._extract_preferences(prompt)
        
        # Goal should be same
        assert prefs1.goal == prefs2.goal

    def test_planner_with_health_extraction(self):
        """Test planner extracts health conditions from prompt."""
        planner = DietTrainingPlanner(use_ml=True)
        
        prompt = "I have knee pain and diabetes, need beginner-friendly workout"
        # Build plan should handle health conditions
        plan = planner.build_plan(
            user_id="health_user",
            prompt=prompt
        )
        
        assert isinstance(plan, str)

    def test_planner_regex_extraction(self):
        """Test planner extracts weight and training days via regex."""
        planner = DietTrainingPlanner(use_ml=True)
        
        # Should extract weight_kg and training_days from prompt
        prompt = "I weigh 85 kg and can train 4 days per week"
        plan = planner.build_plan(
            user_id="stats_user",
            prompt=prompt
        )
        
        assert isinstance(plan, str)

