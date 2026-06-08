#!/usr/bin/env python3
"""
Functional integration test for email system.
Tests actual OTP email sending with both SMTP and SendGrid.

Usage:
    python send_test_email.py [--provider smtp|sendgrid] [--email your@email.com]
    
Example:
    docker exec nuetra-auth-service-1 python send_test_email.py --provider sendgrid --email test@example.com
"""

import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def send_otp_email(email: str, provider: str = None, otp_code: str = "123456"):
    """Send a test OTP email"""
    
    if provider:
        os.environ["APP_ENV"] = "production" if provider == "sendgrid" else "development"
    
    try:
        from app.core.email import get_email_service
        
        service = get_email_service()
        provider_name = type(service._provider).__name__
        
        print(f"\n{'='*60}")
        print(f"SENDING TEST OTP EMAIL")
        print(f"{'='*60}")
        print(f"Provider: {provider_name}")
        print(f"Recipient: {email}")
        print(f"OTP Code: {otp_code}")
        print(f"From: {service._provider._settings.smtp_from_name} <{service._provider._settings.smtp_from_email}>")
        
        # Send the OTP
        service.send_otp(email, otp_code)
        
        print(f"\n✅ Email sent successfully!")
        print(f"\nNext steps:")
        print(f"1. Check your email inbox for OTP: {otp_code}")
        print(f"2. If using SendGrid, verify at: https://app.sendgrid.com/email_activity")
        print(f"3. Check container logs: docker logs nuetra-auth-service-1 | grep email")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_invitation_email(email: str, password: str, role: str = "team_member", provider: str = None):
    """Send a test invitation email"""
    
    if provider:
        os.environ["APP_ENV"] = "production" if provider == "sendgrid" else "development"
    
    try:
        from app.core.email import get_email_service
        
        service = get_email_service()
        provider_name = type(service._provider).__name__
        
        print(f"\n{'='*60}")
        print(f"SENDING TEST INVITATION EMAIL")
        print(f"{'='*60}")
        print(f"Provider: {provider_name}")
        print(f"Recipient: {email}")
        print(f"Role: {role}")
        print(f"Temporary Password: {password}")
        print(f"From: {service._provider._settings.smtp_from_name} <{service._provider._settings.smtp_from_email}>")
        
        # Send the invitation
        service.send_invitation(email, password, role)
        
        print(f"\n✅ Invitation email sent successfully!")
        print(f"\nNext steps:")
        print(f"1. Check your email inbox for invitation")
        print(f"2. Use password: {password}")
        print(f"3. If using SendGrid, verify at: https://app.sendgrid.com/email_activity")
        print(f"4. Check container logs: docker logs nuetra-auth-service-1 | grep email")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_email_logs():
    """Show recent email-related logs"""
    import subprocess
    
    print(f"\n{'='*60}")
    print(f"RECENT EMAIL LOGS")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail=20", "nuetra-auth-service-1"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.split('\n')
        email_lines = [l for l in lines if any(keyword in l.lower() for keyword in ['email', 'sendgrid', 'smtp', 'mail'])]
        
        if email_lines:
            for line in email_lines:
                print(line)
        else:
            print("(No email-related logs found in last 20 lines)")
            print("\nShowing last 20 lines:")
            for line in lines[-20:]:
                if line.strip():
                    print(line)
    except Exception as e:
        print(f"Error reading logs: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Test email sending functionality")
    parser.add_argument(
        "--provider",
        choices=["smtp", "sendgrid"],
        help="Email provider to test (auto-detected if not specified)"
    )
    parser.add_argument(
        "--email",
        default="test@example.com",
        help="Email address to send test email to (default: test@example.com)"
    )
    parser.add_argument(
        "--type",
        choices=["otp", "invitation"],
        default="otp",
        help="Email type to send (default: otp)"
    )
    parser.add_argument(
        "--password",
        default="TempPass123!",
        help="Temporary password for invitation email (default: TempPass123!)"
    )
    parser.add_argument(
        "--role",
        default="team_member",
        help="Role for invitation email (default: team_member)"
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Show email logs after sending"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'🚀 EMAIL INTEGRATION TEST 🚀'.center(60)}\n")
    
    success = False
    if args.type == "otp":
        success = send_otp_email(args.email, args.provider)
    else:
        success = send_invitation_email(args.email, args.password, args.role, args.provider)
    
    if args.logs:
        check_email_logs()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
