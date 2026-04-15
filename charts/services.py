from django.db import transaction
from django.db.models import Count, Q

from charts.models import Artist, Genre, RatingEntry, RatingSnapshot, Song, VoteItem


def get_song_ranking(genre: Genre | None = None, limit: int = 10):
    queryset = Song.objects.filter(is_active=True).select_related("artist", "genre")
    if genre:
        queryset = queryset.filter(genre=genre)
    return queryset.annotate(
        total_votes=Count(
            "vote_items",
            filter=Q(vote_items__vote_type=VoteItem.Types.SONG),
        )
    ).order_by("-total_votes", "title")[:limit]


def get_artist_ranking(genre: Genre | None = None, limit: int = 10):
    queryset = Artist.objects.filter(is_active=True).select_related("genre")
    if genre:
        queryset = queryset.filter(genre=genre)
    return queryset.annotate(
        total_votes=Count(
            "vote_items",
            filter=Q(vote_items__vote_type=VoteItem.Types.ARTIST),
        )
    ).order_by("-total_votes", "name")[:limit]


@transaction.atomic
def generate_rating_snapshot(*, title: str, rating_type: str, genre=None, poll=None, user=None, limit: int = 20):
    snapshot = RatingSnapshot.objects.create(
        title=title,
        rating_type=rating_type,
        genre=genre,
        poll=poll,
        created_by=user,
    )

    ranking = get_song_ranking(genre=genre, limit=limit)
    if rating_type == RatingSnapshot.Types.ARTIST:
        ranking = get_artist_ranking(genre=genre, limit=limit)

    entries = []
    for position, item in enumerate(ranking, start=1):
        entries.append(
            RatingEntry(
                snapshot=snapshot,
                position=position,
                total_votes=getattr(item, "total_votes", 0),
                song=item if rating_type == RatingSnapshot.Types.SONG else None,
                artist=item if rating_type == RatingSnapshot.Types.ARTIST else None,
            )
        )
    RatingEntry.objects.bulk_create(entries)
    return snapshot
