from django.db import models
from polymorphic.models import PolymorphicModel

from shoop.apps.provides import get_provide_objects


def get_business_logic_models():
    return get_provide_objects("shipping_business_logic_models")


class Carrier(models.Model):
    name = models.CharField()


class ServiceProviderModule(object):
    def get_service_choices():
        pass
        # voisi palauttaa esim.
        return [
            ("joku-identifier", "Joku toimitus"),
            ("toinen", "Toinen toimitus"),
        ]


class CarrierModule(ServiceProviderModule):
    pass


class PaymentProcessorModule(ServiceProviderModule):  # vanha PaymentMethodModule
    pass


class ShippingBusinessLogic(PolymorphicModel):
    name = None

    class Meta:
        abtract = True

    def get_price_for(self, source):
        pass

    def get_shipping_time_for(self, source):
        """
        :rtype: ShippingTimeRange
        """
        pass

    def is_available_for(self, source):
        if not self.shipping_method.enabled:
            return False
        return True


class ConstantPriceBusinessLogic(ShippingBusinessLogic):
    price = YoungMoneyField()


class WeightPricedtBusinessLogic(ShippingBusinessLogic):

    def calculate_price(self, order_source):
        return order_source.weight * 1000  # haha php javascript


class SmartPostTurku(WeightPricedtBusinessLogic):
    name = "kek"
    description = "kekbur"
    kerroin = "100x 1kilo"


class SmartpostHelsinki(WeightPricedtBusinessLogic):
    name = "heasa"
    description = "stadi"


class ShippingMethod(models.Model):
    carrier = models.ForeignKey(Carrier)
    carrier_module_identifier = models.CharField()
    carrier_module_service_identifier = models.CharField()

    business_logic = models.ForeignKey(
        ShippingBusinessLogic, on_delete=models.SET_NULL)

    def get_price_for(self, source):
        if not self.business_logic:
            return None
        return self.business_logic.get_price_for(source)

    def get_shipping_time_for(self, source):
        """
        :rtype: ShippingTimeRange
        """
        if not self.business_logic:
            return None
        return self.business_logic.get_shipping_time_for(source)
        pass

    def is_available_for(self, source):
        if not self.business_logic:
            return None
        return self.business_logic.is_available_for(source)


class ShippingTimeRange(object):
    @property
    def min_time(self):
        """
        :rtype: datetime.timedelta
        """

    @property
    def max_time(self):
        """
        :rtype: datetime.timedelta
        """

    def __str__(self):
        return _("%(min)s--%(max)s days") % {
            "min": self.min_time.days, "max": self.max_time.days
        }

