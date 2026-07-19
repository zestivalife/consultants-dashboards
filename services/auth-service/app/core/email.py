import smtplib
import socket
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailProviderBase(ABC):
    """Abstract base for email providers (SMTP, SendGrid, etc.)"""

    def __init__(self) -> None:
        self._settings = get_settings()

    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> None:
        """Send email via provider. Raises exception on failure."""
        pass

    def _build_otp_html(self, code: str) -> str:
        return (
            "<div style='font-family:sans-serif;max-width:480px;margin:auto'>"
            "<h2>Verify your email</h2>"
            f"<p>Your one-time verification code is:</p>"
            f"<h1 style='letter-spacing:8px;text-align:center'>{code}</h1>"
            f"<p>This code expires in {self._settings.otp_expiry_seconds // 60} minutes.</p>"
            "<p>If you did not request this, please ignore this email.</p>"
            "</div>"
        )


class SMTPEmailProvider(EmailProviderBase):
    """SMTP-based email provider (local/dev)"""

    _TIMEOUT_SECONDS = 10

    def send(self, to: str, subject: str, html_body: str) -> None:
        s = self._settings
        server: smtplib.SMTP | None = None
        
        logger.info(
            "smtp_email_sending",
            provider="SMTP",
            to=to,
            subject=subject,
            host=s.smtp_host,
            port=s.smtp_port,
            timeout_seconds=self._TIMEOUT_SECONDS,
        )
        
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{s.smtp_from_name} <{s.smtp_from_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        try:
            # Connect to SMTP server
            server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=self._TIMEOUT_SECONDS)
            # Keep all follow-up SMTP operations bounded as well, including auth.
            if server.sock is not None:
                server.sock.settimeout(self._TIMEOUT_SECONDS)
            server.ehlo()
            
            # Start TLS if configured
            if s.smtp_use_tls:
                server.starttls()
                if server.sock is not None:
                    server.sock.settimeout(self._TIMEOUT_SECONDS)
                server.ehlo()

            # Authenticate if credentials provided
            if s.smtp_user:
                server.login(s.smtp_user, s.smtp_password)

            # Send email
            server.sendmail(s.smtp_from_email, to, msg.as_string())
            
            logger.info(
                "smtp_email_sent_successfully",
                to=to,
                subject=subject,
                provider="SMTP",
            )
        except (socket.timeout, TimeoutError) as exc:
            logger.error(
                "smtp_timeout",
                to=to,
                subject=subject,
                error=str(exc),
                exception_type=type(exc).__name__,
                timeout_seconds=self._TIMEOUT_SECONDS,
                provider="SMTP",
            )
            raise TimeoutError(
                f"SMTP server did not respond within {self._TIMEOUT_SECONDS} seconds"
            ) from exc
        except smtplib.SMTPAuthenticationError as exc:
            logger.error(
                "smtp_auth_failed",
                to=to,
                detail=str(exc),
                exception_type=type(exc).__name__,
                timeout_seconds=self._TIMEOUT_SECONDS,
                provider="SMTP",
            )
            raise
        except smtplib.SMTPRecipientsRefused as exc:
            logger.error(
                "smtp_recipient_refused",
                to=to,
                detail=str(exc),
                exception_type=type(exc).__name__,
                provider="SMTP",
            )
            raise
        except smtplib.SMTPException as exc:
            logger.error(
                "smtp_exception",
                to=to,
                detail=str(exc),
                exception_type=type(exc).__name__,
                timeout_seconds=self._TIMEOUT_SECONDS,
                provider="SMTP",
            )
            raise
        except Exception as exc:
            logger.error(
                "smtp_send_failed",
                to=to,
                subject=subject,
                error=str(exc),
                exception_type=type(exc).__name__,
                timeout_seconds=self._TIMEOUT_SECONDS,
                provider="SMTP",
            )
            raise
        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception as exc:
                    logger.warning(
                        "smtp_connection_cleanup_failed",
                        to=to,
                        error=str(exc),
                        exception_type=type(exc).__name__,
                        provider="SMTP",
                    )
                    try:
                        server.close()
                    except Exception:
                        pass


class SendGridEmailProvider(EmailProviderBase):
    """SendGrid API-based email provider (production)"""

    def __init__(self) -> None:
        super().__init__()
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, Content, To
        except ImportError:
            raise ImportError(
                "sendgrid package not installed. "
                "Install with: pip install sendgrid"
            )
        
        self.SendGridAPIClient = SendGridAPIClient
        self.Mail = Mail
        self.Email = Email
        self.Content = Content
        self.To = To
        
        self.api_key = self._settings.sendgrid_api_key
        if not self.api_key:
            raise ValueError(
                "SENDGRID_API_KEY environment variable not set. "
                "Please configure it for production."
            )

    def send(self, to: str, subject: str, html_body: str) -> None:
        s = self._settings
        
        logger.info(
            "sendgrid_email_sending",
            provider="SendGrid",
            to=to,
            subject=subject,
        )
        
        try:
            # Build email
            email = self.Mail(
                from_email=f"{s.smtp_from_name} <{s.smtp_from_email}>",
                to_emails=self.To(to),
                subject=subject,
                html_content=self.Content("text/html", html_body),
            )
            
            # Send via SendGrid API
            sg = self.SendGridAPIClient(api_key=self.api_key)
            response = sg.send(email)
            
            if response.status_code in [200, 201, 202]:
                logger.info(
                    "sendgrid_email_sent_successfully",
                    to=to,
                    subject=subject,
                    status_code=response.status_code,
                    provider="SendGrid",
                )
            else:
                logger.error(
                    "sendgrid_send_failed",
                    to=to,
                    status_code=response.status_code,
                    response=response.body,
                    provider="SendGrid",
                )
                raise Exception(
                    f"SendGrid API returned {response.status_code}: {response.body}"
                )
        except Exception as exc:
            logger.error(
                "sendgrid_send_failed",
                to=to,
                subject=subject,
                error=str(exc),
                provider="SendGrid",
            )
            raise


class EmailService:
    """
    Composite email service with provider selection and graceful fallback.

    Provider selection order (checked in this order):
    1. EMAIL_PROVIDER=sendgrid  → always use SendGrid (raises if key missing)
    2. EMAIL_PROVIDER=smtp      → always use SMTP
    3. EMAIL_PROVIDER=auto      → SendGrid if SENDGRID_API_KEY is set, else SMTP
       (This is the default and the recommended setting for Docker/production.)
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._provider = self._init_provider()

    def _init_provider(self) -> EmailProviderBase:
        """Initialize appropriate provider based on EMAIL_PROVIDER setting."""
        settings = self._settings
        mode = (settings.email_provider or "auto").lower().strip()

        if mode == "sendgrid":
            logger.info("email_provider_init", provider="SendGrid", mode="explicit")
            return SendGridEmailProvider()

        if mode == "smtp":
            logger.info("email_provider_init", provider="SMTP", mode="explicit")
            return SMTPEmailProvider()

        # mode == "auto" (default): use SendGrid if API key is set, fallback to SMTP
        if settings.sendgrid_api_key:
            try:
                logger.info(
                    "email_provider_init",
                    provider="SendGrid",
                    mode="auto",
                    env=settings.app_env,
                )
                return SendGridEmailProvider()
            except (ImportError, ValueError) as exc:
                logger.warning(
                    "sendgrid_init_failed_auto_fallback",
                    detail=str(exc),
                    fallback="SMTP",
                )
                return SMTPEmailProvider()

        logger.info(
            "email_provider_init",
            provider="SMTP",
            mode="auto",
            reason="SENDGRID_API_KEY not set",
            env=settings.app_env,
        )
        return SMTPEmailProvider()

    def send(self, to: str, subject: str, html_body: str) -> None:
        """Send email using configured provider."""
        self._provider.send(to, subject, html_body)

    def send_otp(self, email: str, code: str) -> None:
        """Send OTP verification email."""
        self.send(
            to=email,
            subject="Nuetra - Verify your email",
            html_body=self._provider._build_otp_html(code),
        )


_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Return singleton EmailService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
