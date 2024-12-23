from django.urls import path

from cp_project.accounts import views

app_name = "accounts"
urlpatterns = [
    path("", views.UserAPIView.as_view(), name="account"),
    path(
        "confirm-email/<int:token_id>",
        views.ConfirmEmailAPIView.as_view(),
        name="confirm-email",
    ),
    path("token/", views.ObtainTokenView.as_view(), name="obtain_token"),
    path("token/refresh", views.RefreshTokenView.as_view(), name="refresh_token"),
]
