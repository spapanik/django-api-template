import pytest

from cp_project.accounts.models import User
from cp_project.lib.utils import JWT

from tests.helpers.client import JsonTestClient
from tests.helpers.factories.account import UserFactory


@pytest.fixture
def json_client() -> JsonTestClient:
    return JsonTestClient()


@pytest.fixture
def inactive_user() -> User:
    email = "jon.snow@winterfell.org"
    password = "WwOQa7;S#8HAr#L^"  # noqa: S105
    user = UserFactory().build(email=email, is_active=False)
    user.set_password(password)
    user.save()
    return user


@pytest.fixture
def active_user() -> User:
    email = "jon.snow@winterfell.org"
    password = "WwOQa7;S#8HAr#L^"  # noqa: S105
    user = UserFactory().build(email=email, is_active=True)
    user.set_password(password)
    user.save()
    return user


@pytest.fixture
def user_tokens(active_user: User) -> dict[str, JWT]:
    return {
        "access": JWT.for_user(active_user, "access"),
        "refresh": JWT.for_user(active_user, "refresh"),
    }
