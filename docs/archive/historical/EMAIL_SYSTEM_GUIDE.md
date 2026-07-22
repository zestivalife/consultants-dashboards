# Email System Refactor Documentation

## Architecture Overview

The auth-service now has a **robust, production-ready email system** that supports both **SMTP** (local/dev) and **SendGrid API** (production) with automatic provider selection.

### Key Features

✅ **Dual Provider Support**
- SMTP for local development
- SendGrid REST API for production
- Automatic fallback if SendGrid fails

✅ **Non-Blocking Email Sending**
- Uses FastAPI BackgroundTasks
- API responses return immediately
- Email failures never block user registration/login

✅ **Comprehensive Error Handling**
- Exceptions logged but not raised
- API succeeds even if email fails
- Graceful degradation in production

✅ **Cloud-Friendly**
- Avoids SMTP port blocking issues
- Uses REST API instead of SMTP protocol
- Works in containerized/cloud environments

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│           FastAPI Endpoint (e.g., /register)        │
│                                                      │
│  async def register(background_tasks: BackgroundTasks):
│      # ... do business logic ...
│      background_tasks.add_task(                      │
│          _send_otp_email_background,                │
│          email=user_email, otp_code=code            │
│      )                                               │
│      return {"success": True}  # Return immediately!│
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│      Background Task (runs after API response)       │
│                                                      │
│  _send_otp_email_background(email, code):           │
│      try:
│          email_service.send_otp(email, code)
│      except Exception as e:
│          logger.error(...)  # Log but don't crash!
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│       EmailService (Provider Selection Logic)        │
│                                                      │
│  if app_env == "production" AND sendgrid_api_key:   │
│      use SendGridEmailProvider()
│  else:
│      use SMTPEmailProvider()
└─────────────────────────────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │                              │
    ┌───┴───┐                    ┌───┴──────┐
    │       │                    │          │
    ↓       ↓                    ↓          ↓
┌────────┐  │  ┌──────────┐  │  │   └─────────────────────┐
│ SMTP   │  │  │ SendGrid │  │  │   │ SendGrid API Server │
│ Server │  │  │ API REST │  │  │   │                     │
│        │  │  │ (Cloud)  │  │  │   │ Reliability: 99.9%+ │
└────────┘  └──└──────────┘  └──┘   │ No Port Issues      │
  Dev Mode      Production Mode      └─────────────────────┘
```

---

## Implementation Details

### 1. Email Service (`app/core/email.py`)

#### Provider Interface
```python
class EmailProviderBase(ABC):
    """Abstract base for email providers"""
    
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> None:
        """Send email. Raises exception on failure."""
        pass
    
    def _build_otp_html(self, code: str) -> str:
        """Build OTP email HTML"""
    
    def _build_invitation_html(self, email: str, temp_password: str, role: str) -> str:
        """Build invitation email HTML"""
```

#### SMTP Provider (Local/Dev)
```python
class SMTPEmailProvider(EmailProviderBase):
    """
    Uses standard SMTP protocol
    
    Features:
    - Works locally without external dependencies
    - Uses MIMEMultipart for email structure
    - Supports TLS/SSL
    - Timeout protection (15 seconds)
    """
    
    def send(self, to: str, subject: str, html_body: str) -> None:
        # Connect to SMTP server
        # Optionally use TLS
        # Authenticate if credentials provided
        # Send via sendmail
```

#### SendGrid Provider (Production)
```python
class SendGridEmailProvider(EmailProviderBase):
    """
    Uses SendGrid REST API
    
    Advantages:
    - No SMTP port blocking in cloud
    - Better deliverability
    - Built-in tracking & analytics
    - No server infrastructure needed
    - 99.9%+ uptime SLA
    """
    
    def send(self, to: str, subject: str, html_body: str) -> None:
        # Build Mail object
        # Send via SendGrid API
        # Check response status (200/201/202)
```

#### Composite Service
```python
class EmailService:
    """Main email service with provider selection"""
    
    def __init__(self):
        # Selects provider based on environment
        self._provider = self._init_provider()
    
    def _init_provider(self) -> EmailProviderBase:
        """
        Decision logic:
        - Production + SendGrid API Key → SendGridEmailProvider
        - Fallback → SMTPEmailProvider
        """
    
    def send(self, to: str, subject: str, html_body: str) -> None:
        """Send email using configured provider"""
    
    def send_otp(self, email: str, code: str) -> None:
        """Convenience method for OTP"""
    
    def send_invitation(self, email: str, temp_password: str, role: str) -> None:
        """Convenience method for invitations"""
```

---

### 2. Background Task Implementation (`app/services/auth_service.py`)

#### Non-Blocking Email Functions
```python
def _send_otp_email_background(email: str, otp_code: str) -> None:
    """
    Send OTP email as background task.
    
    IMPORTANT: Never raises exceptions!
    - Runs AFTER API response is sent
    - Failures are logged but not propagated
    - Ensures APIs never timeout due to email
    """
    try:
        get_email_service().send_otp(email, otp_code)
        logger.info("otp_email_sent_background", email=email)
    except Exception as e:
        logger.error(
            "otp_email_failed_background",
            email=email,
            error=str(e),
            note="Email sending failed but API response continues"
        )

def _send_invitation_email_background(email: str, temp_password: str, role: str) -> None:
    """
    Send invitation email as background task.
    
    Same pattern: try/catch/log, never raise.
    """
    try:
        get_email_service().send_invitation(email, temp_password, role)
        logger.info("invitation_email_sent_background", email=email)
    except Exception as e:
        logger.error(
            "invitation_email_failed_background",
            email=email,
            error=str(e),
            note="Email sending failed but API response continues"
        )
```

---

### 3. API Route Integration (`app/api/v1/routes/auth.py`)

#### Register Endpoint
```python
@router.post("/register")
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None  # Injected by FastAPI
):
    """
    Register new user with NON-BLOCKING email.
    
    Flow:
    1. Create user account
    2. Generate OTP
    3. Add email task to background
    4. Return response (don't wait for email)
    """
    
    result = await auth_service.register(
        body.email, body.password, session
    )
    
    if background_tasks and result.get("otp_code"):
        # Queue email task (won't block API response)
        background_tasks.add_task(
            auth_service._send_otp_email_background,
            email=body.email,
            otp_code=result["otp_code"]
        )
    
    # Return immediately! Email sends in background
    return {
        "success": True,
        "message": "Registration successful. Check your email for OTP.",
        "message_id": result.get("message_id")
    }

# Resend OTP uses the same pattern
@router.post("/resend-otp")
async def resend_otp(
    body: ResendOtpRequest,
    session: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    result = await auth_service.resend_otp(body.email, session)
    
    if background_tasks and result.get("otp_code"):
        background_tasks.add_task(
            auth_service._send_otp_email_background,
            email=body.email,
            otp_code=result["otp_code"]
        )
    
    return {"success": True, "message": "OTP sent. Check your email."}
```

---

## Configuration

### 1. Environment Variables (`config.py`)

#### SMTP Configuration (Local/Dev)
```python
# SMTP / Email (for local development)
smtp_host: str = "localhost"
smtp_port: int = 587
smtp_user: str = ""
smtp_password: str = ""
smtp_from_email: str = "noreply@nuetra.com"
smtp_from_name: str = "Nuetra"
smtp_use_tls: bool = True
smtp_use_ssl: bool = False
```

#### SendGrid Configuration (Production)
```python
# SendGrid / Email (for production)
# API Key from https://app.sendgrid.com/settings/api_keys
sendgrid_api_key: str = ""  # Set via environment variable

# Or directly in config for development:
sendgrid_api_key: str = "SG.xxxxxxxxxxxxx"
```

#### Environment-Based Switching
```python
# app_env is read from APP_ENV environment variable
app_env: str = "development"  # or "production"

# Decision:
# if app_env == "production" AND sendgrid_api_key:
#     use SendGrid
# else:
#     use SMTP
```

---

### 2. Docker Compose Configuration

```yaml
auth-service:
  environment:
    # Local/Dev (SMTP)
    SMTP_HOST: smtp.sendgrid.net
    SMTP_PORT: "587"
    SMTP_USER: "apikey"
    SMTP_PASSWORD: "SG.xxxxxxxxxxxxx"  # SendGrid API key as SMTP password
    SMTP_FROM_EMAIL: "noreply@nuetra.com"
    SMTP_FROM_NAME: "Nuetra"
    SMTP_USE_TLS: "true"
    SMTP_USE_SSL: "false"
    
    # Production (SendGrid API)
    APP_ENV: "production"
    SENDGRID_API_KEY: ${SENDGRID_API_KEY:-""}  # From environment
```

---

### 3. Environment Setup

#### Local Development
```bash
# Option 1: Use local mailhog or similar for testing
export APP_ENV=development
export SMTP_HOST=mailhog
export SMTP_PORT=1025

# Option 2: Use SendGrid SMTP (port 587, TLS)
export SMTP_HOST=smtp.sendgrid.net
export SMTP_PORT=587
export SMTP_USER=apikey
export SMTP_PASSWORD="SG.xxxxxxxxxxxxx"  # SendGrid API key
```

#### Production
```bash
# Use SendGrid REST API (recommended)
export APP_ENV=production
export SENDGRID_API_KEY="SG.xxxxxxxxxxxxx"

# SMTP variables still used as fallback
export SMTP_HOST=smtp.sendgrid.net
export SMTP_PORT=587
export SMTP_USER=apikey
export SMTP_PASSWORD="SG.xxxxxxxxxxxxx"
```

---

## Deployment Checklist

### ✅ Local Development Setup
- [x] Install sendgrid package: `pip install sendgrid`
- [x] SMTP variables configured
- [x] Can test with local mailhog or Mailtrap
- [x] No SendGrid API key needed

### ✅ Production Setup
- [ ] Get SendGrid account: https://sendgrid.com
- [ ] Create API key (don't use master)
- [ ] Set `SENDGRID_API_KEY` environment variable
- [ ] Verify sender email is authenticated in SendGrid
- [ ] Set `APP_ENV=production`
- [ ] Test email sending in staging first

### ✅ Monitoring & Debugging
- [ ] Enable structured logging in production
- [ ] Monitor email failures in logs
- [ ] Set up SendGrid webhooks for delivery tracking
- [ ] Configure alerts for email failures
- [ ] Test fallback to SMTP if API key issues

---

## Testing Email System

### Local Testing

#### 1. Test OTP Email
```python
# In Python shell or test file
from app.core.email import get_email_service

service = get_email_service()
print(f"Using provider: {type(service._provider).__name__}")

# Send test OTP
service.send_otp(
    email="test@example.com",
    code="123456"
)
```

#### 2. Test Invitation Email
```python
service.send_invitation(
    email="newmember@company.com",
    temp_password="TempPass123!",
    role="team_member"
)
```

#### 3. Test Background Task
```bash
# Start the service
uvicorn app.main:app --reload

# Make registration request
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Check logs for email sending:
# - "email_provider_init", provider="SMTP" or "SendGrid"
# - "smtp_email_sent_successfully" OR "sendgrid_email_sent_successfully"
# - "otp_email_sent_background"
```

### Production Testing (Staging)

#### 1. Verify SendGrid API Key
```bash
curl https://api.sendgrid.com/v3/mail/send \
  -X POST \
  -H "Authorization: Bearer $SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "personalizations": [{"to": [{"email": "test@example.com"}]}],
    "from": {"email": "noreply@nuetra.com"},
    "subject": "Test",
    "content": [{"type": "text/html", "value": "<p>Test</p>"}]
  }'
```

#### 2. Monitor Delivery
```bash
# Check SendGrid Activity Feed
# https://app.sendgrid.com/activity

# Or via API
curl https://api.sendgrid.com/v3/mail_settings/event_webhook \
  -X GET \
  -H "Authorization: Bearer $SENDGRID_API_KEY"
```

---

## Troubleshooting

### Issue: "Email provider init failed"

**Cause**: SendGrid initialization failed, falling back to SMTP

**Solution**:
1. Check SENDGRID_API_KEY is set correctly
2. Verify key format: `SG.xxxxxxxxxxxxx`
3. Check API key has mail send permissions
4. See logs for specific error

```python
logger.warning("sendgrid_init_failed", detail=str(exc), fallback="SMTP")
```

### Issue: "SMTP connection timeout"

**Cause**: SMTP server unreachable or blocked by firewall

**Solution**:
1. Check SMTP_HOST and SMTP_PORT are correct
2. For SendGrid SMTP: use `smtp.sendgrid.net:587` with TLS
3. In cloud environments, prefer SendGrid API (REST) instead
4. Use telnet to test connectivity: `telnet smtp.sendgrid.net 587`

### Issue: "SendGrid API returned 401"

**Cause**: Invalid or missing API key

**Solution**:
```bash
# Verify API key format
echo $SENDGRID_API_KEY  # Should start with "SG."

# Get new key from SendGrid dashboard
# https://app.sendgrid.com/settings/api_keys

# Test
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.sendgrid.com/v3/mail/validate
```

### Issue: "Email not arriving"

**Cause**: Various possible causes

**Solutions**:
1. Check SendGrid Activity Feed for delivery status
2. Verify sender email is authenticated in SendGrid
3. Check recipient spam/junk folder
4. Look for SPF/DKIM/DMARC authentication issues
5. Check SendGrid logs for bounce/drop reasons

---

## Performance Characteristics

### SMTP Method (Local/Dev)
- **Speed**: 1-3 seconds per email
- **Reliability**: Depends on SMTP server
- **Cost**: Free (if self-hosted)
- **Cloud-Friendly**: ❌ Port 587/25 often blocked

### SendGrid API Method (Production)
- **Speed**: 200-500ms per API call (non-blocking)
- **Reliability**: 99.9%+ uptime SLA
- **Cost**: ~$0.10 per 1000 emails
- **Cloud-Friendly**: ✅ HTTPS port 443, always works

---

## Best Practices

1. **Never Block API on Email**
   - Always use background tasks
   - Return success immediately
   - Log failures, don't raise

2. **Use SendGrid for Production**
   - More reliable than SMTP
   - Better deliverability
   - No port issues in cloud
   - Better analytics/tracking

3. **Test Email System**
   - Test locally with SMTP
   - Test in staging with SendGrid
   - Monitor sendgrid activity feed
   - Set up alerts for failures

4. **Secure API Keys**
   - Use environment variables
   - Never commit keys to git
   - Use restricted API keys (mail send only)
   - Rotate keys regularly

5. **Monitor & Log Everything**
   - Log provider selection
   - Log success/failure
   - Log recipient addresses
   - Use structured logging

---

## References

- [SendGrid REST API Docs](https://docs.sendgrid.com/api-reference/mail-send/mail-send)
- [SendGrid Python Library](https://github.com/sendgrid/sendgrid-python)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [SMTP RFC 5321](https://tools.ietf.org/html/rfc5321)

---

## Conclusion

The refactored email system provides:
- ✅ Reliable email delivery in production (SendGrid)
- ✅ Simple local development (SMTP)
- ✅ Non-blocking API responses (BackgroundTasks)
- ✅ Graceful error handling
- ✅ Clear provider selection logic
- ✅ Easy monitoring and debugging

**Result**: Registration and login APIs never fail due to email issues! 🚀
