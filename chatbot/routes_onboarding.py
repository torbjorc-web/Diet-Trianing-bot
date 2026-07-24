from fastapi import APIRouter

from chatbot.onboarding import (
    ONBOARDING_QUESTIONS,
    UserOnboardingProfile,
    normalize_training_setting,
    profile_to_dict,
)
from chatbot.schemas import OnboardingSubmitRequest


def create_onboarding_router(onboarding_store) -> APIRouter:
    router = APIRouter(tags=["onboarding"])

    @router.get("/onboarding/questions")
    def onboarding_questions() -> dict:
        return {"questions": ONBOARDING_QUESTIONS}

    @router.post("/onboarding/submit")
    def onboarding_submit(req: OnboardingSubmitRequest) -> dict:
        profile = UserOnboardingProfile(
            user_id=req.user_id,
            full_name=req.full_name.strip(),
            goal=req.goal.strip().lower(),
            training_level=req.training_level.strip().lower(),
            meal_preference=req.meal_preference,
            weight_kg=req.weight_kg,
            health_notes=req.health_notes.strip() or "none",
            training_setting=normalize_training_setting(req.training_setting),
        )
        onboarding_store.upsert(profile)
        return {"saved": True, "profile": profile_to_dict(profile)}

    @router.get("/onboarding/{user_id}")
    def onboarding_get(user_id: str) -> dict:
        profile = onboarding_store.get(user_id)
        if profile is None:
            return {"found": False}
        return {"found": True, "profile": profile_to_dict(profile)}

    @router.delete("/onboarding/{user_id}")
    def onboarding_clear(user_id: str) -> dict:
        removed = onboarding_store.clear(user_id)
        return {"removed": removed}

    return router
