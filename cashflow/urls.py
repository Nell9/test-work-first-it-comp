from django.urls import path

from . import views

# Страницы веб-приложения.
urlpatterns = [
    path("", views.RecordListView.as_view(), name="record_list"),
    path("records/new/", views.RecordCreateView.as_view(), name="record_create"),
    path("records/<int:pk>/edit/", views.RecordEditView.as_view(), name="record_edit"),
    path("references/", views.ReferencesView.as_view(), name="references"),
]
