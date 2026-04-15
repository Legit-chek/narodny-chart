from django import forms

from charts.models import Genre, Poll, PollArtistOption, PollSongOption, VoteDraftItem
from core.forms import StyledFormMixin


class PollVoteForm(StyledFormMixin, forms.Form):
    song_choices = forms.ModelMultipleChoiceField(
        label="Песни",
        queryset=PollSongOption.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    artist_choices = forms.ModelMultipleChoiceField(
        label="Исполнители",
        queryset=PollArtistOption.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, poll: Poll, *args, **kwargs):
        self.poll = poll
        super().__init__(*args, **kwargs)
        self.fields["song_choices"].queryset = poll.song_options.select_related("song", "song__artist")
        self.fields["artist_choices"].queryset = poll.artist_options.select_related("artist")

        if not poll.vote_for_songs:
            self.fields.pop("song_choices")
        if not poll.vote_for_artists:
            self.fields.pop("artist_choices")

    def clean_song_choices(self):
        choices = self.cleaned_data.get("song_choices")
        if choices and len(choices) > self.poll.max_song_choices:
            raise forms.ValidationError(
                f"Можно выбрать не более {self.poll.max_song_choices} песен."
            )
        return choices

    def clean_artist_choices(self):
        choices = self.cleaned_data.get("artist_choices")
        if choices and len(choices) > self.poll.max_artist_choices:
            raise forms.ValidationError(
                f"Можно выбрать не более {self.poll.max_artist_choices} исполнителей."
            )
        return choices

    def clean(self):
        cleaned_data = super().clean()
        songs = cleaned_data.get("song_choices")
        artists = cleaned_data.get("artist_choices")

        if not songs and not artists:
            raise forms.ValidationError("Выберите хотя бы одну песню или одного исполнителя.")
        return cleaned_data


class PollFilterForm(StyledFormMixin, forms.Form):
    genre = forms.ModelChoiceField(
        label="Жанр",
        queryset=Genre.objects.all(),
        required=False,
        empty_label="Все жанры",
    )
    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=(
            ("", "Все"),
            ("active", "Активные"),
            ("upcoming", "Скоро стартуют"),
            ("finished", "Завершенные"),
        ),
    )


class RatingFilterForm(StyledFormMixin, forms.Form):
    genre = forms.ModelChoiceField(
        label="Жанр",
        queryset=Genre.objects.all(),
        required=False,
        empty_label="Все жанры",
    )


def draft_initial_data(user, poll):
    initial = {}
    draft_items = VoteDraftItem.objects.filter(user=user, poll=poll)
    song_ids = list(
        draft_items.filter(vote_type=VoteDraftItem.Types.SONG).values_list("song_id", flat=True)
    )
    artist_ids = list(
        draft_items.filter(vote_type=VoteDraftItem.Types.ARTIST).values_list("artist_id", flat=True)
    )
    if song_ids:
        initial["song_choices"] = poll.song_options.filter(song_id__in=song_ids)
    if artist_ids:
        initial["artist_choices"] = poll.artist_options.filter(artist_id__in=artist_ids)
    return initial
