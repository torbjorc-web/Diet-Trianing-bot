from typing import List, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["alice"])
    prompt: str = Field(
        ...,
        min_length=1,
        examples=["Make both meal and training plan for fat loss with 4 days training"],
    )
    use_history: bool = Field(
        default=True,
        description="Use recent history to interpret follow-up prompts.",
    )
    history_turns: int = Field(
        default=3,
        ge=1,
        le=10,
        description="How many previous turns to include as context.",
    )
    use_onboarding: bool = Field(
        default=True,
        description="Use stored onboarding profile as context for planning.",
    )


class OnboardingSubmitRequest(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["alice"])
    full_name: str = Field(..., min_length=1, examples=["Anna Hansen"])
    goal: str = Field(..., min_length=1, examples=["fat loss"])
    training_level: str = Field(..., min_length=1, examples=["beginner"])
    meal_preference: Literal["halal", "kosher", "vegan", "vegetarian", "none"] = Field(
        ...,
        examples=["halal"],
        description="Allowed values: halal, kosher, vegan, vegetarian, none",
    )
    weight_kg: float | None = Field(default=None, gt=0, examples=[78])
    health_notes: str = Field(default="none", examples=["knee discomfort"])
    training_setting: str = Field(..., min_length=1, examples=["studio"])


class BatchChatRequest(BaseModel):
    requests: List[ChatRequest] = Field(default_factory=list)
