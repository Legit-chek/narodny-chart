from django import forms
from django.db import transaction

from accounts.models import ClientProfile
from clients.models import AdPlacement, ClientContract, ContractItem, Service
from core.forms import StyledFormMixin


class ClientContractForm(StyledFormMixin, forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        label="Услуги",
        queryset=Service.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ClientContract
        fields = ("title", "company_name", "contact_phone", "description", "services")

    def save(self, user, commit=True):
        with transaction.atomic():
            contract = super().save(commit=False)
            contract.client = user
            if commit:
                contract.save()
                items = [
                    ContractItem(
                        contract=contract,
                        service=service,
                        quantity=1,
                        unit_price=service.price,
                    )
                    for service in self.cleaned_data["services"]
                ]
                ContractItem.objects.bulk_create(items)
                contract.recalculate_total()
        return contract


class AdPlacementForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AdPlacement
        fields = (
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
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser and user.role != user.Roles.ADMIN:
            self.fields["contract"].queryset = ClientContract.objects.filter(client=user)

    def clean(self):
        cleaned_data = super().clean()
        placement_type = cleaned_data.get("placement_type")
        poll = cleaned_data.get("poll")
        contract = cleaned_data.get("contract")

        if placement_type == AdPlacement.Types.POLL_SPOT and not poll:
            self.add_error("poll", "Для платного места в опросе выберите конкретное голосование.")
        if contract and self.user and contract.client_id != self.user.id and not self.user.is_staff:
            self.add_error("contract", "Можно использовать только собственные договоры.")
        return cleaned_data

    def save(self, commit=True):
        placement = super().save(commit=False)
        if self.user:
            placement.client = self.user
        if commit:
            placement.save()
        return placement


class ClientProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ("company_name", "phone", "website", "about")
