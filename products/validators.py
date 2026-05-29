from django.core.exceptions import ValidationError

MAX_REFERENCE_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_REFERENCE_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def validate_reference_image_extension(file_obj):
    extension = file_obj.name.rsplit(".", 1)[-1].lower() if "." in file_obj.name else ""
    if extension not in ALLOWED_REFERENCE_IMAGE_EXTENSIONS:
        raise ValidationError("Unsupported file extension for product reference media.")


def validate_reference_image_file_size(file_obj):
    if getattr(file_obj, "size", 0) > MAX_REFERENCE_IMAGE_SIZE:
        raise ValidationError("Product reference media file is too large.")
