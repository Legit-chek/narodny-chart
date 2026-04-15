from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, TemplateView, View

from charts.forms import PollFilterForm, PollVoteForm, RatingFilterForm, draft_initial_data
from charts.models import (
    Genre,
    Poll,
    VoteDraftItem,
    VoteItem,
    VoteSubmission,
)
from charts.services import get_artist_ranking, get_song_ranking


class GenreListView(ListView):
    model = Genre
    template_name = "charts/genre_list.html"
    context_object_name = "genres"


class PollListView(ListView):
    model = Poll
    template_name = "charts/poll_list.html"
    context_object_name = "polls"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Poll.objects.select_related("genre")
            .prefetch_related("song_options__song", "artist_options__artist")
            .order_by("-starts_at")
        )
        self.filter_form = PollFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            genre = self.filter_form.cleaned_data.get("genre")
            status = self.filter_form.cleaned_data.get("status")
            if genre:
                queryset = queryset.filter(genre=genre)
            if status == "active":
                queryset = queryset.active()
            elif status == "upcoming":
                queryset = queryset.upcoming()
            elif status == "finished":
                queryset = queryset.finished()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class PollDetailView(LoginRequiredMixin, View):
    template_name = "charts/poll_detail.html"

    def get_poll(self):
        return get_object_or_404(
            Poll.objects.select_related("genre").prefetch_related(
                "song_options__song__artist", "artist_options__artist"
            ),
            slug=self.kwargs["slug"],
        )

    def get(self, request, *args, **kwargs):
        poll = self.get_poll()
        submission = VoteSubmission.objects.filter(user=request.user, poll=poll).first()
        initial = draft_initial_data(request.user, poll)
        form = PollVoteForm(poll, initial=initial)
        return self.render_response(poll, form, submission)

    def post(self, request, *args, **kwargs):
        poll = self.get_poll()
        submission = VoteSubmission.objects.filter(user=request.user, poll=poll).first()
        if submission:
            messages.info(request, "Вы уже отправили финальный голос по этому голосованию.")
            return redirect(poll.get_absolute_url())

        if not poll.is_active:
            messages.warning(request, "Это голосование сейчас недоступно для отправки.")
            return redirect(poll.get_absolute_url())

        form = PollVoteForm(poll, request.POST)
        if not form.is_valid():
            return self.render_response(poll, form, submission)

        action = request.POST.get("action")
        song_options = form.cleaned_data.get("song_choices", [])
        artist_options = form.cleaned_data.get("artist_choices", [])

        self._save_draft(request.user, poll, song_options, artist_options)
        if action == "save":
            messages.success(request, "Черновик голосов сохранен.")
            return redirect(poll.get_absolute_url())

        with transaction.atomic():
            submission = VoteSubmission.objects.create(user=request.user, poll=poll)
            vote_items = [
                VoteItem(
                    submission=submission,
                    vote_type=VoteItem.Types.SONG,
                    song=option.song,
                )
                for option in song_options
            ]
            vote_items.extend(
                VoteItem(
                    submission=submission,
                    vote_type=VoteItem.Types.ARTIST,
                    artist=option.artist,
                )
                for option in artist_options
            )
            VoteItem.objects.bulk_create(vote_items)
            VoteDraftItem.objects.filter(user=request.user, poll=poll).delete()

        messages.success(request, "Ваш голос отправлен в общий рейтинг.")
        return redirect(poll.get_absolute_url())

    def _save_draft(self, user, poll, song_options, artist_options):
        VoteDraftItem.objects.filter(user=user, poll=poll).delete()
        draft_items = [
            VoteDraftItem(user=user, poll=poll, vote_type=VoteDraftItem.Types.SONG, song=option.song)
            for option in song_options
        ]
        draft_items.extend(
            VoteDraftItem(user=user, poll=poll, vote_type=VoteDraftItem.Types.ARTIST, artist=option.artist)
            for option in artist_options
        )
        VoteDraftItem.objects.bulk_create(draft_items)

    def render_response(self, poll, form, submission):
        submission_items = []
        draft_song_items = []
        draft_artist_items = []
        if submission:
            submission_items = submission.items.select_related("song__artist", "artist")
        else:
            draft_items = VoteDraftItem.objects.filter(user=self.request.user, poll=poll).select_related(
                "song__artist", "artist"
            )
            draft_song_items = [item.song for item in draft_items if item.song_id]
            draft_artist_items = [item.artist for item in draft_items if item.artist_id]
        from django.shortcuts import render

        return render(
            self.request,
            self.template_name,
            {
                "poll": poll,
                "form": form,
                "submission": submission,
                "submission_items": submission_items,
                "draft_song_items": draft_song_items,
                "draft_artist_items": draft_artist_items,
            },
        )


class RatingsView(TemplateView):
    template_name = "charts/ratings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = RatingFilterForm(self.request.GET or None)
        genre = None
        if form.is_valid():
            genre = form.cleaned_data.get("genre")

        context.update(
            {
                "filter_form": form,
                "selected_genre": genre,
                "song_ratings": get_song_ranking(genre=genre, limit=20),
                "artist_ratings": get_artist_ranking(genre=genre, limit=20),
            }
        )
        return context
