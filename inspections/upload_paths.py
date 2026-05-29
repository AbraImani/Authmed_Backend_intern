from pathlib import Path
import re


def normalize_upload_filename(filename):
    base_name = Path(filename).name.lower().strip()
    base_name = re.sub(r"[^a-z0-9._-]+", "-", base_name)
    base_name = re.sub(r"-+", "-", base_name).strip("-._")
    return base_name or "file"


def inspection_evidence_upload_to(instance, filename):
    organization_id = getattr(getattr(instance, "inspection", None), "organization_id", None) or "unassigned"
    inspection_id = getattr(instance, "inspection_id", None) or "draft"
    evidence_type = getattr(instance, "evidence_type", None) or "evidence"
    return f"organizations/{organization_id}/inspections/{inspection_id}/evidence/{evidence_type}/{normalize_upload_filename(filename)}"
