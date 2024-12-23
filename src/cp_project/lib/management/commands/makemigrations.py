from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.commands.makemigrations import Command as MakeMigrations

from cp_project.lib.utils import format_app_migrations, save_migration_hashes

if TYPE_CHECKING:
    from django.db.migrations import Migration


class Command(MakeMigrations):
    @staticmethod
    def update_options(options: dict[str, object]) -> None:
        options["include_header"] = False

    def handle(self, *args: object, **options: object) -> None:
        self.update_options(options)

        super().handle(*args, **options)
        if self.dry_run:
            return

        save_migration_hashes()

    def write_migration_files(
        self,
        changes: dict[str, list[Migration]],
        update_previous_migration_paths: dict[str, str] | None = None,
    ) -> None:
        super().write_migration_files(changes, update_previous_migration_paths)
        if self.dry_run:
            return

        self.format_migrations(changes)

    def format_migrations(self, changes: dict[str, list[Migration]]) -> None:
        for app_label, app_migrations in changes.items():
            format_app_migrations(app_label, app_migrations)
