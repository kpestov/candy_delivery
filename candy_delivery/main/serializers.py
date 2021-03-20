from itertools import chain

from django.db import transaction
from rest_framework import serializers

from . import base_serializers
from .models import Courier, CourierType, Region


class UintListField(serializers.ListField):
    child = serializers.IntegerField(min_value=0)


class StringListField(serializers.ListField):
    child = serializers.CharField(max_length=11)


class CourierSerializer(base_serializers.ModelSerializer):
    courier_id = serializers.IntegerField(source='id', required=True)
    courier_type = serializers.ChoiceField(required=True, choices=[field.name for field in CourierType])
    regions = UintListField(min_length=1, default=list)
    working_hours = StringListField(default=list)
    # todo: написать валидацию на формат промежутков врмени working_hours (HH:MM-HH:MM)

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'regions', 'working_hours')


class CourierSerializerOut(base_serializers.Serializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        fields = ('id',)


class CourierListSerializer(base_serializers.Serializer):
    data = CourierSerializer(many=True)

    class Meta:
        fields = ('data', )

    def _bulk_create_couriers(self, validated_couriers):
        return Courier.objects.bulk_create([
            Courier(
                id=validated_courier_data['id'],
                courier_type=validated_courier_data['courier_type'],
                working_hours=validated_courier_data['working_hours'],

            ) for validated_courier_data in validated_couriers
        ])

    def _bulk_create_regions(self, validated_couriers):
        region_ids = [
            validated_courier_data.get('regions')
            for validated_courier_data in validated_couriers
        ]
        Region.objects.bulk_create([
            Region(id=region_id) for region_id in set(chain.from_iterable(region_ids))
        ])

    def create(self, data):
        validated_couriers = data.get('data')
        with transaction.atomic():
            created_couriers = self._bulk_create_couriers(validated_couriers)
            self._bulk_create_regions(validated_couriers)
        return created_couriers
