from django.conf import settings


def resolve_enabled_steps(overrides=None):
    defaults = {"ocr": True, "comparison": True, "scoring": True, "ai_enrichment": False}
    configured = getattr(settings, "INSPECTION_INTELLIGENCE_STEPS", {})
    for values in (configured, {} if overrides is None else overrides):
        if not isinstance(values, dict):
            raise ValueError("enabled_steps must be an object of boolean flags.")
        if set(values) - set(defaults) or any(type(value) is not bool for value in values.values()):
            raise ValueError("Unknown processing step or non-boolean flag.")
        defaults.update(values)
    return defaults
