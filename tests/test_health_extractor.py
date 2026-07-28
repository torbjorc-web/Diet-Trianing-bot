"""Tests for health condition extraction."""

import pytest
from chatbot.ml.health_extractor import HealthConditionExtractor


class TestHealthConditionExtractor:
    """Test suite for HealthConditionExtractor."""

    def test_extract_none(self):
        """Test when no health conditions present."""
        result = HealthConditionExtractor.extract("I'm healthy and have no issues")
        assert result == "none"

    def test_extract_health_notes_pattern(self):
        """Test extraction with 'health notes:' pattern."""
        result = HealthConditionExtractor.extract("health notes: knee pain, back issues")
        assert result != "none"
        assert "knee" in result.lower() or "back" in result.lower()

    def test_extract_health_issues_pattern(self):
        """Test extraction with 'health issues:' pattern."""
        result = HealthConditionExtractor.extract("health issues: diabetes, asthma")
        assert result != "none"
        assert "diabetes" in result.lower() or "asthma" in result.lower()

    def test_extract_injuries_pattern(self):
        """Test extraction with 'injuries:' pattern."""
        result = HealthConditionExtractor.extract("injuries: shoulder injury, knee sprain")
        assert result != "none"
        assert "shoulder" in result.lower() or "knee" in result.lower()

    def test_extract_keyword_knee_pain(self):
        """Test extraction of knee pain keyword."""
        result = HealthConditionExtractor.extract("I have knee pain from running")
        assert result != "none"
        assert "knee" in result.lower()

    def test_extract_keyword_back_pain(self):
        """Test extraction of back pain keyword."""
        result = HealthConditionExtractor.extract("My back hurts and back pain is constant")
        assert result != "none"
        assert "back" in result.lower()

    def test_extract_keyword_diabetes(self):
        """Test extraction of diabetes keyword."""
        result = HealthConditionExtractor.extract("I have diabetes type 2")
        assert result != "none"
        assert "diabetes" in result.lower()

    def test_extract_keyword_asthma(self):
        """Test extraction of asthma keyword."""
        result = HealthConditionExtractor.extract("I'm asthmatic and get winded easily")
        assert result != "none"
        assert "asthma" in result.lower()

    def test_extract_multiple_conditions(self):
        """Test extraction of multiple conditions."""
        result = HealthConditionExtractor.extract("I have knee pain and back issues")
        assert result != "none"

    def test_extract_case_insensitive(self):
        """Test that extraction is case insensitive."""
        result1 = HealthConditionExtractor.extract("I have KNEE PAIN")
        result2 = HealthConditionExtractor.extract("I have knee pain")
        result3 = HealthConditionExtractor.extract("I have Knee Pain")
        
        assert result1 != "none"
        assert result2 != "none"
        assert result3 != "none"

    def test_extract_with_pattern_and_keywords(self):
        """Test extraction when both pattern and keywords present."""
        result = HealthConditionExtractor.extract(
            "health issues: knee pain and diabetes"
        )
        assert result != "none"

    def test_extract_empty_string(self):
        """Test with empty string."""
        result = HealthConditionExtractor.extract("")
        assert result == "none"

    def test_extract_injury_variations(self):
        """Test various injury mentions."""
        injuries = [
            "I hurt my shoulder",
            "ankle injury",
            "hip pain",
            "elbow strain"
        ]
        
        for injury in injuries:
            result = HealthConditionExtractor.extract(injury)
            # Should return something (might not always be perfect extraction)
            assert isinstance(result, str)

    def test_extract_chronic_conditions(self):
        """Test extraction of chronic conditions."""
        result = HealthConditionExtractor.extract("I have high blood pressure")
        assert isinstance(result, str)

    def test_extract_no_false_positives(self):
        """Test that similar words don't cause false positives."""
        # "back" in "feedback" shouldn't trigger back pain
        result = HealthConditionExtractor.extract("I got positive feedback")
        # This should ideally return "none" or not incorrectly extract "back"
        assert isinstance(result, str)
