"""Job lifecycle transition rules and helpers."""
from __future__ import annotations

from datetime import datetime

from src.schemas.base import JobStatusEnum


TERMINAL_STATUSES = {
    JobStatusEnum.COMPLETED.value,
    JobStatusEnum.FAILED.value,
    JobStatusEnum.ABORTED.value,
}


ALLOWED_TRANSITIONS = {
    JobStatusEnum.QUEUED.value: {
        JobStatusEnum.PROCESSING.value,
        JobStatusEnum.ABORTED.value,
        JobStatusEnum.FAILED.value,
    },
    JobStatusEnum.PROCESSING.value: {
        JobStatusEnum.COMPLETED.value,
        JobStatusEnum.FAILED.value,
        JobStatusEnum.ABORTED.value,
    },
    JobStatusEnum.COMPLETED.value: set(),
    JobStatusEnum.FAILED.value: set(),
    JobStatusEnum.ABORTED.value: set(),
}


def is_terminal(status: str | None) -> bool:
    """Return True if status is terminal."""
    return (status or "") in TERMINAL_STATUSES


def can_transition(current_status: str | None, next_status: str) -> bool:
    """Return whether a transition is valid based on lifecycle rules."""
    current = current_status or ""
    if current == next_status:
        return True
    return next_status in ALLOWED_TRANSITIONS.get(current, set())


def apply_transition(
    job,
    next_status: str,
    *,
    error_message: str | None = None,
    result_payload: dict | None = None,
    set_completed_at: bool = True,
) -> None:
    """Apply a validated status transition to an EvaluationJob model object."""
    current = getattr(job, "status", None)
    if not can_transition(current, next_status):
        raise ValueError(f"Invalid job status transition: {current} -> {next_status}")

    job.status = next_status
    if error_message is not None:
        job.error_message = error_message
    if result_payload is not None:
        job.result_payload = result_payload
    if set_completed_at and is_terminal(next_status):
        job.completed_at = datetime.utcnow()
