"""Data models for user feedback."""

from dataclasses import dataclass


@dataclass
class UserFeedback:
    """Represents user feedback on a generated plan."""

    timestamp: str
    user_id: str
    prompt: str
    detected_goal: str
    user_goal: str | None  # What user said goal should be
    detected_diet_style: str
    user_diet_style: str | None
    detected_training_level: str
    user_training_level: str | None
    plan_quality: int  # 1-5 rating
    specific_feedback: str  # Free text feedback
    helpful: bool  # Was the plan helpful?
