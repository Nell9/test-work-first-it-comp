from django.core.management.base import BaseCommand

from cashflow.models import Category, Status, Subcategory, Type


class Command(BaseCommand):
    """Заполняет справочники демо-данными из примеров ТЗ.

    Запуск: python manage.py seed_demo
    Команду можно вызывать повторно — дубликаты не создаются (get_or_create).
    """

    help = "Заполнить справочники примерами данных из ТЗ"

    def handle(self, *args, **options):
        # Статусы
        for name in ["Бизнес", "Личное", "Налог"]:
            Status.objects.get_or_create(name=name)

        # Типы
        income, _ = Type.objects.get_or_create(name="Пополнение")
        expense, _ = Type.objects.get_or_create(name="Списание")

        # Категории и подкатегории из примера. Обе категории — расходные,
        # «Маркетинг» по ТЗ относится к типу «Списание».
        structure = {
            expense: {
                "Инфраструктура": ["VPS", "Proxy"],
                "Маркетинг": ["Farpost", "Avito"],
            },
        }
        for type_obj, categories in structure.items():
            for category_name, subcategories in categories.items():
                category, _ = Category.objects.get_or_create(
                    type=type_obj, name=category_name
                )
                for sub_name in subcategories:
                    Subcategory.objects.get_or_create(
                        category=category, name=sub_name
                    )

        self.stdout.write(self.style.SUCCESS("Демо-данные загружены."))
