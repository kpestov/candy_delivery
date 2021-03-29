import logging
import operator

from collections import namedtuple
from itertools import groupby
from typing import (
    Iterable, List, Dict
)
from datetime import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Subquery

from datetimerange import DateTimeRange

from ..utils import (
    cast_hours_to_objects, remove_time_intervals_over_current_time
)
from .enums import (
    CourierEarningCoefficient, CourierType
)
from .order import Order

logger = logging.getLogger(__name__)


__all__ = ['Courier', 'Region', 'OrderDeliveryHours', 'CourierWorkingHours']


OrderDeliveryHours = namedtuple('OrderDeliveryHours', 'start end')
CourierWorkingHours = namedtuple('CourierWorkingHours', 'start end')


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
    def rating(self) -> float:
        """
        Рассчитывает рейтинг курьера.
        Рейтинг рассчитывается следующим образом:
        (60*60 - min(t, 60*60))/(60*60) * 5,
        где t - минимальное из средних времен доставки по районам (в секундах), t = min(td[1], td[2], ..., td[n])
        td[i] - среднее время доставки заказов по району i (в секундах)
        """
        min_average_time_by_regions = min(self.get_average_delivery_times_by_region())
        result = (60 * 60 - min(min_average_time_by_regions, 60 * 60)) / (60 * 60) * 5
        return round(result, 2)

    @property
    def earnings(self) -> int:
        """
        Рассчитывает заработок курьера.
        Заработок рассчитывается как сумма оплаты за каждый завершенный развоз:
        sum = ∑(500 * C) ,
        C — коэффициент, зависящий от типа курьера (пеший — 2, велокурьер — 5, авто — 9) на момент формирования развоза
        """
        self.get_completed_orders().count()
        return 500 * self.get_completed_orders().count() * getattr(CourierEarningCoefficient, self.courier_type)

    @staticmethod
    def get_orders_delivery_times(orders: Iterable['Order']) -> List[float]:
        """
        Рассчитывает вреия доставки всех заказов курьера.
        Время доставки одного заказа определяется как разница между временем окончания этого заказа
        и временем окончания предыдущего заказа
        (или временем назначения заказов, если вычисляется время для первого заказа)
        """
        complete_times = [
            order.complete_time
            for order in sorted(orders, key=lambda x: x.complete_time, reverse=True)
        ]
        # добавляем время назначения первого заказа
        complete_times.append(orders[-1].assign_time)

        return [
            delivery_time.total_seconds()
            for delivery_time in map(
                lambda x: operator.sub(*x),
                zip(complete_times[:-1], complete_times[1:])
            )
        ]

    def get_average_delivery_times_by_region(self) -> List[float]:
        """Рассчитывает среднее время доставки (в секундах) заказов по всем районам, в которых работает курьер"""
        result = []
        orders_by_region = self._group_orders_by_region(
            data=self.get_completed_orders()
        )
        for _, orders in orders_by_region.items():
            orders_delivery_times = self.get_orders_delivery_times(orders)
            result.append(
                    sum(orders_delivery_times)/len(orders_delivery_times)
            )
        return result

    @property
    def max_weight(self) -> int:
        """Максимальный вес, который может унести курьер"""
        return getattr(CourierType, self.courier_type).value

    def has_valid_working_hours(self, today: datetime) -> bool:
        """Проверяет, может ли курьер в принципе выйти на работу"""
        remove_time_intervals_over_current_time(self, 'working_hours', today=today)
        return True if self.working_hours else False

    @staticmethod
    def _group_orders_by_region(data: Iterable['Order'], key_func=lambda x: x.region_id) -> Dict[int, List['Order']]:
        """Выполняет группировку заказов курьера по районам"""
        groped_orders = {}
        data = sorted(data, key=key_func)
        for key, group in groupby(data, key_func):
            groped_orders[key] = list(group)
        return groped_orders

    def _get_ini_orders(self) -> Iterable['Order']:
        """Получает начальные заказы для курьера, которые подходят по весу и району"""
        return (
            Order.objects
            .filter(region_id__in=Subquery(self.regions.values('id')))
            .filter(weight__lte=self.max_weight)
            .filter(courier_id__isnull=True)
            .filter(complete_time__isnull=True)
            .filter(assign_time__isnull=True)
        )

    def _is_working_hours_overlap(self, delivery_hours: Iterable['OrderDeliveryHours']) -> bool:
        """Проверяет пересечение рабочих часов курьера с часами доставки заказов"""
        for order_interval in delivery_hours:
            for courier_interval in self.working_hours:
                courier_time = DateTimeRange(courier_interval.start, courier_interval.end)
                order_time = DateTimeRange(order_interval.start, order_interval.end)
                time_delta = courier_time.intersection(order_time)

                # т.е.проверяем существует ли пересечение в принципе
                if time_delta.is_valid_timerange():
                    # подходит только, если промежутки пересекаются хотя бы на 1 секунду
                    # например: {9:00-18:00} & {18:00-19:00} -> не подходит, {9:00-18:01} & {18:00-19:00} -> подходит
                    if time_delta.timedelta.seconds:
                        return True
        return False

    def get_orders_to_unassign(self, today: datetime) -> Iterable['Order']:
        """Возвращает заказы, которые необходимо снять с курьера, вследствие изменения его атрибутов"""
        result = []
        current_assigned_orders = self.get_assigned_orders()
        cast_hours_to_objects(self, 'working_hours', CourierWorkingHours, today)

        if self.working_hours[-1].end.time() < today.time():
            # т.е. рабочий день курьера уэе закончился
            return current_assigned_orders.all()

        orders_not_passed_by_weight = (
            current_assigned_orders
            .filter(weight__gt=self.max_weight)
        )
        result.extend(orders_not_passed_by_weight.all())

        for order in current_assigned_orders.all():
            # костыль, который связан с отсутствием поддержки not in lookup в django orm
            if order.region_id not in self.regions.values_list('id', flat=True) and order not in result:
                result.append(order)

        if current_assigned_orders:
            for order in current_assigned_orders.all():
                cast_hours_to_objects(order, 'delivery_hours', OrderDeliveryHours, today)
                if not self._is_working_hours_overlap(order.delivery_hours):
                    result.append(order)
        return result

    def get_suitable_orders(self, today: datetime) -> Iterable['Order']:
        """Возвращает подходящие для курьера заказы в зависимости от веса, района и времени доставки"""
        result = list(self.get_assigned_orders().all())
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

    def get_assigned_orders(self):
        """Возвращает заказы, которые были назначены курьеру"""
        return (
            self.orders
            .filter(assign_time__isnull=False)
            .filter(complete_time__isnull=True)
        )

    @property
    def has_completed_orders(self) -> bool:
        """Проверяет, есть ли у курьера хотя бы один завершенный заказ"""
        return True if self.get_completed_orders() else False

    def get_completed_orders(self):
        """Возвращает завершенные заказы курьера"""
        return (
            self.orders
            .filter(assign_time__isnull=False)
            .filter(complete_time__isnull=False)
        )

    def add_order(
            self,
            grouped_orders: Dict[int, List['Order']],
            couriers_orders: List['Order'],
            today: datetime
    ) -> Iterable['Order']:
        """
        Добавляет заказы курьеру, пока у него есть свободное место.
        Если места больше нет, то возвращается текущий набор заказов
        """
        current_weight = 0
        current_assigned_orders = self.get_assigned_orders()
        if current_assigned_orders:
            current_weight = sum([order.weight for order in current_assigned_orders])

        space_left = self.max_weight - current_weight

        for _, orders in grouped_orders.items():
            for order in sorted(orders, key=lambda x: (x.weight, x.delivery_hours[0].end)):
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
        """Метод записывает в базу новые районы из json payload. Если такой район уже есть в базе, то он игнорируется"""
        regions_from_db = cls.objects.filter(id__in=regions_to_add).values_list('id', flat=True)
        if len(regions_to_add) != len(regions_from_db):
            regions_to_write = regions_to_add.difference(set(regions_from_db))
            cls.objects.bulk_create([Region(id=region_id) for region_id in regions_to_write])
