"""Application boundary between processing services and Celery transport."""


def enqueue_inspection_run(run_id, enabled_steps):
    from inspections.tasks import process_inspection_run

    return process_inspection_run.delay(run_id, enabled_steps)
