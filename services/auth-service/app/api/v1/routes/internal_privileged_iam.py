import asyncio
import uuid
from html import escape

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.config import get_settings
from app.core.email import get_email_service
from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.internal_privileged_iam import PrivilegedInvitationAccept, PrivilegedInvitationCreate, PrivilegedMfaConfirm, PrivilegedOutOfBandApproval
from app.services import internal_privileged_iam_service as service

router = APIRouter(tags=["internal-privileged-iam"])

@router.post("/owner/internal-privileged-invitations", status_code=202)
async def request_invitation(body: PrivilegedInvitationCreate, session: AsyncSession=Depends(get_db), current_user: UserResponse=Depends(get_current_user)):
    record=await service.initiate(session,actor_id=current_user.id,email=str(body.email),phone=body.phone,first_name=body.first_name,last_name=body.last_name)
    return success_response(data={"invitation_id":str(record.id),"status":record.status},message="Privileged invitation awaiting independent approval")

@router.post("/owner/internal-privileged-invitations/{invitation_id}/approve", status_code=202)
async def approve_invitation(invitation_id: uuid.UUID, session: AsyncSession=Depends(get_db), current_user: UserResponse=Depends(get_current_user)):
    record,token=await service.approve(session,actor_id=current_user.id,invitation_id=invitation_id)
    link=f"{get_settings().frontend_url.rstrip('/')}/internal-admin/activate?token={token}"
    body=f"<p>Hello {escape(record.first_name)},</p><p>Your Zestiva Internal administrator invitation was approved.</p><p><a href=\"{escape(link)}\">Verify email and enrol MFA</a></p><p>This single-use link expires shortly.</p>"
    try: await asyncio.to_thread(get_email_service().send,record.email,"Zestiva Internal administrator invitation",body)
    except Exception:
        record.status="PENDING_APPROVAL"; record.token_hash=None; record.approved_by_user_id=None; record.approved_at=None; record.expires_at=None
        await session.commit(); raise
    return success_response(data={"invitation_id":str(record.id),"status":record.status},message="Privileged invitation delivered")

@router.post("/owner/internal-privileged-invitations/{invitation_id}/approve-out-of-band", status_code=202)
async def approve_invitation_out_of_band(
    invitation_id: uuid.UUID,
    body: PrivilegedOutOfBandApproval,
    session: AsyncSession=Depends(get_db),
    current_user: UserResponse=Depends(get_current_user),
):
    record, token = await service.approve_out_of_band(
        session,
        actor_id=current_user.id,
        invitation_id=invitation_id,
        confirmed_email=str(body.confirmed_email),
        confirmed_phone=body.confirmed_phone,
        reason=body.reason,
    )
    response = success_response(
        data={
            "invitation_id": str(record.id),
            "status": record.status,
            "enrolment_token": token,
            "expires_at": record.expires_at,
            "handoff": "DISPLAY_ONCE_SECURE_OUT_OF_BAND",
        },
        message="One-time privileged enrolment credential issued",
        status_code=202,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response

@router.post("/auth/internal-privileged-invitations/accept")
async def accept_invitation(body: PrivilegedInvitationAccept, session: AsyncSession=Depends(get_db)):
    activation,uri=await service.accept(session,token=body.token,password=body.password)
    return success_response(data={"activation_token":activation,"otp_auth_uri":uri,"status":"MFA_ENROLMENT_REQUIRED"},message="Email verified; MFA enrolment required")

@router.post("/auth/internal-privileged-invitations/confirm-mfa")
async def confirm_mfa(body: PrivilegedMfaConfirm, session: AsyncSession=Depends(get_db)):
    await service.confirm_mfa(session,activation_token=body.activation_token,code=body.code)
    return success_response(data={"status":"ACTIVE","login_required":True},message="MFA enrolled; sign in with password and authenticator code")

@router.post("/owner/internal-privileged-users/{user_id}/revoke")
async def revoke_privileged_user(user_id: uuid.UUID, session: AsyncSession=Depends(get_db), current_user: UserResponse=Depends(get_current_user)):
    await service.revoke(session,actor_id=current_user.id,user_id=user_id)
    return success_response(data={"user_id":str(user_id),"status":"REVOKED"},message="Internal privileged access revoked")
