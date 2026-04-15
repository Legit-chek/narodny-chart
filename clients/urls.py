from django.urls import path

from clients.views import (
    AdPlacementCreateView,
    AdPlacementUpdateView,
    ClientDashboardView,
    ContractCreateView,
    ContractDetailView,
    ServiceListView,
)

app_name = "clients"

urlpatterns = [
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("dashboard/", ClientDashboardView.as_view(), name="dashboard"),
    path("contracts/new/", ContractCreateView.as_view(), name="contract-create"),
    path("contracts/<int:pk>/", ContractDetailView.as_view(), name="contract-detail"),
    path("placements/new/", AdPlacementCreateView.as_view(), name="placement-create"),
    path("placements/<int:pk>/edit/", AdPlacementUpdateView.as_view(), name="placement-update"),
]
