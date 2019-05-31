from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from prices import Money, TaxedMoney

from ...checkout.models import Checkout
from ...discount.models import SaleQueryset
from . import ZERO_TAXED_MONEY
from .avatax import interface as avatax_interface
from .vatlayer import interface as vatlayer_interface


def get_total_gross(checkout: Checkout, discounts: SaleQueryset) -> TaxedMoney:
    """Calculate total gross for checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_total_gross(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_total_gross(checkout, discounts)

    return checkout.get_total(discounts)


def get_subtotal_gross(checkout: Checkout, discounts: SaleQueryset) -> TaxedMoney:
    """Calculate subtotal gross for checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_subtotal_gross(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_subtotal_gross(checkout, discounts)

    return checkout.get_subtotal(discounts)


def get_shipping_gross(checkout: Checkout, discounts: SaleQueryset) -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    if not checkout.shipping_method:
        return ZERO_TAXED_MONEY
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_shipping_gross(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_shipping_gross(checkout, discounts)
    return checkout.shipping_method.get_total()


def get_lines_with_taxes(checkout: Checkout, discounts):
    lines_taxes = defaultdict(lambda: Decimal("0.0"))

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_lines_with_taxes(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_lines_with_taxes(checkout, discounts)

    return [(line, lines_taxes[line.variant.sku]) for line in checkout.lines.all()]


def apply_taxes_to_shipping(price: Money, shipping_address: "Address") -> TaxedMoney:
    """Apply taxes for shiping methods that user can use during checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.apply_taxes_to_shipping(price, shipping_address)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        # FIXME
        pass
    return TaxedMoney(net=price, gross=price)


def get_tax_rate_type_choices():
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_tax_rate_type_choices()
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return []
    return []


def get_line_total_gross(checkout_line: "CheckoutLine", discounts):
    if settings.VATLAYER_ACCESS_KEY:
        return checkout_line.get_total(discounts)  # FIXME
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_line_total_gross(checkout_line, discounts)
    return checkout_line.get_total(discounts)


def get_order_line_total_gross(order_line: "OrderLine", discounts):
    if settings.VATLAYER_ACCESS_KEY:
        return order_line.variant.get_price(
            discounts
        )  # FIXME unit_price or total_price ?
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_order_line_total_gross(order_line, discounts)
    return order_line.variant.get_price(discounts)  # FIXME unit_price or total_price ?


def apply_taxes_to_variant(variant: "ProductVariant", price: Money, country: "Country"):
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.apply_taxes_to_variant(variant, price, country)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return TaxedMoney(
            net=price, gross=price
        )  # FIXME for know we don't know how to get product prices
    return TaxedMoney(net=price, gross=price)


def apply_taxes_to_product(product: "Product", price: Money, country: "Country"):
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.apply_taxes_to_product(product, price, country)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return TaxedMoney(net=price, gross=price)
    return TaxedMoney(net=price, gross=price)
