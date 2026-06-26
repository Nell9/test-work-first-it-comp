from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from cashflow.models import Category, Record, Status, Subcategory, Type


class ApiTestData(APITestCase):
    """Общий набор справочников для API-тестов."""

    def setUp(self):
        self.business = Status.objects.create(name="Бизнес")

        self.expense = Type.objects.create(name="Списание")
        self.income = Type.objects.create(name="Пополнение")

        # Дерево для типа «Списание».
        self.marketing = Category.objects.create(name="Маркетинг", type=self.expense)
        self.avito = Subcategory.objects.create(name="Avito", category=self.marketing)
        self.farpost = Subcategory.objects.create(
            name="Farpost", category=self.marketing
        )

        # Дерево для типа «Пополнение» — для проверок несоответствий.
        self.sales = Category.objects.create(name="Продажи", type=self.income)
        self.retail = Subcategory.objects.create(name="Розница", category=self.sales)

    def valid_payload(self, **overrides):
        payload = {
            "type": self.expense.id,
            "category": self.marketing.id,
            "subcategory": self.avito.id,
            "amount": "1000.00",
        }
        payload.update(overrides)
        return payload


class SmokeTests(ApiTestData):
    """«Дымовые» тесты: основные эндпоинты вообще отвечают."""

    def test_list_endpoints_return_200(self):
        for url in [
            "/api/records/",
            "/api/statuses/",
            "/api/types/",
            "/api/categories/",
            "/api/subcategories/",
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, url)

    def test_pages_load(self):
        record = Record.objects.create(
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=500,
        )
        for url in [
            "/",
            "/records/new/",
            f"/records/{record.id}/edit/",
            "/references/",
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, url)

    def test_pages_set_csrf_cookie(self):
        response = self.client.get("/")
        self.assertIn("csrftoken", response.cookies)


class RecordCrudTests(ApiTestData):
    """Полный цикл работы с записью через API."""

    def test_create_record(self):
        response = self.client.post(
            "/api/records/", self.valid_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Record.objects.count(), 1)
        # В ответе есть текстовые поля для таблицы.
        self.assertEqual(response.data["type_name"], "Списание")
        self.assertEqual(response.data["category_name"], "Маркетинг")
        self.assertEqual(response.data["subcategory_name"], "Avito")

    def test_create_defaults_date_to_today(self):
        response = self.client.post(
            "/api/records/", self.valid_payload(), format="json"
        )
        self.assertEqual(response.data["date"], date.today().isoformat())

    def test_create_with_custom_date_and_status(self):
        payload = self.valid_payload(date="2025-01-01", status=self.business.id)
        response = self.client.post("/api/records/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["date"], "2025-01-01")
        self.assertEqual(response.data["status_name"], "Бизнес")

    def test_retrieve_record(self):
        record = Record.objects.create(
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=1000,
        )
        response = self.client.get(f"/api/records/{record.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], record.id)

    def test_update_record(self):
        record = Record.objects.create(
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=1000,
        )
        payload = self.valid_payload(subcategory=self.farpost.id, amount="2500.50")
        response = self.client.put(
            f"/api/records/{record.id}/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record.refresh_from_db()
        self.assertEqual(record.subcategory, self.farpost)
        self.assertEqual(str(record.amount), "2500.50")

    def test_delete_record(self):
        record = Record.objects.create(
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=1000,
        )
        response = self.client.delete(f"/api/records/{record.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Record.objects.count(), 0)


class RecordValidationTests(ApiTestData):
    """Серверная валидация обязательных полей и бизнес-правил."""

    def test_amount_required(self):
        payload = self.valid_payload()
        del payload["amount"]
        response = self.client.post("/api/records/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_type_category_subcategory_required(self):
        for field in ["type", "category", "subcategory"]:
            payload = self.valid_payload()
            del payload[field]
            response = self.client.post("/api/records/", payload, format="json")
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST, field
            )
            self.assertIn(field, response.data)

    def test_amount_must_be_positive(self):
        response = self.client.post(
            "/api/records/", self.valid_payload(amount="0"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_status_is_optional(self):
        response = self.client.post(
            "/api/records/", self.valid_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["status"])

    def test_category_must_belong_to_type(self):
        # Категория «Продажи» относится к «Пополнению», а тип указан «Списание».
        payload = self.valid_payload(category=self.sales.id)
        response = self.client.post("/api/records/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)

    def test_subcategory_must_belong_to_category(self):
        # Подкатегория «Розница» не относится к «Маркетингу».
        payload = self.valid_payload(subcategory=self.retail.id)
        response = self.client.post("/api/records/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subcategory", response.data)


class RecordFilterTests(ApiTestData):
    """Фильтрация списка записей."""

    def setUp(self):
        super().setUp()
        self.old = Record.objects.create(
            date=date(2025, 1, 1),
            status=self.business,
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=100,
        )
        self.new = Record.objects.create(
            date=date(2025, 6, 1),
            type=self.income,
            category=self.sales,
            subcategory=self.retail,
            amount=200,
        )

    def test_filter_by_date_range(self):
        response = self.client.get(
            "/api/records/?date_from=2025-05-01&date_to=2025-12-31"
        )
        ids = [row["id"] for row in response.data]
        self.assertEqual(ids, [self.new.id])

    def test_filter_by_status(self):
        response = self.client.get(f"/api/records/?status={self.business.id}")
        ids = [row["id"] for row in response.data]
        self.assertEqual(ids, [self.old.id])

    def test_filter_by_type(self):
        response = self.client.get(f"/api/records/?type={self.income.id}")
        ids = [row["id"] for row in response.data]
        self.assertEqual(ids, [self.new.id])

    def test_filter_by_category_and_subcategory(self):
        response = self.client.get(f"/api/records/?category={self.marketing.id}")
        self.assertEqual([row["id"] for row in response.data], [self.old.id])
        response = self.client.get(f"/api/records/?subcategory={self.retail.id}")
        self.assertEqual([row["id"] for row in response.data], [self.new.id])


class ReferenceApiTests(ApiTestData):
    """CRUD по справочникам и фильтрация зависимостей."""

    def test_create_status(self):
        response = self.client.post(
            "/api/statuses/", {"name": "Налог"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_category_with_type(self):
        response = self.client.post(
            "/api/categories/",
            {"name": "Инфраструктура", "type": self.expense.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type_name"], "Списание")

    def test_categories_filtered_by_type(self):
        response = self.client.get(f"/api/categories/?type={self.expense.id}")
        names = [row["name"] for row in response.data]
        self.assertEqual(names, ["Маркетинг"])

    def test_subcategories_filtered_by_category(self):
        response = self.client.get(
            f"/api/subcategories/?category={self.marketing.id}"
        )
        names = sorted(row["name"] for row in response.data)
        self.assertEqual(names, ["Avito", "Farpost"])

    def test_cannot_delete_type_in_use(self):
        Record.objects.create(
            type=self.expense,
            category=self.marketing,
            subcategory=self.avito,
            amount=1000,
        )
        response = self.client.delete(f"/api/types/{self.expense.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        # Тип на месте.
        self.assertTrue(Type.objects.filter(id=self.expense.id).exists())

    def test_can_delete_unused_status(self):
        response = self.client.delete(f"/api/statuses/{self.business.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_type_with_categories(self):
        # У типа есть категории — даже без записей удалять нельзя, иначе
        # дерево справочника удалилось бы каскадом.
        response = self.client.delete(f"/api/types/{self.expense.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Type.objects.filter(id=self.expense.id).exists())

    def test_cannot_delete_category_with_subcategories(self):
        response = self.client.delete(f"/api/categories/{self.marketing.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Category.objects.filter(id=self.marketing.id).exists())

    def test_can_delete_empty_category(self):
        empty = Category.objects.create(name="Прочее", type=self.expense)
        response = self.client.delete(f"/api/categories/{empty.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
