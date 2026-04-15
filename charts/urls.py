from django.urls import path

from charts.views import GenreListView, PollDetailView, PollListView, RatingsView

app_name = "charts"

urlpatterns = [
    path("genres/", GenreListView.as_view(), name="genre-list"),
    path("polls/", PollListView.as_view(), name="poll-list"),
    path("polls/<slug:slug>/", PollDetailView.as_view(), name="poll-detail"),
    path("ratings/", RatingsView.as_view(), name="ratings"),
]
