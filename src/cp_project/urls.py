from django.urls import include, path

urlpatterns = [
    path("accounts/", include("cp_project.accounts.urls", namespace="accounts")),
]
