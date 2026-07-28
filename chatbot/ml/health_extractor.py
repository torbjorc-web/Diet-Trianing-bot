"""Health condition extraction from user prompts."""

import re


class HealthConditionExtractor:
    """Extract and recognize health conditions from text."""

    # Common health keywords mapped to descriptions
    HEALTH_KEYWORDS = {
        "knee": "knee pain/issues",
        "back pain": "back pain",
        "lower back": "lower back pain",
        "upper back": "upper back pain",
        "shoulder": "shoulder issues",
        "elbow": "elbow pain",
        "wrist": "wrist pain",
        "ankle": "ankle issues",
        "arthritis": "arthritis",
        "diabetes": "diabetes",
        "asthma": "asthma",
        "hypertension": "high blood pressure",
        "high blood pressure": "hypertension",
        "heart": "heart condition",
        "cardiac": "cardiac issues",
        "respiratory": "respiratory issues",
        "pregnancy": "pregnancy",
        "osteoporosis": "osteoporosis",
        "injury": "injury",
        "injured": "injured",
    }

    @staticmethod
    def extract(prompt: str) -> str:
        """Extract health conditions from prompt.

        Args:
            prompt: User prompt text

        Returns:
            Extracted health notes or "none"
        """
        lowered = prompt.lower()
        found_conditions = []

        # Check for explicit health notes format
        health_patterns = [
            r"health notes?:\s*(.+?)(?:\.|,|$)",
            r"health issues?:\s*(.+?)(?:\.|,|$)",
            r"injur(?:y|ies):\s*(.+?)(?:\.|,|$)",
        ]

        for pattern in health_patterns:
            match = re.search(pattern, lowered)
            if match:
                return match.group(1).strip()

        # Check for keyword matches
        for keyword, condition in HealthConditionExtractor.HEALTH_KEYWORDS.items():
            if keyword in lowered:
                found_conditions.append(condition)

        if found_conditions:
            return ", ".join(set(found_conditions))  # Remove duplicates

        return "none"
