from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from accounts.mixins import AdminRequiredMixin
from charts.models import Artist, Genre, Poll, Song, VoteSubmission
from charts.services import get_artist_ranking, get_song_ranking
from clients.models import AdPlacement, ClientContract, Service
from core.forms import (
    ArtistAdminForm,
    ContractAdminForm,
    GenreAdminForm,
    PlacementAdminForm,
    PollAdminForm,
    ServiceAdminForm,
    SiteAdminUserForm,
    SongAdminForm,
)


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured_genres = Genre.objects.order_by("name")[:4]
        top_by_genre = []

        for genre in featured_genres:
            top_by_genre.append(
                {
                    "genre": genre,
                    "songs": get_song_ranking(genre=genre, limit=3),
                    "artists": get_artist_ranking(genre=genre, limit=3),
                }
            )

        context.update(
            {
                "active_polls": Poll.objects.active()[:6],
                "popular_songs": get_song_ranking(limit=5),
                "popular_artists": get_artist_ranking(limit=5),
                "top_by_genre": top_by_genre,
            }
        )
        return context


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.role == request.user.Roles.ADMIN:
            return redirect("core:admin-dashboard")
        if request.user.role == request.user.Roles.CLIENT:
            return redirect("clients:dashboard")
        return redirect("accounts:dashboard")


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "core/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "users_count": self.request.user.__class__.objects.count(),
                "active_polls_count": Poll.objects.active().count(),
                "contracts_count": ClientContract.objects.count(),
                "placements_count": AdPlacement.objects.count(),
                "submissions_count": VoteSubmission.objects.count(),
                "genres": Genre.objects.annotate(song_count=Count("songs")).order_by("-song_count")[:6],
                "recent_contracts": ClientContract.objects.select_related("client").order_by("-created_at")[:5],
                "admin_reports_url": reverse("reports:dashboard"),
                "admin_sections": [
                    {"title": "Жанры", "description": "Каталог жанров и направлений.", "url": reverse("core:admin-genres")},
                    {"title": "Исполнители", "description": "Артисты и их карточки.", "url": reverse("core:admin-artists")},
                    {"title": "Песни", "description": "Музыкальный каталог треков.", "url": reverse("core:admin-songs")},
                    {"title": "Голосования", "description": "Опросы и состав вариантов.", "url": reverse("core:admin-polls")},
                    {"title": "Услуги", "description": "Прайс и клиентские пакеты.", "url": reverse("core:admin-services")},
                    {"title": "Пользователи", "description": "Роли и доступ внутри сайта.", "url": reverse("core:admin-users")},
                    {"title": "Договоры", "description": "Заявки клиентов и статусы.", "url": reverse("core:admin-contracts")},
                    {"title": "Размещения", "description": "Баннеры и места в опросах.", "url": reverse("core:admin-placements")},
                ],
            }
        )
        return context


class SiteAdminSectionMixin(AdminRequiredMixin):
    section_title = ""
    section_description = ""
    back_url = reverse_lazy("core:admin-dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "section_title": self.section_title,
                "section_description": self.section_description,
                "back_url": self.back_url,
            }
        )
        return context


class SiteAdminListView(SiteAdminSectionMixin, TemplateView):
    template_name = "core/admin_entity_list.html"
    create_url = None
    create_label = "Добавить"

    def get_rows(self):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "rows": self.get_rows(),
                "create_url": self.create_url,
                "create_label": self.create_label,
            }
        )
        return context


class SiteAdminFormView(SiteAdminSectionMixin):
    template_name = "core/admin_entity_form.html"
    submit_label = "Сохранить"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_label"] = self.submit_label
        context["back_url"] = self._resolve_back_url()
        return context

    def _resolve_back_url(self):
        success_url = getattr(self, "success_url", None)
        if success_url:
            return str(success_url)
        return str(self.back_url)


class SiteAdminDeleteView(SiteAdminSectionMixin, DeleteView):
    template_name = "core/admin_confirm_delete.html"
    object_label = "объект"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_label"] = self.object_label
        success_url = getattr(self, "success_url", None)
        context["back_url"] = str(success_url or self.back_url)
        return context


class AdminGenreListView(SiteAdminListView):
    section_title = "Жанры"
    section_description = "Управление музыкальными жанрами на сайте."
    create_url = reverse_lazy("core:admin-genre-create")

    def get_rows(self):
        genres = Genre.objects.annotate(song_total=Count("songs"), artist_total=Count("artists")).order_by("name")
        rows = []
        for genre in genres:
            rows.append(
                {
                    "title": genre.name,
                    "subtitle": genre.description or "Без описания",
                    "details": [f"Песен: {genre.song_total}", f"Исполнителей: {genre.artist_total}"],
                    "status": "Активный каталог",
                    "edit_url": reverse("core:admin-genre-edit", args=[genre.pk]),
                    "delete_url": reverse("core:admin-genre-delete", args=[genre.pk]),
                }
            )
        return rows


class AdminGenreCreateView(SiteAdminFormView, CreateView):
    form_class = GenreAdminForm
    template_name = "core/admin_entity_form.html"
    section_title = "Новый жанр"
    section_description = "Добавьте новый жанр в музыкальный каталог."
    success_url = reverse_lazy("core:admin-genres")


class AdminGenreUpdateView(SiteAdminFormView, UpdateView):
    model = Genre
    form_class = GenreAdminForm
    section_title = "Редактирование жанра"
    section_description = "Измените название, slug и описание жанра."
    success_url = reverse_lazy("core:admin-genres")


class AdminGenreDeleteView(SiteAdminDeleteView):
    model = Genre
    success_url = reverse_lazy("core:admin-genres")
    section_title = "Удаление жанра"
    section_description = "Это действие удалит жанр и связанные записи."
    object_label = "жанр"


class AdminArtistListView(SiteAdminListView):
    section_title = "Исполнители"
    section_description = "Управление артистами и их музыкальными профилями."
    create_url = reverse_lazy("core:admin-artist-create")

    def get_rows(self):
        artists = Artist.objects.select_related("genre").order_by("name")
        return [
            {
                "title": artist.name,
                "subtitle": artist.genre.name,
                "details": [artist.country or "Страна не указана", f"Песен: {artist.songs.count()}"],
                "status": "Активен" if artist.is_active else "Скрыт",
                "edit_url": reverse("core:admin-artist-edit", args=[artist.pk]),
                "delete_url": reverse("core:admin-artist-delete", args=[artist.pk]),
            }
            for artist in artists
        ]


class AdminArtistCreateView(SiteAdminFormView, CreateView):
    form_class = ArtistAdminForm
    section_title = "Новый исполнитель"
    section_description = "Создайте карточку исполнителя для каталога."
    success_url = reverse_lazy("core:admin-artists")


class AdminArtistUpdateView(SiteAdminFormView, UpdateView):
    model = Artist
    form_class = ArtistAdminForm
    section_title = "Редактирование исполнителя"
    section_description = "Обновите данные исполнителя."
    success_url = reverse_lazy("core:admin-artists")


class AdminArtistDeleteView(SiteAdminDeleteView):
    model = Artist
    success_url = reverse_lazy("core:admin-artists")
    section_title = "Удаление исполнителя"
    section_description = "Это действие удалит исполнителя и связанные песни."
    object_label = "исполнителя"


class AdminSongListView(SiteAdminListView):
    section_title = "Песни"
    section_description = "Управление каталогом песен и их связями."
    create_url = reverse_lazy("core:admin-song-create")

    def get_rows(self):
        songs = Song.objects.select_related("artist", "genre").order_by("title")
        return [
            {
                "title": song.title,
                "subtitle": f"{song.artist.name} · {song.genre.name}",
                "details": [
                    f"Год: {song.release_year or 'не указан'}",
                    f"Голосов: {song.vote_items.count()}",
                ],
                "status": "Активна" if song.is_active else "Скрыта",
                "edit_url": reverse("core:admin-song-edit", args=[song.pk]),
                "delete_url": reverse("core:admin-song-delete", args=[song.pk]),
            }
            for song in songs
        ]


class AdminSongCreateView(SiteAdminFormView, CreateView):
    form_class = SongAdminForm
    section_title = "Новая песня"
    section_description = "Добавьте новый трек в каталог."
    success_url = reverse_lazy("core:admin-songs")


class AdminSongUpdateView(SiteAdminFormView, UpdateView):
    model = Song
    form_class = SongAdminForm
    section_title = "Редактирование песни"
    section_description = "Обновите данные трека."
    success_url = reverse_lazy("core:admin-songs")


class AdminSongDeleteView(SiteAdminDeleteView):
    model = Song
    success_url = reverse_lazy("core:admin-songs")
    section_title = "Удаление песни"
    section_description = "Это действие удалит песню из каталога."
    object_label = "песню"


class AdminPollListView(SiteAdminListView):
    section_title = "Голосования"
    section_description = "Создание и настройка опросов прямо на сайте."
    create_url = reverse_lazy("core:admin-poll-create")

    def get_rows(self):
        polls = Poll.objects.select_related("genre").annotate(
            song_total=Count("song_options"),
            artist_total=Count("artist_options"),
        ).order_by("-starts_at")
        rows = []
        for poll in polls:
            if poll.is_active:
                status = "Активно"
            elif poll.is_finished:
                status = "Завершено"
            else:
                status = "Запланировано"
            rows.append(
                {
                    "title": poll.title,
                    "subtitle": poll.genre.name,
                    "details": [
                        f"{poll.starts_at:%d.%m.%Y %H:%M} - {poll.ends_at:%d.%m.%Y %H:%M}",
                        f"Песен: {poll.song_total}, исполнителей: {poll.artist_total}",
                    ],
                    "status": status,
                    "edit_url": reverse("core:admin-poll-edit", args=[poll.pk]),
                    "delete_url": reverse("core:admin-poll-delete", args=[poll.pk]),
                }
            )
        return rows


class AdminPollCreateView(SiteAdminFormView, CreateView):
    form_class = PollAdminForm
    section_title = "Новое голосование"
    section_description = "Создайте опрос и сразу выберите песни и исполнителей."
    success_url = reverse_lazy("core:admin-polls")


class AdminPollUpdateView(SiteAdminFormView, UpdateView):
    model = Poll
    form_class = PollAdminForm
    section_title = "Редактирование голосования"
    section_description = "Меняйте период, правила и состав вариантов."
    success_url = reverse_lazy("core:admin-polls")


class AdminPollDeleteView(SiteAdminDeleteView):
    model = Poll
    success_url = reverse_lazy("core:admin-polls")
    section_title = "Удаление голосования"
    section_description = "Это действие удалит голосование и его варианты."
    object_label = "голосование"


class AdminServiceListView(SiteAdminListView):
    section_title = "Услуги"
    section_description = "Прайс-лист клиентских услуг и рекламных пакетов."
    create_url = reverse_lazy("core:admin-service-create")

    def get_rows(self):
        services = Service.objects.order_by("name")
        return [
            {
                "title": service.name,
                "subtitle": service.description,
                "details": [f"Цена: {service.price} ₽"],
                "status": "Активна" if service.is_active else "Скрыта",
                "edit_url": reverse("core:admin-service-edit", args=[service.pk]),
                "delete_url": reverse("core:admin-service-delete", args=[service.pk]),
            }
            for service in services
        ]


class AdminServiceCreateView(SiteAdminFormView, CreateView):
    form_class = ServiceAdminForm
    section_title = "Новая услуга"
    section_description = "Добавьте услугу для клиентского кабинета."
    success_url = reverse_lazy("core:admin-services")


class AdminServiceUpdateView(SiteAdminFormView, UpdateView):
    model = Service
    form_class = ServiceAdminForm
    section_title = "Редактирование услуги"
    section_description = "Обновите цену и условия размещения."
    success_url = reverse_lazy("core:admin-services")


class AdminServiceDeleteView(SiteAdminDeleteView):
    model = Service
    success_url = reverse_lazy("core:admin-services")
    section_title = "Удаление услуги"
    section_description = "Удалите услугу из прайс-листа."
    object_label = "услугу"


class AdminUserListView(SiteAdminListView):
    section_title = "Пользователи"
    section_description = "Роли и статусы учетных записей внутри сайта."

    def get_rows(self):
        User = get_user_model()
        users = User.objects.order_by("username")
        return [
            {
                "title": user.username,
                "subtitle": user.email,
                "details": [
                    f"Роль: {user.get_role_display()}",
                    user.get_full_name() or "Имя не заполнено",
                ],
                "status": "Активен" if user.is_active else "Отключен",
                "edit_url": reverse("core:admin-user-edit", args=[user.pk]),
            }
            for user in users
        ]


class AdminUserUpdateView(SiteAdminFormView, UpdateView):
    model = get_user_model()
    form_class = SiteAdminUserForm
    section_title = "Редактирование пользователя"
    section_description = "Измените роль, контактные данные и статус доступа."
    success_url = reverse_lazy("core:admin-users")


class AdminContractListView(SiteAdminListView):
    section_title = "Договоры"
    section_description = "Заявки клиентов и смена статусов обработки."

    def get_rows(self):
        contracts = ClientContract.objects.select_related("client").order_by("-created_at")
        return [
            {
                "title": contract.title,
                "subtitle": contract.company_name,
                "details": [
                    f"Клиент: {contract.client.username}",
                    f"Сумма: {contract.total_amount} ₽",
                ],
                "status": contract.get_status_display(),
                "view_url": reverse("clients:contract-detail", args=[contract.pk]),
                "edit_url": reverse("core:admin-contract-edit", args=[contract.pk]),
            }
            for contract in contracts
        ]


class AdminContractUpdateView(SiteAdminFormView, UpdateView):
    model = ClientContract
    form_class = ContractAdminForm
    section_title = "Редактирование договора"
    section_description = "Управляйте статусом заявки и контактными данными."
    success_url = reverse_lazy("core:admin-contracts")


class AdminPlacementListView(SiteAdminListView):
    section_title = "Размещения"
    section_description = "Баннеры, спонсорские блоки и платные места в опросах."
    create_url = reverse_lazy("core:admin-placement-create")

    def get_rows(self):
        placements = AdPlacement.objects.select_related("client", "contract", "poll").order_by("-id")
        rows = []
        for placement in placements:
            details = [f"Клиент: {placement.client.username}", f"Договор: {placement.contract.title}"]
            if placement.poll:
                details.append(f"Опрос: {placement.poll.title}")
            rows.append(
                {
                    "title": placement.title,
                    "subtitle": placement.get_placement_type_display(),
                    "details": details,
                    "status": placement.get_status_display(),
                    "edit_url": reverse("core:admin-placement-edit", args=[placement.pk]),
                }
            )
        return rows


class AdminPlacementCreateView(SiteAdminFormView, CreateView):
    form_class = PlacementAdminForm
    section_title = "Новое размещение"
    section_description = "Создайте рекламное размещение прямо из админ-панели сайта."
    success_url = reverse_lazy("core:admin-placements")


class AdminPlacementUpdateView(SiteAdminFormView, UpdateView):
    model = AdPlacement
    form_class = PlacementAdminForm
    section_title = "Редактирование размещения"
    section_description = "Измените баннер, ссылку, статус и привязку к договору."
    success_url = reverse_lazy("core:admin-placements")
