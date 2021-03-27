from rest_framework import serializers


class UintListField(serializers.ListField):
    child = serializers.IntegerField(min_value=0)


class StringListField(serializers.ListField):
    child = serializers.CharField(max_length=11)


class FluentAPIMixin:
    """
    Mixin, расширяющий api сериализаторов
    - позволяет не вызывать is_valid на сериализаторе отдельным методом
    """

    def load(self):
        """
        Метод, валидирующий и десериализующий входные данные в словарь

        Examples:
            validated_data = Serializer(data=request.data).load()
        """
        self.is_valid(raise_exception=True)
        return self.validated_data

    def load_and_save(self):
        """
        Метод, валидирующий данные и сохраняющий/обновляющий объект в бд

        Examples:
            Create:
                created_obj = Serializer(data=request.data).load_and_save()

            Update:
                updated_obj = Serializer(instance=old_to_update, data=request.data, partial=False).load_and_save()
        """
        self.is_valid(raise_exception=True)
        return self.save()


class Serializer(FluentAPIMixin, serializers.Serializer):
    pass


class ModelSerializer(FluentAPIMixin, serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(ModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
