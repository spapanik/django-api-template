from cp_project.wsgi import application


def test_application() -> None:
    assert application is not None
