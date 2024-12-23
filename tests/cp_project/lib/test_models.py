import pytest

from cp_project.accounts.models import User


class TestBaseModel:
    """Tests for the base model.

    The BaseModel is an abstract model, so we will test it
    via the user model.
    """

    @property
    def emails(self) -> set[str]:
        return {
            "user1@gmail.com",
            "user2@gmail.com",
            "user3@gmail.com",
        }

    @pytest.fixture(autouse=True)
    def _create_users(self) -> None:
        users = [
            User(email=email, is_superuser=False, is_staff=False)
            for email in self.emails
        ]
        User.objects.bulk_create(users)

    @pytest.mark.django_db
    def test_bulk_create(self) -> None:
        assert User.objects.count() == 3

    @pytest.mark.django_db
    def test_random(self) -> None:
        assert User.objects.random().email in self.emails

    @pytest.mark.django_db
    def test_get_by_oid(self) -> None:
        user = User.objects.random()
        assert user == User.objects.get_by_oid(user.oid)

    @pytest.mark.django_db
    def test_filter_by_oid(self) -> None:
        user = User.objects.random()
        assert User.objects.filter_by_oid([user.oid]).count() == 1

    @pytest.mark.django_db
    def test_flat_values(self) -> None:
        assert set(User.objects.flat_values("email")) == self.emails

    @pytest.mark.django_db
    def test_update(self) -> None:
        User.objects.all().update(is_staff=True)
        assert User.objects.filter(is_staff=True).count() == 3

    @pytest.mark.django_db
    @pytest.mark.parametrize("fields", [["is_staff"], ["is_staff", "updated_at"]])
    def test_bulk_update(self, fields: list[str]) -> None:
        users = []
        for user in User.objects.all():
            user.is_staff = True
            users.append(user)

        updated_users = User.objects.bulk_update(users, fields=fields)
        assert updated_users == 3
        assert User.objects.filter(is_staff=True).count() == 3
