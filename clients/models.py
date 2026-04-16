from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class Service(models.Model):
    name = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Описание")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    conditions = models.TextField("Условия", blank=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ("price", "name")

    def __str__(self) -> str:
        return self.name


class ClientContract(models.Model):
    class Statuses(models.TextChoices):
        NEW = "new", "Новый"
        REVIEW = "review", "На рассмотрении"
        APPROVED = "approved", "Подтвержден"
        DECLINED = "declined", "Отклонен"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_contracts",
        verbose_name="Клиент",
    )
    title = models.CharField("Название заявки", max_length=255)
    company_name = models.CharField("Компания", max_length=255)
    contact_phone = models.CharField("Телефон", max_length=32)
    description = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=16, choices=Statuses.choices, default=Statuses.NEW)
    total_amount = models.DecimalField("Итоговая сумма", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.company_name} - {self.title}"

    def get_absolute_url(self):
        return reverse("clients:contract-detail", kwargs={"pk": self.pk})

    def recalculate_total(self):
        total = sum((item.subtotal for item in self.items.all()), Decimal("0.00"))
        self.total_amount = total
        self.save(update_fields=["total_amount", "updated_at"])


class ContractItem(models.Model):
    contract = models.ForeignKey(
        ClientContract,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Договор",
    )
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="contract_items", verbose_name="Услуга")
    quantity = models.PositiveIntegerField("Количество", default=1)
    unit_price = models.DecimalField("Цена за единицу", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Позиция договора"
        verbose_name_plural = "Позиции договора"
        unique_together = ("contract", "service")

    def __str__(self) -> str:
        return f"{self.contract}: {self.service}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class AdPlacement(models.Model):
    class Types(models.TextChoices):
        BANNER = "banner", "Баннер"
        POLL_SPOT = "poll_spot", "Платное место в опросе"
        SPONSOR = "sponsor", "Спонсорский блок"

    class Statuses(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ACTIVE = "active", "Активно"
        PAUSED = "paused", "Приостановлено"
        FINISHED = "finished", "Завершено"

    contract = models.ForeignKey(
        ClientContract,
        on_delete=models.CASCADE,
        related_name="placements",
        verbose_name="Договор",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ad_placements",
        verbose_name="Клиент",
    )
    poll = models.ForeignKey(
        "charts.Poll",
        on_delete=models.SET_NULL,
        related_name="placements",
        verbose_name="Голосование",
        null=True,
        blank=True,
    )
    placement_type = models.CharField("Тип размещения", max_length=16, choices=Types.choices)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Файл баннера", upload_to="placements/", blank=True)
    image_url = models.URLField("URL баннера", blank=True)
    target_url = models.URLField("Ссылка перехода", blank=True)
    status = models.CharField("Статус", max_length=16, choices=Statuses.choices, default=Statuses.DRAFT)
    starts_at = models.DateTimeField("Старт", null=True, blank=True)
    ends_at = models.DateTimeField("Окончание", null=True, blank=True)

    class Meta:
        verbose_name = "Рекламное размещение"
        verbose_name_plural = "Рекламные размещения"
        ordering = ("-id",)

    def __str__(self) -> str:
        return self.title
