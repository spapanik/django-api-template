import re
from functools import lru_cache
from http import HTTPMethod, HTTPStatus
from pathlib import Path
from typing import TypedDict

from dj_settings import ConfigParser

from cp_project.lib.types import JSONType

from tests.helpers.api_spec.validators import Validator, get_validator

BASE_PATH = Path(__file__).parent


MethodSpecs = dict[HTTPStatus, Validator]
PathSpecs = dict[HTTPMethod, MethodSpecs]


class LoadedSpecs(TypedDict):
    regex: dict[re.Pattern[str], PathSpecs]
    static: dict[str, PathSpecs]


@lru_cache
def load_specs() -> LoadedSpecs:
    output: LoadedSpecs = {
        "regex": {},
        "static": {},
    }
    data_files = BASE_PATH.joinpath("apps").glob("*.yaml")
    data = ConfigParser(list(data_files)).data
    for key, value in data.items():
        if value.pop("regex", False):
            output["regex"][re.compile(key)] = parse_spec(value)
        else:
            output["static"][key] = parse_spec(value)
    return output


def parse_spec(data: dict[str, dict[int, JSONType]]) -> PathSpecs:
    output: dict[HTTPMethod, MethodSpecs] = {}
    for key, value in data.items():
        output[HTTPMethod(key)] = {
            HTTPStatus(status_code): get_validator(specs)
            for status_code, specs in value.items()
        }
    return output
