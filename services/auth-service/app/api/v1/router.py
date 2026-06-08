from fastapi import APIRouter
from app.api.v1.routes import health, auth, corporate, team_lead, team_member, notifications, email_test

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(corporate.router, prefix="/corporate-admin")
api_router.include_router(team_lead.router, prefix="/team-lead")
api_router.include_router(team_member.router, prefix="/team-member")
api_router.include_router(notifications.router, prefix="/notifications")
api_router.include_router(email_test.router, prefix="/email")
