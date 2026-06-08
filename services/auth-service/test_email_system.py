#!/usr/bin/env python3
"""
Test script to verify email service configuration and functionality.

Usage:
    python test_email_system.py [--environment production|development]
    
Example:
    # Test local development (SMTP)
    python test_email_system.py --environment development
    
    # Test production (SendGrid)
    python test_email_system.py --environment production
"""

import os
import sys
import argparse
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "auth-service"))

def test_smtp_config():
    """Test SMTP configuration"""
    from app.config import get_settings
    settings = get_settings()
    
    print("\n" + "="*60)
    print("SMTP CONFIGURATION TEST")
    print("="*60)
    
    print(f"Host: {settings.smtp_host}")
    print(f"Port: {settings.smtp_port}")
    print(f"User: {settings.smtp_user or '(not set)'}")
    print(f"Password: {'***' if settings.smtp_password else '(not set)'}")
    print(f"From Email: {settings.smtp_from_email}")
    print(f"From Name: {settings.smtp_from_name}")
    print(f"Use TLS: {settings.smtp_use_tls}")
    print(f"Use SSL: {settings.smtp_use_ssl}")
    
    # Validate
    if not settings.smtp_host:
        print("⚠️  WARNING: SMTP_HOST not configured")
        return False
    
    print("✅ SMTP Configuration: OK")
    return True


def test_sendgrid_config():
    """Test SendGrid configuration"""
    from app.config import get_settings
    settings = get_settings()
    
    print("\n" + "="*60)
    print("SENDGRID CONFIGURATION TEST")
    print("="*60)
    
    api_key = settings.sendgrid_api_key
    
    if not api_key:
        print("❌ SENDGRID_API_KEY not set")
        print("   Run: export SENDGRID_API_KEY='SG.xxxxxxxxxxxxx'")
        return False
    
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    
    if not api_key.startswith("SG."):
        print("❌ ERROR: Invalid SendGrid API key format (should start with 'SG.')")
        return False
    
    print("✅ SendGrid API Key: Valid format")
    return True


def test_provider_selection():
    """Test email provider selection logic"""
    from app.config import get_settings
    from app.core.email import EmailService
    
    settings = get_settings()
    
    print("\n" + "="*60)
    print("EMAIL PROVIDER SELECTION TEST")
    print("="*60)
    
    print(f"APP_ENV: {settings.app_env}")
    print(f"SendGrid API Key: {'Set' if settings.sendgrid_api_key else 'Not set'}")
    
    try:
        service = EmailService()
        provider_name = type(service._provider).__name__
        print(f"Selected Provider: {provider_name}")
        
        if settings.app_env == "production":
            if provider_name == "SendGridEmailProvider":
                print("✅ Production mode using SendGrid")
            else:
                print("⚠️  Production mode but using SMTP (SendGrid not configured)")
        else:
            if provider_name == "SMTPEmailProvider":
                print("✅ Development mode using SMTP")
            else:
                print("⚠️  Development mode but using SendGrid")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_smtp_provider():
    """Test SMTP provider functionality"""
    from app.core.email import SMTPEmailProvider
    
    print("\n" + "="*60)
    print("SMTP PROVIDER TEST")
    print("="*60)
    
    try:
        provider = SMTPEmailProvider()
        print("✅ SMTP Provider initialized successfully")
        
        # Test HTML building
        otp_html = provider._build_otp_html("123456")
        if "123456" in otp_html:
            print("✅ OTP HTML template works")
        else:
            print("❌ OTP HTML template broken")
            return False
        
        invitation_html = provider._build_invitation_html(
            "test@example.com", "TempPass123!", "team_member"
        )
        if "test@example.com" in invitation_html:
            print("✅ Invitation HTML template works")
        else:
            print("❌ Invitation HTML template broken")
            return False
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_sendgrid_provider():
    """Test SendGrid provider functionality"""
    from app.config import get_settings
    
    settings = get_settings()
    
    print("\n" + "="*60)
    print("SENDGRID PROVIDER TEST")
    print("="*60)
    
    if not settings.sendgrid_api_key:
        print("⚠️  Skipping: SendGrid API key not configured")
        return None
    
    try:
        from app.core.email import SendGridEmailProvider
        provider = SendGridEmailProvider()
        print("✅ SendGrid Provider initialized successfully")
        
        # Test that sendgrid library is available
        print("✅ sendgrid library imported successfully")
        
        # Test HTML building
        otp_html = provider._build_otp_html("654321")
        if "654321" in otp_html:
            print("✅ OTP HTML template works")
        else:
            print("❌ OTP HTML template broken")
            return False
        
        return True
    except ImportError:
        print("❌ ERROR: sendgrid library not installed")
        print("   Run: pip install sendgrid")
        return False
    except ValueError as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_email_send_capability():
    """Test if providers can send emails (mock)"""
    
    print("\n" + "="*60)
    print("EMAIL SEND CAPABILITY TEST")
    print("="*60)
    
    from app.core.email import get_email_service
    
    service = get_email_service()
    provider_name = type(service._provider).__name__
    
    print(f"Provider: {provider_name}")
    print(f"From: {service._provider._settings.smtp_from_name} <{service._provider._settings.smtp_from_email}>")
    print(f"To: (would send emails in production)")
    
    # Test methods exist
    assert hasattr(service, 'send_otp'), "send_otp method missing"
    assert hasattr(service, 'send_invitation'), "send_invitation method missing"
    assert hasattr(service, 'send'), "send method missing"
    
    print("✅ All email methods available")
    return True


def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description="Test email system configuration")
    parser.add_argument(
        "--environment",
        choices=["development", "production"],
        default="development",
        help="Environment to test (default: development)"
    )
    args = parser.parse_args()
    
    # Set environment for testing
    if args.environment == "production":
        os.environ["APP_ENV"] = "production"
    
    print("\n" + "🔍 EMAIL SYSTEM DIAGNOSTIC TEST 🔍".center(60))
    
    results = {}
    
    # Run tests
    results['smtp_config'] = test_smtp_config()
    results['sendgrid_config'] = test_sendgrid_config()
    results['provider_selection'] = test_provider_selection()
    results['smtp_provider'] = test_smtp_provider()
    results['sendgrid_provider'] = test_sendgrid_provider()
    results['email_send'] = test_email_send_capability()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is None:
            status = "⊘ SKIP"
        else:
            status = "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    print("-"*60)
    print(f"Results: {passed} passed, {skipped} skipped, {failed} failed (of {total})")
    
    if failed == 0:
        print("\n✅ EMAIL SYSTEM READY FOR USE!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. See above for details.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
