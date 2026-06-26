from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Status(models.Model):
    """Справочник статусов записи (Бизнес, Личное, Налог...).

    Значения по ТЗ — расширяемые, поэтому статус вынесен в отдельную таблицу,
    а не сделан перечислением в коде.
    """

    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Type(models.Model):
    """Справочник типов операции (Пополнение, Списание...). Тоже расширяемый."""

    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        verbose_name = "Тип"
        verbose_name_plural = "Типы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    """Категория. Привязана к типу — например, «Маркетинг» относится к «Списанию».

    Одно и то же название категории допускается в разных типах, поэтому
    уникальность задаётся парой (тип, название).
    """

    name = models.CharField("Название", max_length=100)
    # PROTECT, чтобы нельзя было удалить тип, под которым ещё висят категории —
    # иначе целое дерево справочника удалилось бы молча.
    type = models.ForeignKey(
        Type,
        verbose_name="Тип",
        on_delete=models.PROTECT,
        related_name="categories",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["type", "name"], name="unique_category_per_type"
            )
        ]

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    """Подкатегория. Привязана к категории (VPS/Proxy -> Инфраструктура)."""

    name = models.CharField("Название", max_length=100)
    # Аналогично категории: не даём удалить категорию с подкатегориями.
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        on_delete=models.PROTECT,
        related_name="subcategories",
    )

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_subcategory_per_category"
            )
        ]

    def __str__(self):
        return self.name


class Record(models.Model):
    """Запись о движении денежных средств (ДДС)."""

    # Дата проставляется автоматически (сегодня), но её можно поменять руками.
    date = models.DateField("Дата записи", default=timezone.localdate)
    # Статус необязателен: в ТЗ среди обязательных полей его нет.
    status = models.ForeignKey(
        Status,
        verbose_name="Статус",
        on_delete=models.PROTECT,
        related_name="records",
        null=True,
        blank=True,
    )
    type = models.ForeignKey(
        Type,
        verbose_name="Тип",
        on_delete=models.PROTECT,
        related_name="records",
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        on_delete=models.PROTECT,
        related_name="records",
    )
    subcategory = models.ForeignKey(
        Subcategory,
        verbose_name="Подкатегория",
        on_delete=models.PROTECT,
        related_name="records",
    )
    amount = models.DecimalField(
        "Сумма",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    comment = models.TextField("Комментарий", blank=True)

    class Meta:
        verbose_name = "Запись ДДС"
        verbose_name_plural = "Записи ДДС"
        # Свежие записи — сверху.
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} — {self.amount} р."
