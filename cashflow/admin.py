from django.contrib import admin

from .models import Category, Record, Status, Subcategory, Type


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "type"]
    list_filter = ["type"]
    search_fields = ["name"]


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    list_filter = ["category"]
    search_fields = ["name"]


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "status",
        "type",
        "category",
        "subcategory",
        "amount",
        "comment",
    ]
    list_filter = ["date", "status", "type", "category", "subcategory"]
    search_fields = ["comment"]
    date_hierarchy = "date"
