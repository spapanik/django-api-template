from http import HTTPStatus

import pytest
from freezegun import freeze_time

from cp_project.accounts.models import User
from cp_project.lib.utils import JWT

from tests.helpers.client import JsonTestClient
from tests.helpers.factories.account import SignupTokenFactory, UserFactory


class TestObtainTokenView:
    email = "jon.snow@winterfell.org"
    password = "WwOQa7;S#8HAr#L^"  # noqa: S105

    @pytest.fixture(autouse=True)
    def _create_user(self) -> None:
        user = UserFactory().build(email=self.email, is_active=True)
        user.set_password(self.password)
        user.save()

    @pytest.mark.django_db
    def test_get_access_token(self, json_client: JsonTestClient) -> None:
        response = json_client.post(
            "/accounts/token/",
            data={"email": self.email, "password": self.password},
        )
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.data, dict)
        assert "access" in response.data
        assert "refresh" in response.data

    @pytest.mark.django_db
    @pytest.mark.parametrize("keys", [[], ["email"], ["password"]])
    def test_get_access_token_missing_keys(
        self, keys: list[str], json_client: JsonTestClient
    ) -> None:
        needed_data = {"email": self.email, "password": self.password}
        response = json_client.post(
            "/accounts/token/",
            data={key: needed_data[key] for key in keys},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert isinstance(response.data, dict)
        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert "message" in response.data["error"]

    @pytest.mark.django_db
    def test_get_access_token_wrong_format(self, json_client: JsonTestClient) -> None:
        response = json_client.post(
            "/accounts/token/", data=[self.email, self.password]
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert isinstance(response.data, dict)
        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert "message" in response.data["error"]

    @pytest.mark.django_db
    def test_get_access_token_wrong_password(self, json_client: JsonTestClient) -> None:
        response = json_client.post(
            "/accounts/token/",
            data={"email": self.email, "password": self.password.lower()},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert isinstance(response.data, dict)
        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert "message" in response.data["error"]


@pytest.mark.django_db
def test_account_creation_success(json_client: JsonTestClient) -> None:
    email = "jon.snow@winterfell.org"
    password = "WwOQa7;S#8HAr#L^"  # noqa: S105
    response = json_client.post(
        "/accounts/",
        data={"email": email, "password": password},
    )
    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("jon.snow@winterfell.org", "password"),
        ("jon.snow at winterfell.org", "WwOQa7;S#8HAr#L^'"),
    ],
)
def test_account_creation_failed(
    email: str, password: str, json_client: JsonTestClient
) -> None:
    response = json_client.post(
        "/accounts/",
        data={"email": email, "password": password},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_account_creation_failed_bad_type(json_client: JsonTestClient) -> None:
    email = "jon.snow@winterfell.org"
    password = "WwOQa7;S#8HAr#L^"  # noqa: S105
    response = json_client.post("/accounts/", data=[email, password])
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_account_creation_failed_duplicate(
    inactive_user: User, json_client: JsonTestClient
) -> None:
    response = json_client.post(
        "/accounts/",
        data={"email": inactive_user.email, "password": "WwOQa7;S#8HAr#L^"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.django_db
def test_refresh_token_success(
    user_tokens: dict[str, JWT], json_client: JsonTestClient
) -> None:
    response = json_client.post(
        "/accounts/token/refresh",
        data={"token": str(user_tokens["refresh"])},
    )
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.data, dict)
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_refresh_token_wrong_type(
    user_tokens: dict[str, JWT], json_client: JsonTestClient
) -> None:
    response = json_client.post(
        "/accounts/token/refresh",
        data={"token": str(user_tokens["access"])},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert isinstance(response.data, dict)
    assert "error" in response.data
    assert isinstance(response.data["error"], dict)
    assert "message" in response.data["error"]


@pytest.mark.django_db
def test_refresh_token_deleted_user(
    user_tokens: dict[str, JWT], json_client: JsonTestClient
) -> None:
    User.objects.get(email=user_tokens["access"].email).delete()
    response = json_client.post(
        "/accounts/token/refresh",
        data={"token": str(user_tokens["refresh"])},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert isinstance(response.data, dict)
    assert "error" in response.data
    assert isinstance(response.data["error"], dict)
    assert "message" in response.data["error"]


@pytest.mark.django_db
def test_refresh_token_cannot_decode(
    user_tokens: dict[str, JWT], json_client: JsonTestClient
) -> None:
    response = json_client.post(
        "/accounts/token/refresh",
        data={"token": str(user_tokens["refresh"])[:-1]},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert isinstance(response.data, dict)
    assert "error" in response.data
    assert isinstance(response.data["error"], dict)
    assert "message" in response.data["error"]


@pytest.mark.django_db
def test_refresh_token_wrong_format(
    user_tokens: dict[str, JWT], json_client: JsonTestClient
) -> None:
    User.objects.get(email=user_tokens["access"].email).delete()
    response = json_client.post(
        "/accounts/token/refresh",
        data=[str(user_tokens["refresh"])],
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert isinstance(response.data, dict)
    assert "error" in response.data
    assert isinstance(response.data["error"], dict)
    assert "message" in response.data["error"]


@pytest.mark.django_db
def test_confirm_email(inactive_user: User, json_client: JsonTestClient) -> None:
    signup_token = SignupTokenFactory().build(user=inactive_user)
    signup_token.save()
    response = json_client.post(f"/accounts/confirm-email/{signup_token.oid}")
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.data is None


@pytest.mark.django_db
def test_confirm_email_no_token(json_client: JsonTestClient) -> None:
    response = json_client.post("/accounts/confirm-email/0")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert isinstance(response.data, dict)
    assert "error" in response.data
    assert isinstance(response.data["error"], dict)
    assert "message" in response.data["error"]


@pytest.mark.django_db
def test_confirm_email_expired_token(
    inactive_user: User, json_client: JsonTestClient
) -> None:
    with freeze_time("1970-01-01"):
        signup_token = SignupTokenFactory().build(user=inactive_user)
    signup_token.save()
    response = json_client.post(f"/accounts/confirm-email/{signup_token.oid}")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert isinstance(response.data, dict)
    assert "error" in response.data
    assert isinstance(response.data["error"], dict)
    assert "message" in response.data["error"]
