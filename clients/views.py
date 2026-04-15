from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from accounts.mixins import ClientRequiredMixin
from clients.forms import AdPlacementForm, ClientContractForm, ClientProfileForm
from clients.models import AdPlacement, ClientContract, Service


class ServiceListView(ListView):
    model = Service
    template_name = "clients/service_list.html"
    context_object_name = "services"

    def get_queryset(self):
        return Service.objects.filter(is_active=True)


class ClientDashboardView(ClientRequiredMixin, TemplateView):
    template_name = "clients/client_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "profile": getattr(self.request.user, "client_profile", None),
                "contracts": ClientContract.objects.filter(client=self.request.user).prefetch_related("items__service")[:10],
                "placements": AdPlacement.objects.filter(client=self.request.user).select_related("contract", "poll")[:10],
                "services": Service.objects.filter(is_active=True)[:6],
                "profile_form": ClientProfileForm(instance=getattr(self.request.user, "client_profile", None)),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        profile = getattr(request.user, "client_profile", None)
        if profile is None:
            raise Http404
        form = ClientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль клиента обновлен.")
        else:
            messages.error(request, "Не удалось обновить профиль клиента.")
        return redirect("clients:dashboard")


class ContractCreateView(ClientRequiredMixin, CreateView):
    form_class = ClientContractForm
    template_name = "clients/contract_form.html"
    success_url = reverse_lazy("clients:dashboard")

    def get_initial(self):
        initial = super().get_initial()
        profile = getattr(self.request.user, "client_profile", None)
        if profile:
            initial["company_name"] = profile.company_name
            initial["contact_phone"] = profile.phone
        return initial

    def form_valid(self, form):
        self.object = form.save(user=self.request.user)
        messages.success(self.request, "Заявка на договор создана и отправлена на рассмотрение.")
        return redirect(self.object.get_absolute_url())


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = ClientContract
    template_name = "clients/contract_detail.html"
    context_object_name = "contract"

    def get_queryset(self):
        queryset = ClientContract.objects.select_related("client").prefetch_related("items__service", "placements")
        if self.request.user.is_staff or self.request.user.role == self.request.user.Roles.ADMIN:
            return queryset
        return queryset.filter(client=self.request.user)


class AdPlacementCreateView(ClientRequiredMixin, CreateView):
    model = AdPlacement
    form_class = AdPlacementForm
    template_name = "clients/ad_placement_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("clients:dashboard")

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Размещение сохранено.")
        return redirect(self.get_success_url())


class AdPlacementUpdateView(ClientRequiredMixin, UpdateView):
    model = AdPlacement
    form_class = AdPlacementForm
    template_name = "clients/ad_placement_form.html"

    def get_queryset(self):
        return AdPlacement.objects.filter(client=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("clients:dashboard")

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Размещение обновлено.")
        return redirect(self.get_success_url())
