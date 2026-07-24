import re
from dataclasses import dataclass


@dataclass
class PlanIntent:
    wants_meal_plan: bool
    wants_training_plan: bool


@dataclass
class UserPreferences:
    goal: str
    diet_style: str
    meal_preference: str
    training_level: str
    training_days: int
    weight_kg: float | None
    health_notes: str
    training_setting: str


class DietTrainingPlanner:
    """Generates simple diet and training plans from natural-language prompts."""

    def build_plan(self, user_id: str, prompt: str) -> str:
        intent = self._detect_intent(prompt)
        preferences = self._extract_preferences(prompt)

        sections: list[str] = [f"Hi {user_id}. Here is your tailored plan:"]

        if intent.wants_meal_plan:
            sections.append(self._build_meal_plan(preferences))

        if intent.wants_training_plan:
            sections.append(self._build_training_plan(preferences))

        if not intent.wants_meal_plan and not intent.wants_training_plan:
            sections.append(
                "I can create a meal plan, a training plan, or both. "
                "Tell me your goal and whether you want meal, training, or both plans."
            )

        sections.append(
            "Safety note: this is educational guidance, not medical advice. "
            "If you have medical conditions, consult a qualified professional."
        )

        return "\n\n".join(sections)

    def _detect_intent(self, prompt: str) -> PlanIntent:
        lowered = prompt.lower()
        meal_keywords = ("meal", "diet", "nutrition", "calorie", "food")
        training_keywords = ("training", "workout", "exercise", "gym", "program")

        wants_meal = any(word in lowered for word in meal_keywords)
        wants_training = any(word in lowered for word in training_keywords)

        if "both" in lowered or "plan for meal and training" in lowered:
            wants_meal = True
            wants_training = True

        return PlanIntent(wants_meal_plan=wants_meal, wants_training_plan=wants_training)

    def _extract_preferences(self, prompt: str) -> UserPreferences:
        lowered = prompt.lower()

        goal = "general fitness"
        if "lose" in lowered or "fat loss" in lowered or "weight loss" in lowered:
            goal = "fat loss"
        elif "gain" in lowered or "muscle" in lowered or "bulk" in lowered:
            goal = "muscle gain"
        elif "maintain" in lowered:
            goal = "maintenance"

        diet_style = "balanced"
        if "vegetarian" in lowered:
            diet_style = "vegetarian"
        elif "vegan" in lowered:
            diet_style = "vegan"
        elif "low carb" in lowered:
            diet_style = "low-carb"
        elif "high protein" in lowered:
            diet_style = "high-protein"

        meal_preference = "none"
        if "halal" in lowered:
            meal_preference = "halal"
        elif "kosher" in lowered:
            meal_preference = "kosher"
        elif "vegan" in lowered:
            meal_preference = "vegan"
        elif "vegetarian" in lowered:
            meal_preference = "vegetarian"

        training_level = "beginner"
        if "intermediate" in lowered:
            training_level = "intermediate"
        elif "advanced" in lowered:
            training_level = "advanced"

        days_match = re.search(r"(\d)\s*(day|days)", lowered)
        training_days = 3
        if days_match:
            training_days = max(2, min(6, int(days_match.group(1))))

        weight_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*(kg|kgs|kilogram|kilograms)", lowered)
        weight_kg: float | None = None
        if weight_match:
            weight_kg = float(weight_match.group(1))

        training_setting = "self"
        if "studio" in lowered or "gym" in lowered:
            training_setting = "studio"
        elif "group" in lowered or "class" in lowered or "team" in lowered:
            training_setting = "group"

        health_notes = "none"
        health_match = re.search(
            r"health notes:\s*(.+)|health issues?:\s*(.+)|injur(?:y|ies):\s*(.+)",
            lowered,
        )
        if health_match:
            matched = next((g for g in health_match.groups() if g), None)
            if matched:
                health_notes = matched.strip()
        elif any(k in lowered for k in ("knee", "back pain", "diabetes", "asthma", "hypertension")):
            health_notes = "has health considerations"

        return UserPreferences(
            goal=goal,
            diet_style=diet_style,
            meal_preference=meal_preference,
            training_level=training_level,
            training_days=training_days,
            weight_kg=weight_kg,
            health_notes=health_notes,
            training_setting=training_setting,
        )

    def _build_meal_plan(self, preferences: UserPreferences) -> str:
        calories = {
            "fat loss": "Target a slight calorie deficit (about 300-400 kcal/day).",
            "muscle gain": "Target a slight calorie surplus (about 250-350 kcal/day).",
            "maintenance": "Eat around maintenance calories.",
            "general fitness": "Eat around maintenance with mostly whole foods.",
        }[preferences.goal]

        protein_tip = "Aim for protein in each meal (eggs, fish, tofu, beans, yogurt)."
        if preferences.diet_style == "vegan":
            protein_tip = "Use tofu, tempeh, lentils, chickpeas, soy yogurt, and protein shakes."
        elif preferences.diet_style == "vegetarian":
            protein_tip = "Use eggs, dairy, tofu, beans, lentils, and Greek yogurt."

        meal_rule = "Follow your preferred foods and avoid items you do not tolerate."
        if preferences.meal_preference == "halal":
            meal_rule = "Use halal-certified proteins and avoid non-halal ingredients."
        elif preferences.meal_preference == "kosher":
            meal_rule = "Use kosher-certified foods and keep meal combinations kosher-compliant."
        elif preferences.meal_preference == "vegan":
            meal_rule = "Exclude all animal products and use plant-based proteins."
        elif preferences.meal_preference == "vegetarian":
            meal_rule = "Exclude meat and fish; include dairy/eggs if suitable."

        return "\n".join(
            [
                "Meal plan:",
                f"- Goal: {preferences.goal} | Style: {preferences.diet_style}",
                f"- Meal preference: {preferences.meal_preference}",
                (
                    f"- Weight reference: {preferences.weight_kg:g} kg"
                    if preferences.weight_kg is not None
                    else "- Weight reference: not provided"
                ),
                f"- {calories}",
                f"- {protein_tip}",
                f"- Preference rule: {meal_rule}",
                (
                    f"- Health consideration: {preferences.health_notes}. Keep intensity moderate and seek professional guidance when needed."
                    if preferences.health_notes != "none"
                    else "- Health consideration: none reported."
                ),
                "- Sample day:",
                "  Breakfast: oats + fruit + protein source",
                "  Lunch: lean protein + rice/potatoes + vegetables",
                "  Dinner: protein + mixed vegetables + healthy fats",
                "  Snacks: fruit, nuts, yogurt, or protein shake",
                "- Hydration: 2-3 liters of water daily.",
            ]
        )

    def _build_training_plan(self, preferences: UserPreferences) -> str:
        rep_range = {
            "beginner": "2-3 sets x 8-12 reps",
            "intermediate": "3-4 sets x 6-12 reps",
            "advanced": "4-5 sets x 5-10 reps",
        }[preferences.training_level]

        days = preferences.training_days
        split = "full-body"
        if days >= 4:
            split = "upper/lower"
        if days >= 5:
            split = "push/pull/legs + cardio"

        return "\n".join(
            [
                "Training plan:",
                f"- Level: {preferences.training_level} | Days/week: {days} | Split: {split}",
                f"- Preferred training setting: {preferences.training_setting}",
                f"- Main work: {rep_range}",
                "- Weekly template:",
                "  Day 1: Squat or leg press, push exercise, row, plank",
                "  Day 2: Hinge movement, pull exercise, overhead press, core",
                "  Day 3: Full-body circuit + 20-30 min easy cardio",
                "  Day 4+: Repeat pattern with progressive overload",
                (
                    "- Environment tip: use compound machines/free weights and cardio stations available in your studio."
                    if preferences.training_setting == "studio"
                    else "- Environment tip: use circuit-style sessions and partner pacing for group training."
                    if preferences.training_setting == "group"
                    else "- Environment tip: use bodyweight, resistance bands, and dumbbells for self-guided sessions."
                ),
                "- Progression: add 1-2 reps or small weight each week.",
                "- Recovery: sleep 7-9 hours and keep 1-2 rest days weekly.",
                (
                    f"- Health note applied: {preferences.health_notes}. Prioritize pain-free range of motion."
                    if preferences.health_notes != "none"
                    else "- Health note applied: none reported."
                ),
            ]
        )
