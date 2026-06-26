import django_filters

from .models import Record


class RecordFilter(django_filters.FilterSet):
    """Фильтры для списка записей ДДС.

    Дата фильтруется периодом (от/до), остальное — точным совпадением по
    справочникам, как и просили в ТЗ.
    """

    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Record
        fields = ["date_from", "date_to", "status", "type", "category", "subcategory"]
