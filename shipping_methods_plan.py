import datetime

from django.db import models
from django.utils.translation import ugettext as _
from polymorphic.models import PolymorphicModel

from shoop.apps.provides import get_provide_objects
from shoop.core.fields import MoneyValueField
from shoop.core.models import Shop
from shoop.utils.properties import MoneyPropped, PriceProperty


def get_shipping_behavior_models():
    return get_provide_objects("shipping_behavior_models")


class Carrier(PolymorphicModel):
    shop = models.ForeignKey(Shop)
    name = models.CharField()

    def get_shipping_services(self):
        """
        :rtype: list[ShippingService]
        """
        return []


class ShippingService(object):
    def __init__(self, identifier, name, behaviors):
        """
        Initialize shipping service.

        :type identifier: str
        :type name: str
        :type behaviors: list[ShippingBehavior]
        """
        self.identifier = identifier
        self.name = name
        self.behaviors = behaviors


class ShippingMethod(models.Model):
    carrier = models.ForeignKey(Carrier)

    # Initialized from ShippingService.identifier
    carrier_service_identifier = models.CharField()

    def get_price_for(self, source):
        """
        :rtype: shoop.core.pricing.Price
        """
        if not self.behaviors:
            return self.carrier.shop.create_price(0)
        return sum(
            behavior.get_price_for(source)
            for behavior in self.behaviors.all())

    def get_shipping_time_for(self, source):
        """
        :rtype: ShippingTimeRange|None
        """
        times = set()
        for behavior in self.behaviors.all():
            shipping_time = behavior.get_shipping_time_for(source)
            if shipping_time:
                times.add(shipping_time.min_time)
                times.add(shipping_time.max_time)
        if not times:
            return None
        return ShippingTimeRange(min(times), max(times))

    def is_available_for(self, source):
        if not self.enabled:
            return False
        if not self.behaviors:
            return None
        return all(
            behavior.is_available_for(source)
            for behavior in self.behaviors.all())


class ShippingBehavior(PolymorphicModel):
    name = None

    owner = models.ForeignKey(ShippingMethod, related_name="behaviors")

    def get_price_for(self, source):
        return self.owner.carrier.shop.create_price(0)

    def get_shipping_time_for(self, source):
        """
        :rtype: ShippingTimeRange|None
        """
        return None

    def is_available_for(self, source):
        return True


class ConstantPriceShippingBehavior(MoneyPropped, ShippingBehavior):
    price_value = MoneyValueField()
    price = PriceProperty(
        'price_value', 'owner.carrier.shop.currency',
        'owner.carrier.shop.prices_include_tax')


class WeightPricedShippingBehavior(ShippingBehavior):

    def calculate_price(self, order_source):
        return order_source.weight * 1000  # haha php javascript


class SmartPostTurku(WeightPricedtBusinessLogic):
    name = "kek"
    description = "kekbur"
    kerroin = "100x 1kilo"


class SmartpostHelsinki(WeightPricedtBusinessLogic):
    name = "heasa"
    description = "stadi"


class ShippingTimeRange(object):
    def __init__(self, min_time, max_time=None):
        assert isinstance(min_time, datetime.timedelta)
        assert max_time is None or isinstance(max_time, datetime.timedelta)
        assert max_time is None or max_time >= min_time
        self.min_time = min_time
        self.max_time = max_time if max_time is not None else min_time

    def __str__(self):
        if self.min_time == self.max_time:
            return _("%s days") % (self.max_time.days,)
        return _("%(min)s--%(max)s days") % {
            "min": self.min_time.days, "max": self.max_time.days}
