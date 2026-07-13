import uuid
from typing import List, cast
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.team import Team, SessionRequest, TeamMembership
from app.db.models.role import Role
from app.db.models.notification import Notification
from app.schemas.corporate import (
    TeamCreate, TeamResponse, EmployeeInvite, EmployeeResponse,
    ConsultantInvite, ConsultantResponse,
    SessionRequestCreate, SessionRequestResponse, DashboardStats, AnalyticsData,
    AuthorityOption, ManagedPersonCreate, ManagedPersonResponse, ManagedPersonUpdate
)
from app.core.response import success_response
from app.core.email import get_email_service
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.user_service import CreateUserCommand, user_service


async def _notify(db: AsyncSession, user_id: uuid.UUID, title: str, message: str, type: str = "system", priority: str = "low"):
    """Fire-and-forget notification creation."""
    try:
        notif = Notification(user_id=user_id, title=title, message=message, type=type, priority=priority)
        db.add(notif)
    except Exception:
        pass

router = APIRouter(tags=["corporate-admin"])

ADMIN_ROLE_NAMES = {"corporate_client", "corporate_admin", "organization_admin", "admin", "superuser", "PLATFORM_OWNER"}
CONSULTANT_ROLE_NAMES = {"consultant", "provider", "dietician", "senior_consultant"}
MENTOR_ROLE_NAMES = {"mentor", "team_lead"}
ADMIN_MANAGED_ROLE_NAMES = {"admin", "organization_admin", "corporate_admin"}
MANAGED_ROLE_NAMES = CONSULTANT_ROLE_NAMES | MENTOR_ROLE_NAMES | ADMIN_MANAGED_ROLE_NAMES
SUPER_ADMIN_ROLE_NAMES = {"superuser", "platform_owner", "PLATFORM_OWNER"}

AUTHORITY_OPTIONS = [
    {"id": "client_read", "label": "Client Directory", "description": "View assigned client records and progress.", "audience": "all"},
    {"id": "plan_review", "label": "Plan Review", "description": "Review and approve nutrition or recovery plans.", "audience": "consultant"},
    {"id": "report_interpretation", "label": "Report Interpretation", "description": "Interpret uploaded blood reports and biomarker summaries.", "audience": "consultant"},
    {"id": "mentor_queue", "label": "Mentor Queue", "description": "Access mentor escalations, support notes, and supervision views.", "audience": "mentor"},
    {"id": "team_supervision", "label": "Team Supervision", "description": "Oversee consultants, mentor follow-through, and review pipeline health.", "audience": "mentor"},
    {"id": "user_management", "label": "User Management", "description": "Create and manage practitioners and admins.", "audience": "admin"},
    {"id": "analytics_read", "label": "Analytics Access", "description": "View intelligence, revenue, and quality dashboards.", "audience": "admin"},
    {"id": "authority_management", "label": "Authority Management", "description": "Grant or revoke authorities for practitioner accounts.", "audience": "admin"},
]

ROLE_DEFAULT_AUTHORITIES = {
    "mentor": ["client_read", "mentor_queue", "team_supervision"],
    "team_lead": ["client_read", "mentor_queue", "team_supervision"],
    "consultant": ["client_read", "plan_review", "report_interpretation"],
    "provider": ["client_read", "plan_review", "report_interpretation"],
    "dietician": ["client_read", "plan_review", "report_interpretation"],
    "senior_consultant": ["client_read", "plan_review", "report_interpretation", "mentor_queue"],
    "admin": ["client_read", "user_management", "analytics_read"],
    "organization_admin": ["client_read", "user_management", "analytics_read"],
    "corporate_admin": ["client_read", "user_management", "analytics_read"],
}


def _ensure_admin_access(current_user):
    if current_user.role not in ADMIN_ROLE_NAMES:
        raise HTTPException(status_code=403, detail="Admin access is required")


def _ensure_super_admin_access(current_user):
    if current_user.role not in SUPER_ADMIN_ROLE_NAMES:
        raise HTTPException(status_code=403, detail="Super admin access is required")


def _company_scope_id(current_user) -> uuid.UUID:
    return current_user.company_id or current_user.id


def _normalize_role_name(role_name: str) -> str:
    return role_name.lower().replace("-", "_").replace(" ", "_")


def _normalize_authorities(role_name: str, authorities: list[str] | None) -> list[str]:
    requested = [value.strip() for value in (authorities or []) if isinstance(value, str) and value.strip()]
    if requested:
        unique = []
        for value in requested:
            if value not in unique:
                unique.append(value)
        return unique
    return ROLE_DEFAULT_AUTHORITIES.get(role_name, ["client_read"])


def _person_payload(user: User, role_name: str) -> ManagedPersonResponse:
    return ManagedPersonResponse(
        id=user.id,
        email=user.email,
        firstName=user.first_name or "",
        lastName=user.last_name or "",
        phone=user.phone,
        role=role_name,
        specialization=user.industry,
        authorities=user.permissions or [],
        createdAt=user.created_at,
    )

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    team_count = await db.scalar(select(func.count(Team.id)).where(Team.company_id == current_user.id))
    employee_count = await db.scalar(select(func.count(User.id)).where(User.company_id == current_user.id))
    session_count = await db.scalar(select(func.count(SessionRequest.id)).where(SessionRequest.company_id == current_user.id))
    
    return success_response({
        "avgWellnessScore": 85,
        "totalEmployees": employee_count or 0,
        "activeEmployees": employee_count or 0,
        "totalTeams": team_count or 0,
        "completedThisMonth": session_count or 0,
    })

@router.post("/teams")
async def create_team(team: TeamCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_team = Team(
        name=team.name,
        description=team.description,
        lead_id=team.leadId,
        company_id=current_user.id
    )
    db.add(new_team)
    await db.flush()  # get new_team.id before commit

    # Auto-enroll the team lead in the team membership
    if team.leadId:
        lead_membership = TeamMembership(
            team_id=new_team.id,
            user_id=team.leadId,
            is_lead=True,
        )
        db.add(lead_membership)
        # Notify the team lead
        await _notify(db, team.leadId, "You've been assigned as Team Lead",
                      f"You are now the lead of team '{team.name}'.", type="team", priority="high")

    await db.commit()
    await db.refresh(new_team)
    resp = TeamResponse.model_validate(new_team).model_dump()
    resp["joinCode"] = new_team.join_code
    return success_response(resp, "Team created successfully")

@router.get("/teams")
async def list_teams(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Team).where(Team.company_id == current_user.id))
    teams = result.scalars().all()
    # map to response to include computed active_members, etc.
    res = []
    for t in teams:
        member_count = await db.scalar(
            select(func.count(TeamMembership.id)).where(TeamMembership.team_id == t.id)
        ) or 0
        res.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "lead_id": t.lead_id,
            "company_id": t.company_id,
            "joinCode": t.join_code,
            "created_at": t.created_at.isoformat(),
            "active_members": member_count,
            "total_members": member_count,
            "engagement": 88,
        })
    return success_response(res)

@router.post("/employees")
async def invite_employee(employee: EmployeeInvite, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_access(current_user)
    # Simple logic to create a user and assign to the company.
    # Resolve requested role
    role_name_in = employee.role.lower().replace('-', '_').replace(' ', '_')
    role_result = await db.execute(select(Role).where(func.lower(Role.name) == role_name_in))
    roleObj = role_result.scalar_one_or_none()
    
    if not roleObj:
        # Fallback to team_member if not found, or member
        fallback_role_result = await db.execute(select(Role).where(Role.name.in_(['team_member', 'member'])))
        roleObj = fallback_role_result.scalars().first()
    
    if not roleObj:
        raise HTTPException(status_code=500, detail="Default roles not configured in database")

    # check if user exists
    existing = await db.scalar(select(User).where(User.email == employee.email))
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    created = await user_service.create_user(
        db,
        CreateUserCommand(
            email=employee.email,
            role_name=roleObj.name,
            first_name=employee.firstName,
            last_name=employee.lastName,
            phone=employee.phone,
            company_id=_company_scope_id(current_user),
            status="ACTIVE",
            is_verified=True,
            actor_user_id=current_user.id,
            audit_event_type="CORPORATE_EMPLOYEE_INVITED",
        ),
    )
    new_user = created.user
    temp_password = created.plain_password
    await db.commit()
    await db.refresh(new_user)

    # Send invitation email
    try:
        get_email_service().send_invitation(new_user.email, temp_password, roleObj.name)
    except Exception as e:
        print(f"Failed to send invitation email to {new_user.email}: {e}")

    # Welcome notification for the invited user
    await _notify(
        db, new_user.id,
        "Welcome to the team!",
        "You've been invited to join the Nuetra wellness platform. Log in to get started.",
        type="invite", priority="medium",
    )
    await db.commit()

    return success_response({"tempPassword": temp_password}, "Employee invited successfully")

@router.get("/employees")
async def list_employees(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_access(current_user)
    result = await db.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.id)
        .where(User.company_id == _company_scope_id(current_user))
    )
    employees = []
    for usr, r in result.all():
        employees.append({
            "id": usr.id,
            "email": usr.email,
            "firstName": usr.first_name or usr.email.split("@")[0],
            "lastName": usr.last_name or "",
            "phone": usr.phone,
            "role": r.name,
            "status": "Active",
            "engagement": 90,
        })
    return success_response(employees)

@router.post("/employees/bulk")
async def invite_employees_bulk(employees: List[EmployeeInvite], db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_access(current_user)
    invited_count = 0
    errors = []
    
    # Pre-fetch roles
    roles_result = await db.execute(select(Role))
    roles_lookup = {r.name.lower(): r.id for r in roles_result.scalars().all()}

    # Bulk Invite
    for emp in employees:
        try:
            # Consistent role resolution
            role_name_in = emp.role.lower().replace('-', '_').replace(' ', '_')
            role_id = roles_lookup.get(role_name_in)
            if not role_id:
                # Try specific map if not found for backwards compatibility with space names
                role_id = roles_lookup.get("team_member") or roles_lookup.get("member")
            
            existing = await db.scalar(select(User).where(User.email == emp.email))
            if existing:
                errors.append(f"{emp.email} already exists")
                continue

            role_obj = await db.scalar(select(Role).where(Role.id == role_id))
            if role_obj is None:
                errors.append(f"{emp.email} role is not configured")
                continue
            created = await user_service.create_user(
                db,
                CreateUserCommand(
                    email=emp.email,
                    role_name=role_obj.name,
                    first_name=emp.firstName,
                    last_name=emp.lastName,
                    phone=emp.phone,
                    company_id=_company_scope_id(current_user),
                    status="ACTIVE",
                    is_verified=True,
                    actor_user_id=current_user.id,
                    audit_event_type="CORPORATE_EMPLOYEE_INVITED",
                ),
            )
            new_user = created.user
            temp_password = created.plain_password
            invited_count += 1
            
            # Send invitation email
            try:
                get_email_service().send_invitation(new_user.email, temp_password, emp.role)
            except Exception as e:
                print(f"Failed to send bulk invitation email to {new_user.email}: {e}")
        except Exception as e:
            errors.append(f"Failed to process {emp.email}: {str(e)}")
            
    await db.commit()
    
    return success_response({"invited": invited_count, "errors": errors}, f"Successfully invited {invited_count} employees.")


@router.get("/consultants")
async def list_consultants(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_access(current_user)
    result = await db.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.id)
        .where(User.company_id == _company_scope_id(current_user))
        .where(func.lower(Role.name).in_(CONSULTANT_ROLE_NAMES))
        .order_by(User.created_at.desc())
    )
    consultants = []
    for usr, role in result.all():
        consultants.append(
            ConsultantResponse(
                id=usr.id,
                email=usr.email,
                firstName=usr.first_name or "",
                lastName=usr.last_name or "",
                phone=usr.phone,
                role=role.name,
                specialization=usr.industry,
                createdAt=usr.created_at,
                authorities=usr.permissions or [],
            ).model_dump(mode="json")
        )
    return success_response(consultants)


@router.post("/consultants")
async def create_consultant(consultant: ConsultantInvite, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_access(current_user)

    role_name_in = consultant.role.lower().replace('-', '_').replace(' ', '_')
    if role_name_in not in CONSULTANT_ROLE_NAMES:
        raise HTTPException(status_code=400, detail="Unsupported consultant role")

    role_result = await db.execute(select(Role).where(func.lower(Role.name) == role_name_in))
    role_obj = role_result.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(status_code=500, detail="Consultant roles are not configured in the database")

    existing = await db.scalar(select(User).where(User.email == consultant.email))
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    created = await user_service.create_user(
        db,
        CreateUserCommand(
            email=consultant.email,
            role_name=role_obj.name,
            first_name=consultant.firstName,
            last_name=consultant.lastName,
            phone=consultant.phone,
            company_id=_company_scope_id(current_user),
            industry=consultant.specialization,
            permissions=ROLE_DEFAULT_AUTHORITIES.get(role_name_in, ["client_read"]),
            status="ACTIVE",
            is_verified=True,
            actor_user_id=current_user.id,
            audit_event_type="CORPORATE_CONSULTANT_INVITED",
        ),
    )
    new_user = created.user
    temp_password = created.plain_password
    await db.flush()
    await AuditLogRepository(db).create("CONSULTANT_ACCOUNT_CREATED", user_id=new_user.id)
    await db.commit()
    await db.refresh(new_user)

    try:
        get_email_service().send_invitation(new_user.email, temp_password, role_obj.name)
    except Exception as e:
        print(f"Failed to send consultant invitation email to {new_user.email}: {e}")

    await _notify(
        db,
        new_user.id,
        "Consultant account ready",
        "Your consultant access has been created. Use the temporary password to sign in and reset it after login.",
        type="invite",
        priority="high",
    )
    await db.commit()

    consultant_payload = ConsultantResponse(
        id=new_user.id,
        email=new_user.email,
        firstName=new_user.first_name or "",
        lastName=new_user.last_name or "",
        phone=new_user.phone,
        role=role_obj.name,
        specialization=new_user.industry,
        createdAt=new_user.created_at,
        authorities=new_user.permissions or [],
    ).model_dump(mode="json")

    return success_response(
        {"consultant": consultant_payload, "tempPassword": temp_password},
        "Consultant account created successfully",
    )


@router.get("/authority-options")
async def get_authority_options(current_user: User = Depends(get_current_user)):
    _ensure_super_admin_access(current_user)
    return success_response([AuthorityOption(**item).model_dump(mode="json") for item in AUTHORITY_OPTIONS])


@router.get("/people")
async def list_people(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_super_admin_access(current_user)
    result = await db.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.id)
        .where(func.lower(Role.name).in_(MANAGED_ROLE_NAMES))
        .order_by(Role.name.asc(), User.created_at.desc())
    )
    people = []
    for usr, role in result.all():
        people.append(_person_payload(usr, role.name).model_dump(mode="json"))
    return success_response(people)


@router.post("/people")
async def create_person(person: ManagedPersonCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_super_admin_access(current_user)

    role_name_in = _normalize_role_name(person.role)
    if role_name_in not in MANAGED_ROLE_NAMES:
        raise HTTPException(status_code=400, detail="Unsupported role")

    role_result = await db.execute(select(Role).where(func.lower(Role.name) == role_name_in))
    role_obj = role_result.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(status_code=500, detail="Role is not configured in the database")

    existing = await db.scalar(select(User).where(User.email == person.email))
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    created = await user_service.create_user(
        db,
        CreateUserCommand(
            email=person.email,
            role_name=role_obj.name,
            first_name=person.firstName,
            last_name=person.lastName,
            phone=person.phone,
            company_id=_company_scope_id(current_user),
            industry=person.specialization,
            permissions=_normalize_authorities(role_name_in, person.authorities),
            status="ACTIVE",
            is_verified=True,
            actor_user_id=current_user.id,
            audit_event_type="CORPORATE_PERSON_CREATED",
        ),
    )
    new_user = created.user
    temp_password = created.plain_password
    await db.flush()
    await AuditLogRepository(db).create("MANAGED_PERSON_CREATED", user_id=new_user.id)
    await db.commit()
    await db.refresh(new_user)

    try:
        get_email_service().send_invitation(new_user.email, temp_password, role_obj.name)
    except Exception as e:
        print(f"Failed to send managed user invitation email to {new_user.email}: {e}")

    await _notify(
        db,
        new_user.id,
        "Workspace account ready",
        "Your platform access has been created. Use the temporary password to sign in and reset it after login.",
        type="invite",
        priority="high",
    )
    await db.commit()

    return success_response(
        {"person": _person_payload(new_user, role_obj.name).model_dump(mode="json"), "tempPassword": temp_password},
        "Workspace account created successfully",
    )


@router.patch("/people/{user_id}/authorities")
async def update_person_authorities(
    user_id: uuid.UUID,
    update: ManagedPersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_super_admin_access(current_user)

    result = await db.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.id)
        .where(User.id == user_id)
        .where(func.lower(Role.name).in_(MANAGED_ROLE_NAMES))
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Managed user not found")

    managed_user, role = row
    managed_user.permissions = _normalize_authorities(role.name, update.authorities)
    await db.commit()
    await db.refresh(managed_user)

    return success_response(
        _person_payload(managed_user, role.name).model_dump(mode="json"),
        "Authorities updated successfully",
    )

@router.post("/sessions")
async def request_session(session: SessionRequestCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"DEBUG PAYLOAD PARSED: {session.model_dump()}")
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
        company_id=current_user.id
    )
    db.add(new_request)
    await db.flush()

    # Notify team lead if session is for a specific team
    if session.team_id:
        team_result = await db.execute(select(Team).where(Team.id == session.team_id))
        team_obj = team_result.scalar_one_or_none()
        if team_obj and team_obj.lead_id:
            await _notify(
                db, team_obj.lead_id,
                "New Session Requested",
                f"A wellness session '{session.title}' has been scheduled for your team.",
                type="session", priority="medium",
            )

    await db.commit()
    await db.refresh(new_request)
    return success_response(SessionRequestResponse.model_validate(new_request), "Session requested successfully")

@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SessionRequest).where(SessionRequest.company_id == current_user.id))
    sessions = result.scalars().all()
    res = [SessionRequestResponse.model_validate(s).model_dump(by_alias=True, mode="json") for s in sessions]
    return success_response(res)

@router.get("/sessions/{session_id}")
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SessionRequest).where(SessionRequest.company_id == current_user.id, SessionRequest.id == session_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return success_response(SessionRequestResponse.model_validate(s).model_dump(by_alias=True, mode="json"))

@router.put("/sessions/{session_id}")
async def update_session(session_id: uuid.UUID, session_update: SessionRequestCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SessionRequest).where(SessionRequest.company_id == current_user.id, SessionRequest.id == session_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    
    s.title = session_update.title
    s.description = session_update.description
    s.type = session_update.type
    s.mode = session_update.mode
    s.duration = session_update.duration
    s.scheduled_at = session_update.scheduled_at
    s.target_audience = session_update.target_audience
    s.timezone = session_update.timezone
    s.request_notes = session_update.request_notes
    s.team_id = session_update.team_id

    await db.commit()
    await db.refresh(s)
    return success_response(SessionRequestResponse.model_validate(s), "Session updated successfully")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(SessionRequest).where(SessionRequest.company_id == current_user.id, SessionRequest.id == session_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(s)
    await db.commit()
    return success_response(None, "Session deleted successfully")

@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response({
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "engagementScores": [70, 75, 82, 85, 80, 88]
    })
