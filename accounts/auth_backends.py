from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOnlyBackend(ModelBackend):
    """Allows regular users to log in only by email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        email = (username or kwargs.get("email") or "").strip().lower()
        if not email or not password:
            return None

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class AdminBootstrapBackend(ModelBackend):
    """Allows a fixed local admin login and creates the admin account if needed."""

    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "12345678"
    ADMIN_EMAIL = "admin@narodny-chart.local"

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username != self.ADMIN_USERNAME or password != self.ADMIN_PASSWORD:
            return None

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=self.ADMIN_USERNAME,
            defaults={
                "email": self.ADMIN_EMAIL,
                "role": User.Roles.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        changed = created
        if user.email != self.ADMIN_EMAIL:
            user.email = self.ADMIN_EMAIL
            changed = True
        if user.role != user.Roles.ADMIN:
            user.role = user.Roles.ADMIN
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if not user.check_password(self.ADMIN_PASSWORD):
            user.set_password(self.ADMIN_PASSWORD)
            changed = True
        if changed:
            user.save()
        return user
