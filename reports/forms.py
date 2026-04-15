from django import forms

from charts.models import Genre, RatingSnapshot
from core.forms import StyledFormMixin
from clients.models import ClientContract


class SalesReportFilterForm(StyledFormMixin, forms.Form):
    start_date = forms.DateField(label="Дата от", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(label="Дата до", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    status = forms.ChoiceField(
        label="Статус договора",
        required=False,
        choices=[("", "Все"), *ClientContract.Statuses.choices],
    )


class PopularityFilterForm(StyledFormMixin, forms.Form):
    genre = forms.ModelChoiceField(
        label="Жанр",
        queryset=Genre.objects.all(),
        required=False,
        empty_label="Все жанры",
    )


class RatingSnapshotForm(StyledFormMixin, forms.Form):
    title = forms.CharField(label="Название снимка", max_length=255)
    genre = forms.ModelChoiceField(
        label="Жанр",
        queryset=Genre.objects.all(),
        required=False,
        empty_label="Все жанры",
    )
    rating_type = forms.ChoiceField(label="Тип рейтинга", choices=RatingSnapshot.Types.choices)
