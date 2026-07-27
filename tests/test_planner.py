import pytest


@pytest.mark.parametrize(
    "prompt, expected_goal",
    [
        ("meal plan to lose weight", "fat loss"),
        ("meal plan for fat loss", "fat loss"),
        ("diet for weight loss", "fat loss"),
        ("training to gain muscle", "muscle gain"),
        ("bulk up program", "muscle gain"),
        ("food plan to maintain my shape", "maintenance"),
        ("just a workout program", "general fitness"),
    ],
)
def test_extracts_goal_from_prompt(planner, prompt, expected_goal):
    assert planner._extract_preferences(prompt).goal == expected_goal


@pytest.mark.parametrize(
    "prompt, expected_style",
    [
        ("vegetarian meal plan", "vegetarian"),
        ("vegan meal plan", "vegan"),
        ("low carb diet", "low-carb"),
        ("high protein diet", "high-protein"),
        ("normal diet", "balanced"),
    ],
)
def test_extracts_diet_style(planner, prompt, expected_style):
    assert planner._extract_preferences(prompt).diet_style == expected_style


@pytest.mark.parametrize(
    "prompt, expected_preference",
    [
        ("halal meal plan", "halal"),
        ("kosher meal plan", "kosher"),
        ("vegan meal plan", "vegan"),
        ("vegetarian meal plan", "vegetarian"),
        ("meal plan", "none"),
    ],
)
def test_extracts_meal_preference(planner, prompt, expected_preference):
    assert planner._extract_preferences(prompt).meal_preference == expected_preference


@pytest.mark.parametrize(
    "prompt, expected_level",
    [
        ("training plan", "beginner"),
        ("intermediate training plan", "intermediate"),
        ("advanced training plan", "advanced"),
    ],
)
def test_extracts_training_level(planner, prompt, expected_level):
    assert planner._extract_preferences(prompt).training_level == expected_level


@pytest.mark.parametrize(
    "prompt, expected_days",
    [
        ("training plan", 3),
        ("training plan 4 days", 4),
        ("training plan with 5days", 5),
        ("training plan 1 day", 2),
        ("training plan 9 days", 6),
    ],
)
def test_extracts_training_days_and_clamps_to_supported_range(planner, prompt, expected_days):
    assert planner._extract_preferences(prompt).training_days == expected_days


@pytest.mark.parametrize(
    "prompt, expected_weight",
    [
        ("meal plan, I weigh 78 kg", 78.0),
        ("meal plan for 102.5 kilograms", 102.5),
        ("meal plan", None),
    ],
)
def test_extracts_weight(planner, prompt, expected_weight):
    assert planner._extract_preferences(prompt).weight_kg == expected_weight


@pytest.mark.parametrize(
    "prompt, expected_setting",
    [
        ("training plan at the studio", "studio"),
        ("gym training plan", "studio"),
        ("group training plan", "group"),
        ("training class plan", "group"),
        ("home training plan", "self"),
    ],
)
def test_extracts_training_setting(planner, prompt, expected_setting):
    assert planner._extract_preferences(prompt).training_setting == expected_setting


def test_extracts_explicit_health_notes(planner):
    preferences = planner._extract_preferences("training plan. health notes: sore shoulder")
    assert preferences.health_notes == "sore shoulder"


def test_infers_health_considerations_from_keywords(planner):
    preferences = planner._extract_preferences("training plan but my knee hurts")
    assert preferences.health_notes == "has health considerations"


def test_health_notes_default_to_none(planner):
    assert planner._extract_preferences("training plan").health_notes == "none"


@pytest.mark.parametrize(
    "prompt, wants_meal, wants_training",
    [
        ("give me a meal plan", True, False),
        ("nutrition advice", True, False),
        ("give me a training plan", False, True),
        ("workout program", False, True),
        ("meal and training plan", True, True),
        ("both please", True, True),
        ("hello there", False, False),
    ],
)
def test_detects_intent(planner, prompt, wants_meal, wants_training):
    intent = planner._detect_intent(prompt)
    assert intent.wants_meal_plan is wants_meal
    assert intent.wants_training_plan is wants_training


def test_meal_only_plan_contains_meal_section_only(planner):
    plan = planner.build_plan(user_id="alice", prompt="vegan meal plan for fat loss")
    assert "Meal plan:" in plan
    assert "Training plan:" not in plan
    assert plan.startswith("Hi alice.")


def test_training_only_plan_contains_training_section_only(planner):
    plan = planner.build_plan(user_id="alice", prompt="advanced training plan 5 days")
    assert "Training plan:" in plan
    assert "Meal plan:" not in plan


def test_combined_plan_contains_both_sections(planner):
    plan = planner.build_plan(
        user_id="alice", prompt="make both meal and training plan for fat loss"
    )
    assert "Meal plan:" in plan
    assert "Training plan:" in plan


def test_plan_without_recognised_intent_returns_guidance(planner):
    plan = planner.build_plan(user_id="alice", prompt="hello")
    assert "I can create a meal plan" in plan
    assert "Meal plan:" not in plan
    assert "Training plan:" not in plan


def test_every_plan_includes_safety_note(planner):
    plan = planner.build_plan(user_id="alice", prompt="hello")
    assert "not medical advice" in plan


def test_meal_plan_reflects_goal_and_preference(planner):
    plan = planner.build_plan(user_id="alice", prompt="halal meal plan to lose weight, 80 kg")
    assert "Goal: fat loss" in plan
    assert "Meal preference: halal" in plan
    assert "halal-certified" in plan
    assert "calorie deficit" in plan
    assert "Weight reference: 80 kg" in plan


def test_meal_plan_for_muscle_gain_uses_surplus(planner):
    plan = planner.build_plan(user_id="alice", prompt="meal plan to gain muscle")
    assert "calorie surplus" in plan


def test_vegan_meal_plan_uses_plant_protein_tips(planner):
    plan = planner.build_plan(user_id="alice", prompt="vegan meal plan")
    assert "tempeh" in plan
    assert "Exclude all animal products" in plan


def test_meal_plan_without_weight_says_not_provided(planner):
    plan = planner.build_plan(user_id="alice", prompt="meal plan")
    assert "Weight reference: not provided" in plan


@pytest.mark.parametrize(
    "prompt, expected_split",
    [
        ("training plan 3 days", "full-body"),
        ("training plan 4 days", "upper/lower"),
        ("training plan 6 days", "push/pull/legs + cardio"),
    ],
)
def test_training_split_depends_on_days(planner, prompt, expected_split):
    assert f"Split: {expected_split}" in planner.build_plan(user_id="alice", prompt=prompt)


@pytest.mark.parametrize(
    "prompt, expected_reps",
    [
        ("training plan", "2-3 sets x 8-12 reps"),
        ("intermediate training plan", "3-4 sets x 6-12 reps"),
        ("advanced training plan", "4-5 sets x 5-10 reps"),
    ],
)
def test_training_rep_range_depends_on_level(planner, prompt, expected_reps):
    assert expected_reps in planner.build_plan(user_id="alice", prompt=prompt)


@pytest.mark.parametrize(
    "prompt, expected_tip",
    [
        ("gym training plan", "compound machines"),
        ("group training plan", "partner pacing"),
        ("training plan at home", "resistance bands"),
    ],
)
def test_training_environment_tip_depends_on_setting(planner, prompt, expected_tip):
    assert expected_tip in planner.build_plan(user_id="alice", prompt=prompt)


def test_health_notes_are_applied_to_both_sections(planner):
    plan = planner.build_plan(
        user_id="alice", prompt="both meal and training plan. health issues: asthma"
    )
    assert "Health consideration: asthma" in plan
    assert "Health note applied: asthma" in plan


def test_plan_generation_is_deterministic(planner):
    prompt = "both meal and training plan for fat loss, 4 days, halal"
    assert planner.build_plan(user_id="alice", prompt=prompt) == planner.build_plan(
        user_id="alice", prompt=prompt
    )
