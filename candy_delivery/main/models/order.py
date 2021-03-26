import logging

from django.db import models
from django.contrib.postgres.fields import ArrayField

from ..exceptions import APIError, Http400
from ..utils import remove_time_intervals_over_current_time

logger = logging.getLogger(__name__)


__all__ = ['Order']


class OrderQuerySet(models.QuerySet):
    def one_or_400(self):
        queryset = list(self)
        queryset_len = len(queryset)

        if queryset_len == 1:
            return queryset[0]
        elif queryset_len == 0:
            raise Http400
        else:
            logger.error('Multiple rows were found for one_or_400()')
            raise Http400


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

    weight = models.DecimalField(max_digits=4, decimal_places=2)
    region = models.ForeignKey('Region', related_name='orders', on_delete=models.SET_NULL, null=True)
    courier = models.ForeignKey('Courier', related_name='orders', on_delete=models.SET_NULL, null=True)
    assign_time = models.DateTimeField(null=True)
    complete_time = models.DateTimeField(null=True)
    delivery_hours = ArrayField(models.CharField(max_length=11), blank=False, default=list)

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'[pk: {self.pk}] [region: {self.region}] [courier: {self.courier}]'

    def save(self, *args, **kwargs):
        if self.complete_time < self.assign_time:
            raise APIError("complete_time can't be less than assign_time")
        super().save(*args, **kwargs)

    def is_possible_to_deliver(self, today):
        remove_time_intervals_over_current_time(self, 'delivery_hours', today=today)
        return True if self.delivery_hours else False
