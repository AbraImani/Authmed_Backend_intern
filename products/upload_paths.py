from pathlib import Path
import re


def normalize_upload_filename(filename):
    """Return a stable lowercase filename safe for storage paths."""
    base_name = Path(filename).name.lower().strip()
    base_name = re.sub(r"[^a-z0-9._-]+", "-", base_name)
    base_name = re.sub(r"-+", "-", base_name).strip("-._")
    return base_name or "file"


def product_reference_cover_upload_to(instance, filename):
    organization_id = getattr(instance, "organization_id", None) or "unassigned"
    reference_id = getattr(instance, "id", None) or "draft"
    return f"organizations/{organization_id}/references/{reference_id}/cover/{normalize_upload_filename(filename)}"


def product_reference_image_upload_to(instance, filename):
    organization_id = getattr(getattr(instance, "product_reference", None), "organization_id", None) or "unassigned"
    reference_id = getattr(instance, "product_reference_id", None) or "draft"
    image_type = getattr(instance, "image_type", None) or "image"
    return f"organizations/{organization_id}/references/{reference_id}/{image_type}/{normalize_upload_filename(filename)}"
