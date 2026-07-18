import socket

import pytest

from app.config import get_settings
from app.core.email import SMTPEmailProvider


def test_smtp_timeout_aborts_and_closes_connection(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.test")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "apikey")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "smtp_use_tls", True)

    smtp_instances = []

    class FakeSocket:
        def __init__(self):
            self.timeouts = []

        def settimeout(self, value):
            self.timeouts.append(value)

    class TimeoutSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout
            self.sock = FakeSocket()
            self.closed = False
            self.quit_called = False
            smtp_instances.append(self)

        def ehlo(self):
            return None

        def starttls(self):
            return None

        def login(self, _user, _password):
            raise socket.timeout("authentication timed out")

        def quit(self):
            self.quit_called = True
            self.closed = True

        def close(self):
            self.closed = True

    monkeypatch.setattr("app.core.email.smtplib.SMTP", TimeoutSMTP)

    provider = SMTPEmailProvider()

    with pytest.raises(TimeoutError, match="SMTP server did not respond within 10 seconds"):
        provider.send(
            to="invitee@example.com",
            subject="Invitation",
            html_body="<p>Hello</p>",
        )

    assert smtp_instances
    smtp = smtp_instances[0]
    assert smtp.timeout == 10
    assert smtp.sock.timeouts == [10, 10]
    assert smtp.quit_called is True
    assert smtp.closed is True
