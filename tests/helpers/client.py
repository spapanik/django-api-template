from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, cast

from django.test import Client

from cp_project.lib.http import JsonResponse

from tests.helpers.api_spec.validation import validate_api_specs

if TYPE_CHECKING:
    from collections.abc import Mapping

    from cp_project.lib.types import JSONType
    from cp_project.lib.utils import JWT


class JsonTestClient(Client):
    @staticmethod
    def _get_headers(
        headers: Mapping[str, str] | None = None, jwt: JWT | None = None
    ) -> dict[str, str]:
        output = {}
        if jwt:
            output["AUTHORIZATION"] = f"Bearer {jwt}"
        for key, value in (headers or {}).items():
            output[key.upper()] = value
        return output

    @staticmethod
    def _get_method_name() -> str:
        return inspect.stack()[1].function

    def get(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().get(
                path,
                follow=follow,
                data=data,  # type: ignore[arg-type]
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def post(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().post(
                path,
                follow=follow,
                data=data,
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def put(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().put(
                path,
                follow=follow,
                data=data,
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def patch(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().patch(
                path,
                follow=follow,
                data=data,
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def delete(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().delete(
                path,
                follow=follow,
                data=data,
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def head(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().head(
                path,
                follow=follow,
                data=data,
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def options(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().options(
                path,
                follow=follow,
                data=data,  # type: ignore[arg-type]
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response

    def trace(  # type: ignore[override]
        self,
        path: str,
        *,
        follow: bool = False,
        data: JSONType = None,
        content_type: str = "application/json",
        headers: Mapping[str, str] | None = None,
        jwt: JWT | None = None,
        assert_api_specs: bool = True,
    ) -> JsonResponse:
        response = cast(
            JsonResponse,
            super().trace(
                path,
                follow=follow,
                data=data,
                content_type=content_type,
                headers=self._get_headers(headers, jwt),
            ),
        )
        if assert_api_specs:
            validate_api_specs(
                response.data,
                path=path,
                status_code=response.status_code,
                method=self._get_method_name(),
            )
        return response
