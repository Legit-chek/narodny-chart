from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Фото жанра", upload_to="genres/", blank=True)

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Artist(models.Model):
    name = models.CharField("Исполнитель", max_length=180)
    slug = models.SlugField("Slug", unique=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name="artists", verbose_name="Жанр")
    country = models.CharField("Страна", max_length=120, blank=True)
    bio = models.TextField("Описание", blank=True)
    image = models.ImageField("Фото исполнителя", upload_to="artists/", blank=True)
    image_url = models.URLField("Изображение", blank=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Исполнитель"
        verbose_name_plural = "Исполнители"
        ordering = ("name",)
        unique_together = ("name", "genre")

    def __str__(self) -> str:
        return self.name


class Song(models.Model):
    title = models.CharField("Название", max_length=180)
    slug = models.SlugField("Slug", unique=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name="songs", verbose_name="Жанр")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="songs", verbose_name="Исполнитель")
    duration_seconds = models.PositiveIntegerField("Длительность, сек", default=180)
    release_year = models.PositiveIntegerField("Год релиза", null=True, blank=True)
    cover = models.ImageField("Обложка", upload_to="songs/", blank=True)
    image_url = models.URLField("Обложка", blank=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Песня"
        verbose_name_plural = "Песни"
        ordering = ("title",)
        unique_together = ("title", "artist")

    def __str__(self) -> str:
        return f"{self.title} - {self.artist.name}"


class PollQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(is_published=True, starts_at__lte=now, ends_at__gte=now)

    def upcoming(self):
        return self.filter(is_published=True, starts_at__gt=timezone.now())

    def finished(self):
        return self.filter(is_published=True, ends_at__lt=timezone.now())


class Poll(models.Model):
    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug", unique=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name="polls", verbose_name="Жанр")
    description = models.TextField("Описание", blank=True)
    starts_at = models.DateTimeField("Начало")
    ends_at = models.DateTimeField("Окончание")
    vote_for_songs = models.BooleanField("Голосование за песни", default=True)
    vote_for_artists = models.BooleanField("Голосование за исполнителей", default=True)
    max_song_choices = models.PositiveIntegerField("Максимум песен", default=3)
    max_artist_choices = models.PositiveIntegerField("Максимум исполнителей", default=3)
    is_published = models.BooleanField("Опубликовано", default=True)

    objects = PollQuerySet.as_manager()

    class Meta:
        verbose_name = "Голосование"
        verbose_name_plural = "Голосования"
        ordering = ("-starts_at",)

    def clean(self):
        super().clean()
        if self.starts_at >= self.ends_at:
            raise ValidationError("Дата окончания должна быть позже даты начала.")
        if not self.vote_for_songs and not self.vote_for_artists:
            raise ValidationError("Нужно включить хотя бы один тип голосования.")

    def __str__(self) -> str:
        return self.title

    @property
    def is_active(self) -> bool:
        now = timezone.now()
        return self.is_published and self.starts_at <= now <= self.ends_at

    @property
    def is_finished(self) -> bool:
        return timezone.now() > self.ends_at

    def get_absolute_url(self):
        return reverse("charts:poll-detail", kwargs={"slug": self.slug})


class PollSongOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="song_options", verbose_name="Голосование")
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="poll_options", verbose_name="Песня")
    display_order = models.PositiveIntegerField("Порядок", default=0)
    is_promoted = models.BooleanField("Платное размещение", default=False)

    class Meta:
        verbose_name = "Опция песни"
        verbose_name_plural = "Опции песен"
        ordering = ("display_order", "song__title")
        unique_together = ("poll", "song")

    def __str__(self) -> str:
        return f"{self.song.title} - {self.song.artist.name}"


class PollArtistOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="artist_options", verbose_name="Голосование")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="poll_options", verbose_name="Исполнитель")
    display_order = models.PositiveIntegerField("Порядок", default=0)
    is_promoted = models.BooleanField("Платное размещение", default=False)

    class Meta:
        verbose_name = "Опция исполнителя"
        verbose_name_plural = "Опции исполнителей"
        ordering = ("display_order", "artist__name")
        unique_together = ("poll", "artist")

    def __str__(self) -> str:
        return self.artist.name


class VoteDraftItem(models.Model):
    class Types(models.TextChoices):
        SONG = "song", "Песня"
        ARTIST = "artist", "Исполнитель"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vote_draft_items",
        verbose_name="Пользователь",
    )
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="draft_items", verbose_name="Голосование")
    vote_type = models.CharField("Тип голоса", max_length=16, choices=Types.choices)
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="draft_votes",
        verbose_name="Песня",
        null=True,
        blank=True,
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name="draft_votes",
        verbose_name="Исполнитель",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Черновой голос"
        verbose_name_plural = "Черновые голоса"
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if self.vote_type == self.Types.SONG and not self.song:
            raise ValidationError("Для типа 'песня' нужно выбрать песню.")
        if self.vote_type == self.Types.ARTIST and not self.artist:
            raise ValidationError("Для типа 'исполнитель' нужно выбрать исполнителя.")
        if self.vote_type == self.Types.SONG and self.artist:
            raise ValidationError("Черновик песни не должен содержать исполнителя.")
        if self.vote_type == self.Types.ARTIST and self.song:
            raise ValidationError("Черновик исполнителя не должен содержать песню.")

    def __str__(self) -> str:
        item = self.song or self.artist
        return f"{self.user} / {self.poll}: {item}"


class VoteSubmission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vote_submissions",
        verbose_name="Пользователь",
    )
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="vote_submissions",
        verbose_name="Голосование",
    )
    submitted_at = models.DateTimeField("Отправлено", auto_now_add=True)

    class Meta:
        verbose_name = "Отправленный голос"
        verbose_name_plural = "Отправленные голоса"
        ordering = ("-submitted_at",)
        constraints = [
            models.UniqueConstraint(fields=("user", "poll"), name="unique_submission_per_user_and_poll"),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.poll}"


class VoteItem(models.Model):
    class Types(models.TextChoices):
        SONG = "song", "Песня"
        ARTIST = "artist", "Исполнитель"

    submission = models.ForeignKey(
        VoteSubmission,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Отправка",
    )
    vote_type = models.CharField("Тип голоса", max_length=16, choices=Types.choices)
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="vote_items",
        verbose_name="Песня",
        null=True,
        blank=True,
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name="vote_items",
        verbose_name="Исполнитель",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Элемент голоса"
        verbose_name_plural = "Элементы голосов"

    def clean(self):
        super().clean()
        if self.vote_type == self.Types.SONG and not self.song:
            raise ValidationError("Для голоса по песне нужна песня.")
        if self.vote_type == self.Types.ARTIST and not self.artist:
            raise ValidationError("Для голоса по исполнителю нужен исполнитель.")

    def __str__(self) -> str:
        item = self.song or self.artist
        return f"{self.submission}: {item}"


class RatingSnapshot(models.Model):
    class Types(models.TextChoices):
        SONG = "song", "Песни"
        ARTIST = "artist", "Исполнители"

    title = models.CharField("Название", max_length=255)
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        related_name="rating_snapshots",
        verbose_name="Жанр",
        null=True,
        blank=True,
    )
    poll = models.ForeignKey(
        Poll,
        on_delete=models.SET_NULL,
        related_name="rating_snapshots",
        verbose_name="Голосование",
        null=True,
        blank=True,
    )
    rating_type = models.CharField("Тип рейтинга", max_length=16, choices=Types.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_snapshots",
        verbose_name="Создал",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Снимок рейтинга"
        verbose_name_plural = "Снимки рейтингов"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class RatingEntry(models.Model):
    snapshot = models.ForeignKey(
        RatingSnapshot,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name="Снимок",
    )
    position = models.PositiveIntegerField("Позиция")
    total_votes = models.PositiveIntegerField("Количество голосов", default=0)
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="rating_entries",
        verbose_name="Песня",
        null=True,
        blank=True,
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name="rating_entries",
        verbose_name="Исполнитель",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Позиция рейтинга"
        verbose_name_plural = "Позиции рейтингов"
        ordering = ("position",)
        unique_together = ("snapshot", "position")

    def __str__(self) -> str:
        item = self.song or self.artist
        return f"{self.snapshot} #{self.position} {item}"
