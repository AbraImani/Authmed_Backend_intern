from .base import BaseInferenceProvider


class FakeInferenceProvider(BaseInferenceProvider):
    provider_name = "fake-inference"

    def infer(self, context):
        return {
            "provider_name": self.provider_name,
            "enabled": True,
            "inspection_id": getattr(context.inspection, "id", None),
            "message": "Fake inference provider used as a stable placeholder.",
            "evidence_count": len(getattr(context, "evidence_items", [])),
        }
