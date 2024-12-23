from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cp_project.lib.types import JSONType

UUID_REGEX = re.compile(r"[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}")
EMAIL_REGEX = re.compile(r"\S+@\S+.\S+")
DATE_REGEX = re.compile(r"\d{4}-(1[0-2]|0[1-9])-(0[1-9]|1\d|2\d|3\d)")
TIME_REGEX = re.compile(r"(2[0-3]|[01]\d):([0-5]\d):([0-5]\d)(.\d{6})?")
DATETIME_REGEX = re.compile(f"{DATE_REGEX.pattern}T{TIME_REGEX.pattern}")


class ConfigurationError(AssertionError):
    def __init__(self, spec: JSONType, obj: object = None) -> None:
        obj_name = obj.__class__.__name__ if obj else "any validator"
        message = f"{spec} is not valid specification for {obj_name}"
        super().__init__(message)


class ValidationError(AssertionError):
    pass


class Validator:
    def __init__(self) -> None:
        raise NotImplementedError

    def _validate(self, json_response: JSONType) -> str:
        raise NotImplementedError

    def validate(self, json_response: JSONType) -> None:
        if error_message := self._validate(json_response):
            raise ValidationError(error_message)


class NoneValidator(Validator):
    def __init__(self) -> None:
        self.spec = None

    def _validate(self, json_response: JSONType) -> str:
        if json_response is None:
            return ""
        return f"Expected None, but returned `{json_response}`"


class BooleanValidator(Validator):
    def __init__(self, *, nullable: bool = False) -> None:
        self.nullable = nullable

    def _validate(self, json_response: JSONType) -> str:
        if isinstance(json_response, bool):
            return ""
        if json_response is not None or not self.nullable:
            return f"Expected a boolean, but returned `{json_response}`"
        return ""


class IntegerValidator(Validator):
    def __init__(
        self, min_value: int | None = None, max_value: int | None = None
    ) -> None:
        self.min_value = min_value
        self.max_value = max_value

    def _validate(self, json_response: JSONType) -> str:
        if not isinstance(json_response, int):
            return f"Expected a integer, but returned `{json_response}`"
        if self.min_value is not None and self.min_value > json_response:
            return (
                f"Response `{json_response}` is less than the min allowed `min_value`"
            )
        if self.max_value is not None and self.max_value < json_response:
            return (
                f"Response `{json_response}` is more than the max allowed `min_value`"
            )
        return ""


class FloatValidator(Validator):
    def __init__(
        self, min_value: float | None = None, max_value: float | None = None
    ) -> None:
        self.min_value = min_value
        self.max_value = max_value

    def _validate(self, json_response: JSONType) -> str:
        if not isinstance(json_response, float):
            return f"Expected a float, but returned `{json_response}`"
        if self.min_value is not None and self.min_value > json_response:
            return (
                f"Response `{json_response}` is less than the min allowed `min_value`"
            )
        if self.max_value is not None and self.max_value < json_response:
            return (
                f"Response `{json_response}` is more than the max allowed `min_value`"
            )
        return ""


class StringValidator(Validator):
    def __init__(self, regex: str | None = None) -> None:
        self.regex = None if regex is None else re.compile(regex)

    def _regex_mismatch(self, json_response: str) -> str:
        return f"`{json_response}` doesn't match `{self.regex}`"

    def _validate(self, json_response: JSONType) -> str:
        if not isinstance(json_response, str):
            return f"Expected a string, but returned `{json_response}`"
        if self.regex is not None and not re.fullmatch(self.regex, json_response):
            return self._regex_mismatch(json_response)
        return ""


class EmailValidator(StringValidator):
    def __init__(self) -> None:
        self.regex = EMAIL_REGEX

    def _regex_mismatch(self, json_response: str) -> str:
        return f"`{json_response}` isn't a valid email"


class UUIDValidator(StringValidator):
    def __init__(self) -> None:
        self.regex = UUID_REGEX

    def _regex_mismatch(self, json_response: str) -> str:
        return f"`{json_response}` isn't a valid UUID string"


class DateValidator(StringValidator):
    def __init__(self) -> None:
        self.regex = DATE_REGEX

    def _regex_mismatch(self, json_response: str) -> str:
        return f"`{json_response}` isn't a valid date string"


class TimeValidator(StringValidator):
    def __init__(self) -> None:
        self.regex = TIME_REGEX

    def _regex_mismatch(self, json_response: str) -> str:
        return f"`{json_response}` isn't a valid time string"


class DatetimeValidator(StringValidator):
    def __init__(self) -> None:
        self.regex = DATETIME_REGEX

    def _regex_mismatch(self, json_response: str) -> str:
        return f"`{json_response}` isn't a valid datetime string"


class ListValidator(Validator):
    def __init__(self, item_validator: Validator) -> None:
        self.item_validator = item_validator

    def _validate(self, json_response: JSONType) -> str:
        if not isinstance(json_response, list):
            return f"Expected a list, but returned `{json_response}`"
        for index, item in enumerate(json_response):
            try:
                self.item_validator.validate(item)
            except ValidationError:
                return f"Item `{index}` of `{json_response}` isn't valid"
        return ""


class DictValidator(Validator):
    def __init__(
        self, required: dict[str, Validator], optional: dict[str, Validator]
    ) -> None:
        self.required = required
        self.optional = optional

    def _validate(self, json_response: JSONType) -> str:
        if not isinstance(json_response, dict):
            return f"Expected a list, but returned `{json_response}`"
        required_keys = set(self.required.keys())
        optional_keys = set(self.optional.keys())
        actual_keys = set(json_response.keys())
        if actual_keys > (required_keys | optional_keys):
            return f"Unexpected keys: `{actual_keys - (required_keys | optional_keys)}`"
        if required_keys > actual_keys:
            return f"Missing keys: `{required_keys - actual_keys}`"

        for key, value in json_response.items():
            if key in self.optional:
                try:
                    self.optional[key].validate(value)
                except ValidationError:
                    return f"Optional `{key}` is present in `{json_response}` has not a valid value"
            elif key in self.required:
                try:
                    self.required[key].validate(value)
                except ValidationError:
                    return (
                        f"Required `{key}` in `{json_response}` has not a valid value"
                    )
        return ""


def get_validator(specs: JSONType) -> Validator:
    if not isinstance(specs, dict):
        raise ConfigurationError(specs)
    if specs["$type"] == "null":
        return NoneValidator()
    if specs["$type"] == "bool":
        nullable = specs.get("$nullable", False)
        if not isinstance(nullable, bool):
            raise ConfigurationError(specs)
        return BooleanValidator(nullable=nullable)
    if specs["$type"] == "int":
        min_value = specs.get("$min_value", None)
        if not isinstance(min_value, int) and min_value is not None:
            raise ConfigurationError(specs)
        max_value = specs.get("$max_value", None)
        if not isinstance(max_value, int) and max_value is not None:
            raise ConfigurationError(specs)
        return IntegerValidator(min_value=min_value, max_value=max_value)
    if specs["$type"] == "float":
        min_value = specs.get("$min_value", None)
        if not isinstance(min_value, float) and min_value is not None:
            raise ConfigurationError(specs)
        max_value = specs.get("$max_value", None)
        if not isinstance(max_value, float) and max_value is not None:
            raise ConfigurationError(specs)
        return FloatValidator(min_value=min_value, max_value=max_value)
    if specs["$type"] == "str":
        if specs.get("$subtype") == "email":
            return EmailValidator()
        if specs.get("$subtype") == "uuid":
            return UUIDValidator()
        if specs.get("$subtype") == "date":
            return DateValidator()
        if specs.get("$subtype") == "time":
            return TimeValidator()
        if specs.get("$subtype") == "datetime":
            return DatetimeValidator()
        regex = specs.get("$regex", None)
        if not isinstance(regex, str) and regex is not None:
            raise ConfigurationError(specs)
        return StringValidator(regex=regex)
    if specs["$type"] == "list":
        return get_validator(specs["$items"])
    if specs["$type"] == "dict":
        optional: dict[str, Validator] = {}
        required: dict[str, Validator] = {}
        properties = specs.get("$properties")
        if not isinstance(properties, dict):
            raise ConfigurationError(specs)
        for key, value in properties.items():
            if not isinstance(value, dict):
                raise ConfigurationError(specs)
            if value.get("$required", True):
                required[key] = get_validator(value)
            else:
                optional[key] = get_validator(value)
        return DictValidator(required=required, optional=optional)

    raise ConfigurationError(specs)
