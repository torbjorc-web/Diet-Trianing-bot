"""Fuzzy matching for improved intent and preference detection."""

import re

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
        tokens = re.findall(r"[a-z]+", lowered)

        meal_keywords = ["meal", "diet", "nutrition", "calorie", "food", "eating"]
        training_keywords = ["training", "workout", "exercise", "gym", "program", "fitness"]

        def _matches_keyword(keyword: str) -> bool:
            # Exact whole-word match is preferred to avoid cross-category false positives.
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                return True

            # For single words, compare against individual tokens so typos like
            # "meel" still map to "meal" without matching unrelated words.
            if " " not in keyword:
                comparable_tokens = [
                    token for token in tokens if len(token) >= max(3, len(keyword) - 1)
                ]
                return any(
                    fuzz.ratio(keyword, token) >= threshold
                    for token in comparable_tokens
                )

            # Multi-word keyword fallback.
            return fuzz.partial_ratio(keyword, lowered) >= max(threshold, 85)

        wants_meal = any(
            _matches_keyword(keyword)
            for keyword in meal_keywords
        )
        wants_training = any(
            _matches_keyword(keyword)
            for keyword in training_keywords
        )

        # Explicit both patterns
        if re.search(r"\bboth\b", lowered):
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
