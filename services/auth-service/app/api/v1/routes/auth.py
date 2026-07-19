from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResendOtpRequest,
    UserResponse,
    VerifyOtpRequest,
)
from app.services import auth_service
from app.api.v1.dependencies import get_current_user

router = APIRouter(tags=["auth"])


def _without_sensitive_fields(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key not in {"otp_code"}}


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/register")
async def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    result = await auth_service.register(
        session,
        email=body.email,
        password=body.password,
        role_name=body.role,
        company_name=body.companyName,
        location=body.location,
        employees=body.employees,
        industry=body.industry,
    )

    # Send OTP email in background — non-blocking, never fails the request
    if result.get("otp_code"):
        background_tasks.add_task(
            auth_service._send_otp_email_background,
            email=body.email,
            otp_code=result["otp_code"],
        )

    return success_response(data=_without_sensitive_fields(result), message="Registration successful", status_code=201)


@router.post("/verify-otp")
async def verify_otp(body: VerifyOtpRequest, session: AsyncSession = Depends(get_db)):
    result = await auth_service.verify_otp_action(session, body.email, body.otp)
    return success_response(data=_without_sensitive_fields(result), message=result["message"])


@router.post("/resend-otp")
async def resend_otp(
    body: ResendOtpRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    result = await auth_service.resend_otp(session, body.email)

    # Send OTP email in background — non-blocking, never fails the request
    if result.get("otp_code"):
        background_tasks.add_task(
            auth_service._send_otp_email_background,
            email=body.email,
            otp_code=result["otp_code"],
        )

    return success_response(data=_without_sensitive_fields(result), message=result["message"])


@router.post("/forgot-password")
async def forgot_password(
    body: ResendOtpRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """Generate an OTP for password reset. Public endpoint (no auth required)."""
    result = await auth_service.forgot_password(session, body.email)

    # Send OTP email in background — non-blocking, never fails the request
    if result.get("otp_code"):
        background_tasks.add_task(
            auth_service._send_otp_email_background,
            email=body.email,
            otp_code=result["otp_code"],
        )

    return success_response(data=_without_sensitive_fields(result), message=result["message"])


@router.post("/login")
async def login(body: LoginRequest, request: Request, session: AsyncSession = Depends(get_db)):
    login_resp = await auth_service.login(
        session,
        body.email,
        body.password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return success_response(
        data=login_resp.model_dump(mode="json"),
        message="Login successful",
    )


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, request: Request, session: AsyncSession = Depends(get_db)):
    tokens = await auth_service.refresh(
        session,
        body.refresh_token,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return success_response(data=tokens.model_dump(mode="json"), message="Token refreshed")


@router.post("/logout")
async def logout(body: RefreshRequest, request: Request, session: AsyncSession = Depends(get_db)):
    user_id_header = request.headers.get("X-User-Id")
    uid = None
    if user_id_header:
        try:
            import uuid
            uid = uuid.UUID(user_id_header)
        except ValueError:
            pass

    result = await auth_service.logout(
        session,
        body.refresh_token,
        user_id=uid,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return success_response(data=result, message="Logged out successfully")


@router.post("/change-temporary-password")
async def change_temporary_password(
    body: ChangePasswordRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await auth_service.change_password(
        session,
        current_user.id,
        body.current_password,
        body.new_password,
        body.confirm_password,
        temporary_only=True,
        issue_new_session=True,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return success_response(data=result.model_dump(mode="json"), message="Password changed")


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await auth_service.change_password(
        session,
        current_user.id,
        body.current_password,
        body.new_password,
        body.confirm_password,
        temporary_only=False,
        issue_new_session=False,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return success_response(data=result, message="Password changed")


@router.get("/me")
async def me(current_user: UserResponse = Depends(get_current_user)):
    return success_response(data=current_user.model_dump(mode="json"))


@router.get("/roles")
async def roles(session: AsyncSession = Depends(get_db)):
    result = await auth_service.list_roles(session)
    return success_response(
        data=[r.model_dump(mode="json") for r in result],
        message="Roles retrieved",
    )
