from rest_framework import serializers

from .models import Category, Record, Status, Subcategory, Type


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["id", "name"]


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ["id", "name"]


class CategorySerializer(serializers.ModelSerializer):
    # Имя типа отдаём для удобства фронтенда, чтобы не делать лишний запрос.
    type_name = serializers.CharField(source="type.name", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "type", "type_name"]


class SubcategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Subcategory
        fields = ["id", "name", "category", "category_name"]


class RecordSerializer(serializers.ModelSerializer):
    # Текстовые поля для таблицы на главной — чтобы не дёргать справочники по id.
    status_name = serializers.CharField(source="status.name", read_only=True)
    type_name = serializers.CharField(source="type.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    subcategory_name = serializers.CharField(source="subcategory.name", read_only=True)

    class Meta:
        model = Record
        fields = [
            "id",
            "date",
            "status",
            "status_name",
            "type",
            "type_name",
            "category",
            "category_name",
            "subcategory",
            "subcategory_name",
            "amount",
            "comment",
        ]

    def validate(self, attrs):
        """Серверная проверка логических зависимостей между справочниками.

        При PATCH часть полей может не прийти — тогда берём значение из
        уже сохранённой записи (self.instance).
        """
        instance = self.instance

        def current(field):
            if field in attrs:
                return attrs[field]
            return getattr(instance, field, None)

        type_ = current("type")
        category = current("category")
        subcategory = current("subcategory")

        # Категория должна относиться к выбранному типу.
        if category is not None and type_ is not None and category.type_id != type_.id:
            raise serializers.ValidationError(
                {"category": "Категория не относится к выбранному типу."}
            )

        # Подкатегория должна принадлежать выбранной категории.
        if (
            subcategory is not None
            and category is not None
            and subcategory.category_id != category.id
        ):
            raise serializers.ValidationError(
                {"subcategory": "Подкатегория не относится к выбранной категории."}
            )

        return attrs
