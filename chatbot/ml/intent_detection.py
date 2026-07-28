"""Fuzzy matching for improved intent and preference detection."""

from fuzzywuzzy import fuzz


class FuzzyMatcher:
    """Fuzzy matching for improved intent and preference detection."""

    @staticmethod
    def match_intent(prompt: str, threshold: int = 70) -> dict[str, bool]:
        """Fuzzy match against meal and training keywords.

        Args:
            prompt: User prompt
            threshold: Fuzzy match threshold (0-100)

        Returns:
            Dict with wants_meal_plan and wants_training_plan booleans
        """
        lowered = prompt.lower()

        meal_keywords = ["meal", "diet", "nutrition", "calorie", "food", "eating"]
        training_keywords = ["training", "workout", "exercise", "gym", "program", "fitness"]

        wants_meal = any(
            fuzz.partial_ratio(keyword, lowered) > threshold
            for keyword in meal_keywords
        )
        wants_training = any(
            fuzz.partial_ratio(keyword, lowered) > threshold
            for keyword in training_keywords
        )

        # Explicit both patterns
        if fuzz.partial_ratio("both", lowered) > 80:
            wants_meal = True
            wants_training = True

        return {"wants_meal_plan": wants_meal, "wants_training_plan": wants_training}

    @staticmethod
    def match_value(text: str, options: list[str], threshold: int = 60) -> str:
        """Fuzzy match text against a list of options.

        Args:
            text: Input text
            options: List of valid options
            threshold: Match threshold (0-100)

        Returns:
            Best matching option or first option if no good match
        """
        if not text or not options:
            if not options:
                return None
            return options[0]

        best_match = options[0]
        best_score = 0

        for option in options:
            score = fuzz.token_set_ratio(text.lower(), option.lower())
            if score > best_score:
                best_score = score
                best_match = option

        if best_score >= threshold:
            return best_match
        return options[0]
