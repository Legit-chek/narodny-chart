from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView

from accounts.forms import LoginForm, UserRegistrationForm
from charts.models import Poll, VoteDraftItem, VoteSubmission


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = UserRegistrationForm

    def form_valid(self, form):
        user = form.save()
        # Registration always creates a regular site user, so we log them in
        # through Django's standard model backend explicitly.
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, "Аккаунт создан. Добро пожаловать в Народный чарт.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.user.get_dashboard_url()


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm


class LogoutView(DjangoLogoutView):
    next_page = "core:home"
    http_method_names = ["get", "post", "head", "options"]

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/user_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update(
            {
                "submissions": VoteSubmission.objects.filter(user=user)
                .select_related("poll", "poll__genre")
                .prefetch_related("items__song", "items__artist")
                .order_by("-submitted_at")[:10],
                "draft_polls": Poll.objects.filter(draft_items__user=user).distinct()[:6],
                "recommended_polls": Poll.objects.active().exclude(vote_submissions__user=user)[:6],
                "draft_items_count": VoteDraftItem.objects.filter(user=user).count(),
            }
        )
        return context
