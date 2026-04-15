from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        user = self.request.user
        return bool(user.is_authenticated and (user.is_superuser or user.role in self.allowed_roles))


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin",)


class ClientRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("client",)
