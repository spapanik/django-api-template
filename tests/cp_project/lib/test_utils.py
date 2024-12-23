from typing import Literal

import pytest
from django.test import override_settings

from cp_project.lib import utils

from tests.helpers.factories.account import UserFactory


class TestJWT:
    @pytest.mark.django_db
    @pytest.mark.parametrize("subject", ["access", "refresh"])
    def test_for_user(self, subject: Literal["access", "refresh"]) -> None:
        user = UserFactory().build(email="jon.snow@winterfell.com")
        user.save()
        jwt = utils.JWT.for_user(user, subject)
        assert jwt.sub == subject
        assert jwt.email == user.email
        assert jwt.exp > 0

    @pytest.mark.django_db
    def test_from_token(self) -> None:
        user = UserFactory().build()
        user.save()
        jwt = utils.JWT.for_user(user, "access")
        token = str(jwt)
        new_jwt = utils.JWT.from_token(token)
        assert new_jwt.sub == jwt.sub
        assert new_jwt.email == jwt.email
        assert new_jwt.exp == jwt.exp


def test_optimus_roundtrip() -> None:
    optimus = utils.Optimus(prime=2, inverse=4611686018427387904, random=0)
    n = 428340
    assert n == optimus.decode(optimus.encode(n))


def test_optimus_defaults() -> None:
    optimus = utils.Optimus()
    assert (optimus.prime * optimus.inverse) % (2**63) == 1


@override_settings(BASE_APP_DOMAIN="192.168.1.128", BASE_APP_PORT=80)
@pytest.mark.parametrize(
    ("path", "kwargs", "expected"),
    [
        ("relative/path", {}, "http://192.168.1.128/relative/path"),
        ("/absolute/path", {}, "http://192.168.1.128/absolute/path"),
        (
            "relative/path",
            {"foo": "bar"},
            "http://192.168.1.128/relative/path?foo=bar",
        ),
    ],
)
def test_get_app_url(path: str, kwargs: dict[str, str], expected: str) -> None:
    assert utils.get_app_url(path, **kwargs).string == expected


def test_hash_migrations() -> None:
    hashed_migrations = utils.get_migrations_info()
    assert "accounts" in hashed_migrations
    initial_account_migration = hashed_migrations["accounts"][0]
    assert initial_account_migration.name == "0001_initial"
    assert str(initial_account_migration).count("::") == 2


def test_saved_hashes() -> None:
    hashed_migrations = utils.get_saved_hashes()
    assert "accounts" in hashed_migrations
    initial_account_migration = hashed_migrations["accounts"][0]
    assert initial_account_migration.name == "0001_initial"
