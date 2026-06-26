from datetime import date

from django.db import IntegrityError
from django.test import TestCase

from cashflow.models import Category, Record, Status, Subcategory, Type


class ModelTests(TestCase):
    """Базовые проверки моделей и заданных на уровне БД ограничений."""

    def setUp(self):
        self.expense = Type.objects.create(name="Списание")
        self.marketing = Category.objects.create(name="Маркетинг", type=self.expense)
        self.avito = Subcategory.objects.create(name="Avito", category=self.marketing)

    def test_str_representations(self):
        self.assertEqual(str(self.expense), "Списание")
        self.assertEqual(str(self.marketing), "Маркетинг")
        self.assertEqual(str(self.avito), "Avito")

    def test_record_defaults_date_to_today(self):
        record = Record.objects.create(
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=1000,
        )
        self.assertEqual(record.date, date.today())
        # Статус не обязателен.
        self.assertIsNone(record.status)

    def test_category_name_unique_within_type(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Маркетинг", type=self.expense)

    def test_same_category_name_allowed_in_other_type(self):
        income = Type.objects.create(name="Пополнение")
        # То же имя категории, но другой тип — так можно.
        category = Category.objects.create(name="Маркетинг", type=income)
        self.assertNotEqual(category.id, self.marketing.id)

    def test_subcategory_name_unique_within_category(self):
        with self.assertRaises(IntegrityError):
            Subcategory.objects.create(name="Avito", category=self.marketing)

    def test_status_name_unique(self):
        Status.objects.create(name="Бизнес")
        with self.assertRaises(IntegrityError):
            Status.objects.create(name="Бизнес")
