from products.models import ProductReference


DUPLICATE_KEYS = (
    ("name", "name"),
    ("sku", "sku"),
    ("supplier", "supplier__name"),
    ("form", "form"),
    ("strength", "strength"),
    ("pack_size", "pack_size"),
)


def find_product_reference_duplicates(organization, normalized_row):
    """Return candidate duplicate product references for an organization.

    The helper is intentionally conservative and only uses fields already
    available in the reference library, while preserving future import columns
    like GTIN or manufacturer for later phases.
    """
    queryset = ProductReference.objects.filter(organization=organization)
    filters = {}
    for normalized_key, model_lookup in DUPLICATE_KEYS:
        value = normalized_row.get(normalized_key)
        if value:
            filters[model_lookup] = value
    if not filters:
        return []

    matches = queryset.filter(**filters).distinct().select_related("organization", "supplier")
    return [
        {
            "id": obj.id,
            "name": obj.name,
            "sku": obj.sku,
            "supplier": getattr(obj.supplier, "name", None),
            "form": obj.form,
            "strength": obj.strength,
            "pack_size": obj.pack_size,
        }
        for obj in matches
    ]
