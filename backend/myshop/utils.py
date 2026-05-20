from utils.common import resolve_upload


def upload_product_image(instance, filename):
    """
    Upload product image
    """
    return resolve_upload(instance.product.name, filename, "products")


def upload_product_category_image(instance, filename):
    """
    Upload product category image

    """
    return resolve_upload(instance.name, filename, "products/categories")


def upload_product_brand_image(instance, filename):
    """
    Upload product brand image
    """
    return resolve_upload(instance.name, filename, "products/brands")