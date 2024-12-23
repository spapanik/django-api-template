from unittest import mock

import pytest
from django.core.management.base import CommandError
from django.core.management.commands.makemigrations import Command as MakeMigrations

from cp_project.lib.management.commands.checkmigrations import Command


@mock.patch.object(MakeMigrations, "handle")
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_hashes",
    new=mock.MagicMock(return_value=True),
)
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_names",
    new=mock.MagicMock(return_value=True),
)
def test_command_call_args(mock_super_handle: mock.Mock) -> None:
    Command().handle()
    expected_call_args = mock.call(
        check_changes=True,
        dry_run=True,
        interactive=False,
        merge=False,
        empty=False,
        name="",
        include_header=False,
        scriptable=False,
        update=False,
        verbosity=0,
    )
    assert mock_super_handle.call_count == 1
    assert mock_super_handle.call_args == expected_call_args


@mock.patch.object(MakeMigrations, "handle", new=mock.MagicMock(side_effect=SystemExit))
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_hashes",
    new=mock.MagicMock(return_value=True),
)
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_names",
    new=mock.MagicMock(return_value=True),
)
def test_command_parent_error() -> None:
    with pytest.raises(CommandError):
        Command().handle()


@mock.patch.object(MakeMigrations, "handle", new=mock.MagicMock())
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_hashes",
    new=mock.MagicMock(return_value=False),
)
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_names",
    new=mock.MagicMock(return_value=True),
)
def test_command_hashes_error() -> None:
    with pytest.raises(CommandError):
        Command().handle()


@mock.patch.object(MakeMigrations, "handle", new=mock.MagicMock())
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_hashes",
    new=mock.MagicMock(return_value=True),
)
@mock.patch(
    "cp_project.lib.management.commands.checkmigrations.validate_migration_names",
    new=mock.MagicMock(return_value=False),
)
def test_command_names_error() -> None:
    with pytest.raises(CommandError):
        Command().handle()
