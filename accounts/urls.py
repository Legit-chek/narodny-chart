from django.urls import path

from accounts.views import LoginView, LogoutView, RegisterView, UserDashboardView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", UserDashboardView.as_view(), name="dashboard"),
]
