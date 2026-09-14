from django.db import transaction

from inspections.models import BatchInspection, InspectionProcessingRun
from inspections.tasks import process_inspection_run


class InspectionProcessingService:
    """Create idempotent processing runs and queue them asynchronously."""

    def schedule(self, inspection: BatchInspection, triggered_by=None, enabled_steps=None):
        with transaction.atomic():
            locked_inspection = BatchInspection.objects.select_for_update().get(pk=inspection.pk)
            active_run = (
                locked_inspection.processing_runs.filter(status__in=["queued", "processing"]).order_by("-created_at").first()
            )
            if active_run is not None:
                active_run.append_log("Duplicate processing request ignored.", level="warning")
                return active_run, False

            run = InspectionProcessingRun.objects.create(
                inspection=locked_inspection,
                created_by=triggered_by,
                status="pending",
                current_stage="ocr",
            )
            run.mark_queued(stage="ocr")
            enabled_steps = enabled_steps or {}
            transaction.on_commit(lambda: process_inspection_run.delay(run.id, enabled_steps))
            return run, True
