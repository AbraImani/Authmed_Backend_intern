def validate_product_reference_csv_headers(fieldnames):
    fieldnames = {name for name in (fieldnames or []) if name}
    if not any(alias in fieldnames for alias in ("name", "product_name", "brand_name")):
        return ["CSV must include a product name column such as 'name', 'product_name', or 'brand_name'."]
    return []
