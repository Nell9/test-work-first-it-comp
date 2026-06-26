from django.db.models import ProtectedError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.response import Response

from .filters import RecordFilter
from .models import Category, Record, Status, Subcategory, Type
from .serializers import (
    CategorySerializer,
    RecordSerializer,
    StatusSerializer,
    SubcategorySerializer,
    TypeSerializer,
)


class ProtectOnDeleteMixin:
    """Аккуратно обрабатываем удаление элемента справочника, который используется.

    Например, нельзя удалить тип, по которому уже заведены записи ДДС —
    вместо 500-й ошибки отдаём понятное сообщение и статус 409.
    """

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Нельзя удалить: элемент используется в других записях."},
                status=http_status.HTTP_409_CONFLICT,
            )


class StatusViewSet(ProtectOnDeleteMixin, viewsets.ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer


class TypeViewSet(ProtectOnDeleteMixin, viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class CategoryViewSet(ProtectOnDeleteMixin, viewsets.ModelViewSet):
    queryset = Category.objects.select_related("type").all()
    serializer_class = CategorySerializer
    # Позволяет фронту запросить категории конкретного типа: /api/categories/?type=1
    filterset_fields = ["type"]


class SubcategoryViewSet(ProtectOnDeleteMixin, viewsets.ModelViewSet):
    queryset = Subcategory.objects.select_related("category").all()
    serializer_class = SubcategorySerializer
    # /api/subcategories/?category=1
    filterset_fields = ["category"]


class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.select_related(
        "status", "type", "category", "subcategory"
    ).all()
    serializer_class = RecordSerializer
    filterset_class = RecordFilter


# --- Страницы (отдают HTML-шаблоны, вся динамика — на JS через API выше) ---
# ensure_csrf_cookie нужен, чтобы в браузере появилась кука csrftoken,
# которую JS подставляет в заголовок при POST/PUT/DELETE.


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RecordListView(TemplateView):
    template_name = "cashflow/record_list.html"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RecordCreateView(TemplateView):
    template_name = "cashflow/record_form.html"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RecordEditView(TemplateView):
    template_name = "cashflow/record_form.html"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ReferencesView(TemplateView):
    template_name = "cashflow/references.html"
