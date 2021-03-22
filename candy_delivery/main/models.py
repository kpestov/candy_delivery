import enum
from django.db import models
from django.contrib.postgres.fields import ArrayField


@enum.unique
class CourierType(enum.IntEnum):
    foot = 10
    bike = 15
    car = 50


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

    @classmethod
    def get_suitable_orders(cls, courier_id):
        pass


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
    region = models.ForeignKey(Region, related_name='orders', on_delete=models.SET_NULL, null=True)
    courier = models.ForeignKey(Courier, related_name='orders', on_delete=models.SET_NULL, null=True)
    assign_time = models.DateTimeField(null=True)
    complete_time = models.DateTimeField(null=True)
    delivery_hours = ArrayField(models.CharField(max_length=11), blank=False, default=list)

    def __str__(self):
        return f'[pk: {self.pk}] [region: {self.region}] [courier: {self.courier}]'
