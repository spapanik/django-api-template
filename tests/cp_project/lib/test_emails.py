from __future__ import annotations

from smtplib import SMTPException
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from cp_project.lib.emails import Attachment
from cp_project.notifications.emails import SignupEmail

if TYPE_CHECKING:
    from django.core.mail import EmailMultiAlternatives

    from cp_project.accounts.models import User


@pytest.mark.django_db
@mock.patch("cp_project.lib.emails.EmailMultiAlternatives", autospec=True)
def test_send_email_with_attachments(
    mock_email: EmailMultiAlternatives, inactive_user: User
) -> None:
    attachments = [
        Attachment(name="file1.txt", content=b"file1 content", mimetype="text/plain"),
        Attachment(name="file2.txt", content=b"file2 content", mimetype="text/plain"),
    ]

    mock_mail = mock_email.return_value  # type: ignore[attr-defined]

    result = SignupEmail.send_email(
        inactive_user, attachments, signup_link="https://example.com/signup"
    )

    assert mock_mail.send.call_count == 1
    assert mock_mail.attach.call_count == 2

    expected_calls = [
        mock.call.attach("file1.txt", b"file1 content", "text/plain"),
        mock.call.attach("file2.txt", b"file2 content", "text/plain"),
    ]
    assert sorted(mock_mail.attach.mock_calls) == expected_calls

    assert result


@pytest.mark.django_db
@mock.patch("cp_project.lib.emails.EmailMultiAlternatives", autospec=True)
def test_send_email_smtp_exception(
    mock_email: EmailMultiAlternatives, inactive_user: User
) -> None:
    mock_mail = mock_email.return_value  # type: ignore[attr-defined]

    mock_mail.send.side_effect = SMTPException

    result = SignupEmail.send_email(
        inactive_user, signup_link="https://example.com/signup"
    )

    mock_mail.send.assert_called_once()

    assert result is False
