from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import ValidationError

from .region import RegionSerializer
from .. import base_serializers

from ..models import Order
from ..utils import validate_time_intervals


class OrderSerializer(base_serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='id', required=True)
    weight = serializers.DecimalField(max_digits=4, decimal_places=2, required=True)
    region = serializers.IntegerField(required=True)
    delivery_hours = base_serializers.StringListField(required=True)

    class Meta:
        model = Order
        fields = ('order_id', 'weight', 'region', 'delivery_hours', 'courier_id')

    def validate_delivery_hours(self, time_intervals):
        return validate_time_intervals(time_intervals)

    def validate_weight(self, value):
        min_weight, max_weight = 0.01, 50.0
        if not (min_weight <= float(value) <= max_weight):
            raise ValidationError(f'Weight of the order must be within the limits of {min_weight} and {max_weight}')
        return value


class OrderListSerializer(base_serializers.Serializer):
    data = OrderSerializer(many=True)

    class Meta:
        fields = ('data', )

    def _bulk_create_orders(self, validated_orders):
        return Order.objects.bulk_create([
            Order(
                id=validated_order_data.get('id'),
                weight=validated_order_data.get('weight'),
                region_id=validated_order_data.get('region'),
                delivery_hours=validated_order_data.get('delivery_hours'),

            ) for validated_order_data in validated_orders
        ])

    def create(self, data):
        validated_orders = data.get('data')
        with transaction.atomic():
            RegionSerializer.bulk_create_regions(validated_orders, obj_key='region')
            created_orders = self._bulk_create_orders(validated_orders)
        return created_orders


class OrderListSerializerOut(base_serializers.Serializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        fields = ('id',)


class OrdersAssignSerializer(base_serializers.ModelSerializer):
    courier_id = serializers.IntegerField(required=True)

    class Meta:
        model = Order
        fields = ('courier_id',)

    def update(self, instances, validated_data):
        courier_id = validated_data.get('courier_id')

        with transaction.atomic():
            for instance in instances:
                instance.courier_id = courier_id
            Order.objects.bulk_update(instances, ['courier_id', 'assign_time'])
        return instances


class OrderCompleteSerializer(base_serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('complete_time',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.complete_time = validated_data.get('complete_time')
            instance.save()
        return instance


class OrderArgsSerializer(base_serializers.Serializer):
    courier_id = serializers.IntegerField(required=True)
    order_id = serializers.IntegerField(required=True)
    complete_time = serializers.DateTimeField(required=True)

    class Meta:
        fields = ('courier_id', 'order_id', 'complete_time')
