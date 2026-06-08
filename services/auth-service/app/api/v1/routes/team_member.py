import uuid
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.team import Team, SessionRequest, TeamMembership
from app.db.models.notification import Notification
from app.db.models.metric import WellnessMetric
from app.db.models.tool_usage import ToolUsage
from app.schemas.auth import UserResponse
from app.schemas.team_member import TeamMemberStats, MemberTeamInfo, JoinTeamRequest, MetricCreate, MetricResponse
from app.schemas.corporate import SessionRequestCreate, SessionRequestResponse
from app.schemas.notification import NotificationResponse
from app.core.response import success_response

router = APIRouter(tags=["team-member"])


@router.get("/profile")
async def get_member_profile(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return success_response({
        "id": str(user.id),
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "phone": user.phone,
        "role": current_user.role,
        "companyId": str(user.company_id) if user.company_id else None,
    })


@router.get("/dashboard/stats")
async def member_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    # Base stats
    completed_sessions = await db.scalar(
        select(func.count(SessionRequest.id)).where(
            SessionRequest.company_id == (current_user.company_id or current_user.id),
            SessionRequest.status == "COMPLETED",
        )
    ) or 0

    total_sessions = await db.scalar(
        select(func.count(SessionRequest.id)).where(
            SessionRequest.company_id == (current_user.company_id or current_user.id),
        )
    ) or 0

    # Helper to get latest metric
    async def get_latest_metric(m_type: str) -> Optional[float]:
        result = await db.execute(
            select(WellnessMetric.value)
            .where(WellnessMetric.user_id == current_user.id, WellnessMetric.type == m_type)
            .order_by(WellnessMetric.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # Fetch metrics
    energy_balance = await get_latest_metric("ENERGY_BALANCE_SCORE")
    body_support = await get_latest_metric("BODY_SUPPORT_SCORE")
    nourishment = await get_latest_metric("NOURISHMENT_SCORE")
    recovery = await get_latest_metric("RECOVERY_SCORE")
    
    # Other metrics for Wellness Tab
    stress_level = await get_latest_metric("STRESS_LEVEL")
    active_calories = await get_latest_metric("ACTIVE_CALORIES")
    heart_rate = await get_latest_metric("HEART_RATE")
    steps_today = await get_latest_metric("STEPS")
    sleep_hours = await get_latest_metric("SLEEP")
    water_liters = await get_latest_metric("HYDRATION")
    sunlight = await get_latest_metric("SUNLIGHT")
    physical_ease = await get_latest_metric("PHYSICAL_EASE_SCORE")

    # Calculate aggregate wellness score (average of the 4 main metrics + others)
    # Normalize steps: 10,000 steps = 100 points
    normalized_steps = (steps_today / 10000 * 100) if steps_today is not None else None
    
    # Normalize heart rate: Ideal resting HR around 60-70. 
    # Using a simple inverse scale where 60-70 = 100, and 100 = 0 points for simplicity in aggregation
    normalized_hr = max(0, min(100, (100 - (heart_rate - 60) if heart_rate is not None else None) if heart_rate is not None else None)) if heart_rate is not None else None

    # Normalize sunlight: 30 minutes = 100 points
    normalized_sunlight = min(100, (sunlight / 30 * 100)) if sunlight is not None else None

    main_metrics = [m for m in [energy_balance, body_support, nourishment, recovery, active_calories, normalized_steps, normalized_hr, normalized_sunlight] if m is not None]
    wellness_score = sum(main_metrics) / len(main_metrics) if main_metrics else None

    # Performance Score Calculation
    # Formula: (Physical Wellness Index × 0.4) + (Energy Balance × 0.15) + (Body Support × 0.15) + (Nourishment × 0.15) + (Recovery × 0.15)
    # Scale: All inputs are 0-100, result is 0-100. Multiply by 10 for "points" display (0-1000) if needed.
    performance_score = None
    if wellness_score is not None:
        eb = energy_balance or 0
        bs = body_support or 0
        ns = nourishment or 0
        rs = recovery or 0
        performance_score = (wellness_score * 0.4) + (eb * 0.15) + (bs * 0.15) + (ns * 0.15) + (rs * 0.15)

    return success_response(
        TeamMemberStats(
            completedSessions=completed_sessions,
            totalSessions=total_sessions,
            completionRate=int((completed_sessions / total_sessions * 100) if total_sessions else 0),
            energyBalance=energy_balance,
            bodySupport=body_support,
            nourishmentScore=nourishment,
            recoveryScore=recovery,
            stressLevel=stress_level,
            activeCalories=active_calories,
            heartRate=heart_rate,
            stepsToday=steps_today,
            waterLiters=water_liters,
            sunlightToday=sunlight,
            physicalEase=physical_ease,
            wellnessScore=wellness_score,
            performanceScore=performance_score
        ).model_dump()
    )


@router.get("/me/team")
async def get_member_team(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamMembership, Team)
        .join(Team, Team.id == TeamMembership.team_id)
        .where(TeamMembership.user_id == current_user.id)
        .limit(1)
    )
    row = result.first()

    if not row:
        return success_response({"team": None, "isLead": False, "joinedAt": None, "membershipId": None})

    membership, team = row
    member_count = await db.scalar(
        select(func.count(TeamMembership.id)).where(TeamMembership.team_id == team.id)
    ) or 0

    return success_response({
        "team": {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "joinCode": team.join_code,
            "memberCount": member_count,
        },
        "isLead": membership.is_lead,
        "joinedAt": membership.joined_at.isoformat(),
        "membershipId": str(membership.id),
    })


@router.post("/teams/join")
async def join_team(
    payload: JoinTeamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    code = payload.teamCode.strip().upper()
    result = await db.execute(select(Team).where(Team.join_code == code))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Invalid team code")

    # Enforce company isolation — team must belong to the same company
    if current_user.company_id and team.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Team belongs to a different company")

    # Check already a member
    existing = await db.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team.id,
            TeamMembership.user_id == current_user.id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this team")

    is_lead = team.lead_id == current_user.id
    membership = TeamMembership(team_id=team.id, user_id=current_user.id, is_lead=is_lead)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)

    return success_response({"membershipId": str(membership.id)}, "Joined team successfully")


@router.get("/metrics")
async def list_metrics(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await db.execute(
        select(WellnessMetric)
        .where(WellnessMetric.user_id == current_user.id)
        .order_by(WellnessMetric.recorded_at.desc())
        .limit(limit)
    )
    metrics = result.scalars().all()
    data = [
        MetricResponse(
            id=m.id,
            type=m.type,
            value=m.value,
            unit=m.unit,
            notes=m.notes,
            recordedAt=m.recorded_at,
        ).model_dump()
        for m in metrics
    ]
    return success_response(data)


@router.post("/metrics")
async def log_metric(
    payload: MetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    metric = WellnessMetric(
        user_id=current_user.id,
        type=payload.type,
        value=payload.value,
        unit=payload.unit,
        notes=payload.notes,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)

    return success_response(
        MetricResponse(
            id=metric.id,
            type=metric.type,
            value=metric.value,
            unit=metric.unit,
            notes=metric.notes,
            recordedAt=metric.recorded_at,
        ).model_dump(),
        "Metric logged successfully",
    )


@router.get("/notifications")
async def get_member_notifications(
    status: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if status == "UNREAD":
        query = query.where(Notification.read == False)  # noqa: E712
    query = query.order_by(Notification.created_at.desc()).limit(limit)

    result = await db.execute(query)
    notifications = result.scalars().all()
    data = [
        NotificationResponse(
            id=n.id,
            title=n.title,
            message=n.message,
            type=n.type,
            priority=n.priority,
            read=n.read,
            timestamp=n.created_at,
        ).model_dump()
        for n in notifications
    ]
    return success_response(data)

@router.post("/sessions")
async def request_session(
    session: SessionRequestCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    # Fetch the user's company_id from db to be safe
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    company_id = user.company_id if user and user.company_id else current_user.id

    new_request = SessionRequest(
        title=session.title,
        description=session.description,
        type=session.type,
        mode=session.mode,
        duration=session.duration,
        scheduled_at=session.scheduled_at,
        target_audience=session.target_audience,
        timezone=session.timezone,
        request_notes=session.request_notes,
        team_id=session.team_id,
        company_id=company_id
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    return success_response(SessionRequestResponse.model_validate(new_request).model_dump(by_alias=True, mode="json"), "Session requested successfully")

@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    company_id = user.company_id if user and user.company_id else current_user.id

    # Fetch all sessions for this company
    result = await db.execute(select(SessionRequest).where(SessionRequest.company_id == company_id))
    sessions = result.scalars().all()
    res = [SessionRequestResponse.model_validate(s).model_dump(by_alias=True, mode="json") for s in sessions]
    return success_response(res)


# ── Tool Usage endpoints ───────────────────────────────────────────────────────

@router.post("/tools/log")
async def log_tool_usage(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Log a completed tool session. Calculates streak automatically."""
    tool_id = payload.get("toolId", "")
    
    # Calculate streak: check if user used this tool yesterday
    yesterday_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) - timedelta(days=1)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    # Most recent usage before today
    last_result = await db.execute(
        select(ToolUsage)
        .where(
            ToolUsage.user_id == current_user.id,
            ToolUsage.tool_id == tool_id,
            ToolUsage.completed_at < today_start,
        )
        .order_by(ToolUsage.completed_at.desc())
        .limit(1)
    )
    last_usage = last_result.scalar_one_or_none()

    if last_usage and last_usage.completed_at >= yesterday_start:
        streak = last_usage.streak_days + 1
    else:
        streak = 1

    usage = ToolUsage(
        user_id=current_user.id,
        tool_id=tool_id,
        tool_name=payload.get("toolName", tool_id),
        sub_type=payload.get("subType"),
        duration_seconds=payload.get("durationSeconds", 0),
        streak_days=streak,
    )
    db.add(usage)
    await db.commit()
    await db.refresh(usage)

    return success_response({
        "id": str(usage.id),
        "toolId": usage.tool_id,
        "streakDays": usage.streak_days,
        "completedAt": usage.completed_at.isoformat(),
    }, "Tool usage logged")


@router.get("/tools/stats")
async def get_tool_stats(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Return per-tool streaks and overall stats for the sidebar."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    week_start = today_start - timedelta(days=7)

    # Count completions today
    completed_today = await db.scalar(
        select(func.count(ToolUsage.id)).where(
            ToolUsage.user_id == current_user.id,
            ToolUsage.completed_at >= today_start,
        )
    ) or 0

    # Total minutes this week
    week_seconds_result = await db.execute(
        select(func.sum(ToolUsage.duration_seconds)).where(
            ToolUsage.user_id == current_user.id,
            ToolUsage.completed_at >= week_start,
        )
    )
    week_seconds = week_seconds_result.scalar() or 0
    week_minutes = round(week_seconds / 60)

    # Per-tool streaks (latest streak value per tool)
    streaks_result = await db.execute(
        select(ToolUsage.tool_id, ToolUsage.streak_days)
        .where(ToolUsage.user_id == current_user.id)
        .order_by(ToolUsage.completed_at.desc())
    )
    tool_streak_map = {}
    for row in streaks_result.all():
        if row.tool_id not in tool_streak_map:
            tool_streak_map[row.tool_id] = row.streak_days

    # Overall best streak across all tools
    best_streak = max(tool_streak_map.values(), default=0)

    return success_response({
        "completedToday": completed_today,
        "weekMinutes": week_minutes,
        "bestStreak": best_streak,
        "toolStreaks": tool_streak_map,
    })


@router.get("/tools/recommendations")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Return 4 personalised tool recommendations based on usage history."""
    # All tools catalogue
    all_tools = [
        {"toolId": "breathing", "toolName": "Breathing", "duration": "5 min",
         "description": "4-7-8 technique for nervous system reset.", "theme": "green", "icon": "breathing"},
        {"toolId": "meditation", "toolName": "Meditation", "duration": "10 min",
         "description": "Guided mindfulness to clear mental clutter.", "theme": "blue", "icon": "movement"},
        {"toolId": "eye-rest", "toolName": "Eye Rest", "duration": "2 min",
         "description": "20-20-20 rule to reduce eye strain.", "theme": "yellow", "icon": "focus"},
        {"toolId": "lungs", "toolName": "Lungs Exercise", "duration": "5 min",
         "description": "Strengthen respiratory muscles.", "theme": "pink", "icon": "hydration"},
        {"toolId": "pomodoro", "toolName": "Focus Mode", "duration": "25 min",
         "description": "Deep work session with Pomodoro intervals.", "theme": "yellow", "icon": "focus"},
    ]

    # Find tools NOT used in the last 24 hours → recommend those first
    recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_result = await db.execute(
        select(ToolUsage.tool_id).where(
            ToolUsage.user_id == current_user.id,
            ToolUsage.completed_at >= recent_cutoff,
        ).distinct()
    )
    recently_used = {row.tool_id for row in recent_result.all()}

    not_used = [t for t in all_tools if t["toolId"] not in recently_used]
    used_less = [t for t in all_tools if t["toolId"] in recently_used]

    # Combine: unused tools first, then recently-used ones; take first 4
    recommendations = (not_used + used_less)[:4]
    return success_response(recommendations)
