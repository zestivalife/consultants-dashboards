"""
Email test endpoint — sends a real email via the configured provider.
Available in all environments for debugging; safe because it requires
an explicit POST with a recipient address.
"""
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from app.config import get_settings
from app.core.email import get_email_service
from app.core.logging import get_logger
from app.core.response import success_response

router = APIRouter(tags=["email-debug"])
logger = get_logger(__name__)


class TestEmailRequest(BaseModel):
    to: EmailStr = "admin@nuetra.in"
    subject: str = "Nuetra — SendGrid test email"


@router.post("/test-email")
async def send_test_email(body: TestEmailRequest):
    """
    Send a real test email via the configured provider (SendGrid or SMTP).
    Use this to verify end-to-end email delivery.
    """
    settings = get_settings()
    svc = get_email_service()
    provider_name = type(svc._provider).__name__

    logger.info(
        "test_email_requested",
        to=body.to,
        provider=provider_name,
        email_provider_setting=settings.email_provider,
        sendgrid_key_present=bool(settings.sendgrid_api_key),
    )

    html_body = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px;
                border:1px solid #e2e8f0;border-radius:12px">
        <h2 style="color:#1a202c">✅ SendGrid is working!</h2>
        <p>This is a test email from <strong>Nuetra auth-service</strong>.</p>
        <table style="width:100%;border-collapse:collapse;margin-top:16px">
            <tr><td style="padding:6px;color:#718096">Provider</td>
                <td style="padding:6px;font-weight:bold">{provider_name}</td></tr>
            <tr><td style="padding:6px;color:#718096">EMAIL_PROVIDER</td>
                <td style="padding:6px">{settings.email_provider}</td></tr>
            <tr><td style="padding:6px;color:#718096">From</td>
                <td style="padding:6px">{settings.smtp_from_email}</td></tr>
            <tr><td style="padding:6px;color:#718096">Environment</td>
                <td style="padding:6px">{settings.app_env}</td></tr>
        </table>
        <p style="color:#718096;font-size:12px;margin-top:20px">
            If you received this, email delivery is fully operational.
        </p>
    </div>
    """

    try:
        svc.send(to=body.to, subject=body.subject, html_body=html_body)
        logger.info("test_email_sent_successfully", to=body.to, provider=provider_name)
        return success_response(
            data={
                "sent_to": body.to,
                "provider": provider_name,
                "email_provider_setting": settings.email_provider,
                "sendgrid_key_present": bool(settings.sendgrid_api_key),
                "from_email": settings.smtp_from_email,
            },
            message=f"Test email sent via {provider_name}. Check your inbox.",
        )
    except Exception as exc:
        logger.error("test_email_failed", to=body.to, provider=provider_name, error=str(exc))
        return success_response(
            data={
                "sent_to": body.to,
                "provider": provider_name,
                "error": str(exc),
                "sendgrid_key_present": bool(settings.sendgrid_api_key),
            },
            message=f"Test email FAILED via {provider_name}. See error details.",
            status_code=500,
        )
