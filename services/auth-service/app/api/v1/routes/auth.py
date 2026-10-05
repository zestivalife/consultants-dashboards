from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ExternalSignupResendRequest,
    ExternalSignupStartRequest,
    ExternalSignupVerifyRequest,
    ExternalConsultantRegisterRequest,
    LoginRequest,
    RefreshRequest,
    UserResponse,
)
from app.services import auth_service
from app.services import external_signup_service
from app.core.recaptcha import verify_recaptcha
from app.api.v1.dependencies import get_current_user

router = APIRouter(tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/external-signup/register", status_code=201)
async def external_signup_register(body: ExternalConsultantRegisterRequest, request: Request, session: AsyncSession = Depends(get_db)):
    client_ip = _client_ip(request)
    await verify_recaptcha(body.recaptcha_token, client_ip)
    result = await external_signup_service.register_without_verification(
        session, body=body, ip_address=client_ip, user_agent=request.headers.get("User-Agent")
    )
    return success_response(data=result, message="Consultant workspace created. Continue onboarding.")


@router.post("/external-signup/start", status_code=202)
async def external_signup_start(body: ExternalSignupStartRequest, request: Request, session: AsyncSession = Depends(get_db)):
    result = await external_signup_service.start(session, body.mobile_number, _client_ip(request))
    return success_response(data=result, message="If eligible, an OTP has been sent.")


@router.post("/external-signup/resend", status_code=202)
async def external_signup_resend(body: ExternalSignupResendRequest, request: Request, session: AsyncSession = Depends(get_db)):
    result = await external_signup_service.resend(session, body.challenge_id, _client_ip(request))
    return success_response(data=result, message="If eligible, a new verification code has been sent.")


@router.post("/external-signup/verify", status_code=201)
async def external_signup_verify(body: ExternalSignupVerifyRequest, request: Request, session: AsyncSession = Depends(get_db)):
    result = await external_signup_service.verify_and_provision(
        session,
        challenge_id=body.challenge_id,
        code=body.code,
        name=body.name,
        email=str(body.email) if body.email else None,
        account_type=body.account_type,
        professional_title=body.professional_title,
        speciality=body.speciality,
        practice_name=body.practice_name,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return success_response(data=result, message="Identity verified. Continue onboarding.")


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
