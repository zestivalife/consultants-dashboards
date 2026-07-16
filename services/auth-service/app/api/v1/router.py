from fastapi import APIRouter
from app.api.v1.routes import (
    auth,
    corporate,
    email_test,
    health,
    identity,
    master_data,
    notifications,
    onboarding,
    people_access,
    team_lead,
    team_member,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(identity.router, prefix="/identity")
api_router.include_router(corporate.router, prefix="/corporate-admin")
api_router.include_router(people_access.router, prefix="/owner/people-access")
api_router.include_router(onboarding.router, prefix="/onboarding")
api_router.include_router(master_data.router, prefix="/owner/master-data")
api_router.include_router(team_lead.router, prefix="/team-lead")
api_router.include_router(team_member.router, prefix="/team-member")
api_router.include_router(notifications.router, prefix="/notifications")
api_router.include_router(email_test.router, prefix="/email")
