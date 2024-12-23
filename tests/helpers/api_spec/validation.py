from __future__ import annotations

import re
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING

from tests.helpers.api_spec.loader import load_specs

if TYPE_CHECKING:
    from cp_project.lib.types import JSONType

    from tests.helpers.api_spec.validators import Validator


def get_endpoint_specs(path: str) -> dict[HTTPMethod, dict[HTTPStatus, Validator]]:
    specs = load_specs()
    if path in specs["static"]:
        return specs["static"][path]
    for regex, endpoint_specs in specs["regex"].items():
        if re.fullmatch(regex, path):
            return endpoint_specs
    msg = f"No available API specs for {path}"
    raise KeyError(msg)


def validate_api_specs(
    json_response: JSONType,
    *,
    path: str,
    status_code: int,
    method: str,
) -> None:
    http_status = HTTPStatus(status_code)
    http_method = HTTPMethod(method.upper())
    get_endpoint_specs(path)[http_method][http_status].validate(json_response)
