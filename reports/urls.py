from django.urls import path

from reports.views import (
    CreateRatingSnapshotView,
    PopularArtistsReportView,
    PopularSongsReportView,
    ReportsDashboardView,
    SalesReportView,
)

app_name = "reports"

urlpatterns = [
    path("", ReportsDashboardView.as_view(), name="dashboard"),
    path("sales/", SalesReportView.as_view(), name="sales"),
    path("songs/", PopularSongsReportView.as_view(), name="popular-songs"),
    path("artists/", PopularArtistsReportView.as_view(), name="popular-artists"),
    path("snapshots/create/", CreateRatingSnapshotView.as_view(), name="snapshot-create"),
]
