from __future__ import annotations

import json
import logging
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING, cast

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from cp_project.accounts.models import User
from cp_project.lib.exceptions import ValidationError
from cp_project.lib.http import JsonResponse
from cp_project.lib.types import JSONType

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class APIView:
    csrf_exempt = True

    def __init__(self, **kwargs: object) -> None:
        # Called in the URLconf
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def has_permissions(_user: User | AnonymousUser) -> bool:
        return True

    @property
    def _allowed_methods(self) -> list[str]:
        return [method for method in HTTPMethod if hasattr(self, method.lower())]

    @classmethod
    def as_view(cls, **initkwargs: object) -> Callable[..., JsonResponse]:  # type: ignore[misc]
        for key in initkwargs:
            if key.upper() in HTTPMethod:
                msg = (
                    f"The method name {key} is not accepted "
                    f"as a keyword argument to {cls.__name__}."
                )
                raise TypeError(msg)
            if not hasattr(cls, key):
                msg = (
                    f"{cls.__name__}() received an invalid keyword {key}. as_view "
                    "only accepts arguments that are already attributes of the class."
                )
                raise TypeError(msg)

        def view(request: HttpRequest, **kwargs: object) -> JsonResponse:
            self = cls(**initkwargs)
            self.setup(request, **kwargs)
            return self.dispatch(**kwargs)

        view.view_class = cls  # type: ignore[attr-defined]
        view.view_initkwargs = initkwargs  # type: ignore[attr-defined]
        view.csrf_exempt = cls.csrf_exempt  # type: ignore[attr-defined]

        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.__annotations__ = cls.dispatch.__annotations__
        view.__dict__.update(cls.dispatch.__dict__)

        return view

    def setup(self, request: HttpRequest, **_kwargs: object) -> None:
        self.request = request
        if hasattr(self, "get") and not hasattr(self, "head"):

            def head(**kwargs: object) -> JsonResponse:
                response = self.get(**kwargs)
                return JsonResponse(
                    None, status=response.status_code, headers=response.headers
                )

            self.head = head

    def dispatch(self, **kwargs: object) -> JsonResponse:
        """Try to dispatch to the right method.

        If a method doesn't exist, defer to the error handler. Also defer to
        the error handler if the request method isn't on the approved list.
        """
        method = self.request.method
        if method not in self._allowed_methods:
            return self.http_method_not_allowed()
        try:
            user: User | AnonymousUser = User.from_request(self.request)
        except LookupError:
            user = AnonymousUser()

        handler = getattr(self, method.lower())
        if self.has_permissions(user):
            self.request.user = user

            return cast(JsonResponse, handler(**kwargs))
        if user.is_anonymous:
            return JsonResponse(
                {"error": {"message": "You must be logged in to perform this action."}},
                status=HTTPStatus.UNAUTHORIZED,
            )

        return JsonResponse(
            {
                "error": {
                    "message": "You do not have permission to perform this action."
                }
            },
            status=HTTPStatus.FORBIDDEN,
        )

    def get_data(self) -> JSONType:
        try:
            return cast(JSONType, json.loads(self.request.body))
        except (json.JSONDecodeError, TypeError) as exc:
            msg = "Invalid JSON"
            raise ValidationError(msg) from exc

    def http_method_not_allowed(self) -> JsonResponse:
        logger.warning(
            "Method Not Allowed (%s): %s",
            self.request.method,
            self.request.path,
        )

        return JsonResponse(
            {
                "error": "Method Not Allowed",
                "allowed_methods": self._allowed_methods,
            }
        )

    def options(self, **_kwargs: object) -> JsonResponse:
        response = JsonResponse(self._allowed_methods, safe=False)
        response.headers["Allow"] = ", ".join(self._allowed_methods)
        return response


class AuthenticatedAPIView(APIView):
    @staticmethod
    def has_permissions(user: User | AnonymousUser) -> bool:
        return user.is_authenticated


class StaffAPIView(APIView):
    @staticmethod
    def has_permissions(user: User | AnonymousUser) -> bool:
        return user.is_staff


class SuperuserAPIView(APIView):
    @staticmethod
    def has_permissions(user: User | AnonymousUser) -> bool:
        return user.is_superuser
