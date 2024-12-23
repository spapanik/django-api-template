# cp_project

[![build][build_badge]][build_url]
[![lint][lint_badge]][lint_url]
[![tests][test_badge]][test_url]
[![license][licence_badge]][licence_url]
[![code style: black][black_badge]][black_url]
[![build automation: yam][yam_badge]][yam_url]
[![Lint: ruff][ruff_badge]][ruff_url]

## Installation (native)

### External tools

From external services running, postgresql to be up and running.

Because the server requires a specific python, that might not be the one
that the operating system uses, we recommend [pyenv] to be installed.
From python packages outside the virtualenv, the project also requires
[phosphorus] and [yamk] to be installed.

The external tools that are assumed to be installed are:

-   [postgres]
-   [yamk]
-   [pyenv]
-   [phosphorus]

We also assume that the postgres user has admin capabilities, and the user can use them non-interactively.

To install the project you need to create and activate a virtual environment.

### Creating the virtualenv

Assuming that you're already in the cloned directory:

```console
$ pyenv install 3.13
$ pyenv shell 3.13
$ python -m venv ~/.local/share/venv/cp_project
$ . ~/.local/share/venv/cp_project
```

If everything is present, the only thing that needs to be done is to use yam to install the project:

```console
$ yam install
```

## Usage

### Running the server

After a successful installation, try getting the server up by:

```console
$ yam runserver
```

There is hot reloading, and yam takes care of all the dependencies
issues. If there are unapplied migrations, you can apply them by:

```console
$ yam migrations
```

### Running the django shell

To run the local django shell, if you're inside the virtual environment,
you can just run:

```console
$ yam shell
```

### Formatting

To fix some simple linting errors, run:

```console
$ yam format
```

### Testing

To run the linting and the tests, run:

```console
$ yam lint
$ yam tests
```

### Updating

Updating the project can be done by yam:

```console
$ yam update
```

[lint_badge]: https://github.com/cp_author/cp_project/actions/workflows/lint.yml/badge.svg
[lint_url]: https://github.com/cp_author/cp_project/actions/workflows/lint.yml
[test_badge]: https://github.com/cp_author/cp_project/actions/workflows/tests.yml/badge.svg
[test_url]: https://github.com/cp_author/cp_project/actions/workflows/tests.yml
[black_badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black_url]: https://github.com/psf/black
[yam_badge]: https://img.shields.io/badge/build%20automation-yamk-success
[yam_url]: https://github.com/spapanik/yamk
[ruff_badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
[ruff_url]: https://github.com/charliermarsh/ruff
[postgres]: https://www.postgresql.org/download/
[yamk]: https://yamk.readthedocs.io/en/stable/installation.html
[pyenv]: https://github.com/pyenv/pyenv#installation
[phosphorus]: https://phosphorus.readthedocs.io/en/latest/
