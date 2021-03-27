import enum


__all__ = ['CourierType', 'CourierEarningCoefficient']


@enum.unique
class CourierType(enum.IntEnum):
    foot = 10
    bike = 15
    car = 50


@enum.unique
class CourierEarningCoefficient(enum.IntEnum):
    foot = 2
    bike = 5
    car = 9
