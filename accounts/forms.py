from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.text import slugify

from accounts.models import User
from core.forms import StyledFormMixin


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.EmailField(label="Email")


class UserRegistrationForm(StyledFormMixin, UserCreationForm):
    name = forms.CharField(label="Имя", max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(
            [
                "name",
                "email",
                "password1",
                "password2",
            ]
        )

        self.fields["name"].help_text = ""
        self.fields["email"].help_text = ""
        self.fields["password1"].help_text = "Минимум 8 символов."
        self.fields["password2"].help_text = ""

        self.fields["name"].widget.attrs["placeholder"] = "Например, Анна"
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def _build_unique_username(self) -> str:
        base_name = self.cleaned_data["name"].strip()
        base_username = slugify(base_name, allow_unicode=True).replace("-", "_")
        if not base_username:
            email_prefix = self.cleaned_data["email"].split("@", 1)[0]
            base_username = slugify(email_prefix, allow_unicode=True).replace("-", "_") or "user"

        candidate = base_username[:150]
        counter = 2
        while User.objects.filter(username=candidate).exists():
            suffix = f"_{counter}"
            candidate = f"{base_username[:150 - len(suffix)]}{suffix}"
            counter += 1
        return candidate

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._build_unique_username()
        user.first_name = self.cleaned_data["name"].strip()
        user.email = self.cleaned_data["email"].lower()
        user.role = User.Roles.USER
        if commit:
            user.save()
        return user
