from itertools import chain

from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import ValidationError

from .. import base_serializers
from ..serializers.region import RegionSerializer
from ..models import Courier, CourierType, Region
from ..utils import validate_time_intervals


class CourierSerializerIn(base_serializers.Serializer):
    courier_id = serializers.IntegerField(required=True)

    class Meta:
        fields = ('courier_id',)


class CourierSerializer(base_serializers.ModelSerializer):
    courier_id = serializers.IntegerField(source='id', required=True)
    courier_type = serializers.ChoiceField(required=True, choices=[field.name for field in CourierType])
    regions = base_serializers.UintListField(min_length=1, default=list)
    working_hours = base_serializers.StringListField(default=list)

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'regions', 'working_hours')

    def validate_working_hours(self, time_intervals):
        return validate_time_intervals(time_intervals)


class CourierSerializerOut(CourierSerializer):
    courier_id = serializers.IntegerField(source='pk', read_only=True)
    regions = RegionSerializer(many=True)

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'working_hours', 'regions')


class CourierListSerializerOut(base_serializers.Serializer):
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
                id=validated_courier_data.get('id'),
                courier_type=validated_courier_data.get('courier_type'),
                working_hours=validated_courier_data.get('working_hours'),

            ) for validated_courier_data in validated_couriers
        ])

    def _bulk_create_couriers_regions(self, validated_couriers):
        region_to_courier_links = []
        for validated_courier_data in validated_couriers:
            courier_id, courier_regions = validated_courier_data.get('id'), validated_courier_data.get('regions')
            for region_id in courier_regions:
                new_region_courier = Region.couriers.through(
                    courier_id=courier_id,
                    region_id=region_id,
                )
                region_to_courier_links.append(new_region_courier)
        Region.couriers.through.objects.bulk_create(region_to_courier_links)

    def create(self, data):
        validated_couriers = data.get('data')
        with transaction.atomic():
            created_couriers = self._bulk_create_couriers(validated_couriers)

            RegionSerializer.bulk_create_regions(validated_couriers, obj_key='regions')
            self._bulk_create_couriers_regions(validated_couriers)
        return created_couriers


class UpdateCourierArgsSerializer(CourierSerializer):
    courier_type = serializers.ChoiceField(required=False, choices=[field.name for field in CourierType])
    regions = base_serializers.UintListField(min_length=1, default=list, required=False)
    working_hours = base_serializers.StringListField(required=False)

    class Meta:
        model = Courier
        fields = ('courier_type', 'regions', 'working_hours')

    def validate(self, data):
        if not data.get('courier_type') and not data.get('regions') and not data.get('working_hours'):
            raise ValidationError()
        return data

    def update(self, instance, validated_data):
        regions_to_update = validated_data.get('regions')

        with transaction.atomic():
            for key, value in validated_data.items():
                if key != 'regions':
                    setattr(instance, key, value)

            if regions_to_update:
                current_regions = instance.regions.values_list('id', flat=True)
                regions_to_add = set(regions_to_update).difference(set(current_regions))

                Region.create_new_regions(regions_to_add)

                regions_to_remove = set(current_regions).difference(set(regions_to_update))
                regions_to_add = regions_to_add.union(set(current_regions))

                instance.regions.set(regions_to_add)
                instance.regions.through.objects.filter(region_id__in=regions_to_remove).delete()

            instance.save()

        return instance
