from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import redirect
from django.views.generic import TemplateView, View

from accounts.mixins import AdminRequiredMixin
from charts.models import RatingSnapshot
from charts.services import generate_rating_snapshot, get_artist_ranking, get_song_ranking
from clients.models import ClientContract
from reports.forms import PopularityFilterForm, RatingSnapshotForm, SalesReportFilterForm


class ReportsDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "reports/admin_reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "sales_form": SalesReportFilterForm(self.request.GET or None),
                "popularity_form": PopularityFilterForm(self.request.GET or None),
                "snapshot_form": RatingSnapshotForm(),
                "latest_snapshots": RatingSnapshot.objects.select_related("genre", "created_by")[:8],
            }
        )
        return context


class SalesReportView(AdminRequiredMixin, TemplateView):
    template_name = "reports/sales_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = SalesReportFilterForm(self.request.GET or None)
        contracts = ClientContract.objects.select_related("client").prefetch_related("items__service")

        if form.is_valid():
            start_date = form.cleaned_data.get("start_date")
            end_date = form.cleaned_data.get("end_date")
            status = form.cleaned_data.get("status")

            if start_date:
                contracts = contracts.filter(created_at__date__gte=start_date)
            if end_date:
                contracts = contracts.filter(created_at__date__lte=end_date)
            if status:
                contracts = contracts.filter(status=status)

        context.update(
            {
                "filter_form": form,
                "contracts": contracts.order_by("-created_at"),
                "total_amount": contracts.aggregate(total=Sum("total_amount"))["total"] or 0,
            }
        )
        return context


class PopularSongsReportView(AdminRequiredMixin, TemplateView):
    template_name = "reports/popular_songs_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PopularityFilterForm(self.request.GET or None)
        genre = None
        if form.is_valid():
            genre = form.cleaned_data.get("genre")
        context.update(
            {
                "filter_form": form,
                "genre": genre,
                "items": get_song_ranking(genre=genre, limit=50),
            }
        )
        return context


class PopularArtistsReportView(AdminRequiredMixin, TemplateView):
    template_name = "reports/popular_artists_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PopularityFilterForm(self.request.GET or None)
        genre = None
        if form.is_valid():
            genre = form.cleaned_data.get("genre")
        context.update(
            {
                "filter_form": form,
                "genre": genre,
                "items": get_artist_ranking(genre=genre, limit=50),
            }
        )
        return context


class CreateRatingSnapshotView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = RatingSnapshotForm(request.POST)
        if form.is_valid():
            snapshot = generate_rating_snapshot(
                title=form.cleaned_data["title"],
                rating_type=form.cleaned_data["rating_type"],
                genre=form.cleaned_data.get("genre"),
                user=request.user,
            )
            messages.success(request, f"Снимок рейтинга «{snapshot.title}» сформирован.")
        else:
            messages.error(request, "Не удалось создать снимок рейтинга.")
        return redirect("reports:dashboard")
