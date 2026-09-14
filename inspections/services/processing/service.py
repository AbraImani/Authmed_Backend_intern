import logging

from django.db import transaction

from inspections.models import BatchInspection, InspectionProcessingRun
from .config import resolve_enabled_steps

logger = logging.getLogger(__name__)


class InspectionProcessingService:
    """Create idempotent runs; dispatch through an injected transport."""

    def __init__(self, enqueue_run):
        self.enqueue_run = enqueue_run

    def _dispatch(self, run_id, enabled_steps):
        try:
            self.enqueue_run(run_id, enabled_steps)
        except Exception:
            logger.exception("Unable to dispatch inspection run %s", run_id)
            with transaction.atomic():
                run = InspectionProcessingRun.objects.select_for_update().get(pk=run_id)
                if run.status == "queued":
                    run.explanation = "Processing transport unavailable; analysis was not started."
                    run.scoring_summary = {"status": "dispatch_unavailable", "requires_review": True}
                    run.save(update_fields=["explanation", "scoring_summary", "updated_at"])
                    run.mark_failed("dispatch_unavailable")

    def schedule(self, inspection: BatchInspection, triggered_by=None, enabled_steps=None):
        enabled_steps = resolve_enabled_steps(enabled_steps)
        with transaction.atomic():
            inspection = BatchInspection.objects.select_for_update().get(pk=inspection.pk)
            active = inspection.processing_runs.filter(status__in=["queued", "processing"]).order_by("-created_at").first()
            if active is not None:
                active.append_log("Duplicate processing request ignored.", level="warning")
                active.save(update_fields=["processing_log", "updated_at"])
                return active, False
            run = InspectionProcessingRun.objects.create(inspection=inspection, created_by=triggered_by)
            run.mark_queued()
            transaction.on_commit(lambda: self._dispatch(run.id, enabled_steps))
        run.refresh_from_db()
        return run, True
