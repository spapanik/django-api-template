from collections.abc import Collection, Iterable
from typing import ClassVar, Self, TypeVar, cast

from django.db import models
from django.db.models.base import ModelBase
from pyutilkit.date_utils import now

from cp_project.lib.utils import Optimus

_T_co = TypeVar("_T_co", bound=models.Model, covariant=True)


class BaseQuerySet(models.QuerySet[_T_co]):
    def bulk_create(
        self,
        objs: Iterable[_T_co],
        batch_size: int | None = None,
        ignore_conflicts: bool = False,  # noqa: FBT001,FBT002
        update_conflicts: bool = False,  # noqa: FBT001,FBT002
        update_fields: Collection[str] | None = None,
        unique_fields: Collection[str] | None = None,
    ) -> list[_T_co]:
        dt = now()
        for obj in objs:
            obj.updated_at = dt  # type: ignore[attr-defined]
            obj.created_at = dt  # type: ignore[attr-defined]
        return super().bulk_create(
            objs,
            batch_size,
            ignore_conflicts,
            update_conflicts,
            update_fields,
            unique_fields,
        )

    def bulk_update(
        self,
        objs: Iterable[_T_co],
        fields: Iterable[str],
        batch_size: int | None = None,
    ) -> int:
        dt = now()
        for obj in objs:
            obj.updated_at = dt  # type: ignore[attr-defined]
        if "updated_at" not in fields:
            fields = [*fields, "updated_at"]
        return super().bulk_update(objs, fields, batch_size)

    def flat_values(self, key: str) -> models.QuerySet[_T_co]:
        return cast(models.QuerySet[_T_co], self.values_list(key, flat=True))

    def random(self) -> _T_co | None:
        return self.order_by("?").first()

    def get_by_oid(self, oid: int) -> _T_co:
        optimus = Optimus()
        return self.get(id=optimus.decode(oid))

    def filter_by_oid(self, oid: list[int]) -> Self:
        optimus = Optimus()
        return self.filter(id__in={optimus.decode(oid_) for oid_ in oid})

    def update(self, **kwargs: object) -> int:
        kwargs.setdefault("updated_at", now())
        return super().update(**kwargs)


class BaseModel(models.Model):
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(default=now, editable=False)

    objects: ClassVar[models.Manager[Self]] = BaseQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(
        self,
        force_insert: bool | tuple[ModelBase, ...] = False,  # noqa: FBT002
        force_update: bool = False,  # noqa: FBT001, FBT002
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        self.updated_at = now()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @property
    def oid(self) -> int:
        optimus = Optimus()
        return optimus.encode(self.id)  # type: ignore[attr-defined]
