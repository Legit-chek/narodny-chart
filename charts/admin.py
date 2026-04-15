from django.contrib import admin

from charts.models import (
    Artist,
    Genre,
    Poll,
    PollArtistOption,
    PollSongOption,
    RatingEntry,
    RatingSnapshot,
    Song,
    VoteDraftItem,
    VoteItem,
    VoteSubmission,
)


class PollSongOptionInline(admin.TabularInline):
    model = PollSongOption
    extra = 1


class PollArtistOptionInline(admin.TabularInline):
    model = PollArtistOption
    extra = 1


class RatingEntryInline(admin.TabularInline):
    model = RatingEntry
    extra = 0


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "genre", "country", "is_active")
    list_filter = ("genre", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "genre", "release_year", "is_active")
    list_filter = ("genre", "is_active")
    search_fields = ("title", "artist__name")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "starts_at", "ends_at", "is_published")
    list_filter = ("genre", "is_published", "vote_for_songs", "vote_for_artists")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PollSongOptionInline, PollArtistOptionInline]


@admin.register(VoteSubmission)
class VoteSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "poll", "submitted_at")
    list_filter = ("poll", "submitted_at")
    search_fields = ("user__username", "poll__title")


@admin.register(VoteItem)
class VoteItemAdmin(admin.ModelAdmin):
    list_display = ("submission", "vote_type", "song", "artist")
    list_filter = ("vote_type",)


@admin.register(VoteDraftItem)
class VoteDraftItemAdmin(admin.ModelAdmin):
    list_display = ("user", "poll", "vote_type", "song", "artist", "created_at")
    list_filter = ("vote_type", "poll")


@admin.register(RatingSnapshot)
class RatingSnapshotAdmin(admin.ModelAdmin):
    list_display = ("title", "rating_type", "genre", "poll", "created_at")
    list_filter = ("rating_type", "genre")
    inlines = [RatingEntryInline]
