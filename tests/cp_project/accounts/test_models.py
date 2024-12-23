from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Protocol

import pytest
from django.test import RequestFactory, override_settings

from cp_project.accounts.models import SignupToken, User

from tests.helpers.factories.account import SignupTokenFactory, UserFactory

if TYPE_CHECKING:
    from pytest_django import DjangoAssertNumQueries

    from cp_project.lib.utils import JWT


class UserCreator(Protocol):
    def __call__(self, email: str, password: str | None = None) -> User: ...


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "is_superuser", "is_staff", "is_active"),
    [
        (User.objects.create_user, False, False, True),
        (User.objects.create_staff, False, True, True),
        (User.objects.create_superuser, True, True, True),
    ],
)
def test_user_created(
    method: UserCreator,
    is_superuser: bool,
    is_staff: bool,
    is_active: bool,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    email = "carl.sagan@physics.com"
    with django_assert_num_queries(1):
        user = method(email=email)

    assert str(user) == email
    assert user.is_superuser is is_superuser
    assert user.is_staff is is_staff
    assert user.is_active is is_active


@pytest.mark.django_db
def test_user_needs_email() -> None:
    with pytest.raises(ValueError, match="An email must be set"):
        User.objects.create_user(email="")


@pytest.mark.django_db
def test_get_user_from_request(user_tokens: dict[str, JWT]) -> None:
    token = user_tokens["access"]
    request = RequestFactory().get("/")
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    user = User.from_request(request=request)
    assert user.email == token.email


@pytest.mark.django_db
def test_get_user_from_request_using_refresh_token(user_tokens: dict[str, JWT]) -> None:
    token = user_tokens["refresh"]
    request = RequestFactory().get("/")
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    with pytest.raises(LookupError):
        User.from_request(request=request)


@pytest.mark.django_db
def test_get_user_from_request_deleted_user(user_tokens: dict[str, JWT]) -> None:
    token = user_tokens["access"]
    request = RequestFactory().get("/")
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    User.objects.get(email=token.email).delete()
    with pytest.raises(LookupError):
        User.from_request(request=request)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("td", "expired"),
    [
        (timedelta(seconds=0), False),
        (timedelta(days=1, seconds=1), True),
    ],
)
@override_settings(SIGNUP_TOKEN_EXPIRY=timedelta(days=1))
def test_expired_signup_token(td: timedelta, expired: bool) -> None:
    user = UserFactory().build()
    user.save()
    signup_token = SignupTokenFactory().build(user=user)
    signup_token.save()
    as_of = signup_token.created_at + td
    assert signup_token.expired(as_of=as_of) is expired
    assert SignupToken.objects.expired(as_of=as_of).count() == int(expired)


@pytest.mark.django_db
def test_signup_token_str() -> None:
    user = UserFactory().build()
    user.save()
    signup_token = SignupTokenFactory().build(user=user)
    signup_token.save()
    assert str(signup_token).startswith("Signup token for ")
