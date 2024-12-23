from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from pyutilkit.date_utils import now

from cp_project.lib.models import BaseModel, BaseQuerySet
from cp_project.lib.utils import JWT, get_app_url

if TYPE_CHECKING:
    from datetime import datetime

    from django.http import HttpRequest
    from pathurl import URL


class UserManager(BaseUserManager.from_queryset(BaseQuerySet["User"])):  # type: ignore[misc]
    use_in_migrations = True

    def _create_user(
        self,
        email: str,
        password: str | None,
        *,
        is_superuser: bool,
        is_staff: bool,
        is_active: bool,
    ) -> User:
        if not email:
            msg = "An email must be set"
            raise ValueError(msg)

        email = self.normalize_email(email)
        user: User = self.model(
            email=email,
            is_superuser=is_superuser,
            is_staff=is_staff,
            is_active=is_active,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: str | None = None, *, is_active: bool = True
    ) -> User:
        return self._create_user(
            email=email,
            password=password,
            is_superuser=False,
            is_staff=False,
            is_active=is_active,
        )

    def create_staff(
        self, email: str, password: str | None = None, *, is_active: bool = True
    ) -> User:

        return self._create_user(
            email=email,
            password=password,
            is_staff=True,
            is_superuser=False,
            is_active=is_active,
        )

    def create_superuser(
        self, email: str, password: str | None = None, *, is_active: bool = True
    ) -> User:

        return self._create_user(
            email=email,
            password=password,
            is_superuser=True,
            is_staff=True,
            is_active=is_active,
        )


class SignupTokenQuerySet(BaseQuerySet["SignupToken"]):
    def expired(self, as_of: datetime | None = None) -> SignupTokenQuerySet:
        as_of = as_of or now()
        return self.filter(created_at__lte=as_of - settings.SIGNUP_TOKEN_EXPIRY)


class SignupTokenManager(models.Manager.from_queryset(SignupTokenQuerySet)):  # type: ignore[misc]
    pass


class User(AbstractUser, BaseModel):
    username = None  # type: ignore[assignment]
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects: ClassVar[UserManager] = UserManager()

    class Meta(AbstractUser.Meta):  # type: ignore[name-defined,misc]
        swappable = "AUTH_USER_MODEL"

    def __str__(self) -> str:
        return self.email

    @classmethod
    def from_request(cls, request: HttpRequest) -> Self:
        bearer = request.META.get("HTTP_AUTHORIZATION")
        if not bearer:
            msg = "No bearer token"
            raise LookupError(msg)

        _, token = bearer.split()
        jwt = JWT.from_token(token)
        if jwt.sub != "access":
            msg = "Not an access token"
            raise LookupError(msg)

        try:
            user: Self = cls.objects.get(email=jwt.email)
        except cls.DoesNotExist as exc:
            msg = "No such user"
            raise LookupError(msg) from exc

        return user

    def get_tokens(self) -> dict[str, str]:
        refresh_token = JWT.for_user(self, "refresh")
        access_token = JWT.for_user(self, "access")
        return {
            "refresh": str(refresh_token),
            "access": str(access_token),
        }

    def get_signup_token(self) -> SignupToken:
        """Get the signup token for this user.

        If one already exists, delete it first. This is to prevent
        expanding the lifetime of a token after the 24h limit.
        """
        SignupToken.objects.filter(user=self).delete()
        signup_token: SignupToken = SignupToken.objects.create(user=self)
        return signup_token


class SignupToken(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="signup_token"
    )

    objects: ClassVar[SignupTokenManager] = SignupTokenManager()

    def expired(self, as_of: datetime | None = None) -> bool:
        as_of = as_of or now()
        return self.created_at <= as_of - settings.SIGNUP_TOKEN_EXPIRY

    @property
    def signup_link(self) -> URL:
        return get_app_url(
            reverse("accounts:confirm-email", kwargs={"token_id": self.oid})
        )

    def __str__(self) -> str:
        return f"Signup token for {self.user}"
