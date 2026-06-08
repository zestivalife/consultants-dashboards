import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.team import Team, SessionRequest, TeamMembership
from app.schemas.auth import UserResponse
from app.schemas.team_lead import TeamLeadStats, TeamLeadTeamInfo, TeamMemberInfo, UpcomingSession
from app.core.response import success_response

router = APIRouter(tags=["team-lead"])


def _require_team_lead(current_user: UserResponse):
    if current_user.role not in ("team_lead",):
        raise HTTPException(status_code=403, detail="Team lead access required")


async def _get_lead_team(db: AsyncSession, lead_id: uuid.UUID) -> Team | None:
    """Get the team where current user is the lead."""
    result = await db.execute(select(Team).where(Team.lead_id == lead_id))
    return result.scalar_one_or_none()


@router.get("/dashboard")
async def team_lead_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    _require_team_lead(current_user)
    team = await _get_lead_team(db, current_user.id)

    total_members = 0
    completed_sessions = 0

    if team:
        total_members = await db.scalar(
            select(func.count(TeamMembership.id)).where(TeamMembership.team_id == team.id)
        ) or 0
        completed_sessions = await db.scalar(
            select(func.count(SessionRequest.id)).where(
                SessionRequest.team_id == team.id,
                SessionRequest.status == "COMPLETED",
            )
        ) or 0

    return success_response(
        TeamLeadStats(
            totalMembers=total_members,
            activeMembers=total_members,
            completedSessions=completed_sessions,
            avgWellnessScore=78,
            pendingRequests=0,
            teamMood=7.8,
            participationRate=78,
        ).model_dump()
    )


@router.get("/team")
async def get_lead_team(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    _require_team_lead(current_user)
    team = await _get_lead_team(db, current_user.id)
    if not team:
        return success_response(None, "No team assigned yet")

    member_count = await db.scalar(
        select(func.count(TeamMembership.id)).where(TeamMembership.team_id == team.id)
    ) or 0

    return success_response(
        TeamLeadTeamInfo(
            id=team.id,
            name=team.name,
            description=team.description,
            joinCode=team.join_code,
            memberCount=member_count,
            createdAt=team.created_at,
        ).model_dump()
    )


@router.get("/team/members")
async def list_team_members(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    _require_team_lead(current_user)
    team = await _get_lead_team(db, current_user.id)
    if not team:
        return success_response([], "No team assigned")

    result = await db.execute(
        select(User, TeamMembership)
        .join(TeamMembership, TeamMembership.user_id == User.id)
        .where(TeamMembership.team_id == team.id)
        .order_by(TeamMembership.joined_at)
    )

    members = []
    for user, membership in result.all():
        members.append(
            TeamMemberInfo(
                id=user.id,
                email=user.email,
                firstName=user.first_name,
                lastName=user.last_name,
                phone=user.phone,
                wellnessScore=85,
                status="Active",
                joinedAt=membership.joined_at,
            ).model_dump()
        )

    return success_response(members)


@router.get("/sessions/upcoming")
async def upcoming_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    _require_team_lead(current_user)
    team = await _get_lead_team(db, current_user.id)
    if not team:
        return success_response([])

    result = await db.execute(
        select(SessionRequest)
        .where(
            SessionRequest.team_id == team.id,
            SessionRequest.status.in_(["SCHEDULED", "PENDING"]),
        )
        .order_by(SessionRequest.scheduled_at)
        .limit(5)
    )
    sessions = result.scalars().all()

    data = [
        UpcomingSession(
            id=s.id,
            title=s.title,
            type=s.type,
            date=s.scheduled_at,
            duration=s.duration,
            participants=0,
            status=s.status,
        ).model_dump()
        for s in sessions
    ]
    return success_response(data)
