from django.core.management.base import CommandError
from django.core.management.commands.makemigrations import Command as MakeMigrations

from cp_project.lib.utils import validate_migration_hashes, validate_migration_names


class Command(MakeMigrations):
    help = "Check if migrations are as expected"

    @staticmethod
    def update_options(options: dict[str, object]) -> None:
        options["check_changes"] = True
        options["dry_run"] = True
        options["interactive"] = False
        options["merge"] = False
        options["empty"] = False
        options["name"] = ""
        options["include_header"] = False
        options["scriptable"] = False
        options["update"] = False
        options["verbosity"] = 0

    def handle(self, *args: object, **options: object) -> None:
        self.update_options(options)

        try:
            super().handle(*args, **options)
        except SystemExit as exc:
            msg = "There are model changes not reflected in migrations"
            raise CommandError(msg) from exc
        self.stdout.write("✔️ All changes are reflected in migrations")

        if not validate_migration_hashes():
            msg = "Migration hashes have changed"
            raise CommandError(msg)
        self.stdout.write("✔️ All hashes are as expected")

        if not validate_migration_names():
            msg = "Migration names are not as expected"
            raise CommandError(msg)
        self.stdout.write("✔️ All migration names are as expected")
