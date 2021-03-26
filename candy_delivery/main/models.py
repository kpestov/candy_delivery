import enum

from collections import namedtuple
from itertools import groupby

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Subquery

from datetimerange import DateTimeRange

from .exceptions import Http400
from .utils import cast_hours_to_objects, remove_time_intervals_over_current_time


@enum.unique
class CourierType(enum.IntEnum):
    foot = 10
    bike = 15
    car = 50


OrderDeliveryHours = namedtuple('OrderDeliveryHours', 'start end')
CourierWorkingHours = namedtuple('CourierWorkingHours', 'start end')

# todo: проверить везьде, чтобы расчет чисел был в decimal, либо во float


class Courier(models.Model):
    """
    Модель курьера
    Attributes:
        courier_type - тип курьера. Возможные значения: foot, bike, car
        working_hours  - график работы курьера (массив строк: [HH:MM-HH:MM, ...])
    """

    courier_type = models.CharField(max_length=4)
    working_hours = ArrayField(models.CharField(max_length=11), blank=True, default=list)

    def __str__(self):
        return f'[pk: {self.pk}] [courier_type: {self.courier_type}] [working_hours: {self.working_hours}]'

    @property
    def rating(self):
        return

    @property
    def earnings(self):
        return

    @property
    def max_load(self):
        return getattr(CourierType, self.courier_type).value

    def has_valid_working_hours(self, today):
        remove_time_intervals_over_current_time(self, 'working_hours', today=today)
        return True if self.working_hours else False

    @staticmethod
    def _group_orders_by_region(data, key_func=lambda x: x.region_id):
        groped_orders = {}
        data = sorted(data, key=key_func)
        for key, group in groupby(data, key_func):
            groped_orders[key] = sorted(list(group), key=lambda x: (x.weight, x.delivery_hours[0].end))
        return groped_orders

    def _get_ini_orders(self):
        return (
            Order.objects
            .filter(region_id__in=Subquery(self.regions.values('id')))
            .filter(weight__lte=self.max_load)
            .filter(courier_id__isnull=True)
            .filter(complete_time__isnull=True)
            .filter(assign_time__isnull=True)
        )

    def _is_working_hours_overlap(self, delivery_hours):
        for order_interval in delivery_hours:
            for courier_interval in self.working_hours:
                courier_time = DateTimeRange(courier_interval.start, courier_interval.end)
                order_time = DateTimeRange(order_interval.start, order_interval.end)
                time_delta = courier_time.intersection(order_time)

                if time_delta.is_valid_timerange():
                    if time_delta.timedelta.seconds:
                        return True
        return False

    def get_suitable_orders(self, today):
        result = list(self.get_current_assigned_orders().all())
        if not self.working_hours:
            return result

        cast_hours_to_objects(self, 'working_hours', CourierWorkingHours, today)

        # если рабочий день курьера закончился, то возвращаем []
        if not self.has_valid_working_hours(today):
            return result

        ini_orders = self._get_ini_orders()
        for order in ini_orders:
            cast_hours_to_objects(order, 'delivery_hours', OrderDeliveryHours, today)

        filtered_orders = [
            order for order in ini_orders
            if order.is_possible_to_deliver(today)
        ]

        grouped_orders = self._group_orders_by_region(filtered_orders)
        self.add_order(grouped_orders, result, today)

        return result

    def get_current_assigned_orders(self):
        return (
            Order.objects
            .filter(courier_id=self.pk)
            .filter(assign_time__isnull=False)
            .filter(complete_time__isnull=True)
        )

    def add_order(self, grouped_orders, couriers_orders, today):
        # todo: сделать так, чтобы в метод попадал только объект заказа и все!
        current_load = 0
        current_assigned_orders = self.get_current_assigned_orders()
        if current_assigned_orders:
            current_load = sum([order.weight for order in current_assigned_orders])

        space_left = self.max_load - current_load

        for _, orders in grouped_orders.items():
            for order in orders:
                if space_left:
                    if self._is_working_hours_overlap(order.delivery_hours) and order.weight <= space_left:
                        couriers_orders.append(order)
                        order.assign_time = today
                        space_left -= order.weight
                else:
                    return couriers_orders


class Region(models.Model):
    """
    Модель района, в котором может работать курьер
    Attributes:
        couriers - курьеры, работающие в данном районе
    """
    couriers = models.ManyToManyField(Courier, related_name='regions', db_table='main_region_m2m_courier')

    def __str__(self):
        return f'[pk: {self.pk}]'

    @classmethod
    def create_new_regions(cls, regions_to_add: set):
        regions_from_db = cls.objects.filter(id__in=regions_to_add).values_list('id', flat=True)
        if len(regions_to_add) != len(regions_from_db):
            regions_to_write = regions_to_add.difference(set(regions_from_db))
            cls.objects.bulk_create([Region(id=region_id) for region_id in regions_to_write])


class OrderQuerySet(models.QuerySet):
    def one_or_400(self):
        queryset = list(self)
        queryset_len = len(queryset)

        if queryset_len == 1:
            return queryset[0]
        elif queryset_len == 0:
            raise Http400
        else:
            raise Http400
            # todo: logger "Multiple rows were found for one_or_none()"


class Order(models.Model):
    """
    Модель заказа
    Attributes:
        weight - вес заказа в кг. Ограничения по весу: 0.01 <= weight <= 50
        region - район, в который необходимо доставить заказ
        courier - курьер, который должен доставить заказ
        assign_time - время назначения заказа
        complete_time - время выполнения заказа
        delivery_hours - временные промежутки, в которые клиенту удобно принять заказ (массив строк: [HH:MM-HH:MM, ...])
    """
    # todo: сделать проверку на уровне базы и на уровне сериализации то, чтобы assign_time было < complete_time
    # todo: не забыть сделать join во всех запросах, чтобы не дублировать запросы к базе
    weight = models.DecimalField(max_digits=4, decimal_places=2)
    region = models.ForeignKey(Region, related_name='orders', on_delete=models.SET_NULL, null=True)
    courier = models.ForeignKey(Courier, related_name='orders', on_delete=models.SET_NULL, null=True)
    assign_time = models.DateTimeField(null=True)
    complete_time = models.DateTimeField(null=True)
    delivery_hours = ArrayField(models.CharField(max_length=11), blank=False, default=list)

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'[pk: {self.pk}] [region: {self.region}] [courier: {self.courier}]'

    def is_possible_to_deliver(self, today):
        remove_time_intervals_over_current_time(self, 'delivery_hours', today=today)
        return True if self.delivery_hours else False
