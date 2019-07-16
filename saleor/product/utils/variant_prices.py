from ...discount.utils import fetch_active_discounts


def _get_product_minimal_variant_price(product, discounts):
    # Start with the product's price as the minimal one
    minimal_variant_price = product.price
    for variant in product.variants.all():
        variant_price = variant.get_price(discounts=discounts)
        minimal_variant_price = min(minimal_variant_price, variant_price)
    return minimal_variant_price


def update_product_minimal_variant_price(product, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    minimal_variant_price = _get_product_minimal_variant_price(product, discounts)
    if product.minimal_variant_price != minimal_variant_price:
        product.minimal_variant_price = minimal_variant_price
        product.save(update_fields=["minimal_variant_price"])
    return product


def update_products_minimal_variant_prices(products, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    for product in products:
        update_product_minimal_variant_price(product, discounts)


def update_products_minimal_variant_prices_of_discount(discount):
    all_discounts = fetch_active_discounts()
    update_products_minimal_variant_prices(discount.products.all(), all_discounts)
    for category in discount.categories.all():
        update_products_minimal_variant_prices(category.products.all(), all_discounts)
    for collection in discount.collections.all():
        update_products_minimal_variant_prices(collection.products.all(), all_discounts)
