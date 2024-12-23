from unittest import mock

from django.core.management.commands.makemigrations import Command as MakeMigrations

from cp_project.lib.management.commands.makemigrations import Command


@mock.patch.object(MakeMigrations, "handle")
@mock.patch("cp_project.lib.management.commands.makemigrations.save_migration_hashes")
def test_command_call_args_dry_run(
    mock_save: mock.Mock, mock_super_handle: mock.Mock
) -> None:
    command = Command()
    command.dry_run = True
    command.handle()
    expected_call_args = mock.call(include_header=False)
    assert mock_super_handle.call_count == 1
    assert mock_super_handle.call_args == expected_call_args
    assert mock_save.call_count == 0


@mock.patch.object(MakeMigrations, "handle")
@mock.patch("cp_project.lib.management.commands.makemigrations.save_migration_hashes")
def test_command_call_args_real_run(
    mock_save: mock.Mock, mock_super_handle: mock.Mock
) -> None:
    command = Command()
    command.dry_run = False
    command.handle()
    expected_call_args = mock.call(include_header=False)
    assert mock_super_handle.call_count == 1
    assert mock_super_handle.call_args == expected_call_args
    assert mock_save.call_count == 1


@mock.patch("cp_project.lib.management.commands.makemigrations.format_app_migrations")
def test_command_formatter(mock_format: mock.Mock) -> None:
    first_mock = mock.MagicMock(name="first")
    second_mock = mock.MagicMock(name="second")
    Command().format_migrations({"first": first_mock, "second": second_mock})
    excepted_call_args_list = [
        mock.call("first", first_mock),
        mock.call("second", second_mock),
    ]
    assert mock_format.call_count == 2
    assert mock_format.call_args_list == excepted_call_args_list


@mock.patch.object(MakeMigrations, "write_migration_files")
@mock.patch.object(Command, "format_migrations")
def test_command_writer_dry_run(
    mock_format: mock.Mock, mock_write: mock.MagicMock
) -> None:
    command = Command()
    command.dry_run = True
    first_mock = mock.MagicMock(name="first")
    command.write_migration_files({"first": first_mock})
    assert mock_write.call_count == 1
    assert mock_write.call_args == mock.call({"first": first_mock}, None)
    assert mock_format.call_count == 0


@mock.patch.object(MakeMigrations, "write_migration_files")
@mock.patch.object(Command, "format_migrations")
def test_command_writer_real_run(
    mock_format: mock.Mock, mock_write: mock.MagicMock
) -> None:
    command = Command()
    command.dry_run = False
    first_mock = mock.MagicMock(name="first")
    command.write_migration_files({"first": first_mock})
    assert mock_write.call_count == 1
    assert mock_write.call_args == mock.call({"first": first_mock}, None)
    assert mock_format.call_count == 1
    assert mock_format.call_args == mock.call({"first": first_mock})
