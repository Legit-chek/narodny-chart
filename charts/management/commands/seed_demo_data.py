from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from charts.models import Artist, Genre, Poll, PollArtistOption, PollSongOption, Song
from clients.models import Service


class Command(BaseCommand):
    help = "Создает тестовые данные для Народного чарта."

    def handle(self, *args, **options):
        User = get_user_model()

        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "role": User.Roles.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not admin.check_password("12345678"):
            admin.set_password("12345678")
            admin.save()

        user, _ = User.objects.get_or_create(
            username="listener",
            defaults={"email": "listener@example.com", "role": User.Roles.USER},
        )
        if not user.has_usable_password():
            user.set_password("listener12345")
            user.save()

        client, _ = User.objects.get_or_create(
            username="brand_partner",
            defaults={"email": "client@example.com", "role": User.Roles.CLIENT},
        )
        if not client.has_usable_password():
            client.set_password("client12345")
            client.save()
        if hasattr(client, "client_profile"):
            client.client_profile.company_name = "Blue Note Media"
            client.client_profile.phone = "+7 900 123-45-67"
            client.client_profile.save()

        genres_data = [
            ("Поп", "pop", "Современная поп-музыка и радиохиты."),
            ("Рок", "rock", "Классический и альтернативный рок."),
            ("Хип-хоп", "hip-hop", "Ритмичные треки и сильный речитатив."),
        ]

        genre_objects = {}
        for name, slug, description in genres_data:
            genre, _ = Genre.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )
            genre_objects[slug] = genre

        artists_data = [
            ("Aurora Lights", "aurora-lights", "pop"),
            ("Silver Bridges", "silver-bridges", "pop"),
            ("Northern Echo", "northern-echo", "rock"),
            ("Stone Avenue", "stone-avenue", "rock"),
            ("Flow District", "flow-district", "hip-hop"),
            ("Verse Union", "verse-union", "hip-hop"),
        ]

        artist_objects = {}
        for name, slug, genre_slug in artists_data:
            artist, _ = Artist.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "genre": genre_objects[genre_slug],
                    "country": "Россия",
                    "bio": f"{name} участвует в главных чартах сезона.",
                },
            )
            artist_objects[slug] = artist

        songs_data = [
            ("Ночной эфир", "nochnoy-efir", "pop", "aurora-lights"),
            ("Свет витрин", "svet-vitrin", "pop", "silver-bridges"),
            ("Пульс мегаполиса", "puls-megapolisa", "pop", "aurora-lights"),
            ("Громче дождя", "gromche-dozhdya", "rock", "northern-echo"),
            ("Стальная волна", "stalnaya-volna", "rock", "stone-avenue"),
            ("Свобода внутри", "svoboda-vnutri", "rock", "northern-echo"),
            ("Район говорит", "rayon-govorit", "hip-hop", "flow-district"),
            ("Белый шум", "belyy-shum", "hip-hop", "verse-union"),
            ("Коды улиц", "kody-ulits", "hip-hop", "flow-district"),
        ]

        song_objects = {}
        for title, slug, genre_slug, artist_slug in songs_data:
            song, _ = Song.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "genre": genre_objects[genre_slug],
                    "artist": artist_objects[artist_slug],
                    "release_year": 2025,
                    "duration_seconds": 210,
                    "description": f"Трек {title} входит в сезонную подборку Народного чарта.",
                },
            )
            song_objects[slug] = song

        now = timezone.now()
        for genre_slug, genre in genre_objects.items():
            poll, _ = Poll.objects.get_or_create(
                slug=f"{genre_slug}-spring-vote",
                defaults={
                    "title": f"Весенний опрос: {genre.name}",
                    "genre": genre,
                    "description": f"Выберите лучших исполнителей и песни жанра {genre.name.lower()}.",
                    "starts_at": now - timedelta(days=2),
                    "ends_at": now + timedelta(days=10),
                    "vote_for_songs": True,
                    "vote_for_artists": True,
                    "max_song_choices": 3,
                    "max_artist_choices": 2,
                    "is_published": True,
                },
            )

            genre_songs = Song.objects.filter(genre=genre)[:3]
            genre_artists = Artist.objects.filter(genre=genre)[:2]
            for index, song in enumerate(genre_songs, start=1):
                PollSongOption.objects.get_or_create(
                    poll=poll,
                    song=song,
                    defaults={"display_order": index},
                )
            for index, artist in enumerate(genre_artists, start=1):
                PollArtistOption.objects.get_or_create(
                    poll=poll,
                    artist=artist,
                    defaults={"display_order": index},
                )

        services = [
            ("Баннер на главной", "banner-home", Decimal("25000.00")),
            ("Платное место в опросе", "featured-poll-slot", Decimal("18000.00")),
            ("Спонсорский пакет жанра", "genre-sponsor", Decimal("42000.00")),
        ]
        for name, slug, price in services:
            Service.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"Услуга «{name}» для продвижения музыкального контента.",
                    "price": price,
                    "conditions": "Срок размещения и детали согласовываются в договоре.",
                },
            )

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы."))
