from django import forms
from django.contrib.auth import get_user_model

from accounts.models import ClientProfile
from charts.models import Artist, Genre, Poll, PollArtistOption, PollSongOption, Song
from clients.models import AdPlacement, ClientContract, Service


class StyledFormMixin:
    """Applies consistent widget classes for project forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing_classes = widget.attrs.get("class", "")

            if isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs["class"] = f"{existing_classes} checkbox-list".strip()
                continue

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{existing_classes} form-check-input".strip()
                continue

            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = f"{existing_classes} form-select".strip()
                continue

            widget.attrs["class"] = f"{existing_classes} form-control".strip()


class GenreAdminForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Genre
        fields = ("name", "slug", "description")


class ArtistAdminForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Artist
        fields = ("name", "slug", "genre", "country", "bio", "image_url", "is_active")


class SongAdminForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Song
        fields = (
            "title",
            "slug",
            "genre",
            "artist",
            "duration_seconds",
            "release_year",
            "image_url",
            "description",
            "is_active",
        )

    def clean(self):
        cleaned_data = super().clean()
        artist = cleaned_data.get("artist")
        genre = cleaned_data.get("genre")
        if artist and genre and artist.genre_id != genre.id:
            self.add_error("artist", "Исполнитель должен относиться к выбранному жанру.")
        return cleaned_data


class PollAdminForm(StyledFormMixin, forms.ModelForm):
    song_candidates = forms.ModelMultipleChoiceField(
        label="Песни для голосования",
        queryset=Song.objects.none(),
        required=False,
    )
    artist_candidates = forms.ModelMultipleChoiceField(
        label="Исполнители для голосования",
        queryset=Artist.objects.none(),
        required=False,
    )

    class Meta:
        model = Poll
        fields = (
            "title",
            "slug",
            "genre",
            "description",
            "starts_at",
            "ends_at",
            "vote_for_songs",
            "vote_for_artists",
            "max_song_choices",
            "max_artist_choices",
            "is_published",
        )
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        genre_id = None
        if self.is_bound:
            genre_id = self.data.get("genre") or None
        elif self.instance.pk:
            genre_id = self.instance.genre_id

        songs_qs = Song.objects.select_related("artist", "genre").order_by("title")
        artists_qs = Artist.objects.select_related("genre").order_by("name")
        if genre_id:
            songs_qs = songs_qs.filter(genre_id=genre_id)
            artists_qs = artists_qs.filter(genre_id=genre_id)

        self.fields["song_candidates"].queryset = songs_qs
        self.fields["artist_candidates"].queryset = artists_qs
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]

        if self.instance.pk:
            self.fields["song_candidates"].initial = self.instance.song_options.values_list("song_id", flat=True)
            self.fields["artist_candidates"].initial = self.instance.artist_options.values_list("artist_id", flat=True)

    def clean(self):
        cleaned_data = super().clean()
        genre = cleaned_data.get("genre")
        songs = cleaned_data.get("song_candidates")
        artists = cleaned_data.get("artist_candidates")

        if genre and songs:
            wrong_songs = [song.title for song in songs if song.genre_id != genre.id]
            if wrong_songs:
                self.add_error("song_candidates", "Все песни должны относиться к выбранному жанру.")
        if genre and artists:
            wrong_artists = [artist.name for artist in artists if artist.genre_id != genre.id]
            if wrong_artists:
                self.add_error("artist_candidates", "Все исполнители должны относиться к выбранному жанру.")
        return cleaned_data

    def save(self, commit=True):
        poll = super().save(commit=commit)
        if commit:
            self._sync_options(poll)
        return poll

    def _sync_options(self, poll):
        selected_songs = list(self.cleaned_data.get("song_candidates", []))
        selected_artists = list(self.cleaned_data.get("artist_candidates", []))

        existing_song_options = {option.song_id: option for option in poll.song_options.all()}
        existing_artist_options = {option.artist_id: option for option in poll.artist_options.all()}

        PollSongOption.objects.filter(poll=poll).exclude(song__in=selected_songs).delete()
        PollArtistOption.objects.filter(poll=poll).exclude(artist__in=selected_artists).delete()

        for index, song in enumerate(selected_songs, start=1):
            option = existing_song_options.get(song.id)
            if option:
                option.display_order = index
                option.save(update_fields=["display_order"])
            else:
                PollSongOption.objects.create(poll=poll, song=song, display_order=index)

        for index, artist in enumerate(selected_artists, start=1):
            option = existing_artist_options.get(artist.id)
            if option:
                option.display_order = index
                option.save(update_fields=["display_order"])
            else:
                PollArtistOption.objects.create(poll=poll, artist=artist, display_order=index)


class ServiceAdminForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "slug", "description", "price", "conditions", "is_active")


class SiteAdminUserForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "role", "is_active")

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.is_superuser:
            user.is_staff = user.role == user.Roles.ADMIN
        if commit:
            user.save()
            if user.role == user.Roles.CLIENT:
                ClientProfile.objects.get_or_create(user=user)
        return user


class ContractAdminForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClientContract
        fields = ("client", "title", "company_name", "contact_phone", "description", "status")


class PlacementAdminForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AdPlacement
        fields = (
            "client",
            "contract",
            "poll",
            "placement_type",
            "title",
            "description",
            "image_url",
            "target_url",
            "status",
            "starts_at",
            "ends_at",
        )
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned_data = super().clean()
        client = cleaned_data.get("client")
        contract = cleaned_data.get("contract")
        if client and contract and contract.client_id != client.id:
            self.add_error("contract", "Договор должен принадлежать выбранному клиенту.")
        return cleaned_data
