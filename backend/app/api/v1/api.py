from fastapi import APIRouter
from app.api.v1.endpoints import auth, recruitment, onboarding,candidate_portal
 
api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(recruitment.router, prefix="/recruitment", tags=["Recruitment"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(candidate_portal.router, prefix="", tags=["Candidate Portal"])