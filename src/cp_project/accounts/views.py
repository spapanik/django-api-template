from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, TypeGuard, cast

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from jwt import DecodeError

from cp_project.accounts.models import SignupToken, User
from cp_project.lib.exceptions import ValidationError
from cp_project.lib.http import JsonResponse
from cp_project.lib.utils import JWT
from cp_project.lib.views import APIView
from cp_project.notifications.emails import SignupEmail

if TYPE_CHECKING:
    from pathurl import URL

    from cp_project.lib.types import JSONType


class TokenView(APIView):
    def _authenticate(self, _data: dict[str, str]) -> User | None:
        raise NotImplementedError

    def get_credentials(self) -> dict[str, str]:
        raise NotImplementedError

    def post(self) -> JsonResponse:
        try:
            credentials = self.get_credentials()
        except ValidationError:
            return JsonResponse(
                {"error": {"message": "Invalid credentials."}},
                status=HTTPStatus.UNAUTHORIZED,
            )

        if (user := self._authenticate(credentials)) is None:
            return JsonResponse(
                {"error": {"message": "Invalid credentials."}},
                status=HTTPStatus.UNAUTHORIZED,
            )
        return JsonResponse(user.get_tokens())


class ObtainTokenView(TokenView):
    def _authenticate(self, data: dict[str, str]) -> User | None:
        return authenticate(email=data["email"], password=data["password"])

    def validate_data(self, data: JSONType) -> TypeGuard[dict[str, str]]:
        if not isinstance(data, dict):
            return False
        email = data.get("email")
        password = data.get("password")
        return isinstance(email, str) and isinstance(password, str)

    def get_credentials(self) -> dict[str, str]:
        data = self.get_data()
        if not self.validate_data(data):
            raise ValidationError

        return {"email": data["email"].lower(), "password": data["password"]}


class RefreshTokenView(TokenView):
    def _authenticate(self, data: dict[str, str]) -> User | None:
        email = data["email"]
        try:
            return cast(User, User.objects.get(email=email))
        except User.DoesNotExist:
            return None

    def validate_data(self, data: JSONType) -> TypeGuard[dict[str, str]]:
        if not isinstance(data, dict):
            return False
        token = data.get("token")
        return isinstance(token, str)

    def get_credentials(self) -> dict[str, str]:
        data = self.get_data()
        if not self.validate_data(data):
            raise ValidationError
        refresh_token = data["token"]
        try:
            token = JWT.from_token(refresh_token)
        except DecodeError as exc:
            msg = "Invalid refresh token"
            raise ValidationError(msg) from exc
        if token.sub != "refresh":
            msg = "Not a refresh token"
            raise ValidationError(msg)
        return {"email": token.email}


class UserAPIView(APIView):
    @staticmethod
    def send_confirmation_email(user: User) -> URL:
        signup_link = user.get_signup_token().signup_link
        SignupEmail.send_email(recipient=user, signup_link=signup_link)
        return signup_link

    def validate_data(self, data: JSONType) -> TypeGuard[dict[str, str]]:
        if not isinstance(data, dict):
            return False
        email = data.get("email")
        password = data.get("password")
        return isinstance(email, str) and isinstance(password, str)

    def get_user_info(self) -> dict[str, str]:
        data = self.get_data()
        if not self.validate_data(data):
            raise ValidationError
        email = data["email"].lower()
        try:
            validate_email(email)
        except DjangoValidationError as exc:
            msg = "Invalid email address"
            raise ValidationError(msg) from exc

        password = data["password"]
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            msg = "Invalid password"
            raise ValidationError(msg, notes=exc.messages) from exc
        return {"email": email, "password": password}

    def post(self) -> JsonResponse:
        try:
            user_info = self.get_user_info()
        except ValidationError as exc:
            return JsonResponse(
                {"error": {"message": str(exc)}}, status=HTTPStatus.BAD_REQUEST
            )
        try:
            user = User.objects.create_user(is_active=False, **user_info)
        except IntegrityError as exc:
            return JsonResponse(
                {"error": {"message": str(exc)}}, status=HTTPStatus.CONFLICT
            )
        self.send_confirmation_email(user)
        return JsonResponse({"message": "OK"}, status=HTTPStatus.CREATED)


class ConfirmEmailAPIView(APIView):
    @staticmethod
    def post(token_id: int) -> JsonResponse:
        try:
            signup_token = SignupToken.objects.get_by_oid(token_id)
        except SignupToken.DoesNotExist:
            return JsonResponse(
                {"error": {"message": "Invalid token."}}, status=HTTPStatus.NOT_FOUND
            )
        if signup_token.expired():
            return JsonResponse(
                {"error": {"message": "Invalid token."}}, status=HTTPStatus.UNAUTHORIZED
            )
        user = signup_token.user
        user.is_active = True
        user.save()
        signup_token.delete()
        return JsonResponse(None, status=HTTPStatus.NO_CONTENT, safe=False)
