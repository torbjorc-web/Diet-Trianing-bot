"""Data models for user feedback."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserFeedback:
    """Represents user feedback on a generated plan."""

    timestamp: str
    user_id: str
    prompt: str
    detected_goal: str
    user_goal: Optional[str]  # What user said goal should be
    detected_diet_style: str
    user_diet_style: Optional[str]
    detected_training_level: str
    user_training_level: Optional[str]
    plan_quality: int  # 1-5 rating
    specific_feedback: str  # Free text feedback
    helpful: bool  # Was the plan helpful?
