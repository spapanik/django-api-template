from __future__ import annotations

import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Self

import jwt
from django.conf import settings
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.writer import MigrationWriter
from pathurl import URL, Query
from pyutilkit.date_utils import now
from pyutilkit.files import hash_file
from pyutilkit.term import SGRCodes, SGRString

if TYPE_CHECKING:
    from django.db.migrations import Migration

    from cp_project.accounts.models import User


@dataclass(frozen=True, slots=True)
class JWT:
    sub: Literal["access", "refresh"]
    email: str
    exp: int

    @classmethod
    def for_user(cls, user: User, jwt_type: Literal["access", "refresh"]) -> Self:
        expiry_delta = (
            settings.REFRESH_TOKEN_EXPIRY
            if jwt_type == "refresh"
            else settings.ACCESS_TOKEN_EXPIRY
        )
        return cls(
            sub=jwt_type,
            email=user.email,
            exp=int((now() + expiry_delta).timestamp()),
        )

    @classmethod
    def from_token(cls, token: str) -> Self:
        return cls(**jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"]))

    def __str__(self) -> str:
        return jwt.encode(asdict(self), settings.SECRET_KEY, algorithm="HS256")


@dataclass(frozen=True, slots=True, order=True)
class MigrationInfo:
    app: str
    prefix: str
    name: str
    hash: str

    def __str__(self) -> str:
        return f"{self.app}::{self.name}::{self.hash}"

    @classmethod
    def from_writer_info(cls, app: str, migration_name: str, path: Path) -> Self:
        prefix, *_ = migration_name.split("_")
        return cls(app=app, prefix=prefix, name=migration_name, hash=hash_file(path))

    @classmethod
    def from_lockfile(cls, lockfile_line: str) -> Self:
        app, migration_name, hash_value = lockfile_line.split("::")
        prefix, *_ = migration_name.split("_")
        return cls(app=app, prefix=prefix, name=migration_name, hash=hash_value)


class Optimus:
    def __init__(
        self,
        prime: int = settings.OPTIMUS_PRIME,
        inverse: int = settings.OPTIMUS_INVERSE,
        random: int = settings.OPTIMUS_RANDOM,
    ) -> None:
        self.max_int = 2**63 - 1
        self.prime = prime
        self.inverse = inverse
        self.random = random

    def encode(self, n: int) -> int:
        return ((n * self.prime) % self.max_int) ^ self.random

    def decode(self, n: int) -> int:
        return ((n ^ self.random) * self.inverse) % self.max_int


def get_app_url(path: str, **kwargs: str | list[str]) -> URL:
    return URL.from_parts(
        scheme=settings.BASE_APP_SCHEME,
        hostname=settings.BASE_APP_DOMAIN,
        port=settings.BASE_APP_PORT,
        path=path,
        query=Query.from_dict(dict_={}, **kwargs),
    )


def format_app_migrations(app_label: str, app_migrations: list[Migration]) -> None:
    SGRString(
        f"Reformatting migrations for `{app_label}`:",
        params=[SGRCodes.BOLD, SGRCodes.CYAN],
    ).print()

    for migration in app_migrations:
        file = MigrationWriter(migration).path
        SGRString(
            f"  📜 Reformatting migration `{migration}`...", params=[SGRCodes.BOLD]
        ).print(end="\t")
        subprocess.run(["black", "--quiet", file], check=True)  # noqa: S603,S607
        subprocess.run(  # noqa: S603
            ["ruff", "check", "--fix-only", "--quiet", file], check=True  # noqa: S607
        )
        SGRString("✔️", params=[SGRCodes.BOLD]).print()


def get_migrations_info() -> dict[str, list[MigrationInfo]]:
    loader = MigrationLoader(None, ignore_no_migrations=True)
    hashes: dict[str, list[MigrationInfo]] = defaultdict(list)
    source = settings.BASE_DIR.joinpath("src")
    for (app, migration_name), migration in loader.graph.nodes.items():
        path = Path(MigrationWriter(migration).path)
        if path.is_relative_to(source):
            hashes[app].append(
                MigrationInfo.from_writer_info(app, migration_name, path)
            )
    return {app: sorted(migrations) for app, migrations in hashes.items()}


def get_app_migrations(app_migrations: list[MigrationInfo]) -> dict[str, MigrationInfo]:
    return {migration.name: migration for migration in app_migrations}


def save_migration_hashes() -> None:
    all_migrations = get_migrations_info()
    with settings.MIGRATION_HASHES_PATH.open("w") as file:
        for app in sorted(get_migrations_info()):
            for migration_info in all_migrations[app]:
                file.write(f"{migration_info}\n")


def get_saved_hashes() -> dict[str, list[MigrationInfo]]:
    hashes: dict[str, list[MigrationInfo]] = defaultdict(list)
    with settings.MIGRATION_HASHES_PATH.open() as file:
        for line in file.readlines():
            migration_info = MigrationInfo.from_lockfile(line.strip())
            hashes[migration_info.app].append(migration_info)
    return {app: sorted(migrations) for app, migrations in hashes.items()}


def validate_migration_names() -> bool:
    valid = True
    for app_name, migrations in get_saved_hashes().items():
        migration_prefixes = [migration.prefix for migration in migrations]
        for prefix in {a for a, b in pairwise(migration_prefixes) if a == b}:
            SGRString(
                f"❌ Two migrations in `{app_name}` have the same prefix `{prefix}`"
            ).print()
            valid = False
        for index, migration_prefix in enumerate(migration_prefixes, start=1):
            name = migrations[index - 1].name
            try:
                migration_order = int(migration_prefix)
            except ValueError:
                SGRString(
                    f"❌ Migration `{name}` in `{app_name}` has an invalid prefix `{migration_prefix}`"
                ).print()
                valid = False
                break
            if migration_order != index:
                SGRString(
                    f"❌ Migration `{name}` in `{app_name}` has an incorrect prefix `{migration_prefix}`"
                ).print()
                valid = False
                break

    return valid


def validate_migration_hashes() -> bool:
    actual_hashes = get_migrations_info()
    saved_hashes = get_saved_hashes()
    if actual_hashes != saved_hashes:
        for key in actual_hashes.keys() - saved_hashes.keys():
            SGRString(f"❌ New app `{key}` has been added").print()
        for key in saved_hashes.keys() - actual_hashes.keys():
            SGRString(f"❌ App `{key}` has been removed").print()
        for key in saved_hashes.keys() & actual_hashes.keys():
            actual_app_hashes = get_app_migrations(actual_hashes[key])
            saved_app_hashes = get_app_migrations(saved_hashes[key])
            for migration_name in actual_app_hashes.keys() - saved_app_hashes.keys():
                SGRString(f"❌ New migration `{migration_name}` has been added").print()
            for migration_name in saved_app_hashes.keys() - actual_app_hashes.keys():
                SGRString(f"❌ Migration `{migration_name}` has been removed").print()
            for migration_name in saved_app_hashes.keys() & actual_app_hashes.keys():
                actual_app_hash = actual_app_hashes[migration_name]
                saved_app_hash = saved_app_hashes[migration_name]
                if actual_app_hash.hash != saved_app_hash.hash:
                    SGRString(
                        f"❌ Hash for migration `{migration_name}` has changed"
                    ).print()
        return False

    return True
