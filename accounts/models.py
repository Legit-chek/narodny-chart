from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Администратор"
        USER = "user", "Пользователь"
        CLIENT = "client", "Клиент"

    email = models.EmailField("Email", unique=True)
    role = models.CharField("Роль", max_length=16, choices=Roles.choices, default=Roles.USER)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def clean(self):
        super().clean()
        if self.role == self.Roles.ADMIN and not self.is_staff:
            raise ValidationError("Администратор должен иметь признак staff.")

    def save(self, *args, **kwargs):
        if self.is_superuser or self.is_staff:
            self.role = self.Roles.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_client(self) -> bool:
        return self.role == self.Roles.CLIENT

    @property
    def is_regular_user(self) -> bool:
        return self.role == self.Roles.USER

    def get_dashboard_url(self) -> str:
        if self.role == self.Roles.CLIENT:
            return reverse("clients:dashboard")
        if self.role == self.Roles.ADMIN:
            return reverse("core:admin-dashboard")
        return reverse("accounts:dashboard")


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    company_name = models.CharField("Компания", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    website = models.URLField("Сайт", blank=True)
    about = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self) -> str:
        return self.company_name or self.user.get_full_name() or self.user.username
