from django.core.exceptions import ValidationError

MAX_INSPECTION_EVIDENCE_SIZE = 15 * 1024 * 1024
ALLOWED_INSPECTION_EVIDENCE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf"}


def validate_inspection_file_extension(file_obj):
    extension = file_obj.name.rsplit(".", 1)[-1].lower() if "." in file_obj.name else ""
    if extension not in ALLOWED_INSPECTION_EVIDENCE_EXTENSIONS:
        raise ValidationError("Unsupported file extension for inspection evidence.")


def validate_inspection_file_size(file_obj):
    if getattr(file_obj, "size", 0) > MAX_INSPECTION_EVIDENCE_SIZE:
        raise ValidationError("Inspection evidence file is too large.")
