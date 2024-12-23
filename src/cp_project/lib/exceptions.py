from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


class LoginRequiredError(RuntimeError):
    pass


class ValidationError(AssertionError):
    def __init__(
        self, message: str = "Validation failed", *, notes: Iterable[str] = ()
    ) -> None:
        super().__init__(message)
        if notes:
            self.__notes__ = list(notes)
