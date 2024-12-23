from factorio import factories, fields

from cp_project.accounts.models import SignupToken, User


class UserFactory(factories.Factory[User]):
    password = fields.StringField()
    last_login = None
    is_superuser = fields.BooleanField()
    is_staff = fields.BooleanField()
    is_active = fields.BooleanField()
    date_joined = fields.DateTimeField()
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()
    email = fields.StringField()


class SignupTokenFactory(factories.Factory[SignupToken]):
    user = fields.FactoryField(UserFactory)
